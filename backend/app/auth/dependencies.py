from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AuthError
from app.core.security import decode_token
from app.users.models import User
from app.users.repository import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthError("Authentication required.")
    user_id = decode_token(credentials.credentials, "access")
    user = UserRepository(db).get(user_id)
    if user is None or not user.active:
        raise AuthError("Authentication required.")
    return user
