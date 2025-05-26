from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(max_length=128, verbose_name="Название")
    measurement_unit = models.CharField(max_length=64, verbose_name="Единица измерения")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(max_length=64, unique=True, verbose_name="Название")
    color = models.CharField(max_length=7, unique=True, verbose_name="Цвет в HEX")
    slug = models.SlugField(max_length=64, unique=True, verbose_name="Уникальный слаг")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", verbose_name="Автор"
    )
    name = models.CharField(max_length=256, verbose_name="Название")
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Изображение",
        default="recipes/images/default_recipe.png",
    )
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингредиенты"
    )
    tags = models.ManyToManyField(Tag, verbose_name="Теги")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Время приготовления (в минутах)",
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента с указанием количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class Favorite(models.Model):
    """Модель избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], name="unique_favorite")
        ]

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в избранное"


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в список покупок"
