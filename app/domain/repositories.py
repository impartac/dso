import datetime
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import CreateMediaAttempt, LoginAttempt, Media, User
from .value_objects import Email, MediaStatus


class UserRepositoryInterface(ABC):

    @abstractmethod
    async def insert(self, entity: User) -> uuid.UUID:
        pass

    @abstractmethod
    async def get(self, id: uuid.UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> User:
        pass


class MediaRepositoryInterface(ABC):

    @abstractmethod
    async def get(self, id: uuid.UUID) -> Optional[Media]:
        pass

    @abstractmethod
    async def insert(self, entity: Media) -> uuid.UUID:
        pass

    @abstractmethod
    async def update(self, entity: Media) -> Optional[Media]:
        pass

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> Media:
        pass

    @abstractmethod
    async def get_by_owner(
        self,
        user_id: uuid.UUID,
        status: Optional[MediaStatus] = MediaStatus.PUBLISHED,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Media]:
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: Optional[MediaStatus] = MediaStatus.PUBLISHED,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Media]:
        pass


class LoginAttemptsRepositoryInterface(ABC):

    @abstractmethod
    async def insert(self, entity: LoginAttempt) -> None:
        pass

    @abstractmethod
    async def get_ips_with_excessive_attempts(
        self, threshhold: int, time_delta: datetime.timedelta
    ) -> List[str]:
        pass

    @abstractmethod
    async def cleanup_old_attempts(self, older_than_mins: int) -> None:
        pass


class CreateMediaAttemptsRepositoryInterface(ABC):
    @abstractmethod
    async def insert(self, entity: CreateMediaAttempt) -> None:
        pass

    @abstractmethod
    async def get_user_ids_with_excessive_attempts(
        self, threshhold: int, time_delta: datetime.timedelta
    ) -> List[uuid.UUID]:
        pass

    @abstractmethod
    async def cleanup_old_attempts(self, older_than_mins: int) -> None:
        pass
