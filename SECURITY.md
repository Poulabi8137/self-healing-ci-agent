# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Active |
| 0.x     | ❌ End of life |

## Reporting a Vulnerability

Please report security issues by opening a GitHub Issue with the label `security`.

Do not disclose the vulnerability publicly until it has been addressed. We aim to respond within 48 hours and patch critical issues within 7 days.

## Security Features

- API key authentication with SHA-256 hashing (plaintext keys never persisted)
- Role-based access control: candidate (read-only), recruiter (workflow execution), admin (key management)
- Sliding-window rate limiting on all POST, auth, AI-heavy, and task endpoints
- Request body size limits enforced via Pydantic Field validators
- Sanitized error responses — no internal details leaked to clients
- Circuit breaker prevents cascading failures from external API outages
- CORS restricted to configured origins in production mode
- Secure HTTP headers via Caddy reverse proxy
- Startup validation of critical secrets
- SessionStorage for frontend auth tokens (no localStorage)
