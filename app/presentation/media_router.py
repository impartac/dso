import uuid
from datetime import datetime, timedelta
from typing import Annotated, List, Optional

from application.dtos import LoginAttemptDTO
from application.services.authentication_service import AuthenticationService
from application.services.authorization_service import AuthorizationService
from application.services.media_service import MediaCRUDService
from application.services.security_monitoring_service import SecurityMonitoringService
from domain.entities import Media, User
from domain.errors import CreateMediaRateLimitException, LoginException, LoginRateLimitException
from domain.value_objects import Email, MediaStatus, SecurityPolicy
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from infrastructure.config import logger, settings
from infrastructure.unit_of_work import UnitOfWork

from .dependencies import (
    get_authentication_service,
    get_authorization_service,
    get_current_user,
    get_media_service,
    get_security_monitoring_service,
    get_uow,
    mask_pii,
)
from .models import (
    LoginRequest,
    MediaCreateRequest,
    MediaDeleteResponse,
    MediaResponse,
    MediaUpdateRequest,
    RegistrationResponse,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
)
from .security_utils import create_access_token, get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)

media_router = APIRouter(prefix="/media")


@media_router.post(
    "/",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_media(
    media_data: MediaCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    media_crud_service: Annotated[MediaCRUDService, Depends(get_media_service)],
    security_monitoring_service : Annotated[SecurityMonitoringService, Depends(get_security_monitoring_service)]
) -> MediaResponse:
    
    request_time =  datetime.now()
        
    try:
        await security_monitoring_service.process_create_media(current_user.id, request_time)
        logger.debug(f"Successful process create_media reuqest. user = {current_user.id}, request_time = {request_time}")
    except CreateMediaRateLimitException as cm_rt:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail= {
                "message": "To many request"
            },
            headers={
                "Retry-After" : str(cm_rt.blocked_until)
            }
        )

    media = await media_crud_service.create_media(
        user_id=current_user.id,
        kind=media_data.kind,
        name=media_data.name,
        title=media_data.title,
        status=media_data.status
    )
    
    return MediaResponse(
        id=media.id,
        kind=media.kind,
        name=media.name,
        title=media.title,
        status=media.status,
        owner_id = media.owner_id,
        created_at=media.created_at,
        updated_at=media.updated_at
    )


@media_router.get(
    "/",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def get_media(
    media_id : uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    media_crud_service: Annotated[MediaCRUDService, Depends(get_media_service)],
    authorization_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> MediaResponse:
    
    media = await media_crud_service.get_media(media_id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message" : "media not found"
            }
        )
    
    if not await authorization_service.can_get_media(current_user.id, media.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message" : "No permission"
            }
        )
    
    return MediaResponse(
        id=media.id,
        kind=media.kind,
        name=media.name,
        title=media.title,
        status=media.status,
        owner_id = media.owner_id,
        created_at=media.created_at,
        updated_at=media.updated_at
    )
    
@media_router.patch(
    "/",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def update_media(
    media_update_data : MediaUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    media_crud_service: Annotated[MediaCRUDService, Depends(get_media_service)],
    authorization_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> MediaResponse:
    
    media = await media_crud_service.get_media(media_update_data.id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message" : "media not found"
            }
        )
    
    if not await authorization_service.can_get_media(current_user.id, media.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message" : "No permission"
            }
        )
    
    media = await media_crud_service.update_media(
        media_update_data.id, 
        media_update_data.title, 
        media_update_data.status,
    )
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message" : "media not found"
            }
        )
    
    return MediaResponse(
        id=media.id,
        kind=media.kind,
        name=media.name,
        title=media.title,
        status=media.status,
        owner_id = media.owner_id,
        created_at=media.created_at,
        updated_at=media.updated_at
    )
    
@media_router.delete(
    "/",
    response_model=MediaDeleteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def delete_media(
    media_id : uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    media_crud_service: Annotated[MediaCRUDService, Depends(get_media_service)],
    authorization_service: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> MediaDeleteResponse:
    
    media = await media_crud_service.get_media(media_id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message" : "media not found"
            }
        )
    
    if not await authorization_service.can_get_media(current_user.id, media.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message" : "No permission"
            }
        )
    
    success = await media_crud_service.delete_media(media_id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message" : "media not found"
            }
        )
    
    return MediaDeleteResponse(
        id = media_id,
        success = success,
    )
    
    