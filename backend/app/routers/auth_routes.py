from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import create_session_token, get_current_user, SESSION_COOKIE_NAME
from app.config import settings
from app.database import get_db
from app.github_client import exchange_code_for_token, get_authenticated_user
from app.models import User
from app.schemas import UserOut

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
async def me(user: User = Depends(get_current_user)):
    return user
