import re
import uuid
from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status

from ..application.authorization_service import AuthorizationService
from ..application.media_service import MediaCRUDService, MediaQueryService
from ..domain.entities import User
from ..infrastructure.config import logger, session_factory, settings
from ..infrastructure.unit_of_work import UnitOfWork


async def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory)


_rate_limit_storage = {}


def check_rate_limit(key: str, limit: int, window: int) -> bool:
    now = datetime.now()
    window_start = now - timedelta(seconds=window)

    if key not in _rate_limit_storage:
        _rate_limit_storage[key] = []

    # Clean old requests
    _rate_limit_storage[key] = [t for t in _rate_limit_storage[key] if t > window_start]

    if len(_rate_limit_storage[key]) >= limit:
        return False

    _rate_limit_storage[key].append(now)
    return True


def mask_pii(data: str) -> str:
    # Маскирование email
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    def mask_email(match):
        email = match.group(0)
        parts = email.split("@")
        username = parts[0]
        domain = parts[1]
        masked_username = username[0] + "***" if len(username) > 1 else "*"
        domain_parts = domain.split(".")
        masked_domain = domain_parts[0][0] + "***" if len(domain_parts[0]) > 1 else "*"
        return f"{masked_username}@{masked_domain}.{domain_parts[1]}"

    data = re.sub(email_pattern, mask_email, data)

    # Маскирование других ПДН
    pii_patterns = [
        r"\b\d{16}\b",  # Номера карт
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    ]

    for pattern in pii_patterns:
        data = re.sub(pattern, "{PII}", data)

    return data


async def get_current_user(
    request: Request, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> User:
    """Зависимость для получения текущего пользователя из JWT токена"""
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    try:
        # Извлекаем токен из заголовка Authorization: Bearer <token>
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    except Exception as e:
        logger.error(f"Unexpected error during JWT decoding: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication error"
        )

    try:
        user_repo = await uow.get_user_repository()
        user = await user_repo.get(uuid.UUID(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier"
        )


async def get_services(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    auth_service = AuthorizationService(uow)
    media_crud_service = MediaCRUDService(uow, auth_service)
    media_query_service = MediaQueryService(uow, auth_service)
    return media_crud_service, media_query_service, auth_service


async def get_media_crud_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MediaCRUDService:
    auth_service = AuthorizationService(uow)
    return MediaCRUDService(uow, auth_service)


async def get_media_query_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MediaQueryService:
    auth_service = AuthorizationService(uow)
    return MediaQueryService(uow, auth_service)


async def get_auth_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> AuthorizationService:
    return AuthorizationService(uow)
