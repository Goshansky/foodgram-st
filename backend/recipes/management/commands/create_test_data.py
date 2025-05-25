import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recipes.models import Tag, Recipe, Ingredient, RecipeIngredient

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает тестовые данные для проекта'

    def handle(self, *args, **options):
        # Создание тегов, если их нет
        tags_data = [
            {'name': 'Завтрак', 'color': '#E26C2D', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#49B64E', 'slug': 'lunch'},
            {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'},
            {'name': 'Десерт', 'color': '#FF0000', 'slug': 'dessert'},
            {'name': 'Вегетарианское', 'color': '#00FF00', 'slug': 'vegetarian'}
        ]
        
        for tag_data in tags_data:
            Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults={
                    'name': tag_data['name'],
                    'color': tag_data['color']
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Теги созданы успешно'))
        
        # Создание тестовых пользователей
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Админ',
                'last_name': 'Админов',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'password': 'user123'
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'first_name': 'Мария',
                'last_name': 'Петрова',
                'password': 'user123'
            }
        ]
        
        users_for_recipes = []
        for user_data in users_data:
            is_staff = user_data.pop('is_staff', False)
            is_superuser = user_data.pop('is_superuser', False)
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()
            
            users_for_recipes.append(user)
        
        self.stdout.write(self.style.SUCCESS('Пользователи созданы успешно'))
        
        # Проверяем, есть ли уже рецепты
        if Recipe.objects.exists():
            self.stdout.write(self.style.SUCCESS('Рецепты уже существуют, пропускаем создание'))
            return
        
        # Создание тестовых рецептов
        if users_for_recipes and Ingredient.objects.exists():
            tags = list(Tag.objects.all())
            ingredients = list(Ingredient.objects.all())
            
            recipes_data = [
                {
                    'name': 'Омлет с сыром',
                    'text': 'Вкусный и питательный омлет с сыром на завтрак.',
                    'cooking_time': 15,
                    'ingredients': [
                        {'ingredient': random.choice(ingredients), 'amount': 2},
                        {'ingredient': random.choice(ingredients), 'amount': 100},
                        {'ingredient': random.choice(ingredients), 'amount': 50}
                    ]
                },
                {
                    'name': 'Паста Карбонара',
                    'text': 'Классическая итальянская паста с беконом и сливочным соусом.',
                    'cooking_time': 30,
                    'ingredients': [
                        {'ingredient': random.choice(ingredients), 'amount': 200},
                        {'ingredient': random.choice(ingredients), 'amount': 100},
                        {'ingredient': random.choice(ingredients), 'amount': 50},
                        {'ingredient': random.choice(ingredients), 'amount': 20}
                    ]
                },
                {
                    'name': 'Салат Цезарь',
                    'text': 'Популярный салат с курицей, сухариками и соусом.',
                    'cooking_time': 20,
                    'ingredients': [
                        {'ingredient': random.choice(ingredients), 'amount': 150},
                        {'ingredient': random.choice(ingredients), 'amount': 100},
                        {'ingredient': random.choice(ingredients), 'amount': 50},
                        {'ingredient': random.choice(ingredients), 'amount': 30}
                    ]
                }
            ]
            
            for user in users_for_recipes:
                for recipe_data in recipes_data:
                    recipe = Recipe.objects.create(
                        author=user,
                        name=recipe_data['name'],
                        text=recipe_data['text'],
                        cooking_time=recipe_data['cooking_time'],
                        image='recipes/images/default_recipe.png'
                    )
                    
                    # Добавление случайных тегов
                    recipe_tags = random.sample(tags, k=random.randint(1, len(tags)))
                    recipe.tags.set(recipe_tags)
                    
                    # Добавление ингредиентов
                    for ingredient_data in recipe_data['ingredients']:
                        RecipeIngredient.objects.create(
                            recipe=recipe,
                            ingredient=ingredient_data['ingredient'],
                            amount=ingredient_data['amount']
                        )
            
            self.stdout.write(self.style.SUCCESS('Рецепты созданы успешно'))
        else:
            self.stdout.write(self.style.WARNING(
                'Не удалось создать рецепты: нет пользователей или ингредиентов'
            )) 