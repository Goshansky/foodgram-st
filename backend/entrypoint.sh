#!/bin/sh
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"
mkdir -p /app/data
echo "Creating migrations..."
python manage.py makemigrations users
python manage.py makemigrations recipes
python manage.py makemigrations api
echo "Applying migrations..."
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py create_default_image
python manage.py import_ingredients
python manage.py create_test_data
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput
fi
exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 