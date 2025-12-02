import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import jwt
import pytest
from freezegun import freeze_time

from app.application.hasher_interface import HasherInterface
from app.application.services.authentication_service import (
    AuthenticationAttempt,
    AuthenticationService,
)
from app.domain.value_objects import Email

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_hasher():
    mock = AsyncMock(spec=HasherInterface)
    mock.verify = AsyncMock()
    mock.get_hash = AsyncMock()
    return mock


@pytest.fixture
def auth_service(mock_uow, mock_hasher):
    """Фикстура для сервиса аутентификации"""
    return AuthenticationService(
        uow=mock_uow,
        hasher=mock_hasher,
        secret_key="test_secret_key",
        algorithm="HS256",
        access_token_expire_minutes=30,
    )


@pytest.mark.asyncio
async def test_login_successful(auth_service, mock_uow, mock_hasher, test_user):
    """Тест успешного входа"""
    # Arrange
    email = Email("test@example.com")
    password = "correct_password"

    mock_hasher.verify.return_value = True
    mock_uow.get_user_repository.return_value.get_by_email.return_value = test_user

    # Act
    result = await auth_service.login(email, password)

    # Assert
    assert result.successful is True
    assert result.token != ""
    mock_uow.get_user_repository.assert_called_once()
    mock_hasher.verify.assert_called_once_with(password, test_user.hash_password)


@pytest.mark.asyncio
async def test_login_user_not_found(auth_service, mock_uow, mock_hasher):
    """Тест входа с несуществующим пользователем"""
    # Arrange
    email = Email("nonexistent@example.com")
    password = "password"

    mock_uow.get_user_repository.return_value.get_by_email.return_value = None

    # Act
    result = await auth_service.login(email, password)

    # Assert
    assert result.successful is False
    assert result.token == ""
    mock_hasher.verify.assert_not_called()


@pytest.mark.asyncio
async def test_login_wrong_password(auth_service, mock_uow, mock_hasher, test_user):
    """Тест входа с неверным паролем"""
    # Arrange
    email = Email("test@example.com")
    password = "wrong_password"

    mock_hasher.verify.return_value = False
    mock_uow.get_user_repository.return_value.get_by_email.return_value = test_user

    # Act
    result = await auth_service.login(email, password)

    # Assert
    assert result.successful is False
    assert result.token == ""
    mock_hasher.verify.assert_called_once_with(password, test_user.hash_password)


@pytest.mark.asyncio
@freeze_time("2022-12-11 12:00:00")
async def test_create_token(auth_service):
    """Тест создания JWT токена"""
    # Arrange
    user_id = uuid.uuid4()

    # Act
    token = await auth_service.create_token(user_id)

    # Assert
    decoded = jwt.decode(
        token,
        auth_service._AuthenticationService__SECRET_KEY,
        algorithms=[auth_service._AuthenticationService__ALGORITHM],
    )

    assert decoded["user_id"] == str(user_id)
    exp_timestamp = decoded["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)

    # Время истечения должно быть через ACCESS_TOKEN_EXPIRE_MINUTES минут
    expected_expiry = datetime.fromisoformat("2022-12-11 12:00:00") + timedelta(
        minutes=auth_service._AuthenticationService__ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Допускаем небольшую погрешность в 1 секунду
    time_difference = abs((exp_datetime - expected_expiry).total_seconds())
    assert time_difference < 1


@pytest.mark.asyncio
async def test_validate_token_valid(auth_service, mock_uow, test_user):
    """Тест валидации корректного токена"""
    # Arrange
    token = await auth_service.create_token(test_user.id)

    mock_uow.get_user_repository.return_value.get.return_value = test_user

    # Act
    result = await auth_service.validate_token(token)

    # Assert
    assert result == test_user
    mock_uow.get_user_repository.assert_called_once()


@pytest.mark.asyncio
async def test_validate_token_invalid_signature(auth_service):
    """Тест валидации токена с неверной подписью"""
    # Arrange
    token = jwt.encode(
        {"user_id": str(uuid.uuid4()), "exp": datetime.now() + timedelta(minutes=30)},
        "wrong_secret_key",
        algorithm="HS256",
    )

    # Act/Assert
    with pytest.raises(jwt.InvalidSignatureError):
        await auth_service.validate_token(token)


@pytest.mark.asyncio
async def test_validate_token_no_user_id(auth_service):
    """Тест валидации токена без user_id"""
    # Arrange
    token = jwt.encode(
        {"exp": datetime.now() + timedelta(minutes=30)},
        auth_service._AuthenticationService__SECRET_KEY,
        algorithm="HS256",
    )

    # Act
    result = await auth_service.validate_token(token)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_validate_token_user_not_found(auth_service, mock_uow):
    """Тест валидации токена для несуществующего пользователя"""
    # Arrange
    user_id = uuid.uuid4()
    token = await auth_service.create_token(user_id)

    mock_uow.get_user_repository.return_value.get.return_value = None

    # Act
    result = await auth_service.validate_token(token)

    # Assert
    assert result is None


# @pytest.mark.asyncio
# async def test_register_user_successful(auth_service, mock_uow, mock_hasher):
#     """Тест успешной регистрации пользователя"""
#     # Arrange
#     email = Email("newuser@example.com")
#     password = "password123"
#     hashed_password = "hashed_password_123"
#     expected_user_id = uuid.uuid4()

#     mock_hasher.get_hash.return_value = hashed_password
#     mock_uow.get_user_repository.return_value.insert.return_value = expected_user_id

#     # Act
#     result = await auth_service.register_user(email, password)

#     # Assert
#     assert result == expected_user_id
#     mock_hasher.get_hash.assert_called_once_with(password)

#     # Проверяем, что создан правильный User объект
#     inserted_user = mock_uow.get_user_repository.return_value.insert.call_args[0][0]
#     assert inserted_user.email == email
#     assert UserRole(inserted_user.role) == UserRole.USER
#     assert inserted_user.hash_password == hashed_password


def test_authentication_attempt_dataclass():
    """Тест структуры AuthenticationAttempt"""
    # Arrange & Act
    attempt = AuthenticationAttempt(successful=True, token="test_token")

    # Assert
    assert attempt.successful is True
    assert attempt.token == "test_token"
    assert attempt.__dataclass_fields__ is not None


@pytest.mark.asyncio
async def test_context_manager_usage(auth_service, mock_uow, mock_hasher, test_user):
    """Тест правильности использования контекстного менеджера в методах"""
    # Arrange
    email = Email("test@example.com")
    password = "password"

    mock_hasher.verify.return_value = True
    mock_uow.get_user_repository.return_value.get_by_email.return_value = test_user

    # Act
    await auth_service.login(email, password)

    # Assert
    mock_uow.__aenter__.assert_called_once()
    mock_uow.__aexit__.assert_called_once()
