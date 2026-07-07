from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import create_session_token, get_current_user, SESSION_COOKIE_NAME
from app.config import settings
from app.database import get_db
from app.github_client import exchange_code_for_token, get_authenticated_user
from app.models import SlackConnection, User
from app.schemas import SlackConnectionIn, SlackConnectionOut, UserOut
from app.slack_client import exchange_code_for_slack_token, join_channel, list_channels

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login():
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_OAUTH_REDIRECT_URL}"
        "&scope=repo,read:user"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def callback(code: str, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    access_token = await exchange_code_for_token(code)
    gh_user = await get_authenticated_user(access_token)

    user = db.query(User).filter(User.github_id == str(gh_user["id"])).first()
    if user:
        user.access_token = access_token
        user.username = gh_user["login"]
        user.avatar_url = gh_user.get("avatar_url")
    else:
        user = User(
            github_id=str(gh_user["id"]),
            username=gh_user["login"],
            avatar_url=gh_user.get("avatar_url"),
            access_token=access_token,
        )
        db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session_token(user.id)
    redirect = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    redirect.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return redirect


@router.post("/logout")
async def logout():
    resp = RedirectResponse(f"{settings.FRONTEND_URL}/")
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    slack = db.query(SlackConnection).filter(SlackConnection.user_id == user.id).first()
    return UserOut(
        id=user.id,
        username=user.username,
        avatar_url=user.avatar_url,
        slack_connected=bool(slack and (slack.access_token or slack.webhook_url)),
        slack_channel_name=slack.channel_name if slack else None,
        slack_team_name=slack.team_name if slack else None,
    )


@router.get("/slack")
async def get_slack_connection(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    slack = db.query(SlackConnection).filter(SlackConnection.user_id == user.id).first()
    if not slack:
        return None
    return SlackConnectionOut(
        team_id=slack.team_id,
        team_name=slack.team_name,
        channel_id=slack.channel_id,
        channel_name=slack.channel_name,
        connected=bool(slack.access_token or slack.webhook_url),
    )


@router.put("/slack", response_model=SlackConnectionOut)
async def upsert_slack_connection(
    body: SlackConnectionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slack = db.query(SlackConnection).filter(SlackConnection.user_id == user.id).first()
    if slack:
        slack.access_token = body.access_token or slack.access_token
        slack.team_id = body.team_id or slack.team_id
        slack.team_name = body.team_name or slack.team_name
        slack.channel_id = body.channel_id
        slack.channel_name = body.channel_name
        slack.webhook_url = None
    else:
        slack = SlackConnection(
            user_id=user.id,
            access_token=body.access_token,
            team_id=body.team_id,
            team_name=body.team_name,
            channel_id=body.channel_id,
            channel_name=body.channel_name,
            webhook_url=None,
        )
        db.add(slack)
    db.commit()
    db.refresh(slack)
    if slack.access_token and slack.channel_id:
        channels = await list_channels(slack.access_token)
        chosen = next((c for c in channels if c["id"] == slack.channel_id), None)
        if chosen and not chosen.get("is_private", False):
            try:
                await join_channel(slack.access_token, slack.channel_id)
            except Exception:
                # If join fails, the bot may already be in the channel or the
                # workspace may restrict joining; posting will still be attempted.
                pass
    return SlackConnectionOut(
        team_id=slack.team_id,
        team_name=slack.team_name,
        channel_id=slack.channel_id,
        channel_name=slack.channel_name,
        connected=bool(slack.access_token or slack.webhook_url),
    )


@router.get("/slack/login")
async def slack_login():
    if not settings.SLACK_CLIENT_ID or not settings.SLACK_OAUTH_REDIRECT_URL:
        raise HTTPException(status_code=400, detail="Slack OAuth is not configured")
    url = (
        "https://slack.com/oauth/v2/authorize"
        f"?client_id={settings.SLACK_CLIENT_ID}"
        f"&scope=chat:write,channels:read,channels:join,groups:read,im:read,mpim:read"
        f"&redirect_uri={settings.SLACK_OAUTH_REDIRECT_URL}"
    )
    return RedirectResponse(url)


@router.get("/slack/callback")
async def slack_callback(code: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    try:
        data = await exchange_code_for_slack_token(code)
        channels = await list_channels(data["access_token"])
        preferred = channels[0] if channels else None
        slack = db.query(SlackConnection).filter(SlackConnection.user_id == user.id).first()
        channel_id = preferred["id"] if preferred else None
        channel_name = preferred["name"] if preferred else None
        if slack:
            slack.access_token = data["access_token"]
            slack.team_id = data.get("team", {}).get("id")
            slack.team_name = data.get("team", {}).get("name")
            slack.channel_id = channel_id
            slack.channel_name = channel_name
            slack.webhook_url = None
        else:
            slack = SlackConnection(
                user_id=user.id,
                access_token=data["access_token"],
                team_id=data.get("team", {}).get("id"),
                team_name=data.get("team", {}).get("name"),
                channel_id=channel_id,
                channel_name=channel_name,
                webhook_url=None,
            )
            db.add(slack)
        db.commit()
        db.refresh(slack)
        if slack.channel_id:
            chosen = next((c for c in channels if c["id"] == slack.channel_id), None)
            if chosen and not chosen.get("is_private", False):
                try:
                    await join_channel(slack.access_token, slack.channel_id)
                except Exception:
                    pass
        return RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Slack OAuth failed: {exc}") from exc


@router.get("/slack/channels")
async def slack_channels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    slack = db.query(SlackConnection).filter(SlackConnection.user_id == user.id).first()
    if not slack or not slack.access_token:
        raise HTTPException(status_code=400, detail="Slack is not connected")
    channels = await list_channels(slack.access_token)
    return [
        {"id": c["id"], "name": c["name"], "is_private": c.get("is_private", False)}
        for c in channels
    ]
