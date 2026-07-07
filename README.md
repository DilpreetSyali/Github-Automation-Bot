# Event-Driven GitHub Automation Bot

A user signs in with GitHub, connects a repo they own, and the bot reacts to
`issues` / `pull_request` / `push` webhooks from that repo: it can add a
label or post a comment back on GitHub, and/or send a Slack alert, based on
rules configured in the dashboard.

## Stack
- **Backend**: FastAPI + SQLAlchemy + Postgres, deployed on Render.
- **Frontend**: Next.js 14 (App Router), deployed on Vercel.
- **DB**: Neon (free Postgres, no card).
 - **Notifications**: Slack OAuth + channel selection, with webhook fallback.
- **Auth**: GitHub OAuth App, session cookie = signed JWT.

## How it works
1. `GET /auth/login` redirects to GitHub OAuth. `/auth/callback` exchanges
   the code for a token, upserts the user, and sets an httpOnly session
   cookie.
2. From the dashboard, the user picks one of their own repos. Connecting a
   repo calls the GitHub API to create a webhook pointed at
   `POST /webhooks/github`, signed with `GITHUB_WEBHOOK_SECRET`.
3. Every inbound webhook is verified via `X-Hub-Signature-256` (HMAC-SHA256)
   **before** anything else happens — unsigned/forged requests get a 401 and
   are never written to the DB.
4. Each delivery is inserted with its GitHub `X-GitHub-Delivery` ID under a
   DB **unique constraint** — if GitHub redelivers the same event (it retries
   on timeout/5xx), the duplicate insert is caught and the event is treated
   as already-processed. Nothing runs twice.
5. Matching rules (event type + field contains/equals a value) trigger:
   add a label, post a comment, and/or send a Slack message. Each outbound
   call is retried up to 3 times with backoff, and every attempt (success or
   failure) is written to `action_logs` — so a Slack or GitHub outage shows
   up as a visible failed action, not a silently dropped event.
6. The dashboard (behind login, scoped to the logged-in user's own repos)
   polls the event log and lets you add/remove rules.
7. PRs are supported too, so pull request webhooks can trigger the same automation flow.

## Live deployment
- **Frontend**: https://github-automation-bot-beta.vercel.app
- **Backend**: https://github-automation-bot-3n85.onrender.com
- **GitHub repo**: https://github.com/DilpreetSyali/Github-Automation-Bot

### How to test the live deployment
1. Visit https://github-automation-bot-beta.vercel.app
2. Sign in with GitHub
3. Connect one of your repos
4. Open an issue on that repo — the bot will auto-label it and send a Slack alert
5. Check the dashboard event log to see everything the bot did


```
backend/    FastAPI app (app/main.py, routers/, models.py)
frontend/   Next.js app (app/page.tsx, app/dashboard/page.tsx)
```

## Run locally

### 1. Create a GitHub OAuth App
Settings → Developer settings → OAuth Apps → New OAuth App.
- Homepage URL: `http://localhost:3000`
- Authorization callback URL: `http://localhost:8000/auth/callback`

### 2. Create a Slack Incoming Webhook
Any Slack workspace → create an app → Incoming Webhooks → Add to channel →
copy the webhook URL.

### 3. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in the values from steps 1-2
uvicorn app.main:app --reload --port 8000
```
Without `DATABASE_URL` set, it falls back to a local `sqlite:///./dev.db` —
fine for local dev, use real Postgres (Neon) in production.

### 4. Frontend
```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
Visit `http://localhost:3000`, sign in with GitHub, connect a repo.

### 5. Triggering a webhook locally
GitHub can't reach `localhost`, so for local testing either:
- Deploy the backend first and point the webhook there, or
- Use a tunnel (ngrok/cloudflared) to expose `localhost:8000` and use that
  URL as `GITHUB_OAUTH_REDIRECT_URL`'s host when connecting a repo.

### Slack setup
To let each user connect their own Slack workspace:
- Create a Slack app with `chat:write`, `channels:read`, `groups:read`, `im:read`, and `mpim:read`.
- Set the redirect URL to `http://localhost:8000/auth/slack/callback`.
- Put `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, and `SLACK_OAUTH_REDIRECT_URL` in `backend/.env`.
- If you want the homepage "Add to Slack" button to point at your app install flow, set `NEXT_PUBLIC_SLACK_CLIENT_ID` in `frontend/.env.local`.
- In the dashboard, click `Connect Slack`, authorize Slack, then choose a channel.
- If Slack shows `invalid_team_for_non_distributed_app`, activate public distribution in the Slack app settings before testing installs from other workspaces.

## Environment variables
See `backend/.env.example` and `frontend/.env.example`. Never commit a real
`.env` — only `.env.example` with placeholders is in the repo.

## Deployment
- **Backend → Render**: New Web Service from this repo, root directory
  `backend`. Build command `pip install -r requirements.txt`, start command
  is read from `Procfile` (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
  `runtime.txt` pins Python 3.11.9. Add all backend env vars in Render's
  dashboard, with `GITHUB_OAUTH_REDIRECT_URL` and `FRONTEND_URL` pointing at
  the real deployed URLs.
- **Frontend → Vercel**: import this repo, root directory `frontend`,
  add `NEXT_PUBLIC_API_URL` pointing at the Render backend URL.
- **DB → Neon**: create a free Postgres project, copy the connection string
  into `DATABASE_URL` on Render.
- Update the GitHub OAuth App's callback URL to the real Render URL once
  deployed.
- Update the Slack app redirect URL to the deployed backend
  `/auth/slack/callback`.

## Security / reliability notes (see quality bar in the assignment)
- Signature verification happens before any DB write or GitHub/Slack call.
- Idempotency is enforced at the DB layer (unique `delivery_id`), not in
  memory, so it survives restarts/redeploys.
- Retries + `action_logs` give visibility into downstream failures instead
  of swallowing them.
- Secrets live only in environment variables; access tokens are never
  returned to the frontend or logged.

## Deliverables checklist
- [x] Deployed backend URL (Render): `https://github-automation-bot-3n85.onrender.com`
- [x] Deployed frontend URL (Vercel): `https://github-automation-bot-beta.vercel.app`
- [x] GitHub repo with commit history
- [x] `README.md` (this file)
- [x] `.env.example` for both apps
- [x] `AI_NOTES.md` — AI context and notes
