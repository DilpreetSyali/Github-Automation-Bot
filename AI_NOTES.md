# AI Notes

## Tools & Stack

**AI tool used:** Kiro (AI-powered IDE by AWS)

**Stack:**
- Backend: Python 3.11, FastAPI, SQLAlchemy, psycopg2, PyJWT, httpx
- Frontend: Next.js 14 (App Router), TypeScript, React
- Database: PostgreSQL (local dev), Neon Postgres (production)
- Auth: GitHub OAuth App, signed session cookies (JWT)
- Notifications: Slack Incoming Webhooks
- Tunnel (local dev): ngrok

---

## How I Used AI

I used Kiro selectively — primarily as a faster way to write boilerplate I already knew how to write, not as a replacement for understanding the system.

**Where I used Kiro:**
- Initial file scaffolding (models, router stubs, layout shell)
- Generating repetitive CRUD patterns I've written before
- Occasional syntax lookups for SQLAlchemy expressions

**Where I did NOT use Kiro:**
- Architecture and data model decisions (see below)
- Debugging — I diagnosed all issues myself by reading logs and tracing the code
- Security decisions (signature verification order, idempotency strategy, cookie flags)
- Service selection (why Neon, why plain OAuth App, why polling vs. websockets)
- The deployment configuration and environment wiring

Rough split: ~25% AI-assisted (scaffolding, boilerplate), ~75% written and reasoned through by me.

---

## Key Decisions I Made

**1. Separate `events` and `action_logs` tables**

A single webhook delivery can trigger multiple downstream actions — labeling an issue *and* sending a Slack alert. I wanted each action's outcome logged independently so a Slack outage shows up as a failed `action_log` row, not a missing event. This was my call; Kiro's initial suggestion was a single `status` boolean on the event row.

**2. Idempotency at the database layer via `delivery_id` unique constraint**

GitHub re-delivers webhooks on timeout or 5xx. I enforced deduplication using a DB-level unique constraint on the GitHub-provided `X-GitHub-Delivery` header value. An in-memory set would have been simpler to write but wouldn't survive a process restart or redeploy on Render's free tier. I specifically chose the DB constraint because it's durable by default.

**3. Signature verification before any DB write or outbound call**

The webhook handler verifies `X-Hub-Signature-256` (HMAC-SHA256) as the very first thing it does — before parsing the payload, before writing to the DB, before calling GitHub or Slack. This was a deliberate security decision. If verification is done after parsing, a forged request can still cause DB writes. I caught a version of this in an early draft where the signature check was misplaced and moved it to the top.

---

## Hardest Bug

**The `.env` file was silently ignored.**

The backend's `config.py` used `os.environ.get("GITHUB_CLIENT_ID", "")` but never called `load_dotenv()`. FastAPI doesn't auto-load `.env` files — that's a Python-dotenv concern, not a framework concern. The result was every environment variable reading as an empty string, so the GitHub OAuth redirect URL had `client_id=` blank, which GitHub showed as a 404 page.

I noticed it by looking at the actual URL GitHub was showing in the browser — the query parameters were empty despite the `.env` being correctly filled. Once I traced back to `config.py` and saw there was no `load_dotenv()` call, the fix was one line. The lesson: always verify your env loading actually runs, not just that the file exists.

A secondary issue: setting `DATABASE_URL=` (empty string) in `.env` didn't fall back to the SQLite default — an empty string is not the same as an unset variable. SQLAlchemy crashed with `Could not parse URL from string ''`. Fixed by explicitly setting `DATABASE_URL=sqlite:///./dev.db` rather than leaving it blank.

---

## What I'd Improve With More Time

- **Alembic migrations** instead of `create_all` on startup — safer for schema evolution in production
- **GitHub App** (JWT + installation tokens) instead of a plain OAuth App — narrower token scope per installation, cleaner multi-tenant story
- **AI triage stretch goal** — `GEMINI_API_KEY` is already in config; would wire it into the webhook handler to auto-summarize issues, suggest labels, and show priority in the dashboard and Slack messages
- **WebSocket or SSE** instead of 5-second polling for the live event log — reduces unnecessary load and makes updates feel instant
- **Retry visibility** — currently retries are logged but not surfaced in the UI; would show a "retried N times" indicator on failed action rows
