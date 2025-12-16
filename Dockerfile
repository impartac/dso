# ============================================================================
# Builder stage
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends\
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .
COPY pyproject.toml .

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем зависимости в виртуальное окружение
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Production stage
# ============================================================================
FROM python:3.11-slim AS production

# Создаем не-root пользователя
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash -m appuser

WORKDIR /app

# Копируем виртуальное окружение из builder stage
COPY --from=builder /opt/venv /opt/venv

# Копируем код приложения
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser pyproject.toml .

# Устанавливаем системные зависимости только для runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Настройка окружения
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOGGER_LEVEL="INFO"

# Переключаемся на не-root пользователя
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["python", "app/main.py"]

# ============================================================================
# Development stage (optional)
# ============================================================================
FROM builder AS development

# Копируем весь код
COPY --chown=appuser:appuser . .

# Создаем не-root пользователя
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash -m appuser
USER appuser

# Разрешаем запись для hot-reload
RUN chmod -R 755 /app

ENV LOGGER_LEVEL="DEBUG"

CMD ["python", "app/main.py"]