# STAGE 1: Сборка зависимостей
FROM python:3.13-slim AS builder

# Системные зависимости + ОБЯЗАТЕЛЬНО curl для установки Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv .venv
COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry
# Устанавливаем зависимости
RUN poetry install --no-interaction --no-root

# STAGE 2: Финальный образ
FROM python:3.13-slim

# Runtime-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем виртуальное окружение и код
COPY --from=builder /app/.venv /app/.venv
COPY . /app/

# Настройка окружения
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Запуск бота
CMD ["python", "-m", "src.main"]