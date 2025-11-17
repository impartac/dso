import uuid
from typing import Optional

from ..domain.value_objects import UserRole
from .unit_of_wrok_interface import UnitOfWorkInterface


class AuthorizationService:
    def __init__(self, uow: UnitOfWorkInterface):
        self._uow = uow

    async def authorize_user(
        self,
        user_id: uuid.UUID,
        required_roles: list[UserRole],
        resource_owner_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Авторизация пользователя

        Args:
            user_id: ID пользователя, который пытается выполнить действие
            required_roles: Список ролей, которые имеют доступ
            resource_owner_id: ID владельца ресурса (для проверки владения)

        Returns:
            bool: True если авторизация успешна
        """
        user_repo = await self._uow.get_user_repository()
        user = await user_repo.get(user_id)

        if not user:
            return False

        # Проверка роли
        if user.role not in required_roles:
            return False

        # Если указан владелец ресурса, проверяем совпадение
        if resource_owner_id and user.id != resource_owner_id:
            # Админы и модераторы могут управлять чужими ресурсами
            if user.role not in [UserRole.ADMIN]:
                return False

        return True

    async def can_manage_media(
        self, user_id: uuid.UUID, media_owner_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Проверка прав на управление медиа

        Args:
            user_id: ID пользователя
            media_owner_id: ID владельца медиа (опционально)
        """
        if media_owner_id:
            # Проверка прав на конкретное медиа
            required_roles = [UserRole.ADMIN, UserRole.USER]
            return await self.authorize_user(user_id, required_roles, media_owner_id)
        else:
            # Проверка прав на создание нового медиа
            required_roles = [UserRole.ADMIN, UserRole.USER]
            return await self.authorize_user(user_id, required_roles)

    async def can_view_admin_panel(self, user_id: uuid.UUID) -> bool:
        """Проверка прав на доступ к админ панели"""
        required_roles = [UserRole.ADMIN]
        return await self.authorize_user(user_id, required_roles)

    async def can_manage_users(self, user_id: uuid.UUID) -> bool:
        """Проверка прав на управление пользователями"""
        required_roles = [UserRole.ADMIN]
        return await self.authorize_user(user_id, required_roles)
