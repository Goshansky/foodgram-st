# Foodgram - Продуктовый помощник

## Описание проекта

Foodgram - это веб-приложение, которое позволяет пользователям публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис "Список покупок" позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Технологии
- Python 3.9
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- Gunicorn

## Запуск проекта

### Предварительные требования
- Docker и Docker Compose

### Локальный запуск

1. Клонируйте репозиторий:
```
git clone https://github.com/username/foodgram-project.git
cd foodgram-project
```

2. Запустите проект с помощью Docker Compose:
```
cd infra
docker-compose up --build
```

4. После запуска контейнеров выполните миграции и загрузите ингредиенты (если это не произошло автоматически):
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py import_ingredients
```

5. Создайте суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```

6. Доступ к проекту:
- Веб-интерфейс: http://localhost
- API-документация: http://localhost/api/docs/
- Админ-панель: http://localhost/admin/

## Примеры API запросов

### Получение списка рецептов
```
GET /api/recipes/
```

### Получение конкретного рецепта
```
GET /api/recipes/{id}/
```

### Создание рецепта (требуется аутентификация)
```
POST /api/recipes/
{
    "ingredients": [
        {
            "id": 1,
            "amount": 10
        }
    ],
    "tags": [
        1,
        2
    ],
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "name": "Название рецепта",
    "text": "Описание рецепта",
    "cooking_time": 5
}
```

### Получение списка покупок (требуется аутентификация)
```
GET /api/recipes/download_shopping_cart/
```

