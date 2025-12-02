from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


@dataclass
class SecurityPolicy:
    """Value Object представляющий политику безопасности (NFR-1)"""

    # Аутентификация
    max_failed_login_attempts: int = 5
    ip_block_duration: timedelta = timedelta(minutes=15)
    failed_attempts_time_window: timedelta = timedelta(minutes=5)

    # Rate Limiting (NFR-2)
    media_creation_limit: int = 10
    media_creation_window: timedelta = timedelta(minutes=1)
    user_block_duration: timedelta = timedelta(minutes=1)

    # Сессии (NFR-21)
    session_timeout: timedelta = timedelta(minutes=30)
    token_expiration: timedelta = timedelta(minutes=30)

    # Файлы (NFR-14)
    max_file_size_mb: int = 100
    allowed_mime_types: tuple = (
        "image/jpeg",
        "image/png",
        "video/mp4",
        "audio/mpeg",
        "application/pdf",
    )

    def validate(self) -> None:
        """Валидация политики"""
        if self.max_failed_login_attempts < 1:
            raise ValueError("Max failed login attempts must be at least 1")
        if self.media_creation_limit < 1:
            raise ValueError("Media creation limit must be at least 1")
        if self.max_file_size_mb <= 0:
            raise ValueError("Max file size must be positive")


@dataclass
class Email:
    value: str

    def masked_for_logs(self) -> str:
        """Маскирование email для логов (NFR-6)"""
        local, domain = self.value.split("@")
        domain_parts = domain.split(".")
        return f"{local[0]}***@{domain_parts[0][0]}***.{domain_parts[-1]}"

    def __eq__(self, other):
        if not isinstance(other, Email):
            return NotImplemented
        return self.value == other.value

    def __str__(self) -> str:
        return self.value


class UserRole(Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class MediaType(Enum):
    MOVIE = "movie"
    COURSE = "course"


class MediaStatus(Enum):
    DRAFT = "draft"
    ARCHIVED = "archived"
    PUBLISHED = "published"
