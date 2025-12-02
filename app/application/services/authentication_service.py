import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt
from domain.entities import User
from domain.value_objects import Email, UserRole

from ..hasher_interface import HasherInterface
from ..unit_of_wrok_interface import UnitOfWorkInterface


@dataclass
class AuthenticationAttempt:
    successful: bool
    token: str


class AuthenticationService:

    def __init__(
        self,
        uow: UnitOfWorkInterface,
        hasher: HasherInterface,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
    ) -> None:
        self._hasher = hasher
        self._uow = uow
        self.__SECRET_KEY = secret_key
        self.__ALGORITHM = algorithm
        self.__ACCESS_TOKEN_EXPIRE_MINUTES = access_token_expire_minutes

    async def login(self, email: Email, password: str) -> AuthenticationAttempt:

        async with self._uow:

            user_repository = await self._uow.get_user_repository()

            user = await user_repository.get_by_email(email)

            if user and await self._hasher.verify(password, user.hash_password):

                token = await self.create_token(user.id)

                return AuthenticationAttempt(
                    successful=True,
                    token=token,
                )

            return AuthenticationAttempt(
                successful=False,
                token="",
            )

    async def create_token(self, user_id: UUID) -> str:

        expire_at = datetime.now() + timedelta(
            minutes=self.__ACCESS_TOKEN_EXPIRE_MINUTES
        )

        encoded_jwt = jwt.encode(
            {"user_id": str(user_id), "exp": expire_at},
            self.__SECRET_KEY,
            algorithm=self.__ALGORITHM,
        )

        return encoded_jwt

    async def validate_token(self, token: str) -> Optional[User]:

        payload = jwt.decode(token, self.__SECRET_KEY, algorithms=[self.__ALGORITHM])

        user_id: str = payload.get("user_id")

        if not user_id:
            return None

        async with self._uow:
            user_repository = await self._uow.get_user_repository()

            user = await user_repository.get(uuid.UUID(user_id))

        return user

    async def register_user(self, email: Email, password: str) -> UUID:

        async with self._uow:
            user_repository = await self._uow.get_user_repository()

            hash_password = await self._hasher.get_hash(password)

            user = User(email, UserRole.USER, hash_password)

            return await user_repository.insert(user)
