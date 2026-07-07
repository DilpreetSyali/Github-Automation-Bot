# AI Notes

## Project Summary

This project is a full-stack GitHub automation bot built with a FastAPI backend and a Next.js frontend.
It supports two automation paths:

- Manual, user-configurable rules from the dashboard
- AI-assisted triage for issue labeling and urgency detection

The system listens to GitHub webhooks, verifies every request with HMAC-SHA256, deduplicates deliveries
with a database unique constraint, and then applies the configured automation flow. For urgent issues,
the bot can also notify Slack.

## Stack

- Backend: Python 3.11, FastAPI, SQLAlchemy, psycopg2, PyJWT, httpx
- Frontend: Next.js 14 (App Router), TypeScript, React
- Database: PostgreSQL locally, Neon Postgres in production
- Auth: GitHub OAuth App with signed session cookies
- Notifications: Slack Incoming Webhooks
- AI: Gemini triage for label suggestion, summary generation, and urgency detection
- Deployment: Render for backend, Vercel for frontend

## How AI Was Used

I used AI as an implementation accelerator, not as a replacement for engineering judgment.

What AI helped with:

- Boilerplate generation for routers, schemas, and UI scaffolding
- Drafting repetitive CRUD and display components
- Speeding up iteration on the issue triage flow
- Helping structure Slack and dashboard output formats

What I verified and designed myself:

- Webhook security and signature verification order
- Idempotency strategy using GitHub delivery IDs
- Data model design for events, actions, repos, and rules
- Deployment wiring for Render, Vercel, and Neon
- Which parts should remain manual rules vs AI automation

## Manual + AI Automation

The final product intentionally includes both options:

- Manual rules let the user define match conditions in the dashboard and trigger labels, comments,
  and Slack notifications based on those rules.
- AI triage reads the issue title and body, infers a label, writes a short summary, and escalates to
  Slack when the issue appears urgent.

That combination was important because it gives the app both deterministic control and intelligent
automation. Manual rules cover exact-match workflows, while AI handles open-ended issue language.

## Key Engineering Decisions

### 1. Separate `events` and `action_logs`

A single webhook delivery can trigger multiple downstream actions. I kept the event record separate
from the action log so each GitHub or Slack action can succeed or fail independently and still be
audited later.

### 2. Database-level idempotency

GitHub redelivers webhooks on retries and timeouts. To prevent duplicate processing, I used the
GitHub `X-GitHub-Delivery` value with a unique constraint in the database instead of relying on
in-memory deduplication.

### 3. Signature verification first

The webhook handler validates `X-Hub-Signature-256` before any database write or outbound API call.
That keeps forged requests from ever reaching downstream logic.

### 4. AI fallback behavior

Because Gemini can hit rate limits on the free tier, I added a fallback classifier so the bot still
produces a label and urgency signal when the model is temporarily unavailable.

## Hardest Bug

The most subtle issue was that environment variables were not being loaded consistently during early
development. The app appeared configured, but the OAuth flow and backend services would fail because
the runtime environment was not matching the local `.env` file.

I resolved that by explicitly loading environment variables in the backend configuration and by making
the deployment setup more explicit for Render and Vercel.

## What I Would Improve With More Time

- Add Alembic migrations instead of relying on startup table creation
- Replace the OAuth App flow with a GitHub App installation flow for tighter repo-scoped permissions
- Add richer AI severity classification, such as priority levels
- Improve the Slack message formatting with cleaner operational summaries
- Replace dashboard polling with WebSockets or Server-Sent Events
- Surface retry counts more clearly in the UI for failed action logs

## Final Status

The project includes the required manual rule-based automation, the AI triage path, the GitHub
dashboard, webhook ingestion, Slack notifications, and production deployment wiring.
It is now in a completed state from a feature standpoint, with the remaining work limited to any
final documentation polish or URL updates.
