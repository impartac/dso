import datetime
import uuid
from dataclasses import dataclass


@dataclass
class LoginAttemptDTO:
    ip_address: str
    user_id: uuid.UUID
    successful: bool
    timestamp: datetime.datetime
