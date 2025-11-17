import datetime
import uuid
from typing import Optional

from pydantic import BaseModel


class LoginAttemptDTO(BaseModel):
    ip_address: str
    user_id: uuid.UUID
    timestamp: datetime.datetime
    successful: bool
    user_agent: Optional[str] = None
