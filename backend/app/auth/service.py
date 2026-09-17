from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, RegisterRequest, TokenPair
from app.categories.service import CategoryService
from app.core.errors import AuthError, ConflictError
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.users.models import User
from app.users.repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> User:
        email = payload.email.strip().lower()
        if self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists.")

        user = User(
            name=payload.name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
            currency=payload.currency.upper(),
            locale=payload.locale,
            timezone=payload.timezone,
        )
        self.users.add(user)
        CategoryService(self.db).seed_defaults(user.id)
        self.db.commit()
        return user

    def login(self, payload: LoginRequest) -> TokenPair:
        user = self.users.get_by_email(payload.email)
        # Verify even when the user is missing so timing does not reveal
        # whether an email is registered.
        password_hash = user.password_hash if user else "$argon2id$v=19$m=65536,t=3,p=4$invalid"
        if not verify_password(payload.password, password_hash) or user is None:
            raise AuthError("Invalid email or password.")
        if not user.active:
            raise AuthError("This account is disabled.")
        return self._tokens_for(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        user_id = decode_token(refresh_token, "refresh")
        user = self.users.get(user_id)
        if user is None or not user.active:
            raise AuthError("Invalid token.")
        return self._tokens_for(user)

    @staticmethod
    def _tokens_for(user: User) -> TokenPair:
        return TokenPair(
            access_token=create_token(user.id, "access"),
            refresh_token=create_token(user.id, "refresh"),
        )
