import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
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
def on_startup():
    # Exercise scope: create_all instead of a migration tool (Alembic would
    # be the real-world choice - see AI_NOTES.md).
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}
