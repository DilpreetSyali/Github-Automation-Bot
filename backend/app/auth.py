import datetime as dt

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

SESSION_COOKIE_NAME = "session"
ALGO = "HS256"


def create_session_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": dt.datetime.utcnow(),
        "exp": dt.datetime.utcnow() + dt.timedelta(days=7),
    }
    return jwt.encode(payload, settings.SESSION_SECRET, algorithm=ALGO)


def decode_session_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=[ALGO])
        return int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_session_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
