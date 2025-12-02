# from datetime import timedelta
# import sys
# from pathlib import Path


# # Добавляем корень проекта в PYTHONPATH
# sys.path.insert(0, str(Path(__file__).parent.parent))

# import uuid
# import pytest
# from fastapi import status
# from httpx import AsyncClient
# from unittest.mock import AsyncMock, MagicMock, patch

# from app.application.services.authentication_service import AuthenticationService, AuthenticationAttempt
# from app.application.services.security_monitoring_service import SecurityMonitoringService
# from app.domain.errors import LoginRateLimitException
# from app.domain.value_objects import Email
# from app.presentation.app import app

# # Моки зависимостей

# @pytest.fixture
# def mock_authentication_service():
#     mock = AsyncMock(spec=AuthenticationService)
#     mock.login = AsyncMock()
#     mock.register_user = AsyncMock()
#     mock.create_token = AsyncMock()
#     return mock

# @pytest.fixture
# def mock_security_monitoring_service():
#     mock = AsyncMock(spec=SecurityMonitoringService)
#     mock.process_login = AsyncMock()
#     mock.record_login_attempt = AsyncMock()
#     return mock

# # Переопределяем зависимости в приложении
# @pytest.fixture(autouse=True)
# def override_dependencies(mock_authentication_service, mock_security_monitoring_service):
#     from app.presentation.dependencies import (
#         get_authentication_service,
#         get_security_monitoring_service
#     )
    
#     app.dependency_overrides[get_authentication_service] = lambda: mock_authentication_service
#     app.dependency_overrides[get_security_monitoring_service] = lambda: mock_security_monitoring_service
    
#     yield
    
#     # Очищаем переопределения после теста
#     app.dependency_overrides.clear()

# # Тесты
# @pytest.mark.asyncio
# async def test_login_success(
#     async_client : AsyncClient,
#     test_app,
#     mock_authentication_service,
#     mock_security_monitoring_service
# ):
#     # Arrange
#     email = "test@example.com"
#     password = "password123"
#     mock_token = "fake_jwt_token_for_test"

#     # Настраиваем моки
#     mock_authentication_service.login.return_value = AuthenticationAttempt(
#         successful=True,
#         token=mock_token,
#     )
#     # {
#     #     "successful": True,
#     #     "token": mock_token,
#     #     "message": "Login successful"
#     # }
    
#     # process_login ничего не возвращает, просто проходит
#     mock_security_monitoring_service.process_login.return_value = None

#     # Act
#     response = await async_client.post(
#         "/login/",
#         data={
#             "username": email,  # OAuth2PasswordRequestForm использует 'username', а не 'email'
#             "password": password,
#         }
#     )
#     # Assert
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["message"] == "Login successful"
#     assert data["token_type"] == "bearer"
    
#     # Проверяем cookie
#     cookies = dict(response.cookies)
#     assert "access_token" in cookies
#     assert cookies["access_token"] == mock_token
    
#     # Проверяем вызовы сервисов
#     # mock_authentication_service.login.assert_called_once_with(
#     #     Email(email), password
#     # )
#     mock_security_monitoring_service.process_login.assert_called_once()

# @pytest.mark.asyncio
# async def test_login_invalid_credentials(
#     async_client,
#     mock_authentication_service, 
#     mock_security_monitoring_service
# ):
#     # Arrange
#     email = "test@example.com"
#     password = "wrong_password"

#     mock_authentication_service.login.return_value = {
#         "successful": False,
#         "token": "",
#         "message": "Invalid credentials"
#     }

#     # Act
#     response = await async_client.post(
#         "/login/",
#         json={"email": email, "password": password}
#     )

#     # Assert
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     data = response.json()
#     assert "detail" in data
#     assert data["detail"] == "Invalid credentials provided"

#     # mock_authentication_service.login.assert_called_once_with(
#     #     Email(email), password
#     # )
#     mock_security_monitoring_service.process_login.assert_called_once()
#     mock_security_monitoring_service.record_login_attempt.assert_called_once()
    
#     # Cookie не должно быть установлено
#     cookies = dict(response.cookies)
#     assert "access_token" not in cookies

# @pytest.mark.asyncio
# async def test_login_rate_limited(
#     async_client,
#     mock_security_monitoring_service
# ):
#     # Arrange
#     email = "test@example.com"
#     password = "password123"
#     retry_after_seconds = 60

#     # Мокируем исключение rate limit
#     # mock_security_monitoring_service.process_login.side_effect = LoginRateLimitException(
#     #     retry_after=retry_after_seconds * timedelta(seconds=1)
#     # )

#     # Act
#     response = await async_client.post(
#         "/login/",
#         json={"email": email, "password": password}
#     )

#     # Assert
#     assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
#     data = response.json()
#     assert "detail" in data
#     assert "Too many requests" in data["detail"]
    
#     # Проверяем заголовок Retry-After
#     assert "Retry-After" in response.headers
#     assert response.headers["Retry-After"] == str(retry_after_seconds)

# @pytest.mark.asyncio
# async def test_login_missing_fields(async_client):
#     # Отправляем POST запрос без обязательных полей
#     response = await async_client.post("/login/", json={})

#     # Assert
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     data = response.json()
#     assert "detail" in data
    
