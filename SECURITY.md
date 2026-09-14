# Security

JWT authentication is included for the API. Set `YTB_SECRET_KEY` and admin credentials
via `.env` (see `.env.example`) before any non-local deployment. The app logs a warning
if the default secret/password are still in use.

Included by default:

- bcrypt password hashing (bcrypt pinned below 4.1 for passlib compatibility)
- per-user project isolation and ownership checks on every asset/job route
- configurable CORS origins (`CORS_ORIGINS`, comma-separated, `*` for dev)
- configurable upload size cap (`MAX_UPLOAD_BYTES`)
- resolved storage paths constrained to the configured workspace on downloads

For internet-facing deployment add:

- TLS/reverse proxy
- rate limiting
- CSRF protection where applicable
- secret manager
- per-user storage quotas
- sandboxed media workers
- backups
- monitoring and audit logs

Never expose an unauthenticated production API. Do not commit `.env` files.