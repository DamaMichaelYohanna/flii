import re
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional
import requests
from django.utils import timezone
from .models import Opportunity
from ai_core.service import AIService

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

HTTP_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}


class LightweightHTMLTextExtractor(HTMLParser):
    """Zero-dependency HTML text and application link extractor."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.title_parts = []
        self.in_title = False
        self.in_script_or_style = False
        self.extracted_links = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "svg"):
            self.in_script_or_style = True
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower == "a":
            href = dict(attrs).get("href", "")
            if href and href.startswith(("http://", "https://")):
                self.extracted_links.append(href)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "svg"):
            self.in_script_or_style = False
        elif tag_lower == "title":
            self.in_title = False

    def handle_data(self, d):
        if self.in_title:
            self.title_parts.append(d)
        elif not self.in_script_or_style:
            text = d.strip()
            if text:
                self.fed.append(text)

    def get_text(self) -> str:
        return " ".join(self.fed)

    def get_title(self) -> str:
        return " ".join(self.title_parts).strip()


class ParallelOpportunityScanner:
    """
    Intelligent Parallel Verification Scanner:
    - Concurrently launches HTTP GET requests to live scholarship portals with realistic browser headers.
    - Follows redirects and extracts portal text, status codes, and discovered direct application URLs.
    - Feeds live data into AIService for structured portal verification and autonomous AI readiness assessment.
    - Synchronizes Opportunity models with real-world opening dates, deadlines, and portal readiness.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.ai_service = AIService.get_instance()

    def fetch_portal_page(self, url: str) -> Dict[str, Any]:
        """Performs a robust, browser-mimicking HTTP launch to test live status."""
        if not url:
            return {
                "success": False,
                "status_code": 0,
                "final_url": "",
                "title": "",
                "text": "",
                "links": [],
                "error": "Empty URL provided",
            }

        try:
            session = requests.Session()
            response = session.get(
                url,
                headers=HTTP_HEADERS,
                timeout=self.timeout,
                allow_redirects=True,
                verify=True,
            )
            
            status_code = response.status_code
            final_url = response.url
            html_content = response.text or ""

            extractor = LightweightHTMLTextExtractor()
            try:
                extractor.feed(html_content)
                text = extractor.get_text()[:6000]
                page_title = extractor.get_title()
                discovered_links = extractor.extracted_links
            except Exception:
                text = re.sub(r'<[^>]+>', ' ', html_content)[:6000]
                page_title = ""
                discovered_links = []

            return {
                "success": status_code < 400,
                "status_code": status_code,
                "final_url": final_url,
                "title": page_title,
                "text": text,
                "links": discovered_links[:20],
                "error": None if status_code < 400 else f"HTTP {status_code}",
            }

        except requests.exceptions.Timeout:
            logger.warning(f"Connection timeout verifying {url}")
            return {
                "success": False,
                "status_code": 408,
                "final_url": url,
                "title": "",
                "text": "",
                "links": [],
                "error": "Connection timed out",
            }
        except requests.exceptions.RequestException as e:
            logger.warning(f"Connection error verifying {url}: {e}")
            return {
                "success": False,
                "status_code": 502,
                "final_url": url,
                "title": "",
                "text": "",
                "links": [],
                "error": str(e),
            }

    def scan_and_verify_single(self, opportunity: Opportunity, user=None) -> Dict[str, Any]:
        """
        Launches live HTTP fetch on opportunity target URL and feeds into AIService.
        Updates model state in database.
        """
        primary_url = opportunity.application_url or opportunity.official_source_url
        target_url = primary_url

        page_result = self.fetch_portal_page(target_url)

        # If primary application_url failed (e.g. 404 or connection error) but official_source_url exists, fallback to check official guide
        if not page_result["success"] and opportunity.official_source_url and opportunity.official_source_url != primary_url:
            fallback_result = self.fetch_portal_page(opportunity.official_source_url)
            if fallback_result["success"]:
                page_result = fallback_result
                target_url = opportunity.official_source_url

        status_code = page_result["status_code"]
        now = timezone.now()

        # Build prompt payload for AI
        candidate_apply_links = [
            l for l in page_result.get("links", [])
            if any(k in l.lower() for k in ["apply", "application", "portal", "register", "admissions", "embark"])
        ]
        
        extra_context = ""
        if candidate_apply_links:
            extra_context = f"\nCandidate Direct Links on Page: {', '.join(candidate_apply_links[:3])}"

        ai_input_text = (
            f"Page Title: {page_result.get('title')}\n"
            f"Final URL: {page_result.get('final_url')}\n"
            f"{extra_context}\n\n"
            f"{page_result.get('text', '')}"
        )

        # Invoke AIService structured portal verification
        ai_verification = self.ai_service.verify_and_scan_portal(
            url=target_url,
            html_or_text=ai_input_text,
            title=opportunity.title,
            http_status=status_code,
            user=user,
        )

        # Update Opportunity fields
        opportunity.scan_http_status = status_code
        opportunity.last_scanned_at = now
        opportunity.portal_type = ai_verification.portal_type
        opportunity.ai_application_readiness = ai_verification.ai_application_readiness

        if ai_verification.cycle_name:
            opportunity.cycle_name = ai_verification.cycle_name

        # If AI discovered a specific direct apply link, update application_url
        if ai_verification.direct_apply_url and ai_verification.direct_apply_url.startswith("http"):
            if not opportunity.application_url or opportunity.application_url == opportunity.official_source_url:
                opportunity.application_url = ai_verification.direct_apply_url

        # Check for discovered opening date
        if ai_verification.detected_opening_date_iso:
            try:
                op_dt = datetime.datetime.strptime(ai_verification.detected_opening_date_iso, "%Y-%m-%d")
                opportunity.opening_date = timezone.make_aware(op_dt)
            except Exception:
                pass

        # Check for discovered closing date
        if ai_verification.detected_closing_date_iso:
            try:
                cl_dt = datetime.datetime.strptime(ai_verification.detected_closing_date_iso, "%Y-%m-%d")
                opportunity.deadline = timezone.make_aware(cl_dt)
            except Exception:
                pass

        opportunity.save(update_fields=[
            "scan_http_status",
            "last_scanned_at",
            "portal_type",
            "ai_application_readiness",
            "cycle_name",
            "application_url",
            "opening_date",
            "deadline",
            "updated_at",
        ])

        return {
            "opportunity_id": opportunity.id,
            "title": opportunity.title,
            "target_url": target_url,
            "application_url": opportunity.application_url,
            "status_code": status_code,
            "is_live": page_result["success"],
            "portal_type": opportunity.portal_type,
            "ai_readiness": opportunity.ai_application_readiness,
            "cycle_name": opportunity.cycle_name,
            "summary": ai_verification.verification_summary,
            "error": page_result.get("error"),
        }

    def scan_opportunities_parallel(
        self,
        opportunities: Optional[List[Opportunity]] = None,
        max_workers: int = 5,
        user=None,
    ) -> Dict[str, Any]:
        """
        Executes parallel verification across multiple opportunities using ThreadPoolExecutor.
        """
        if opportunities is None:
            opportunities = list(Opportunity.objects.filter(status='active'))

        results = []
        ready_count = 0
        live_count = 0
        broken_count = 0

        logger.info(f"Launching parallel AI portal scan on {len(opportunities)} opportunities (workers={max_workers})...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_opp = {
                executor.submit(self.scan_and_verify_single, opp, user): opp
                for opp in opportunities
            }

            for future in as_completed(future_to_opp):
                opp = future_to_opp[future]
                try:
                    res = future.result()
                    results.append(res)
                    if res["is_live"]:
                        live_count += 1
                    else:
                        broken_count += 1
                    if res["ai_readiness"] == "ready":
                        ready_count += 1
                except Exception as e:
                    logger.error(f"Error scanning {opp.title}: {e}")
                    results.append({
                        "opportunity_id": opp.id,
                        "title": opp.title,
                        "target_url": opp.application_url,
                        "status_code": 0,
                        "is_live": False,
                        "portal_type": opp.portal_type,
                        "ai_readiness": "manual_only",
                        "cycle_name": opp.cycle_name,
                        "summary": f"Scan failed due to unhandled exception: {e}",
                        "error": str(e),
                    })
                    broken_count += 1

        return {
            "total_scanned": len(results),
            "live_count": live_count,
            "ready_for_ai": ready_count,
            "broken_count": broken_count,
            "results": results,
        }
