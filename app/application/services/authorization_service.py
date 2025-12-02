import uuid
from typing import Optional

from domain.repositories import UserRepositoryInterface
from domain.value_objects import UserRole

from ..unit_of_wrok_interface import UnitOfWorkInterface


class AuthorizationService:
    
    _uow : UnitOfWorkInterface
    
    def __init__(self, uow: UnitOfWorkInterface):
        self._uow = uow

    async def _authorize_user(self, user_id: uuid.UUID, 
        required_roles: list[UserRole], 
        resource_owner_id: Optional[uuid.UUID] = None,
    ) -> bool:
        
        async with self._uow:
            user_repository = await self._uow.get_user_repository()
            
            user = await user_repository.get(user_id)
            
            if not user:
                return False

            if user.role not in required_roles:
                return False

            if resource_owner_id is not None:
                
                if user.role != UserRole.ADMIN and user.id != resource_owner_id:
                    return False

            return True

    async def can_manage_media(self, user_id: uuid.UUID, media_owner_id: Optional[uuid.UUID] = None) -> bool:
        required_roles = [UserRole.ADMIN]
        return await self._authorize_user(user_id, required_roles, media_owner_id)
    
    async def can_get_media(self, user_id: uuid.UUID, media_owner_id: Optional[uuid.UUID]) -> bool: 
        return await self._authorize_user(user_id, [UserRole.ADMIN, UserRole.USER], media_owner_id)
