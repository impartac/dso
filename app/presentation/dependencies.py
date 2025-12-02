import re
from typing import Annotated, Optional

from application.services.authentication_service import AuthenticationService
from application.services.authorization_service import AuthorizationService
from application.services.media_service import MediaCRUDService
from application.services.security_monitoring_service import SecurityMonitoringService
from application.unit_of_wrok_interface import UnitOfWorkInterface
from domain.entities import User
from domain.value_objects import SecurityPolicy, UserRole
from fastapi import Depends, HTTPException, Request, status
from infrastructure.config import session_factory, settings
from infrastructure.hasher import Hasher
from infrastructure.unit_of_work import UnitOfWork


async def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory)


async def get_security_monitoring_service(
    uow: Annotated[UnitOfWorkInterface, Depends(get_uow)]
) -> SecurityMonitoringService:
    policy = SecurityPolicy()
    return SecurityMonitoringService(uow, policy)


async def get_authorization_service(
    uow: Annotated[UnitOfWorkInterface, Depends(get_uow)]
) -> AuthorizationService:
    return AuthorizationService(uow)


async def get_authentication_service(
    uow: Annotated[UnitOfWorkInterface, Depends(get_uow)]
) -> AuthenticationService:
    hasher = Hasher()
    return AuthenticationService(uow, hasher, settings.SECRET_KEY)


async def get_media_service(
    uow: Annotated[UnitOfWorkInterface, Depends(get_uow)]
) -> MediaCRUDService:
    return MediaCRUDService(uow)


async def get_current_user(
    request: Request,
    auth_service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> User:

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - no token in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.validate_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_admin_user(
    user: Annotated[Optional[User], Depends(get_current_user)]
) -> Optional[User]:
    return user if user and user.role == UserRole.ADMIN else None


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
