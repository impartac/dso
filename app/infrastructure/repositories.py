import datetime
import uuid
from typing import List, Optional

from domain.entities import CreateMediaAttempt, LoginAttempt, Media, User
from domain.repositories import (
    CreateMediaAttemptsRepositoryInterface,
    LoginAttemptsRepositoryInterface,
    MediaRepositoryInterface,
    UserRepositoryInterface,
)
from domain.value_objects import Email, MediaStatus
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .orm import (
    CreateMediaAttemptORM,
    LoginAttemptORM,
    MediaORM,
    UserORM,
    create_media_attempt_from_entity,
    login_attempt_from_entity,
    login_attempt_to_entity,
    media_from_entity,
    media_to_entity,
    user_from_entity,
    user_to_entity,
)


class Repository:

    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session


class UserRepository(Repository, UserRepositoryInterface):

    async def insert(self, entity: User) -> None:
        orm = user_from_entity(entity)
        self._session.add(orm)
        await self._session.flush()

    async def get(self, id: uuid.UUID) -> Optional[User]:
        stmt = select(UserORM).where(UserORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return user_to_entity(orm) if orm else None

    async def get_by_email(self, email: Email) -> Optional[User]:
        stmt = select(UserORM).where(UserORM.email == str(email))
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return user_to_entity(orm) if orm else None

    async def update(self, entity: User) -> None:
        stmt = select(UserORM).where(UserORM.id == entity.id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()

        orm.email = entity.email
        orm.role = entity.role
        orm.hash_password = entity.hash_password
        orm.updated_at = datetime.datetime.now()

        await self._session.flush()

    async def delete(self, id: uuid.UUID) -> bool:
        stmt = select(UserORM).where(UserORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()

        if orm:
            await self._session.delete(orm)
            await self._session.flush()
            return True
        return False


class MediaRepository(Repository, MediaRepositoryInterface):

    async def get(self, id: uuid.UUID) -> Optional[Media]:
        stmt = select(MediaORM).where(MediaORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return media_to_entity(orm) if orm else None

    async def insert(self, entity: Media) -> uuid.UUID:
        orm = media_from_entity(entity)
        self._session.add(orm)
        await self._session.flush()
        return orm.id

    async def update(self, entity: Media) -> Optional[Media]:
        stmt = select(MediaORM).where(MediaORM.id == entity.id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()

        if not orm:
            return None

        orm.kind = entity.kind
        orm.name = entity.name
        orm.title = entity.title
        orm.status = entity.status
        orm.owner_id = entity.owner_id
        orm.updated_at = datetime.datetime.now()

        await self._session.flush()
        return media_to_entity(orm)

    async def delete(self, id: uuid.UUID) -> Optional[Media]:
        stmt = select(MediaORM).where(MediaORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()

        if orm:
            await self._session.delete(orm)
            await self._session.flush()
            return media_to_entity(orm)
        return None

    async def get_by_owner(
        self,
        owner_id: uuid.UUID,
        status: Optional[MediaStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Media]:
        stmt = select(MediaORM).where(MediaORM.owner_id == owner_id)

        if status:
            stmt = stmt.where(MediaORM.status == status)

        stmt = stmt.offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        orm_list = result.scalars().all()
        return [media_to_entity(orm) for orm in orm_list]

    async def get_by_status(
        self, status: MediaStatus, skip: int = 0, limit: int = 100
    ) -> List[Media]:
        stmt = select(MediaORM).where(MediaORM.status == status)
        stmt = stmt.offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        orm_list = result.scalars().all()
        return [media_to_entity(orm) for orm in orm_list]


class LoginAttemptsRepository(Repository, LoginAttemptsRepositoryInterface):

    async def insert(self, entity: LoginAttempt) -> None:
        orm = login_attempt_from_entity(entity)
        self._session.add(orm)
        await self._session.flush()

    async def get_ips_with_excessive_attempts(
        self, threshold: int, time_delta: datetime.timedelta,
    ) -> List[str]:
        time_threshold = datetime.datetime.now() - time_delta

        stmt = (
            select(LoginAttemptORM.ip_address)
            .where(
                and_(
                    LoginAttemptORM.timestamp >= time_threshold,
                )
            )
            .group_by(LoginAttemptORM.ip_address)
            .having(func.count(1) >= threshold)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def cleanup_old_attempts(self, older_than_mins: int) -> None:
        time_threshold = datetime.datetime.now() - datetime.timedelta(
            minutes=older_than_mins
        )

        stmt = delete(LoginAttemptORM).where(LoginAttemptORM.timestamp < time_threshold)

        await self._session.execute(stmt)
        await self._session.flush()

class CreateMediaAttemptsRepository(Repository, CreateMediaAttemptsRepositoryInterface):
    async def insert(self, entity: CreateMediaAttempt) -> None:
        orm = create_media_attempt_from_entity(entity)
        self._session.add(orm)
        await self._session.flush()

    async def get_user_ids_with_excessive_attempts(
        self, threshold: int, time_delta: datetime.timedelta
    ) -> List[uuid.UUID]:
        time_threshold = datetime.datetime.now() - time_delta

        stmt = (
            select(CreateMediaAttemptORM.user_id)
            .where(
                and_(
                    CreateMediaAttemptORM.timestamp >= time_threshold,
                )
            )
            .group_by(CreateMediaAttemptORM.user_id)
            .having(func.count(1) >= threshold)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def cleanup_old_attempts(self, older_than_mins : int) -> None:
        time_threshold = datetime.datetime.now() - datetime.timedelta(
            minutes=older_than_mins
        )

        stmt = delete(CreateMediaAttemptORM).where(CreateMediaAttemptORM.timestamp < time_threshold)

        await self._session.execute(stmt)
        await self._session.flush()
