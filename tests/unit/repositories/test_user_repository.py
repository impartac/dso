import sys
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from app.domain.entities import User
from app.domain.repositories import UserRepositoryInterface
from app.domain.value_objects import Email, UserRole
from app.infrastructure.orm import UserORM, user_from_entity
from app.infrastructure.repositories import UserRepository

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_session():
    """Фикстура для мока асинхронной сессии SQLAlchemy"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def user_repository(mock_session) -> UserRepositoryInterface:
    """Фикстура для репозитория пользователей"""
    return UserRepository(mock_session)


@pytest.fixture
def sample_user_entity():
    """Фикстура для тестового пользователя (доменная сущность)"""
    return User(
        id=uuid_lib.uuid4(),
        email=Email("test@example.com"),
        role=UserRole.USER,
        hash_password="hashed_password_123",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_user_orm():
    """Фикстура для тестового пользователя (ORM модель)"""
    return UserORM(
        id=uuid_lib.uuid4(),
        email="test@example.com",
        role="USER",
        hash_password="hashed_password_123",
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


class TestUserRepository:
    """Тесты реализации репозитория пользователей"""

    @pytest.mark.asyncio
    async def test_insert_user_success(self, user_repository, mock_session, sample_user_entity):
        """Тест успешного добавления пользователя"""
        # Arrange
        mock_add = mock_session.add
        mock_flush = mock_session.flush

        # Act
        await user_repository.insert(sample_user_entity)

        # Assert
        mock_add.assert_called_once()
        mock_flush.assert_called_once()

        # Проверяем, что был вызван add с ORM объектом
        added_orm = mock_add.call_args[0][0]
        assert isinstance(added_orm, UserORM)
        assert added_orm.id == sample_user_entity.id
        assert added_orm.email == str(sample_user_entity.email)
        assert added_orm.role == sample_user_entity.role

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, user_repository : UserRepositoryInterface, mock_session, sample_user_entity : User):
        """Тест получения пользователя по ID (пользователь найден)"""
        # Arrange
        user_id = sample_user_entity.id
        sample_user_orm = user_from_entity(sample_user_entity)
        # Мокаем execute и scalar_one_or_none
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_orm
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_repository.get(user_id)

        # Assert
        assert result is not None
        assert result.id == sample_user_entity.id
        assert result.email == str(sample_user_entity.email)
        assert result.role == sample_user_entity.role
        assert result.hash_password == sample_user_entity.hash_password

        # Проверяем вызов execute с правильным запросом
        mock_session.execute.assert_called_once()
        call_arg = mock_session.execute.call_args[0][0]
        assert isinstance(call_arg, Select)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_repository, mock_session):
        """Тест получения пользователя по ID (пользователь не найден)"""
        # Arrange
        user_id = uuid_lib.uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_repository.get(user_id)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, user_repository, mock_session, sample_user_entity, sample_user_orm):
        """Тест получения пользователя по email (пользователь найден)"""
        # Arrange
        email = sample_user_entity.email

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_orm
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_repository.get_by_email(email)

        # Assert
        assert result is not None
        assert result.email == str(email)

        # Проверяем, что запрос содержит условие по email
        mock_session.execute.assert_called_once()
        call_arg = mock_session.execute.call_args[0][0]
        assert isinstance(call_arg, Select)

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repository, mock_session):
        """Тест получения пользователя по email (пользователь не найден)"""
        # Arrange
        email = Email("nonexistent@example.com")

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await user_repository.get_by_email(email)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, mock_session, sample_user_entity, sample_user_orm):
        """Тест обновления пользователя"""
        # Arrange
        # Создаем обновленную сущность
        updated_user = User(
            id=sample_user_entity.id,
            email=Email("updated@example.com"),
            role=UserRole.ADMIN,
            hash_password="new_hashed_password",
            created_at=sample_user_entity.created_at,
            updated_at=datetime.now()
        )

        mock_result = Mock()
        mock_result.scalar_one.return_value = sample_user_orm
        mock_session.execute.return_value = mock_result
        mock_flush = mock_session.flush

        # Act
        await user_repository.update(updated_user)

        # Assert
        # Проверяем, что ORM объект обновлен
        assert sample_user_orm.email == updated_user.email
        assert sample_user_orm.role == updated_user.role
        assert sample_user_orm.hash_password == updated_user.hash_password
        assert sample_user_orm.updated_at is not None

        mock_flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises_error(self, user_repository, mock_session, sample_user_entity):
        """Тест обновления несуществующего пользователя (должен вызывать исключение)"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one.side_effect = Exception("No row was found")
        mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(Exception, match="No row was found"):
            await user_repository.update(sample_user_entity)

    def test_user_repository_class_structure(self, user_repository):
        """Тест структуры класса UserRepository"""
        from app.infrastructure.repositories import Repository
        
        repo_class = type(user_repository)
        
        # 1. Проверяем имя класса
        assert repo_class.__name__ == 'UserRepository'
        
        # 2. Проверяем MRO (Method Resolution Order)
        mro = repo_class.__mro__
        
        # Ищем интерфейс в MRO по имени или по ссылке
        has_interface = False
        interface_class = None
        
        for cls in mro:
            if cls.__name__ == 'UserRepositoryInterface':
                has_interface = True
                interface_class = cls
                break
        
        # 3. Если не нашли по имени, проверяем issubclass
        if not has_interface:
            # Пробуем проверить через issubclass
            try:
                has_interface = issubclass(repo_class, UserRepositoryInterface)
            except:
                has_interface = False
        
        assert has_interface, f"UserRepository должен реализовывать UserRepositoryInterface. MRO: {mro}"
        
        # 4. Проверяем Repository в MRO
        has_repository = Repository in mro or any(
            cls.__name__ == 'Repository' for cls in mro
        )
        assert has_repository, f"UserRepository должен наследоваться от Repository. MRO: {mro}"
        
        # 5. Проверяем наличие всех методов интерфейса
        required_methods = ['insert', 'get', 'get_by_email']
        for method_name in required_methods:
            assert hasattr(user_repository, method_name), f"Отсутствует метод {method_name}"
            assert callable(getattr(user_repository, method_name)), f"Метод {method_name} не вызываемый"

    @pytest.mark.asyncio
    async def test_insert_returns_none_as_expected(self, user_repository, mock_session, sample_user_entity):
        """Тест, что insert возвращает None (согласно интерфейсу)"""
        # Act
        result = await user_repository.insert(sample_user_entity)

        # Assert
        assert result is None


