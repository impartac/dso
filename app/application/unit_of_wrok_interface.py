from abc import ABC, abstractmethod

from ..domain.repositories import (
    MediaRepositoryInterface,
    SecurityRepositoryInterface,
    UserRepositoryInterface,
)


class UnitOfWorkInterface(ABC):
    @abstractmethod
    async def get_user_repository(self) -> UserRepositoryInterface:
        pass

    @abstractmethod
    async def get_security_repository(self) -> SecurityRepositoryInterface:
        pass

    @abstractmethod
    async def get_media_repository(self) -> MediaRepositoryInterface:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass