from django.db import transaction
from django.conf import settings
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from users.models import User


class ImageUrlField(serializers.ImageField):

    def to_representation(self, value):
        if not value:
            return ""

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(value.url)
        return value.url


class SignupSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "password": {"required": True, "write_only": True},
        }

    def validate_email(self, value):
        if len(value) > settings.MAX_EMAIL_LENGTH:
            raise serializers.ValidationError(
                f"Email должен содержать не более {settings.MAX_EMAIL_LENGTH} символов."
            )
        return value

    def validate_username(self, value):
        if len(value) > settings.MAX_USERNAME_LENGTH:
            raise serializers.ValidationError(
                f"Username должен содержать не более {settings.MAX_USERNAME_LENGTH} символов."
            )
        return value

    def validate_first_name(self, value):
        if len(value) > settings.MAX_FIRST_NAME_LENGTH:
            raise serializers.ValidationError(
                f"Имя должно содержать не более {settings.MAX_FIRST_NAME_LENGTH} символов."
            )
        return value

    def validate_last_name(self, value):
        if len(value) > settings.MAX_LAST_NAME_LENGTH:
            raise serializers.ValidationError(
                f"Фамилия должна содержать не более {settings.MAX_LAST_NAME_LENGTH} символов."
            )
        return value


class ProfileSerializer(UserSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()


class SetAvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        if value is None:
            raise serializers.ValidationError("Поле avatar обязательно.")
        return value


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")

    def validate_amount(self, value):
        if value < settings.MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError(
                f"Количество ингредиента должно быть не меньше {settings.MIN_INGREDIENT_AMOUNT}!"
            )
        return value


class RecipeListSerializer(serializers.ModelSerializer):

    author = ProfileSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = ImageUrlField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):

    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField(required=True)
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate(self, data):
        if self.instance is not None and self.context["request"].method == "PATCH":
            if "ingredients" not in data:
                raise serializers.ValidationError(
                    {"ingredients": ["Обязательное поле."]}
                )
        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужно добавить хотя бы один ингредиент!")
        ingredient_ids = [item["id"].id for item in value]
        unique_ids = set(ingredient_ids)

        if len(ingredient_ids) != len(unique_ids):
            raise serializers.ValidationError("Ингредиенты не должны повторяться!")

        return value

    def validate_cooking_time(self, value):
        if value < settings.MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f"Время приготовления должно быть не меньше {settings.MIN_COOKING_TIME} минуты!"
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        instance.recipe_ingredients.all().delete()
        self._create_recipe_ingredients(instance, ingredients_data)

        instance = super().update(instance, validated_data)
        return instance

    def _create_recipe_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = ImageUrlField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(ProfileSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        recipes = obj.recipes.all()

        if limit:
            try:
                limit = int(limit)
                recipes = recipes[:limit]
            except ValueError:
                pass

        serializer = RecipeMinifiedSerializer(recipes, many=True, context=self.context)
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=("user", "recipe"),
                message="Рецепт уже добавлен в избранное",
            )
        ]

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=("user", "recipe"),
                message="Рецепт уже добавлен в список покупок",
            )
        ]

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe, context=self.context).data
