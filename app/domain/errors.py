import datetime


class SecurityException(Exception):
    """Базовое исключение для security модуля"""

    pass


class LoginException(SecurityException):
    pass


class LoginRateLimitException(LoginException):
    def __init__(self, blocked_until: datetime.datetime):
        self.blocked_until = blocked_until
        super().__init__(f"Login blocked until {blocked_until}")


class RateLimitException(SecurityException):
    def __init__(self, blocked_until: datetime.datetime):
        self.blocked_until = blocked_until
        super().__init__(f"Rate limit exceeded. Blocked until {blocked_until}")
