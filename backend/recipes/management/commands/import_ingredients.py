import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON-файла'

    def handle(self, *args, **options):
        try:
            data_path = os.path.join(
                settings.BASE_DIR, '..', 'data', 'ingredients.json'
            )

            with open(data_path, 'r', encoding='utf-8') as file:
                ingredients = json.load(file)

            ingredients_to_create = []
            for ingredient in ingredients:
                ingredients_to_create.append(
                    Ingredient(
                        name=ingredient['name'],
                        measurement_unit=ingredient['measurement_unit']
                    )
                )

            Ingredient.objects.bulk_create(
                ingredients_to_create,
                ignore_conflicts=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно импортировано {len(ingredients_to_create)} '
                    'ингредиентов'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка импорта ингредиентов: {e}')
            ) 