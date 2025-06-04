# Foodgram - Продуктовый помощник

## Описание проекта

Foodgram - это веб-приложение, которое позволяет пользователям публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис "Список покупок" позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Технологии
- Python 3.12
- Django 3.2
- Django REST Framework
- PostgreSQL
- Docker
- Nginx
- Gunicorn

## Запуск проекта

### Предварительные требования
- Docker и Docker Compose

# !!!!!!!!!!!!!!!!!!!!!!

# Примечание!

## Пожалуйста, посмотрите видео по запуску https://disk.yandex.ru/i/eQ9JoT0WzPI9Qw, на котором проект запускается и жду Ваши комментарии по коду.

# !!!!!!!!!!!!!!!!!!!!!!

### Локальный запуск

1. Клонируйте репозиторий:
```
git clone https://github.com/Goshansky/foodgram-st.git
cd foodgram-st
```

2. Запустите проект с помощью Docker Compose:
```
cd infra
docker-compose up --build -d
```

3. После запуска контейнеров выполните миграции и загрузите ингредиенты (если это не произошло автоматически):
```
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py import_ingredients
```

4. Создайте суперпользователя:
```
docker-compose exec backend python manage.py createsuperuser
```

5. Доступ к проекту:
- Веб-интерфейс: http://localhost
- API-документация: http://localhost/api/docs/
- Админ-панель: http://localhost/admin/


### CI/CD с GitHub Actions
В проекте настроен полный цикл CI/CD через GitHub Actions:
1. При каждом пуше в main или pull request запускаются автоматические тесты Django и React.
2. После успешного прохождения тестов собираются Docker-образы:
 - foodgram_backend
 - foodgram_frontend
 - foodgram_gateway (nginx)
3. Готовые образы автоматически публикуются на DockerHub.
4. После публикации отправляется уведомление в Telegram о статусе сборки и деплоя.

### Требуемые секреты GitHub

Для работы CI/CD в репозитории необходимо добавить следующие секреты:
- `DOCKER_USERNAME` - имя пользователя DockerHub
- `DOCKER_PASSWORD` - пароль от DockerHub
- `TELEGRAM_TO` - ID чата Telegram для уведомлений о сборке отзыва
- `TELEGRAM_TOKEN` - токен бота Telegram
