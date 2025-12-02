import re

import bcrypt
from application.hasher_interface import HasherInterface


class Hasher(HasherInterface):
    
    def __init__(self, rounds: int = 12):
        self.rounds = rounds
        self._bcrypt_pattern = re.compile(r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$')
    
    async def get_hash(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")

        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(
            password.encode('utf-8'), 
            salt
        )
        return hashed.decode('utf-8')
    
    async def verify(self, password: str, hashed_password: str) -> bool:
        """Проверяет пароль"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False
        