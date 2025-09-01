- Only write production-ready code, no mock, fake, demo, or placeholder code
- Always write production ready code
- Never create mock data, designs, or code
- when making edits or additions, check any related API endpoints and ensure all are properly connected
- when finished make changes, test build, commit to remote git repo
- Unless explicity required, you (claude) will do everything you can to avoid manual intervention during the process of fixing, update, or editing this project

# Current System Status (August 2025)

## Authentication System Conversion Complete
- **COMPLETED**: Converted from registration-key system to open SaaS authentication
- **Backend**: New `auth_open.py` module with JWT-based registration/login endpoints
- **Frontend**: Registration form updated, email verification pages created
- **Database**: Alembic migration 016 removes registration keys, adds email verification fields
- **Config**: Email verification disabled by default (can be enabled later)

## Current Production Deployment (Render.com)
- **Main API**: https://socialmedia-api-wxip.onrender.com (FastAPI backend)
- **Frontend**: https://socialmedia-frontend-pycc.onrender.com (React app)
- **Database**: PostgreSQL with pgvector extension
- **Redis**: Configured but background worker has memory issues (not critical)

## Known Issues
- **CRITICAL**: Registration and login forms reload the page with empty fields instead of signing users in
- **Background Worker**: Failing due to memory limits (>2GB RAM usage) - non-critical for core functionality
- **Authentication Flow**: Frontend can connect to backend but authentication process fails silently, forms reset

## Recent Changes
- Created `backend/core/security.py` with JWTHandler class
- Fixed router registry import errors
- Updated frontend with new auth pages (EmailVerification, ForgotPassword, ResetPassword)
- All authentication endpoints should be available at `/api/auth/*`
- research the internet to confirm the proper way to fix or produce what youre working on
- Guardrail: production-ready only — no mock/fake/demo data in app code or migrations; mocks allowed in tests only; scan & confirm no banned patterns in the diff.