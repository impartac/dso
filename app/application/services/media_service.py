import uuid
from typing import List, Optional

from domain.entities import Media
from domain.value_objects import MediaStatus, MediaType

from ..unit_of_wrok_interface import UnitOfWorkInterface


class MediaCRUDService:

    _uow: UnitOfWorkInterface

    def __init__(self, uow: UnitOfWorkInterface):
        self._uow = uow

    async def create_media(
        self,
        user_id: uuid.UUID,
        kind: MediaType,
        name: str,
        title: str,
        status: MediaStatus = MediaStatus.DRAFT,
    ) -> Media:

        media = Media(
            kind=kind, name=name, title=title, status=status, owner_id=user_id
        )
        async with self._uow:
            media_repository = await self._uow.get_media_repository()
            media_id = await media_repository.insert(media)

        media.id = media_id

        return media

    async def get_media(self, media_id: uuid.UUID) -> Optional[Media]:

        async with self._uow:
            media_repository = await self._uow.get_media_repository()
            media = await media_repository.get(media_id)
            if not media:
                return None

            return media

    async def update_media(
        self,
        media_id: uuid.UUID,
        title: Optional[str] = None,
        status: Optional[MediaStatus] = None,
    ) -> Optional[Media]:

        async with self._uow:
            media_repository = await self._uow.get_media_repository()

            media = await media_repository.get(media_id)

            if not media:
                return None

            if title is not None:
                media.title = title
            if status is not None:
                media.status = status

            return await media_repository.update(media)

    async def delete_media(self, media_id: uuid.UUID) -> bool:
        """
        Удаление медиа

        Args:
            media_id: ID медиа
            user_id: ID пользователя
        """

        async with self._uow:
            media_repository = await self._uow.get_media_repository()

            media = await media_repository.get(media_id)

            if not media:
                return False

            deleted_media = await media_repository.delete(media_id)
            return deleted_media is not None

    async def get_user_media(
        self,
        user_id: uuid.UUID,
        status: Optional[MediaStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Media]:
        """
        Получение медиа пользователя

        Args:
            user_id: ID пользователя
            status: Фильтр по статусу (опционально)
            skip: Пропуск записей
            limit: Лимит записей
        """
        async with self._uow:
            media_repository = await self._uow.get_media_repository()
            return await media_repository.get_by_owner(user_id, status, skip, limit)


# class MediaQueryService:
#     def __init__(self, uow: UnitOfWorkInterface, auth_service: AuthorizationService):
#         self._uow = uow
#         self._auth_service = auth_service

#     async def get_media_by_status(
#         self, user_id: uuid.UUID, status: MediaStatus, skip: int = 0, limit: int = 100
#     ) -> List[Media]:
#         """
#         Получение медиа по статусу

#         Args:
#             user_id: ID пользователя, выполняющего запрос
#             status: Статус для фильтрации
#             skip: Пропуск записей
#             limit: Лимит записей
#         """
#         # Только админы и модераторы могут смотреть все медиа по статусу
#         if not await self._auth_service.can_view_admin_panel(user_id):
#             raise PermissionError(
#                 "User doesn't have permission to query media by status"
#             )

#         media_repo = await self._uow.get_media_repository()
#         return await media_repo.get_by_status(status, skip, limit)

#     async def search_media(
#         self,
#         user_id: uuid.UUID,
#         title_query: Optional[str] = None,
#         media_type: Optional[MediaType] = None,
#         status: Optional[MediaStatus] = None,
#         skip: int = 0,
#         limit: int = 100,
#     ) -> List[Media]:
#         """
#         Расширенный поиск медиа (только для админов/модераторов)

#         Args:
#             user_id: ID пользователя
#             title_query: Поиск по заголовку
#             media_type: Фильтр по типу
#             status: Фильтр по статусу
#             skip: Пропуск записей
#             limit: Лимит записей
#         """
#         if not await self._auth_service.can_view_admin_panel(user_id):
#             raise PermissionError("User doesn't have permission to search media")

#         # Здесь можно добавить более сложную логику поиска
#         # В текущей реализации используем базовые фильтры
#         media_repo = await self._uow.get_media_repository()

#         if status:
#             media_list = await media_repo.get_by_status(status, skip, limit)
#         else:
#             # Если статус не указан, получаем все медиа (с пагинацией)
#             # В реальной реализации нужно добавить соответствующий метод в репозиторий
#             media_list = await media_repo.get_by_status(
#                 MediaStatus.PUBLISHED, skip, limit
#             )

#         # Фильтрация на уровне Python (в реальном приложении лучше делать на уровне БД)
#         if title_query:
#             media_list = [
#                 m for m in media_list if title_query.lower() in m.title.lower()
#             ]

#         if media_type:
#             media_list = [m for m in media_list if m.kind == media_type]

#         return media_list
