import datetime
from uuid import UUID

from domain.entities import CreateMediaAttempt, LoginAttempt
from domain.errors import CreateMediaRateLimitException, LoginRateLimitException
from domain.value_objects import SecurityPolicy

from ..unit_of_wrok_interface import UnitOfWorkInterface


class SecurityMonitoringService:
    _uow: UnitOfWorkInterface
    _security_policy: SecurityPolicy

    def __init__(self, uow: UnitOfWorkInterface, policy: SecurityPolicy) -> None:
        self._uow = uow
        self._security_policy = policy

    async def process_login(self, ip: str, request_time: datetime.datetime) -> None:
        if await self._ip_is_blocked(ip):
            await self.record_login_attemp(ip, request_time)
            raise LoginRateLimitException(
                request_time + self._security_policy.ip_block_duration
            )

    async def process_create_media(
        self, user_id: UUID, request_time: datetime.datetime
    ) -> None:
        await self.record_create_media_attempt(user_id, request_time)

        if await self._user_is_blocked(user_id):

            raise CreateMediaRateLimitException(
                request_time + self._security_policy.user_block_duration
            )

    async def record_create_media_attempt(
        self, user_id: UUID, request_time: datetime.datetime
    ) -> None:

        entity = await self._create_media_attemp_from_dto(user_id, request_time)

        async with self._uow:
            create_media_attempt_repository = (
                await self._uow.get_create_media_attempt_repository()
            )
            await create_media_attempt_repository.insert(entity)

    async def record_login_attemp(
        self, ip: str, request_time: datetime.datetime
    ) -> None:

        entity = await self._create_login_attemp_from_dto(ip, request_time)

        async with self._uow:
            security_repository = await self._uow.get_login_attempts_repository()
            await security_repository.insert(entity)

    async def _ip_is_blocked(self, ip: str) -> bool:
        """NFR-1"""

        async with self._uow:
            security_repository = await self._uow.get_login_attempts_repository()

            ips_with_excessive_attempts = (
                await security_repository.get_ips_with_excessive_attempts(
                    self._security_policy.max_failed_login_attempts,
                    self._security_policy.failed_attempts_time_window,
                )
            )

        return ip in ips_with_excessive_attempts

    async def _user_is_blocked(self, user_id: UUID) -> bool:
        """NFR-2"""
        async with self._uow:
            create_media_attempt_repository = (
                await self._uow.get_create_media_attempt_repository()
            )

            query = create_media_attempt_repository.get_user_ids_with_excessive_attempts

            banned_users = await query(
                self._security_policy.media_creation_limit,
                self._security_policy.media_creation_window,
            )

        return user_id in banned_users

    async def _create_login_attemp_from_dto(
        self, ip: str, request_time: datetime.datetime
    ) -> LoginAttempt:
        return LoginAttempt(
            ip_address=ip,
            timestamp=request_time,
        )

    async def _create_media_attemp_from_dto(
        self, user_id: UUID, request_time: datetime.datetime
    ) -> CreateMediaAttempt:
        return CreateMediaAttempt(user_id=user_id, timestamp=request_time)
