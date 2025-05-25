import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag)
from users.models import Subscription, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на просматриваемого."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user, author=obj
        ).exists()


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для установки аватара пользователя."""
    class Meta:
        model = User
        fields = ('avatar',)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа на установку аватара."""
    class Meta:
        model = User
        fields = ('avatar',)
        read_only_fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class Base64ImageField(serializers.ImageField):
    """Поле для работы с изображениями в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в списке покупок."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=user, recipe=obj
        ).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент!'
            )
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться!'
            )
        return value

    def validate_tags(self, value):
        """Валидация тегов."""
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один тег!'
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги не должны повторяться!'
            )
        return value

    def validate_cooking_time(self, value):
        """Валидация времени приготовления."""
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть не меньше 1 минуты!'
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)

        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._create_recipe_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        """Создание связей между рецептом и ингредиентами."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    def to_representation(self, instance):
        """Представление созданного/обновленного рецепта."""
        return RecipeListSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор для упрощенного представления рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(CustomUserSerializer):
    """Сериализатор для пользователя с рецептами."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получение рецептов пользователя с учетом лимита."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов пользователя."""
        return obj.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном'
            )
        ]

    def to_representation(self, instance):
        """Представление избранного рецепта."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок'
            )
        ]

    def to_representation(self, instance):
        """Представление рецепта в списке покупок."""
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class RecipeGetShortLinkSerializer(serializers.Serializer):
    """Сериализатор для получения короткой ссылки на рецепт."""
    short_link = serializers.URLField(source='short-link') 