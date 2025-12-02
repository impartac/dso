import datetime
from typing import Annotated

from application.services.authentication_service import AuthenticationService
from application.services.security_monitoring_service import SecurityMonitoringService
from domain.errors import LoginRateLimitException
from domain.value_objects import Email
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from infrastructure.config import settings
from pydantic import EmailStr

from .dependencies import (
    get_authentication_service,
    get_authorization_service,
    get_security_monitoring_service,
)
from .models import LoginResponse
from .security_utils import get_client_ip

login_router = APIRouter(prefix="/login")


@login_router.post(
    "/",
    response_model=LoginResponse,
)
async def login(
    response: Response,
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    security_monitoring_service: Annotated[SecurityMonitoringService, Depends(get_security_monitoring_service)],
    authentication_service: Annotated[AuthenticationService, Depends(get_authentication_service)]
) -> LoginResponse:
    try:
        client_ip = await get_client_ip(request)
        request_time = datetime.datetime.now()

        try:
            await security_monitoring_service.process_login(client_ip, request_time)
        except LoginRateLimitException as lr_exception:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error" : "Too many requests"
                },
                headers={
                    "Retry-After" : str(lr_exception.retry_after)
                }
            )
            
        email = Email(form_data.username)

        attempt = await authentication_service.login(email, form_data.password)

        if not attempt.successful:
            await security_monitoring_service.record_login_attemp(client_ip, request_time)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Invalid credentials provided",
                },
            )
        
        response.set_cookie(
            key="access_token",
            value=attempt.token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
            
        return LoginResponse(
            message="Login successful",
            token_type = "bearer",
            expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = {
                "message" : str(e)
            }
        )
        
    


@login_router.post(
    "/create",
    response_model=LoginResponse,
)
async def create_user(
    response: Response,
    email: EmailStr,
    password: str,
    authentication_service: Annotated[AuthenticationService, Depends(get_authentication_service)]
) -> LoginResponse:
    user_id = await authentication_service.register_user(Email(email), password)
    
    
    token = await authentication_service.create_token(user_id)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return LoginResponse(
        message="Login successful",
        token_type = "bearer",
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
