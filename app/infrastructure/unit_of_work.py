from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..application.unit_of_wrok_interface import UnitOfWorkInterface
from .repositories import MediaRepository, SecurityRepository, UserRepository


class UnitOfWork(UnitOfWorkInterface):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        
        # Repositories
        self._user_repository: Optional[UserRepository] = None
        self._media_repository: Optional[MediaRepository] = None
        self._security_repository: Optional[SecurityRepository] = None

    async def __aenter__(self):
        self._session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        
        if self._session:
            await self._session.close()

    async def get_user_repository(self) -> UserRepository:
        if self._user_repository is None:
            if not self._session:
                raise RuntimeError("Session is not initialized. Use context manager.")
            self._user_repository = UserRepository(self._session)
        return self._user_repository

    async def get_security_repository(self) -> SecurityRepository:
        if self._security_repository is None:
            if not self._session:
                raise RuntimeError("Session is not initialized. Use context manager.")
            self._security_repository = SecurityRepository(self._session)
        return self._security_repository

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