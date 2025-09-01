# Production Roadmap - Lily AI Social Media Agent

## Executive Summary - What's Left for 100% Autonomy

### Critical Gaps (Top Priority)

1. **App Authentication (No OAuth)**: Replace demo AuthContext and optional Auth0 paths with a first-party email/password system
2. **Replace Stubs/Mocks**: Notifications, metrics, workflow routers still loading stub modules
3. **Social Posting Connectors**: Finalize publish flows for X, , Instagram with token storage, refresh, retries
4. **Autonomous Loop**: Ensure Celery worker + beat schedule daily/weekly workflows
5. **Observability/SRE**: Prometheus endpoint + Sentry tracing, structured logs, dashboard

## PR-01: Run the Real API in Production (No Stubs)

### Files to Modify
- `Dockerfile`
- `app.py`
- `backend/api/notifications_stub.py` → deprecate
- `backend/api/workflow_stub.py` → deprecate
- `backend/api/metrics_stub.py` → replace with real metrics router

### Changes

**Dockerfile:**
```diff
- CMD ["uvicorn", "backend.main_minimal:app", "--host", "0.0.0.0", "--port", "8000"]
+ CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**app.py:**
```diff
- ("notifications_stub", "backend.api.notifications_stub"),
- ("workflow_stub", "backend.api.workflow_stub"),
- ("metrics", "backend.api.metrics_stub"),
+ ("notifications", "backend.api.notifications"),
+ ("workflow", "backend.api.workflow"),
+ ("metrics", "backend.api.performance_monitoring"),
+ ("integration_services", "backend.api.integration_services"),
```

### Acceptance Criteria
- `/` shows loaded_modules without any `*_stub`
- `/docs` lists notifications, workflow, metrics, integrations paths
- Container healthcheck passes; `/health` ok

## PR-02: Application Authentication (No OAuth)

### Backend Implementation
- Add **FastAPI Users** with SQLAlchemy adapter
- Provide endpoints: `/auth/register`, `/auth/jwt/login`, `/auth/jwt/refresh`, `/auth/verify`, `/auth/forgot-password`, `/auth/reset-password`
- Use argon2 hashing and JWT with refresh
- Optional: Enable TOTP 2FA (pyotp) and email verification
- Create Role/Org tables for multi-tenancy

### Frontend Implementation
- Replace `frontend/src/contexts/AuthContext.jsx` demo mode
- Add pages: Login, Register, Forgot/Reset, Verify Email, 2FA
- Store tokens (httpOnly cookie for access token)
- Interceptor to refresh tokens on 401

### Recommended Libraries
- **FastAPI Users** (JWT, SQLAlchemy adapters)
- **SuperTokens FastAPI** (alternative)
- **Ory Kratos** (headless identity, enterprise-ready)

### Acceptance Criteria
- Register/login flow works without Auth0
- JWT verified by backend dependency across protected routers
- Email verification and password reset flow tested end-to-end

## PR-03: Social Platform Connectors

### Backend Requirements

#### Token Storage
- New tables: `SocialAccount` and `OAuthToken`
- Encrypt token fields at rest (Fernet/AES-GCM)

#### Platform-Specific Implementation

**X (Twitter):**
- Use v2 post tweet endpoint and media upload
- Handle INIT/APPEND/FINALIZE flow
- Add backoff on 429 rate limits

**:**
- Register asset → upload → create UGC post
- Support Pages & Member posts

**Instagram Graph:**
- Create container → publish flow
- Support image, carousel, reels

**Facebook Pages:**
- Standard Graph publish endpoints

**TikTok:**
- Business API (if approved)
- Handle rate limits

### Frontend Requirements
- "Connect Accounts" wizard in Settings
- Post composer with media attach, previews, character counters
- Analytics dashboard with graphs per platform

### Acceptance Criteria
- Connect accounts from UI
- Create and publish post with media
- Metrics appear next day

## PR-04: Replace Mock Memory/Embeddings with Production Vector Search

### Option A: pgvector (Recommended)
- Install extension in PostgreSQL
- Add migration for vector columns and indexes
- Use pgvector-python with SQLAlchemy
- Keep dimensions consistent with embedding model

### Option B: FAISS
- Keep FAISSMemorySystem but remove dev fallback
- Persist the index
- Add periodic rebuild

### Acceptance Criteria
- `/api/vector/search` returns real semantically-similar items from DB
- Content generation retrieval uses DB-backed search

## PR-05: Research & Insights - Remove Mock Results

### Changes
- Replace any "mock X//Trends" branches
- Keep Serper for web/news with cache & backoff
- Persist research artifacts (ResearchData, Insight)
- Link to WorkflowExecution

### Acceptance Criteria
- `/api/autonomous/research/latest` returns real results with sources and timestamps

## PR-06: Content Persistence & Scheduling

### Database Changes
- Replace in-memory dict with DB writes
- Tables: `Content`, `ContentItem`, `ScheduledPost`
- Add idempotency keys

### Task Hardening
- Resolve media IDs, chunk uploads, finalize, publish
- Exponential backoff on failure
- Mark as failed and create Notification on permanent error

### Acceptance Criteria
- Creating content persists to DB
- Scheduling enqueues Celery job
- Job publishes and updates status

## PR-07: Orchestrator - Fully Autonomous Daily/Weekly Loops

### Celery Beat Schedule
- `daily_content`
- `weekly_report`
- `nightly_metrics`

### Requirements
- Steps run in separate tasks
- Stream progress via WebSocket/SSE
- Make steps idempotent
- Write WorkflowExecution rows

### Acceptance Criteria
- Logs show daily cycle running without manual triggers
- Frontend receives progress updates

## PR-08: Metrics, Monitoring, Alerts

### Implementation
- Add Prometheus instrumentation endpoint (`/metrics`)
- Add Sentry for errors & traces
- Ship structured JSON logs
- Grafana dashboards

### Code Snippets

**Prometheus:**
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, include_in_schema=False)
```

