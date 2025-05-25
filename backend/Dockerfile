FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y netcat-openbsd

COPY . .

# Создание директорий для миграций, если их нет
RUN mkdir -p /app/recipes/migrations /app/users/migrations /app/api/migrations \
    && touch /app/recipes/migrations/__init__.py \
    && touch /app/users/migrations/__init__.py \
    && touch /app/api/migrations/__init__.py

# Генерация миграций
RUN python manage.py makemigrations users recipes

# Установка прав на выполнение скрипта
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/bin/sh", "entrypoint.sh"] 