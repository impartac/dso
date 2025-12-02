from abc import ABC, abstractmethod


class HasherInterface(ABC):
    
    @abstractmethod
    async def get_hash(self, password : str) -> str:
        pass
    
    @abstractmethod
    async def verify(self, password: str, hashed_password: str) -> bool:
        pass