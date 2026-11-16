# Security review — 2026-11-16

Scope: local source review, lockfile advisory scans, PostgreSQL regression tests and Render deployment preparation. No live Render resources were created and no external penetration test was performed. This is not a guarantee that no vulnerabilities exist.

## Findings fixed

| Finding | Remediation |
|---|---|
| Development HTTP settings unsafe for public deployment | Production refuses startup without secure cookies and HTTPS public origin |
| Disabled sessions could become usable again after reactivation | Disable revokes all sessions; authenticated writes read identity after acquiring the transaction lock |
| Unbounded request bodies and parallel password hashing | 16 KiB body cap before parsing; maximum two concurrent Argon2 operations |
| Auth limiter state unbounded and not thread-safe | Locked, bounded 10,000-key limiter; general write limiter added |
| Accumulating login sessions | Expired sessions pruned on login; maximum five sessions per user |
| Local bootstrap stores passwords on ephemeral disk | Production bootstrap reads environment secrets, preserves existing accounts, refuses role collisions, never writes/logs passwords |
| Missing public browser defenses | Production origin checks, HSTS, CSP, no-store private API responses and disabled interactive API documentation |
| Alternate env files/dumps could enter Git | Ignore .env.*, .dump and .backup; keep .env.example |

Retained: Argon2id, opaque hashed session tokens, HttpOnly/SameSite cookies, CSRF, role/owner checks, SQLAlchemy parameterized SQL, React text escaping, input validation, atomic settlement and DB constraints. Reviewed application paths contained no unsafe HTML rendering, untrusted SQL concatenation or unauthenticated privileged endpoints.

## Verification

- pip-audit 2.10.1 against the pinned backend lock: **no known vulnerabilities found**. Used no-deps/disable-pip mode because the lock records installed transitive dependencies. Audit tool isolated from the application environment.
- npm audit against the frontend lock: **0 known vulnerabilities**, including development dependencies.
- **27 tests passed**, including seven added security/deployment cases. One upstream TestClient deprecation warning remains informational.
- TypeScript/Vite production build passed.
- Tracked secret-path review found only .env.example; no tracked .runtime credentials, real env files or private keys. This was not a comprehensive historical secret-scanner audit.

Evidence is in docs/evidence/python-security-audit.json, npm-security-audit.json, security-test-results.txt and pytest.xml.

## Residual limitations

- Single Uvicorn worker; rate limits are in memory and reset on restart. The supplied command does not trust forwarded client-IP headers, so Render proxy traffic may share a limiter bucket. Larger usage needs a verified trusted-proxy strategy and shared rate limiting.
- No email verification, CAPTCHA, password recovery or MFA. Public signups consume storage; ALLOW_REGISTRATION=false can close signup after classroom accounts are created.
- Read traffic and per-account storage are not fully quota-limited. This student application is not hardened against determined distributed denial-of-service/database-filling attacks.
- Free PostgreSQL expires after 30 days and lacks paid backup features. UptimeRobot cannot change this.
- Audits are append-only through APIs, not protected from database administrators.
- Bootstrap env-password changes do not rotate existing hashes. Use distinct strong privileged passwords and never share them with ordinary traders.
- Keep UI/API on one HTTPS origin and update PUBLIC_ORIGIN if the domain changes. Keep secrets out of Git/logs/screenshots.
- Advisory scans are snapshots of known issues. Re-run them before future releases; perform the live smoke checklist after deployment.

Sources: https://render.com/docs/free ; https://render.com/docs/native-runtimes ; https://render.com/docs/python-version ; https://render.com/docs/postgresql-creating-connecting
