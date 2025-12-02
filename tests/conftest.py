import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.append("app")


from app.application.services.authentication_service import AuthenticationService
from app.application.services.authorization_service import AuthorizationService
from app.application.services.media_service import MediaCRUDService
from app.application.services.security_monitoring_service import (
    SecurityMonitoringService,
)
from app.application.unit_of_wrok_interface import UnitOfWorkInterface
from app.domain.entities import User
from app.domain.value_objects import Email, SecurityPolicy, UserRole
from app.infrastructure.config import settings
from app.infrastructure.hasher import Hasher

# Импорт моделей для создания таблиц
from app.infrastructure.orm import Base
from app.infrastructure.unit_of_work import UnitOfWork
from app.presentation.app import app


# Фикстура для тестовой базы данных
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    # Используем тестовую базу данных (например, SQLite в памяти)
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очистка
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# Фикстура для тестовой сессии
@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


# Фикстура для мока UnitOfWorkInterface
@pytest.fixture
def mock_uow() -> UnitOfWorkInterface:
    mock = Mock(spec=UnitOfWorkInterface)
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()

    # Моки для репозиториев
    mock.users = Mock()
    mock.users.get_by_email = AsyncMock()
    mock.users.add = AsyncMock()
    mock.users.get = AsyncMock()

    mock.media = Mock()
    mock.media.get_all = AsyncMock()
    mock.media.get = AsyncMock()
    mock.media.add = AsyncMock()
    mock.media.update = AsyncMock()
    mock.media.delete = AsyncMock()

    mock.security_logs = Mock()
    mock.security_logs.add = AsyncMock()
    mock.security_logs.get_ips_with_excessive_attempts = AsyncMock()

    return mock


# Фикстура для test_session_maker
@pytest.fixture
def test_session_maker(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# Фикстура для реального UnitOfWork
@pytest_asyncio.fixture
async def real_uow(test_session_maker) -> UnitOfWork:
    return UnitOfWork(test_session_maker)


# Фикстура для SecurityPolicy
@pytest.fixture
def security_policy() -> SecurityPolicy:
    return SecurityPolicy()


# Фикстура для Hasher
@pytest.fixture
def hasher() -> Hasher:
    return Hasher()


# Фикстура для AuthenticationService с моком
@pytest.fixture
def auth_service_mock(mock_uow, hasher) -> AuthenticationService:
    return AuthenticationService(mock_uow, hasher, settings.SECRET_KEY)


# Фикстура для AuthenticationService с реальной БД
@pytest.fixture
def auth_service_real(real_uow, hasher) -> AuthenticationService:
    return AuthenticationService(real_uow, hasher, settings.SECRET_KEY)


# Фикстура для AuthorizationService
@pytest.fixture
def authz_service_mock(mock_uow) -> AuthorizationService:
    return AuthorizationService(mock_uow)


# Фикстура для SecurityMonitoringService
@pytest.fixture
def security_service_mock(mock_uow, security_policy) -> SecurityMonitoringService:
    return SecurityMonitoringService(mock_uow, security_policy)


# Фикстура для MediaCRUDService
@pytest.fixture
def media_service_mock(mock_uow) -> MediaCRUDService:
    return MediaCRUDService(mock_uow)


# Фикстура для тестового пользователя
@pytest_asyncio.fixture
async def test_user() -> User:
    return User(
        id=uuid4(),
        email=Email("test@example.com"),
        role=UserRole.USER,
        hash_password=await Hasher().get_hash("password123"),
    )


# Фикстура для тестового админа
@pytest_asyncio.fixture
async def test_admin() -> User:
    return User(
        id=uuid4(),
        email=Email("admin@example.com"),
        role=UserRole.ADMIN,
        hash_password=(await Hasher().get_hash("admin123")),
    )


# Фикстура для Async HTTP клиента
@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Фикстура для Request с cookies
@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self, cookies=None, client_host="127.0.0.1"):
            self.cookies = cookies or {}
            self.headers = {}
            self.client = Mock()
            self.client.host = client_host

    return MockRequest


# Фикстура для тестов с токеном
@pytest.fixture
def authorized_request(mock_request, auth_service_mock, test_user):
    request = mock_request()
    # Настраиваем мок для создания токена
    token = auth_service_mock.create_access_token(data={"sub": str(test_user.email)})
    request.cookies["access_token"] = token
    return request


# Фикстура для тестового приложения с переопределенными зависимостями
@pytest.fixture
def test_app():
    # Используем существующее приложение с переопределенными зависимостями

    # Создаем моки для тестового приложения
    test_app = FastAPI()

    # Импортируем и подключаем роутеры
    from app.presentation.login_router import login_router
    from app.presentation.media_router import media_router

    test_app.include_router(login_router)
    test_app.include_router(media_router)

    return test_app


# Фикстура для тестовых данных в БД
@pytest_asyncio.fixture
async def test_data_setup(test_session):
    """Фикстура для создания тестовых данных в БД"""
    from app.domain.entities import User
    from app.domain.value_objects import Email, UserRole

    # Создаем тестового пользователя
    user = User(
        email=Email("test@example.com"),
        role=UserRole.USER,
        hash_password=await Hasher().get_hash("testpassword"),
    )

    test_session.add(user)
    await test_session.commit()

    return {"user": user}


# Фикстура для проверки PII маскирования
@pytest.fixture
def pii_test_data():
    return {
        "email": "john.doe@example.com",
        "credit_card": "1234567812345678",
        "ssn": "123-45-6789",
        "normal_text": "Hello world",
    }


# Фикстура для временной директории для медиафайлов
@pytest.fixture
def temp_media_dir(tmp_path):
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    return media_dir


# Фикстура для тестовой конфигурации
@pytest.fixture
def test_settings():
    """Фикстура для тестовых настроек"""

    class TestSettings:
        SECRET_KEY = "test-secret-key-for-testing-only"
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    return TestSettings()
