import datetime

from pydantic import BaseModel


class LoginAttemptDTO(BaseModel):
    ip_address: str
    timestamp: datetime.datetime
    successful: bool