#     # Проверяем, что есть ошибки для полей email и password
#     errors = data["detail"]
#     field_names = []
#     for error in errors:
#         if "loc" in error and len(error["loc"]) > 1:
#             field_names.append(error["loc"][1])
#     assert "email" in field_names or "password" in field_names

# # --- Тесты для ручки /login/create (регистрация) ---

# @pytest.mark.asyncio
# async def test_create_user_success(
#     async_client,
#     mock_authentication_service
# ):
#     # Arrange
#     email = "newuser@example.com"
#     password = "secure_password_123"
#     mock_token = "fake_jwt_token_for_new_user"
#     new_user_id = uuid.uuid4()

#     mock_authentication_service.register_user.return_value = new_user_id
#     mock_authentication_service.create_token.return_value = mock_token

#     # Act
#     response = await async_client.post(
#         "/login/create",
#         json={
#             "email": email,
#             "password": password
#         }
#     )

#     # Assert
#     assert response.status_code == status.HTTP_201_CREATED
#     data = response.json()
    
#     assert data["message"] == "User created successfully"
#     assert data["token_type"] == "bearer"
#     assert "expires_in" in data

#     mock_authentication_service.register_user.assert_called_once_with(
#         Email(email), password
#     )
#     mock_authentication_service.create_token.assert_called_once_with(
#         new_user_id
#     )

#     # Проверяем cookie
#     cookies = dict(response.cookies)
#     assert "access_token" in cookies
#     assert cookies["access_token"] == mock_token

# @pytest.mark.asyncio
# async def test_create_user_email_already_exists(
#     async_client,
#     mock_authentication_service
# ):
#     # Arrange
#     email = "existing@example.com"
#     password = "secure_password_123"

#     # Имитируем исключение

#     # Act
#     response = await async_client.post(
#         "/login/create",
#         json={"email": email, "password": password}
#     )

#     # Assert
#     assert response.status_code == status.HTTP_409_CONFLICT
#     data = response.json()
#     assert "detail" in data
#     assert "already exists" in data["detail"].lower()
    
#     mock_authentication_service.register_user.assert_called_once_with(
#         Email(email), password
#     )
#     mock_authentication_service.create_token.assert_not_called()

# @pytest.mark.asyncio
# async def test_create_user_password_too_weak(
#     async_client,
#     mock_authentication_service
# ):
#     # Arrange
#     email = "weakpass@example.com"
#     password = "weak"  # Слишком слабый пароль



#     # Act
#     response = await async_client.post(
#         "/login/create",
#         json={"email": email, "password": password}
#     )

#     # Assert
#     assert response.status_code == status.HTTP_400_BAD_REQUEST
#     data = response.json()
#     assert "detail" in data
#     assert "weak" in data["detail"].lower()
    
#     mock_authentication_service.register_user.assert_called_once_with(
#         Email(email), password
#     )
#     mock_authentication_service.create_token.assert_not_called()

# @pytest.mark.asyncio
# async def test_create_user_missing_fields(async_client):
#     # Отправляем POST запрос без обязательных полей
#     response = await async_client.post("/login/create", json={})

#     # Assert
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     data = response.json()
#     assert "detail" in data
    
#     # Проверяем, что есть ошибки для полей email и password
#     errors = data["detail"]
#     field_names = []
#     for error in errors:
#         if "loc" in error and len(error["loc"]) > 1:
#             field_names.append(error["loc"][1])
#     assert "email" in field_names or "password" in field_names

# # Тесты для logout
# @pytest.mark.asyncio
# async def test_logout_success(async_client):
#     # Act
#     response = await async_client.post("/logout/")
    
#     # Assert
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["message"] == "Logout successful"
    
#     # Проверяем, что cookie очищено
#     cookies = dict(response.cookies)
#     assert "access_token" in cookies
#     assert cookies["access_token"] == ""  # Пустая строка означает удаление cookie

# @pytest.mark.asyncio
# async def test_get_current_user_success(
#     async_client,
#     mock_authentication_service
# ):
#     # Arrange
#     mock_user = {
#         "id": str(uuid.uuid4()),
#         "email": "test@example.com",
#         "role": "user"
#     }
#     mock_authentication_service.validate_token = AsyncMock(return_value=mock_user)
    
#     # Устанавливаем cookie с токеном
#     token = "valid_token"
    
#     # Act
#     response = await async_client.get(
#         "/current-user/",
#         cookies={"access_token": token}
#     )
    
#     # Assert
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["email"] == mock_user["email"]
#     mock_authentication_service.validate_token.assert_called_once_with(token)

# @pytest.mark.asyncio
# async def test_get_current_user_no_token(async_client):
#     # Act
#     response = await async_client.get("/current-user/")
    
#     # Assert
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     data = response.json()
#     assert "detail" in data
#     assert "Not authenticated" in data["detail"]

# @pytest.mark.asyncio
# async def test_get_current_user_invalid_token(
#     async_client,
#     mock_authentication_service
# ):
#     # Arrange
#     mock_authentication_service.validate_token = AsyncMock(return_value=None)
    
#     # Act
#     response = await async_client.get(
#         "/current-user/",
#         cookies={"access_token": "invalid_token"}
#     )
    
#     # Assert
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#     data = response.json()
#     assert "detail" in data
#     assert "Invalid or expired token" in data["detail"]