import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f"temp.{ext}")
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):

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
        if len(value) > 254:
            raise serializers.ValidationError(
                "Email должен содержать не более 254 символов."
            )
        return value

    def validate_username(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                "Username должен содержать не более 150 символов."
            )
        return value

    def validate_first_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                "Имя должно содержать не более 150 символов."
            )
        return value

    def validate_last_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                "Фамилия должна содержать не более 150 символов."
            )
        return value


class CustomUserSerializer(UserSerializer):

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
        return Subscription.objects.filter(user=user, author=obj).exists()


class SetAvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        if value is None:
            raise serializers.ValidationError("Поле avatar обязательно.")
        return value


class SetAvatarResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("avatar",)
        read_only_fields = ("avatar",)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


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
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeListSerializer(serializers.ModelSerializer):

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
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
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        view = self.context.get("request").parser_context.get("view")
        if view and view.action == "retrieve":
            if "tags" in representation:
                representation.pop("tags")

        if isinstance(self.root.instance, list) or (view and view.action == "list"):
            if "tags" in representation:
                representation.pop("tags")

        return representation


class RecipeCreateSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=False
    )
    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField(required=True)
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужно добавить хотя бы один ингредиент!")
        ingredient_ids = [item["id"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться!")
        for item in value:
            if item["amount"] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть не меньше 1!"
                )
        return value

    def validate_tags(self, value):
        if value and len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться!")
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть не меньше 1 минуты!"
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        if tags:
            recipe.tags.set(tags)
        self._create_recipe_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        if "tags" in validated_data:
            tags = validated_data.pop("tags")
            instance.tags.clear()
            if tags:
                instance.tags.set(tags)

        if "ingredients" in validated_data:
            ingredients_data = validated_data.pop("ingredients")
            instance.recipe_ingredients.all().delete()
            self._create_recipe_ingredients(instance, ingredients_data)
        elif self.partial:
            pass
        else:
            raise serializers.ValidationError({"ingredients": ["Обязательное поле."]})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

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
        representation = RecipeListSerializer(instance, context=self.context).data

        if "tags" in representation:
            representation.pop("tags")

        return representation


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(CustomUserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ("recipes", "recipes_count")

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

        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


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

    def validate(self, data):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            raise serializers.ValidationError(
                "Для добавления в избранное необходимо авторизоваться"
            )
        return data

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

    def validate(self, data):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            raise serializers.ValidationError(
                "Для добавления в список покупок необходимо авторизоваться"
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(instance.recipe, context=self.context).data
