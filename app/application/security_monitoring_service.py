from uuid import UUID

from ..domain.entities import LoginAttempt
from ..domain.errors import LoginException, LoginRateLimitException
from ..domain.repositories import SecurityRepositoryInterface
from ..domain.value_objects import SecurityPolicy
from .dtos import LoginAttemptDTO


class SecurityMonitoringService:
    _security_repo: SecurityRepositoryInterface
    _security_policy: SecurityPolicy

    def __init__(
        self, repo: SecurityRepositoryInterface, policy: SecurityPolicy
    ) -> None:
        self._security_repo = repo
        self._security_policy = policy

    async def process(self, dto: LoginAttemptDTO) -> None:
        if not dto.successful:
            if await self._ip_is_blocked(dto):
                raise LoginRateLimitException(
                    dto.timestamp + self._security_policy.ip_block_duration
                )
            raise LoginException()

    async def _record_login_attemp(self, dto: LoginAttemptDTO) -> UUID:

        entity = await self._create_login_attemp_from_dto(dto)

        return await self._security_repo.insert(entity)

    async def _ip_is_blocked(self, dto: LoginAttemptDTO) -> bool:
        """NFR-1"""

        ips_with_excessive_attempts = (
            await self._security_repo.get_ips_with_excessive_attempts(
                self._security_policy.max_failed_login_attempts,
                self._security_policy.failed_attempts_time_window,
            )
        )

        return dto.ip_address not in ips_with_excessive_attempts

    async def _create_login_attemp_from_dto(self, dto: LoginAttemptDTO) -> LoginAttempt:
        return LoginAttempt(
            ip_address=dto.ip_address,
            user_id=dto.user_id,
            timestamp=dto.timestamp,
            successful=dto.successful,
        )
