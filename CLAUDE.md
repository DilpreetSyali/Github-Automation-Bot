# Project context for AI assistants

This is a small full-stack app: FastAPI backend + Next.js frontend, implementing
an event-driven GitHub automation bot (see the assignment PDF/README for full spec).

## Stack
- Backend: FastAPI, SQLAlchemy, Postgres (Neon), deployed on Render.
- Frontend: Next.js 14 (App Router), deployed on Vercel.
- Notifications: Slack Incoming Webhook.
- Auth: GitHub OAuth App (web flow), session = signed JWT in an httpOnly cookie.

## Non-negotiable behaviors (don't regress these)
1. `POST /webhooks/github` MUST verify `X-Hub-Signature-256` via HMAC-SHA256
   before touching the DB or calling any external API.
2. Every webhook delivery is deduped on `Event.delivery_id` (DB unique
   constraint, not an in-memory set) — GitHub redelivers on timeout/5xx.
3. Outbound calls (GitHub write-back, Slack) go through `_retry()` in
   `webhooks.py`, which logs every attempt to `ActionLog`. Don't swap this
   for a fire-and-forget call.
4. Secrets only ever come from environment variables. Never hardcode a
   token/secret, never log `access_token` or webhook payload secrets.
5. Session cookie is httpOnly + secure in production + samesite=lax.

## Where things live
- `backend/app/routers/webhooks.py` — the core event pipeline (signature
  check → idempotent insert → rule matching → GitHub/Slack actions).
- `backend/app/models.py` — schema; `Event` and `ActionLog` are separate
  tables on purpose (one event can trigger multiple actions).
- `frontend/app/dashboard/page.tsx` — single dashboard page, polls
  `/repos/{id}/events` every 5s for a "live" log (no websockets, by design,
  to keep this exercise-scoped).

## Known gaps (intentional, see AI_NOTES.md)
- No Alembic migrations — `Base.metadata.create_all` on startup.
- No GitHub App / JWT installation auth — plain OAuth App only.
- AI triage stretch goal (Gemini) is not wired in yet.
