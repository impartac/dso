import datetime


class SecurityException(Exception):
    """Базовое исключение для security модуля"""

    pass


class RateLimitException(SecurityException):
    def __init__(self, blocked_until: datetime.datetime):
        self.blocked_until = blocked_until
        super().__init__(f"Rate limit exceeded. Blocked until {blocked_until}")


class CreateMediaRateLimitException(RateLimitException):
    pass


class LoginException(Exception):
    """Базовое исключение для ошибок аутентификации"""

    pass


class LoginRateLimitException(LoginException):
    """Исключение при превышении лимита попыток входа"""

    def __init__(self, retry_after: datetime.datetime):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after: {retry_after}")


class InvalidCredentialsException(LoginException):
    """Исключение при неверных учетных данных"""

    pass


class UserNotFoundException(LoginException):
    """Исключение когда пользователь не найден"""

    pass
