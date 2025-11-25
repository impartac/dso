import uuid
from datetime import datetime, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from ..application.dtos import LoginAttemptDTO
from ..application.security_monitoring_service import SecurityMonitoringService
from ..domain.entities import User
from ..domain.errors import LoginException, LoginRateLimitException
from ..domain.value_objects import Email, MediaStatus, SecurityPolicy
from ..infrastructure.config import logger, settings
from ..infrastructure.unit_of_work import UnitOfWork
from .dependencies import (
    check_rate_limit,
    get_current_user,
    get_services,
    get_uow,
    mask_pii,
)
from .models import (
    LoginRequest,
    MediaCreateRequest,
    MediaResponse,
    MediaUpdateRequest,
    RegistrationResponse,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
)
from .security_utils import create_access_token, get_password_hash, verify_password

router = APIRouter()


# Роуты
@router.post(
    "/media", response_model=MediaResponse, status_code=status.HTTP_201_CREATED
)
async def create_media(
    media_data: MediaCreateRequest,
    request: Request,
    services: Annotated[tuple, Depends(get_services)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Создание нового медиа (NFR-2: Rate limiting)"""

    # Rate limiting (NFR-2)
    user_key = f"media_create:{current_user.id}"
    if not check_rate_limit(user_key, limit=10, window=60):
        logger.warning(
            f"Rate limit triggered for user {current_user.id} - rule_id: media_create"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": "60"},
        )

    media_crud_service, _, _ = services

    try:
        media = await media_crud_service.create_media(
            user_id=current_user.id,
            kind=media_data.kind,
            name=media_data.name,
            title=media_data.title,
            status=media_data.status,
        )
        return MediaResponse(**media.__dict__)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/media/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: uuid.UUID,
    services: Annotated[tuple, Depends(get_services)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Получение медиа по ID"""
    media_crud_service, _, _ = services

    media = await media_crud_service.get_media(media_id, current_user.id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    return MediaResponse(**media.__dict__)


@router.put("/media/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: uuid.UUID,
    media_data: MediaUpdateRequest,
    services: Annotated[tuple, Depends(get_services)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Обновление медиа"""
    media_crud_service, _, _ = services

    media = await media_crud_service.update_media(
        media_id=media_id,
        user_id=current_user.id,
        title=media_data.title,
        status=media_data.status,
    )

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )

    return MediaResponse(**media.__dict__)


@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: uuid.UUID,
    services: Annotated[tuple, Depends(get_services)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Удаление медиа"""
    media_crud_service, _, _ = services

    success = await media_crud_service.delete_media(media_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Media not found"
        )


@router.get("/media", response_model=List[MediaResponse])
async def get_user_media(
    services: Annotated[tuple, Depends(get_services)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: Optional[MediaStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Получение медиа пользователя"""
    media_crud_service, _, _ = services

    media_list = await media_crud_service.get_user_media(
        user_id=current_user.id, status=status, skip=skip, limit=limit
    )

    return [MediaResponse(**media.__dict__) for media in media_list]


@router.get("/admin/media", response_model=List[MediaResponse])
async def get_media_by_status(
    services: Annotated[tuple, Depends(get_services)],
    current_user: Annotated[User, Depends(get_current_user)],
    media_status: MediaStatus = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Получение медиа по статусу (только для админов)"""
    _, media_query_service, auth_service = services

    # Проверка прав (NFR-5)
    if not await auth_service.can_view_admin_panel(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )

    media_list = await media_query_service.get_media_by_status(
        user_id=current_user.id, status=media_status, skip=skip, limit=limit
    )

    return [MediaResponse(**media.__dict__) for media in media_list]


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}


# Security endpoints
@router.post("/auth/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    response: Response,  # Добавляем параметр response
):
    """Аутентификация пользователя (NFR-1, NFR-5, NFR-7)"""
    correlation_id = str(uuid.uuid4())

    async with uow:
        try:
            user_repo = await uow.get_user_repository()
            security_repo = await uow.get_security_repository()

            # Инициализация сервиса мониторинга безопасности
            security_policy = SecurityPolicy(
                max_failed_login_attempts=5,
                failed_attempts_time_window=timedelta(minutes=5),
                ip_block_duration=timedelta(minutes=15),
            )
            security_monitoring = SecurityMonitoringService(security_repo, security_policy)

            # Получаем IP адрес клиента
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent")

            # Ищем пользователя
            user = await user_repo.get_by_email(login_data.email)
            if not user:
                # Пользователь не найден - создаем DTO для неудачной попытки
                # Используем временный UUID для несуществующего пользователя
                temp_user_id = uuid.uuid4()
                login_dto = LoginAttemptDTO(
                    ip_address=client_ip,
                    user_id=temp_user_id,
                    timestamp=datetime.now(),
                    successful=False,
                    user_agent=user_agent,
                )

                try:
                    await security_monitoring.process(login_dto)
                except LoginRateLimitException as e:
                    retry_seconds = int((e.retry_after - datetime.now()).total_seconds())
                    logger.warning(
                        f"Login rate limit exceeded for IP {client_ip} - \
                            Correlation ID: {correlation_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many login attempts. Please try again later.",
                        headers={"Retry-After": str(retry_seconds)},
                    )

                # Имитация проверки пароля для предотвращения timing attacks
                verify_password(login_data.password, get_password_hash("dummy_password"))

                logger.warning(
                    f"Failed login attempt: user not found - Email: {mask_pii(login_data.email)} - \
                    Correlation ID: {correlation_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            # Создаем DTO для попытки входа
            login_dto = LoginAttemptDTO(
                ip_address=client_ip,
                user_id=user.id,
                timestamp=datetime.now(),
                successful=True,  # Пока предполагаем неудачу
                user_agent=user_agent,
            )

            # Проверяем пароль
            if not verify_password(login_data.password, user.hash_password):
                try:
                    await security_monitoring.process(login_dto)
                except LoginRateLimitException as e:
                    retry_seconds = int((e.retry_after - datetime.utcnow()).total_seconds())
                    logger.warning(
                        f"Login rate limit exceeded for user {user.id} -\
                            Correlation ID: {correlation_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many login attempts. Please try again later.",
                        headers={"Retry-After": str(retry_seconds)},
                    )

                logger.warning(
                    f"Failed login attempt: invalid password - User ID: {user.id} -\
                        Correlation ID: {correlation_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            # Пароль верный - обновляем DTO для успешной попытки
            login_dto.successful = True

            try:
                await security_monitoring.process(login_dto)
            except LoginRateLimitException as e:
                # Это маловероятно для успешной попытки, но обрабатываем на всякий случай
                retry_seconds = int((e.retry_after - datetime.utcnow()).total_seconds())
                logger.warning(
                    f"Login rate limit exceeded during successful login - User ID: {user.id} -\
                        Correlation ID: {correlation_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Please try again later.",
                    headers={"Retry-After": str(retry_seconds)},
                )

            # Создание JWT токена
            access_token = create_access_token(data={"sub": str(user.id)})
            
            # Установка токена в куки
            token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,  # Защита от XSS атак
                secure=True,    # Только HTTPS в production
                samesite="lax", # Защита от CSRF атак
                max_age=int(token_expires.total_seconds()),
                expires=int((datetime.now() + token_expires).timestamp()),
            )

            # Дополнительная кука для хранения информации о пользователе (не чувствительная)
            response.set_cookie(
                key="user_info",
                value=f"{user.id}:{user.role}",
                httponly=False,  # Доступна из JavaScript
                secure=True,
                samesite="lax",
                max_age=int(token_expires.total_seconds()),
            )

            await uow.commit()

            logger.info(
                f"Successful login: User ID: {user.id} - Correlation ID: {correlation_id}"
            )

            return TokenResponse(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse(
                    id=user.id,
                    email=str(user.email),
                    role=user.role,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                ),
            )

        except HTTPException:
            await uow.rollback()
            raise
        except LoginException as e:
            await uow.rollback()
            logger.error(f"Login exception: {e} - Correlation ID: {correlation_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
            )
        except Exception as e:
            await uow.rollback()
            logger.error(
                f"Unexpected error during login: {e} - Correlation ID: {correlation_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during login",
            )

@router.post("/auth/logout")
async def logout():
    """Выход из системы (NFR-7)"""
    # Инвалидация сессии/токена
    return {"message": "Logged out successfully"}


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]):
    """Получение профиля текущего пользователя"""
    return UserResponse(
        id=current_user.id,
        email=str(current_user.email),
        role=current_user.role,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post(
    "/auth/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserCreateRequest, uow: Annotated[UnitOfWork, Depends(get_uow)]
):
    """
    Регистрация нового пользователя

    - Валидация email и пароля
    - Проверка уникальности email
    - Хеширование пароля
    - Создание пользователя в базе данных
    - Отправка приветственного email (в фоне)
    """
    correlation_id = str(uuid.uuid4())

    try:
        async with uow as uow:
            user_repo = await uow.get_user_repository()

            # Проверка существования пользователя с таким email
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user:
                logger.warning(
                    f"Registration attempt with existing email: {user_data.email} - \
                        Correlation ID: {correlation_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists",
                )

            # Rate limiting для регистрации (NFR-2)
            ip_key = f"registration:ip:{user_data.email.split('@')[-1]}"
            if not check_rate_limit(
                ip_key, limit=3, window=3600
            ):  # 3 попытки в час с одного домена
                logger.warning(
                    f"Registration rate limit exceeded for domain: {user_data.email} - \
                        Correlation ID: {correlation_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many registration attempts. Please try again later.",
                    headers={"Retry-After": "3600"},
                )

            # Создание пользователя
            user = User(
                email=Email(user_data.email),
                role=user_data.role,
                hash_password=get_password_hash(user_data.password),
            )

            await user_repo.insert(user)
            await uow.commit()

            # Логируем успешную регистрацию
            logger.info(
                f"User registered successfully: {user_data.email} - User ID: {user.id} - \
                    Correlation ID: {correlation_id}"
            )

            return RegistrationResponse(
                message="User registered successfully",
                user_id=user.id,
                email=user_data.email,
            )

    except HTTPException:
        await uow.rollback()
        raise
    except Exception as e:
        await uow.rollback()
        logger.error(e)
        logger.error(
            f"Error during user registration: {e} - \
                Correlation ID: {correlation_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration",
        )
