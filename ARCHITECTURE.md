# Flii - System Architecture

Flii is an AI-powered scholarship and postgraduate application assistant built with Django, PostgreSQL/SQLite, Celery/Redis, Tailwind CSS, and Google Gemini.

## 1. Core Architecture Principles

1. **AI as Assistant, Human as Owner**: The AI performs information synthesis, matching analysis, and grounded drafting. Consequential actions (submissions, messaging, referee invitations) strictly require human approval.
2. **Ground Truth & Anti-Hallucination**: The AI writes and reasons only using verified facts stored in the user's `ApplicantProfile`, `StoryBank`, and verified `Opportunity` source records.
3. **Strict Multi-Tenant Isolation**: Every document, application, story, and AI interaction is isolated to the authenticated user.
4. **Provider-Agnostic AI Service**: AI capabilities are mediated through `AIService` and abstract `AIProvider` interfaces with structured Pydantic schema validation.

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|   Landing Page | Dashboard | Opportunity Explorer | Workspace | Story Bank | Vault|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                DJANGO APP LAYER                                   |
|   accounts | applicants | opportunities | matching | applications | stories       |
|   documents | notifications | dashboard | agent | ai                              |
+-----------------------------------------------------------------------------------+
        |                                       |                     |
        v                                       v                     v
+------------------+                   +------------------+   +---------------------+
| RELATIONAL DB    |                   | FLII AGENT       |   | CELERY / REDIS      |
| (PostgreSQL/     |                   | - Tools Registry |   | - Deadline Checks   |
|  SQLite)         |                   | - Action Approval|   | - Opportunity Sync  |
+------------------+                   | - Audit Logger   |   | - Async Matching    |
                                       +------------------+   +---------------------+
                                                |
                                                v
                                       +------------------+
                                       |   AI SERVICE     |
                                       | - Grounded KB    |
                                       | - GeminiProvider |
                                       | - Pydantic Parse |
                                       +------------------+
```

## 2. App Responsibilities

- **`accounts`**: User authentication, password reset, profile status, and 7-step onboarding wizard.
- **`applicants`**: Relational models for Education, Employment, Skills, Projects, Achievements, Certifications, Research Interests, Study Goals, and Language Proficiencies.
- **`stories`**: STAR-framework story bank (Situation, Challenge, Action, Result, Lesson, Skills) to supply verified qualitative evidence.
- **`documents`**: Document Vault with file integrity checks, classification (CV, Transcript, Passport, Recommendation, etc.), and secure access control.
- **`opportunities`**: Curated scholarship and fellowship catalog with source verification timestamps, deadlines, eligibility criteria, and extensible `OpportunityDiscoveryService`.
- **`matching`**: Deterministic & AI-assisted matching engine comparing applicant profiles to opportunity constraints, outputting eligibility verdicts and Profile Fit scores.
- **`applications`**: Application lifecycle workspaces (Planning -> Preparing -> In Progress -> Ready for Review -> Submitted -> Offer), requirement matrices, document bindings, and action tasks.
- **`ai`**: `PersonalKnowledgeBase` context compiler, `AIProvider` abstractions, Gemini integration with Pydantic JSON schemas, and AI writing assistant.
- **`agent`**: ReAct/Tool-calling orchestration agent with human-in-the-loop `AgentAction` approvals (Pending, Approved, Rejected) and `AIAuditLog`.
- **`notifications`**: In-app notifications for approaching deadlines, pending approvals, and missing requirements.
- **`dashboard`**: Executive applicant command center aggregating metrics, urgent deadlines, and action items.

## 3. Future Browser Automation Architecture
```
[ApplicationExecutionService]
          |
   [BrowserAgent]
          |
   [PortalAdapter] (e.g. DAADPortal, UniAssistPortal, CheveningPortal)
          |
   Human-in-the-Loop Review & Approval -> Submission
```
The MVP contains the abstract interfaces and simulation hooks for this workflow.
