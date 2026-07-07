from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.github_client import create_webhook, list_user_repos
from app.models import Event, Repo, User
from app.schemas import ConnectRepoIn, EventOut, RepoOut

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("/github")
async def github_repos(user: User = Depends(get_current_user)):
    """List the user's own GitHub repos, so the frontend can offer a picker."""
    repos = await list_user_repos(user.access_token)
    return [
        {"owner": r["owner"]["login"], "name": r["name"], "full_name": r["full_name"]}
        for r in repos
        if not r.get("archived")
    ]


@router.get("", response_model=list[RepoOut])
async def connected_repos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Repo).filter(Repo.user_id == user.id).all()


@router.post("", response_model=RepoOut)
async def connect_repo(
    body: ConnectRepoIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Repo)
        .filter(Repo.user_id == user.id, Repo.owner == body.owner, Repo.name == body.name)
        .first()
    )
    if existing:
        return existing

    webhook_url = f"{settings.GITHUB_OAUTH_REDIRECT_URL.rsplit('/auth', 1)[0]}/webhooks/github"
    hook = await create_webhook(
        user.access_token, body.owner, body.name, webhook_url, settings.GITHUB_WEBHOOK_SECRET
    )

    repo = Repo(
        user_id=user.id,
        github_repo_id=str(hook.get("id", "")),
        owner=body.owner,
        name=body.name,
        webhook_id=str(hook.get("id", "")),
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repo_id}/events", response_model=list[EventOut])
async def repo_events(
    repo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repo).filter(Repo.id == repo_id, Repo.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    events = (
        db.query(Event)
        .options(joinedload(Event.actions))
        .filter(
            Event.repo_id == repo.id,
            Event.event_type == "issues",
        )
        .order_by(Event.received_at.desc())
        .limit(100)
        .all()
    )
    return events
