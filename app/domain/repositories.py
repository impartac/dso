import datetime
import uuid
from abc import ABC, abstractmethod
from typing import List

from .entities import LoginAttempt, Media, User


class UserRepositoryInterface(ABC):

    @abstractmethod
    async def insert(self, entity: User) -> uuid.UUID:
        pass

    @abstractmethod
    async def get(self, id: uuid.UUID) -> User:
        pass


class MediaRepositoryInterface(ABC):

    @abstractmethod
    async def get(self, id: uuid.UUID) -> Media:
        pass

    @abstractmethod
    async def insert(self, entity: Media) -> uuid.UUID:
        pass

    @abstractmethod
    async def update(self, entity: Media) -> Media:
        pass

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> Media:
        pass


class SecurityRepositoryInterface(ABC):
    @abstractmethod
    async def get(self, id: uuid.UUID) -> LoginAttempt:
        pass

    @abstractmethod
    async def insert(self, entity: LoginAttempt) -> uuid.UUID:
        pass

    @abstractmethod
    async def get_ips_with_excessive_attempts(
        self, threshhold: int, time_delta: datetime.timedelta
    ) -> List[str]:
        pass

    @abstractmethod
    async def cleanup_old_attempts(self, older_than_mins) -> None:
        pass
