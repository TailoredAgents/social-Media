# Branch Protection Configuration Guide

## Automated Configuration (When GitHub CLI is available)

Run this command to apply branch protection rules:

```bash
gh auth login
gh api repos/:owner/:repo/branches/master/protection \
  --method PUT \
  --input .github/branch-protection-config.json
```

## Manual Configuration via GitHub Web Interface

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Click **Add rule** or edit existing rule for `master` branch
4. Configure the following settings:

### Required Status Checks
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- Select these required status checks:
  - `Backend Tests / test`
  - `Backend Tests / lint-and-format`
  - `Backend Tests / api-tests`
  - `Frontend CI / test`
  - `Frontend CI / security-scan`
  - `Code Quality / frontend-quality`
  - `Code Quality / backend-quality`
  - `Security Scan / frontend-security`
  - `Security Scan / backend-security`
  - `Security Scan / codeql-analysis`

### Pull Request Requirements
- ✅ Require a pull request before merging
- ✅ Require approvals: **1**
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require approval of the most recent push
- ✅ Require conversation resolution before merging

### Additional Restrictions
- ❌ Do not require administrators to follow these rules
- ❌ Do not restrict pushes that create matching branches
- ❌ Do not allow force pushes
- ❌ Do not allow deletions
- ✅ Allow fork syncing

## Verification

After configuration, test with a pull request to ensure:
- All CI/CD workflows run successfully
- Required approvals are enforced
- Status checks must pass before merge
- Conversation resolution is required

## Configuration File

The complete configuration is stored in `.github/branch-protection-config.json` for reference and automated application.