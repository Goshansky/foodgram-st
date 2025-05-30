from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
from users.models import Subscription, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    RecipeMinifiedSerializer,
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
    UserWithRecipesSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None

    def list(self, request, *args, **kwargs):
        name_param = request.query_params.get("name")
        if name_param:
            queryset = []
            for ingredient in self.get_queryset():
                if ingredient.name.startswith(name_param):
                    queryset.append(ingredient)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RecipeCreateSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=["get"], permission_classes=[AllowAny], url_path="get-link"
    )
    def get_link(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            return Response({"short-link": f"/recipes/{recipe.id}/"})
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора рецепта"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user

            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен в избранное"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора рецепта"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user
            favorite = Favorite.objects.filter(user=user, recipe=recipe)

            if not favorite.exists():
                return Response(
                    {"errors": "Рецепт не найден в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора рецепта"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user

            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен в список покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора рецепта"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user
            shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)

            if not shopping_cart.exists():
                return Response(
                    {"errors": "Рецепт не найден в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора рецепта"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shopping_cart__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        shopping_list = []
        shopping_list.append("============= СПИСОК ПОКУПОК =============")
        shopping_list.append("")
        
        for index, item in enumerate(ingredients, start=1):
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            amount = item["total_amount"]
            shopping_list.append(f"{index}. {name} ({unit}) — {amount}")
        
        shopping_list.append("")
        shopping_list.append("========= ПРИЯТНОГО ПРИГОТОВЛЕНИЯ! =========")
        
        response = HttpResponse("\n".join(shopping_list), content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'
        return response

    def update(self, request, *args, **kwargs):
        self.get_object()

        if request.method == "PATCH" and "ingredients" not in request.data:
            return Response(
                {"ingredients": ["Обязательное поле."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    pagination_class = CustomPagination
    http_method_names = ["get", "post", "delete", "put"]

    def get_serializer_class(self):
        if self.action == "create":
            from djoser.serializers import UserCreateSerializer

            return UserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in [
            "me",
            "me_avatar",
            "delete_avatar",
            "subscriptions",
            "subscribe",
            "unsubscribe",
            "set_password",
        ]:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = CustomUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            subscriptions, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        try:
            author = get_object_or_404(User, pk=pk)
            user = request.user

            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора пользователя"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        try:
            author = get_object_or_404(User, pk=pk)
            user = request.user
            subscription = Subscription.objects.filter(user=user, author=author)

            if not subscription.exists():
                return Response(
                    {"errors": "Вы не подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {"errors": "Неверный формат идентификатора пользователя"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=False,
        methods=["put", "post"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def me_avatar(self, request):
        if "avatar" not in request.data:
            return Response(
                {"avatar": ["Обязательное поле."]}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SetAvatarSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_serializer = SetAvatarResponseSerializer(request.user)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"errors": "Необходимо указать текущий и новый пароль"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"current_password": ["Неправильный пароль"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
