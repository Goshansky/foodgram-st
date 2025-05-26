import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Создает изображение по умолчанию для рецептов"

    def handle(self, *args, **options):
        try:
            # Путь к директории для изображений рецептов
            images_dir = os.path.join(settings.MEDIA_ROOT, "recipes", "images")

            # Создаем директорию, если она не существует
            os.makedirs(images_dir, exist_ok=True)

            # Путь к файлу изображения по умолчанию
            default_image_path = os.path.join(images_dir, "default_recipe.png")

            # Проверяем, существует ли файл
            if not os.path.exists(default_image_path):
                # Создаем простое изображение
                with open(default_image_path, "wb") as f:
                    # Минимальное изображение JPEG
                    f.write(
                        bytes(
                            [
                                0xFF,
                                0xD8,
                                0xFF,
                                0xE0,
                                0x00,
                                0x10,
                                0x4A,
                                0x46,
                                0x49,
                                0x46,
                                0x00,
                                0x01,
                                0x01,
                                0x01,
                                0x00,
                                0x48,
                                0x00,
                                0x48,
                                0x00,
                                0x00,
                                0xFF,
                                0xDB,
                                0x00,
                                0x43,
                                0x00,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xFF,
                                0xC0,
                                0x00,
                                0x0B,
                                0x08,
                                0x00,
                                0x01,
                                0x00,
                                0x01,
                                0x01,
                                0x01,
                                0x11,
                                0x00,
                                0xFF,
                                0xC4,
                                0x00,
                                0x14,
                                0x00,
                                0x01,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0xFF,
                                0xC4,
                                0x00,
                                0x14,
                                0x10,
                                0x01,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0x00,
                                0xFF,
                                0xDA,
                                0x00,
                                0x08,
                                0x01,
                                0x01,
                                0x00,
                                0x00,
                                0x3F,
                                0x00,
                                0x37,
                                0xFF,
                                0xD9,
                            ]
                        )
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Изображение по умолчанию создано: {default_image_path}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Изображение по умолчанию уже существует: {default_image_path}"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при создании изображения по умолчанию: {e}")
            )
