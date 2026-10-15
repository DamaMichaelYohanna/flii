from django.core.management.base import BaseCommand
from opportunities.models import Opportunity
from opportunities.scanner import ParallelOpportunityScanner


class Command(BaseCommand):
    help = "Concurrently scan, launch, and verify scholarship portal links using parallel AI API"

    def add_arguments(self, parser):
        parser.add_argument(
            '--parallel',
            type=int,
            default=5,
            help='Number of parallel worker threads (default: 5)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of opportunities to scan (0 = all)'
        )

    def handle(self, *args, **options):
        parallel = options['parallel']
        limit = options['limit']

        qs = Opportunity.objects.filter(status='active').order_by('id')
        if limit > 0:
            qs = qs[:limit]

        opps = list(qs)
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"==> Launching parallel AI scan on {len(opps)} scholarship portals with {parallel} workers..."
        ))

        scanner = ParallelOpportunityScanner(timeout=12)
        summary = scanner.scan_opportunities_parallel(opportunities=opps, max_workers=parallel)

        self.stdout.write("\n" + "=" * 90)
        self.stdout.write(f"{'TITLE':<40} {'HTTP':<6} {'STATUS':<10} {'AI READINESS':<16} {'PORTAL TYPE'}")
        self.stdout.write("-" * 90)

        for res in summary['results']:
            http_str = str(res['status_code']) if res['status_code'] else 'ERR'
            is_live_str = "ACTIVE" if res['is_live'] else "DOWN/ERR"
            title_truncated = (res['title'][:37] + "...") if len(res['title']) > 40 else res['title']
            
            style_fn = self.style.SUCCESS if res['is_live'] else self.style.ERROR
            self.stdout.write(style_fn(
                f"{title_truncated:<40} {http_str:<6} {is_live_str:<10} {res['ai_readiness']:<16} {res['portal_type']}"
            ))

        self.stdout.write("=" * 90)
        self.stdout.write(self.style.SUCCESS(
            f"\nScan Summary:\n"
            f"  Total Scanned:        {summary['total_scanned']}\n"
            f"  Active Portals:       {summary['live_count']}\n"
            f"  Ready for AI Apply:   {summary['ready_for_ai']}\n"
            f"  Down/Broken Portals:  {summary['broken_count']}\n"
        ))
