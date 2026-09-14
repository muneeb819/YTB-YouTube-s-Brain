# Security

JWT authentication is included for the API. Change YTB_SECRET_KEY and admin credentials before deployment.

For internet-facing deployment add:
- TLS/reverse proxy
- stricter CORS
- rate limiting
- CSRF protection where applicable
- per-user storage isolation
- secret manager
- upload size/type limits
- sandboxed media workers
- backups
- monitoring and audit logs

Never expose an unauthenticated production API.
