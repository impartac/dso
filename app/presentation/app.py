from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from infrastructure.config import logger, settings

from .login_router import login_router
from .media_router import media_router


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
    lifespan=lifespan,
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

# @app.middleware("http")
# async def security_middleware(request: Request, call_next):
#     start_time = datetime.now()
#     correlation_id = str(uuid.uuid4())

#     client_host = request.client.host if request.client else "unknown"
#     log_message = f"Request: {request.method} {request.url} - Client: {client_host} - \
#         Correlation ID: {correlation_id}"
#     logger.info(mask_pii(log_message))

#     try:
#         response = await call_next(request)

#         process_time = (datetime.now() - start_time).total_seconds() * 1000
#         logger.info(
#             f"Response: {response.status_code} - Time: {process_time:.2f}ms - \
#                 Correlation ID: {correlation_id}"
#         )

#         response.headers["X-Content-Type-Options"] = "nosniff"
#         response.headers["X-Frame-Options"] = "DENY"
#         response.headers["X-XSS-Protection"] = "1; mode=block"
#         response.headers["Correlation-ID"] = correlation_id

#         return response

#     except Exception as exc:
#         logger.error(
#             f"Unhandled exception: {str(exc)} - Correlation ID: {correlation_id}"
#         )
#         raise


app.include_router(login_router)
app.include_router(media_router)
