import hashlib
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Request
from infrastructure.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля с использованием bcrypt"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Хеширование пароля с использованием bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def hash_sha256(data: str) -> str:
    """SHA256 хеш для user agent"""
    return hashlib.sha256(data.encode()).hexdigest()


async def get_client_ip(request: Request) -> str:
    headers_to_check = [
        "x-forwarded-for",
        "x-real-ip",
        "x-client-ip",
        "cf-connecting-ip",
        "true-client-ip",
    ]

    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            if header == "x-forwarded-for" and "," in ip:
                ip = ip.split(",")[0].strip()
            return ip

    if request.client and request.client.host:
        return request.client.host

    return "unknown"