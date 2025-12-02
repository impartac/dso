import datetime
import uuid
from dataclasses import dataclass, field
from typing import Optional

from .value_objects import Email, MediaStatus, MediaType, UserRole


@dataclass
class Media:
    kind: MediaType
    name: str
    title: str
    status: MediaStatus
    owner_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self):
        # Ensure updated_at is set to created_at when first created
        if self.updated_at == self.created_at:
            self.updated_at = self.created_at


@dataclass
class User:
    email: Email
    role: UserRole
    hash_password: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self):

        if self.updated_at == self.created_at:
            self.updated_at = self.created_at


@dataclass
class LoginAttempt:
    ip_address: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)


@dataclass
class CreateMediaAttempt:
    user_id : uuid.UUID
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
