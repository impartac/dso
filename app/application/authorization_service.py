from ..domain.repositories import UserRepositoryInterface


class AuthorizationService:
    _user_repo: UserRepositoryInterface
