import datetime
import uuid
from dataclasses import dataclass
from typing import Optional

from .value_objects import Email, MediaStatus, MediaType, UserRole


@dataclass
class Media:
    id: uuid.UUID
    kind: MediaType
    name: str
    title: str
    status: MediaStatus
    owner_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass
class User:
    id: uuid.UUID
    email: Email
    role: UserRole
    hash_password: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass
class LoginAttempt:
    ip_address: str
    user_id: uuid.UUID
    timestamp: datetime.datetime
    successful: bool
    user_agent: Optional[str] = None
