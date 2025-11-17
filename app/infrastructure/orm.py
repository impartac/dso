import datetime
import hashlib
import uuid
from typing import List, Optional

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..domain.entities import LoginAttempt, Media, User
from ..domain.value_objects import Email, MediaStatus, MediaType, UserRole


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    """ORM модель для пользователя"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"),  # Явно указываем имя типа
        nullable=False,
        default=UserRole.USER,
    )
    hash_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Связи
    media_items: Mapped[List["MediaORM"]] = relationship(
        "MediaORM", back_populates="owner", cascade="all, delete-orphan"
    )
    login_attempts: Mapped[List["LoginAttemptORM"]] = relationship(
        "LoginAttemptORM", back_populates="user", cascade="all, delete-orphan"
    )

    # Индексы
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_created_at", "created_at"),
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
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Связи
    owner: Mapped["UserORM"] = relationship("UserORM", back_populates="media_items")

    # Индексы для поиска
    __table_args__ = (
        Index("ix_media_owner_status", "owner_id", "status"),
        Index("ix_media_kind_status", "kind", "status"),
        Index("ix_media_created_at", "created_at"),
    )


class LoginAttemptORM(Base):
    """ORM модель для попыток входа (NFR-1, NFR-5)"""

    __tablename__ = "login_attempts"

    # Primary key для базы данных
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Поля соответствующие доменной сущности
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    successful: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Дополнительные поля для безопасности/аудита
    user_agent_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Связи
    user: Mapped["UserORM"] = relationship("UserORM", back_populates="login_attempts")

    # Индексы для security мониторинга
    __table_args__ = (
        Index("ix_login_attempts_ip_timestamp", "ip_address", "timestamp"),
        Index("ix_login_attempts_user_timestamp", "user_id", "timestamp"),
        Index("ix_login_attempts_successful", "successful"),
    )


# Фабричные методы для User
def user_to_entity(orm: UserORM) -> User:
    """Преобразование UserORM в доменную сущность User"""
    return User(
        id=orm.id,
        email=Email(orm.email),
        role=orm.role,
        hash_password=orm.hash_password,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def user_from_entity(user: User) -> UserORM:
    """Создание UserORM из доменной сущности User"""
    return UserORM(
        id=user.id,
        email=str(user.email),
        role=user.role,
        hash_password=user.hash_password,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# Фабричные методы для Media
def media_to_entity(orm: MediaORM) -> Media:
    """Преобразование MediaORM в доменную сущность Media"""
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
    """Создание MediaORM из доменной сущности Media"""
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


# Фабричные методы для LoginAttempt
def login_attempt_to_entity(orm: LoginAttemptORM) -> LoginAttempt:
    """Преобразование LoginAttemptORM в доменную сущность LoginAttempt"""
    return LoginAttempt(
        ip_address=orm.ip_address,
        user_id=orm.user_id,
        timestamp=orm.timestamp,
        successful=orm.successful,
        user_agent=orm.user_agent,
    )


def login_attempt_from_entity(attempt: LoginAttempt) -> LoginAttemptORM:
    """Создание LoginAttemptORM из доменной сущности LoginAttempt"""
    user_agent_hash = None
    if attempt.user_agent:
        user_agent_hash = hashlib.sha256(attempt.user_agent.encode()).hexdigest()

    return LoginAttemptORM(
        ip_address=attempt.ip_address,
        user_id=attempt.user_id,
        timestamp=attempt.timestamp,
        successful=attempt.successful,
        user_agent=attempt.user_agent,
        user_agent_hash=user_agent_hash,
    )
