# ============================================================================
# STAGE 1: Builder - Установка зависимостей и тестирование
# ============================================================================
FROM python:3.11-slim AS builder

# Установка переменных окружения для оптимизации Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка необходимых системных пакетов для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Копирование файлов зависимостей
COPY requirements.txt requirements-dev.txt ./

# Установка зависимостей в виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Копирование исходного кода для тестирования
COPY . .

# Запуск тестов
RUN pytest -v --tb=short

# ============================================================================
# STAGE 2: Runtime - Минимальный продакшн образ
# ============================================================================
FROM python:3.11-slim

# Метаданные образа
LABEL maintainer="DevOps Team" \
      version="1.0" \
      description="Production-ready Python FastAPI application"

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Установка curl для healthcheck (минимальные зависимости)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Создание непривилегированного пользователя с домашней директорией
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 -d /app appuser && \
    mkdir -p /tmp/app /var/log/app && \
    chown -R appuser:appuser /app /tmp/app /var/log/app

# Копирование виртуального окружения из builder stage
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Копирование только необходимого исходного кода (без dev зависимостей и тестов)
COPY --chown=appuser:appuser --exclude=tests --exclude=.pytest_cache \
     --exclude=.git --exclude=__pycache__ . .

# Создание директорий для логов и временных файлов
RUN mkdir -p /tmp/app /var/log/app && \
    chown -R appuser:appuser /tmp/app /var/log/app

# Expose port
EXPOSE 8000

# Healthcheck: проверка доступности приложения
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Переключение на непривилегированного пользователя
USER appuser

# Run приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
