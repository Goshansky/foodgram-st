#!/bin/sh

# Ожидание доступности базы данных
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Создание директории для данных, если она не существует
mkdir -p /app/data

# Создание миграций для всех приложений
echo "Creating migrations..."
python manage.py makemigrations users
python manage.py makemigrations recipes
python manage.py makemigrations api

# Выполнение миграций для всех приложений
echo "Applying migrations..."
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic --no-input

# Создание изображения по умолчанию для рецептов
python manage.py create_default_image

# Импорт ингредиентов
python manage.py import_ingredients

# Создание тестовых данных
python manage.py create_test_data

# Создание суперпользователя (опционально)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput
fi

# Запуск сервера Gunicorn
exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 