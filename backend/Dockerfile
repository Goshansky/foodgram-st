FROM python:3.9-slim

WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip3 install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y netcat-openbsd

# Копируем конфигурационные файлы проекта
COPY ./foodgram ./foodgram/
COPY ./manage.py .

# Создаем директории для приложений и их миграций
RUN mkdir -p recipes users api \
    && mkdir -p recipes/migrations users/migrations api/migrations \
    && touch recipes/migrations/__init__.py \
    && touch users/migrations/__init__.py \
    && touch api/migrations/__init__.py

# Копируем код приложений
COPY ./recipes ./recipes/
COPY ./users ./users/
COPY ./api ./api/

# Копируем скрипт запуска
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/bin/sh", "entrypoint.sh"] 