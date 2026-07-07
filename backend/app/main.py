import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.github_client import update_webhook
from app.models import Repo
from app.routers import auth_routes, repos, rules, webhooks

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="GitHub Automation Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(repos.router)
app.include_router(rules.router)
app.include_router(webhooks.router)


@app.on_event("startup")
async def on_startup():
    # Exercise scope: create_all instead of a migration tool (Alembic would
    # be the real-world choice - see AI_NOTES.md).
    Base.metadata.create_all(bind=engine)
    _repair_slack_connection_columns()
    await _repair_repo_webhooks()


def _repair_slack_connection_columns() -> None:
    inspector = inspect(engine)
    if "slack_connections" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("slack_connections")}
    desired = {
        "access_token": "TEXT",
        "team_id": "VARCHAR",
        "team_name": "VARCHAR",
        "channel_id": "VARCHAR",
        "channel_name": "VARCHAR",
        "webhook_url": "TEXT",
        "updated_at": "DATETIME",
    }

    missing = [(name, ddl) for name, ddl in desired.items() if name not in existing]
    with engine.begin() as conn:
        for name, ddl in missing:
            conn.execute(text(f"ALTER TABLE slack_connections ADD COLUMN {name} {ddl}"))
        conn.execute(text("ALTER TABLE slack_connections ALTER COLUMN webhook_url DROP NOT NULL"))


async def _repair_repo_webhooks() -> None:
    db = SessionLocal()
    webhook_url = f"{settings.GITHUB_OAUTH_REDIRECT_URL.rsplit('/auth', 1)[0]}/webhooks/github"
    try:
        repos = (
            db.query(Repo)
            .options(joinedload(Repo.owner_user))
            .filter(Repo.webhook_id.isnot(None))
            .all()
        )
        for repo in repos:
            if not repo.webhook_id or not repo.owner_user:
                continue
            try:
                await update_webhook(
                    repo.owner_user.access_token,
                    repo.owner,
                    repo.name,
                    repo.webhook_id,
                    webhook_url,
                    settings.GITHUB_WEBHOOK_SECRET,
                )
            except Exception:
                logging.exception("Failed to repair webhook for %s/%s", repo.owner, repo.name)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
