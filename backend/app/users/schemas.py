from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import EmailStr

from app.shared.schemas import ApiModel


class UserOut(ApiModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    currency: str
    locale: str
    timezone: str
    created_at: datetime
