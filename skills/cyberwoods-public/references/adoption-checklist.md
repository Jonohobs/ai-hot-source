# Cyberwoods Public Adoption Checklist

## Pre-Adoption Checks

- Confirm package names on official registries.
- Review repo history: age, commit cadence, maintainer continuity.
- Inspect install hooks and setup scripts.
- Check for unnecessary credential or filesystem access.
- Verify tool identity; avoid duplicate-name confusion.

## Approval Gates

- Require explicit human approval for installs.
- Require explicit human approval for elevated or destructive actions.
- Keep a short written rationale for each approved high-risk action.

## Safe Rollout

- Adopt in smallest possible scope first.
- Prefer pinned versions and lockfiles.
- Re-run a quick security scan after integration.