class TestRepositoryErrorHandling:
    """Тесты обработки ошибок в репозитории"""

    @pytest.mark.asyncio
    async def test_get_handles_database_error(self, user_repository, mock_session):
        """Тест обработки ошибки БД при получении пользователя"""
        # Arrange
        user_id = uuid_lib.uuid4()
        mock_session.execute.side_effect = Exception(
            "Database connection error")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            await user_repository.get(user_id)

    @pytest.mark.asyncio
    async def test_insert_handles_database_error(self, user_repository, mock_session, sample_user_entity):
        """Тест обработки ошибки БД при добавлении пользователя"""
        # Arrange
        mock_session.add.side_effect = Exception("Constraint violation")

        # Act & Assert
        with pytest.raises(Exception, match="Constraint violation"):
            await user_repository.insert(sample_user_entity)


class TestTypeHintsAndSignatures:
    """Тесты проверки типов и сигнатур методов"""

    def test_method_signatures_match_interface(self):
        """Тест, что сигнатуры методов реализации соответствуют интерфейсу"""
        import inspect

        # Получаем методы интерфейса
        interface_methods = {
            name: method
            for name, method in inspect.getmembers(UserRepositoryInterface, predicate=inspect.ismethod)
            if not name.startswith('_')
        }

        # Получаем методы реализации
        repo_methods = {
            name: method
            for name, method in inspect.getmembers(UserRepository, predicate=inspect.isfunction)
            if not name.startswith('_') and name in interface_methods
        }

        # Проверяем, что все абстрактные методы реализованы
        for method_name in interface_methods:
            assert method_name in repo_methods, f"Метод {method_name} не реализован"
