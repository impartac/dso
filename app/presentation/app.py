import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from ..infrastructure.config import logger, settings
from .dependencies import mask_pii
from .handlers import router
from .models import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application starting up")
    yield
    # Shutdown
    logger.info("Application shutting down")


app = FastAPI(
    title="Media Catalog API",
    description="Secure media catalog management system",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(GZipMiddleware, minimum_size=1000)





# Глобальные обработчики ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = str(uuid.uuid4())
    
    # Логируем с маскировкой PII
    log_message = f"HTTP error {exc.status_code}: {exc.detail} - Correlation ID: {correlation_id}"
    logger.error(mask_pii(log_message))
    
    error_response = ErrorResponse(
        error="Произошла ошибка",
        correlation_id=correlation_id,
        timestamp=datetime.utcnow()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response.dict())
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = str(uuid.uuid4())
    
    # Логируем полную ошибку, но возвращаем унифицированное сообщение
    logger.error(f"Internal server error: {str(exc)} - Correlation ID: {correlation_id}")
    
    error_response = ErrorResponse(
        error="Произошла ошибка",
        correlation_id=correlation_id,
        timestamp=datetime.utcnow()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(error_response.dict())
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = str(uuid.uuid4())
    
    logger.warning(f"Validation error: {exc.errors()} - Correlation ID: {correlation_id}")
    
    error_response = ErrorResponse(
        error="Некорректные данные",
        correlation_id=correlation_id,
        timestamp=datetime.utcnow()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response.dict())
    )

# Middleware для логирования и безопасности
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    start_time = datetime.now()
    correlation_id = str(uuid.uuid4())
    
    # Логируем запрос с маскировкой PII
    client_host = request.client.host if request.client else "unknown"
    log_message = f"Request: {request.method} {request.url} - Client: {client_host} - Correlation ID: {correlation_id}"
    logger.info(mask_pii(log_message))
    
    try:
        response = await call_next(request)
        
        # Логируем ответ
        process_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Response: {response.status_code} - Time: {process_time:.2f}ms - Correlation ID: {correlation_id}")
        
        # Добавляем security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Correlation-ID"] = correlation_id
        
        return response
        
    except Exception as exc:
        logger.error(f"Unhandled exception: {str(exc)} - Correlation ID: {correlation_id}")
        raise


app.include_router(router)