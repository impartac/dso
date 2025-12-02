from typing import Optional

from application.unit_of_wrok_interface import UnitOfWorkInterface
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories import (
    CreateMediaAttemptsRepository,
    LoginAttemptsRepository,
    MediaRepository,
    UserRepository,
)


class UnitOfWork(UnitOfWorkInterface):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None

        # Repositories - инициализируем сразу как None
        self._user_repository: Optional[UserRepository] = None
        self._media_repository: Optional[MediaRepository] = None
        self._login_attempts_repository: Optional[LoginAttemptsRepository] = None
        self._create_media_attemp_repository: Optional[
            CreateMediaAttemptsRepository
        ] = None

    async def __aenter__(self):
        self._session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            # Всегда закрываем сессию
            if self._session:
                await self._session.close()
                self._session = None
            # Сбрасываем репозитории при выходе из контекста
            self._reset_repositories()

    def _reset_repositories(self) -> None:
        """Сбрасывает репозитории при завершении работы"""
        self._user_repository = None
        self._media_repository = None
        self._login_attempts_repository = None
        self._create_media_attemp_repository = None

    async def get_user_repository(self) -> UserRepository:
        if self._user_repository is None:
            if not self._session:
                raise RuntimeError("Session is not initialized. Use context manager.")
            self._user_repository = UserRepository(self._session)
        return self._user_repository

    async def get_login_attempts_repository(self) -> LoginAttemptsRepository:
        if self._login_attempts_repository is None:
            if not self._session:
                raise RuntimeError("Session is not initialized. Use context manager.")
            self._login_attempts_repository = LoginAttemptsRepository(self._session)
        return self._login_attempts_repository

    async def get_create_media_attempt_repository(
        self,
    ) -> CreateMediaAttemptsRepository:
        if self._create_media_attemp_repository is None:
            if not self._session:
                raise RuntimeError("Session is not initialized. Use context manager.")
            self._create_media_attemp_repository = CreateMediaAttemptsRepository(
                self._session
            )
        return self._create_media_attemp_repository

    async def get_media_repository(self) -> MediaRepository:
        if self._media_repository is None:
            if not self._session:
                raise RuntimeError("Session is not initialized. Use context manager.")
            self._media_repository = MediaRepository(self._session)
        return self._media_repository

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()