**Sentry:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.2
)
```

### Acceptance Criteria
- `/metrics` exposes Prometheus metrics
- Sentry dashboard receives errors
- Grafana shows live charts

## PR-09: Notifications (Real Service + UI)

### Requirements
- Tie to real events: publish success/failure, token expiry, workflow state
- Add channels: UI (toast + inbox), email, Slack webhook

### Acceptance Criteria
- Publishing failure raises high-priority notification
- User can mark read/filter

## PR-10: Frontend - Remove Demo Code

### Changes Required
- Replace AuthContext.jsx
- Wire all pages to live APIs:
  - Memory pages call `/api/vector/*`
  - Calendar shows scheduled posts from DB
  - Analytics uses stored metrics
  - Settings → Connect Accounts wizard
- Add WebSocket/SSE for live workflow events

### Acceptance Criteria
- No components rely on demo flags
- Hard refresh shows live data everywhere

## PR-11: Security Hardening & Secrets

### Requirements
- Centralize all secrets
- Encrypt token columns (Fernet)
- Add request rate limiting (slowapi)
- Validate file uploads

### Acceptance Criteria
- Secrets loaded only via env/providers
- No secrets in git
- Rate-limit headers observed

## PR-12: Multi-tenancy & Roles

### Database Changes
- Every row carries `org_id`
- Tables: `Organization`, `Role`, `Membership`
- RBAC: owner/admin/editor/viewer

### Acceptance Criteria
- Users only see their org's data
- Role tests pass

## PR-13: Tests & QA

### Test Strategy
- Remove tests against mock APIs
- Unit tests (pure logic)
- Integration tests with sandbox
- E2E with Playwright

### Acceptance Criteria
- CI green
- Coverage: backend ≥80%, frontend ≥70%
- E2E passes in CI

## PR-14: Documentation & Easy Setup

### Requirements
- One-command setup via `make up`
- First-Run Wizard page
- Clear platform app registration instructions

## Concrete File-Level Fixes Needed Now

1. **Routers** - swap stub modules in app.py
2. **Content Store** - replace dict in content_real.py with DB
3. **Vector Store** - remove mocks, wire pgvector/FAISS
4. **Goals** - migrate file-based to DB models
5. **Dockerfile** - run app:app instead of main_minimal
6. **Monitoring** - add /metrics router
7. **Integrations** - ensure integration_services.py is loaded
8. **Research** - finish Trends/ API calls

## Data Model Additions

### New Tables Required
```sql
-- Organization & Multi-tenancy
Organization(id, name, slug, settings_json)
UserOrganization(user_id, org_id, role)

-- Social Accounts
SocialAccount(id, org_id, user_id, provider, handle, external_account_id, meta)
OAuthToken(account_id, access_token, refresh_token, expires_at, scopes, enc_salt)

-- Content Management
Content(id, org_id, author_id, topic, prompt, tone, context_json, created_at)
ContentItem(id, content_id, platform, body, media_refs_json, status, scheduled_at, posted_at, external_url, external_id)
ScheduledPost(id, content_item_id, run_at, status, attempts, last_error, job_id)

-- Analytics
PlatformMetric(id, org_id, account_id, platform, ts_bucket, metric_name, value)
```

## Deployment Checklist

- [ ] Switch container entrypoint to app:app
- [ ] Configure environment secrets
- [ ] PostgreSQL with pgvector enabled
- [ ] Redis for Celery broker
- [ ] Prometheus & Grafana up
- [ ] Sentry DSN configured

## Suggested Order of Implementation

1. **Phase 1:** PR-01 (routers) + PR-02 (auth)
2. **Phase 2:** PR-06 (content DB) + PR-03 (connectors)
3. **Phase 3:** PR-07 (orchestrator + beat schedules)
4. **Phase 4:** PR-04 (vector store) + PR-05 (research sources)
5. **Phase 5:** PR-08 (observability) + PR-09 (notifications)
6. **Phase 6:** PR-10 (frontend clean wiring)
7. **Phase 7:** PR-11 through PR-14 (security, tenancy, tests, docs)

## End-to-End Acceptance Test

1. Register new user, create org, verify email
2. Connect X, , Instagram accounts
3. Set brand voice + platforms + cadence in Settings
4. Turn on Autopilot
5. Observe Celery beat runs daily_content at 09:00 org local time
6. UI shows scheduled content, published posts, metrics charts
7. After a week: weekly report with trend lines appears

## Key External References

- [FastAPI Users](https://github.com/fastapi-users/fastapi-users)
- [SuperTokens FastAPI](https://supertokens.com/docs/passwordless/pre-built-ui/setup/backend/python-fastapi)
- [Ory Kratos](https://github.com/ory/kratos)
- [X/Twitter API Docs](https://developer.x.com/en/docs/twitter-api)
- [ API Docs](https://learn.microsoft.com/en-us//)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Serper API](https://serper.dev)
- [pgvector](https://github.com/pgvector/pgvector)
- [Prometheus FastAPI](https://pypi.org/project/prometheus-fastapi-instrumentator/)
- [Sentry FastAPI](https://docs.sentry.io/platforms/python/integrations/fastapi/)