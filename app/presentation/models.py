import re
import uuid
from datetime import datetime
from typing import Any, Optional

from domain.value_objects import MediaStatus, MediaType, UserRole
from pydantic import BaseModel, EmailStr, field_validator


class JSONEncodable(BaseModel):
    """Базовый класс для моделей с поддержкой сериализации datetime"""

    def dict(self, *args, **kwargs) -> dict[str, Any]:
        """Переопределяем dict для сериализации datetime"""
        d = super().model_dump(*args, **kwargs)
        return self._convert_datetime_to_iso(d)

    def _convert_datetime_to_iso(self, obj: Any) -> Any:
        """Рекурсивно преобразует datetime в ISO строку"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._convert_datetime_to_iso(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_to_iso(item) for item in obj]
        else:
            return obj


class MediaCreateRequest(BaseModel):
    kind: MediaType
    name: str
    title: str
    status: MediaStatus = MediaStatus.DRAFT

    @field_validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Invalid file name")
        return v

    @field_validator("title")
    def validate_title(cls, v):
        if len(v) > 255:
            raise ValueError("Title too long")
        return v


class MediaUpdateRequest(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    status: Optional[MediaStatus] = None


class MediaResponse(JSONEncodable):
    id: uuid.UUID
    kind: MediaType
    name: str
    title: str
    status: MediaStatus
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaDeleteResponse(JSONEncodable):
    id: uuid.UUID
    success: bool


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("email")
    def validate_email_domain(cls, v):
        # Простая проверка домена
        domain = v.split("@")[-1]
        if domain in ["example.com", "test.com"]:
            raise ValueError("Please use a real email domain")
        return v


class UserResponse(JSONEncodable):
    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ErrorResponse(JSONEncodable):
    error: str
    correlation_id: str
    timestamp: datetime


class SuccessResponse(JSONEncodable):
    message: str
    correlation_id: str
    timestamp: datetime


class RegistrationResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    email: str


class LoginResponse(BaseModel):
    message: str
    token_type: str
    expires_in: int
