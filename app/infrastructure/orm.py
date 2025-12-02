import datetime
import hashlib
import uuid
from typing import List, Optional

from domain.entities import CreateMediaAttempt, LoginAttempt, Media, User
from domain.value_objects import Email, MediaStatus, MediaType, UserRole
from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    """ORM модель для пользователя"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[Email] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"),  # Явно указываем имя типа
        nullable=False,
        default=UserRole.USER,
    )
    hash_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        nullable=False,
    )

    # Связи
    media_items: Mapped[List["MediaORM"]] = relationship(
        "MediaORM", back_populates="owner", cascade="all, delete-orphan"
    )



class MediaORM(Base):
    """ORM модель для медиа контента"""

    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kind: Mapped[MediaType] = mapped_column(
        SQLEnum(MediaType, name="media_type"), nullable=False  # Явно указываем имя типа
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[MediaStatus] = mapped_column(
        SQLEnum(MediaStatus, name="media_status"),  # Явно указываем имя типа
        nullable=False,
        default=MediaStatus.DRAFT,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        nullable=False,
    )

    # Связи
    owner: Mapped["UserORM"] = relationship("UserORM", back_populates="media_items")


class LoginAttemptORM(Base):
    """ORM модель для попыток входа (NFR-1, NFR-5)"""

    __tablename__ = "login_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)

    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )

class CreateMediaAttemptORM(Base):
    """ORM модель для попыток входа (NFR-1, NFR-5)"""

    __tablename__ = "create_media_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.now, nullable=False
    )


def user_to_entity(orm: UserORM) -> User:

    return User(
        id=orm.id,
        email=orm.email,
        role=orm.role,
        hash_password=orm.hash_password,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def user_from_entity(user: User) -> UserORM:

    return UserORM(
        id=user.id,
        email=str(user.email),
        role=user.role,
        hash_password=user.hash_password,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def media_to_entity(orm: MediaORM) -> Media:

    return Media(
        id=orm.id,
        kind=orm.kind,
        name=orm.name,
        title=orm.title,
        status=orm.status,
        owner_id=orm.owner_id,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def media_from_entity(media: Media) -> MediaORM:

    return MediaORM(
        id=media.id,
        kind=media.kind,
        name=media.name,
        title=media.title,
        status=media.status,
        owner_id=media.owner_id,
        created_at=media.created_at,
        updated_at=media.updated_at,
    )


def login_attempt_to_entity(orm: LoginAttemptORM) -> LoginAttempt:

    return LoginAttempt(
        ip_address=orm.ip_address,
        timestamp=orm.timestamp,
    )


def login_attempt_from_entity(attempt: LoginAttempt) -> LoginAttemptORM:

    return LoginAttemptORM(
        ip_address=attempt.ip_address,
        timestamp=attempt.timestamp,
    )

def create_media_attempt_to_entity(orm: CreateMediaAttemptORM) -> CreateMediaAttempt:

    return CreateMediaAttempt(
        user_id=orm.user_id,
        timestamp=orm.timestamp,
    )


def create_media_attempt_from_entity(attempt: CreateMediaAttempt) -> CreateMediaAttemptORM:

    return CreateMediaAttemptORM(
        user_id=attempt.user_id,
        timestamp=attempt.timestamp,
    )
