import logging
from dataclasses import dataclass
from typing import List

from fastapi.security import HTTPBearer
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

security = HTTPBearer()

class Settings(BaseSettings):
    # JWT настройки (NFR-5)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS настройки
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Security настройки (NFR-1)
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    FAILED_ATTEMPTS_TIME_WINDOW: int = 300  # 5 minutes
    IP_BLOCK_DURATION: int = 900  # 15 minutes
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/mediacatalog"
    
    # Database connection settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
    # Application settings
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG, 
    future=True
)

session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)