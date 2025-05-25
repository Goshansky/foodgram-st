from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           ShoppingCart, Tag)
from users.models import Subscription, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, FavoriteSerializer,
                         IngredientSerializer, RecipeCreateSerializer,
                         RecipeListSerializer, RecipeMinifiedSerializer,
                         SetAvatarSerializer, SetAvatarResponseSerializer,
                         ShoppingCartSerializer, TagSerializer,
                         UserWithRecipesSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeListSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        return self._add_to_list(
            request, pk, FavoriteSerializer, 'recipe', 'user'
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        return self._delete_from_list(
            request, pk, Favorite, 'recipe', 'Рецепт удален из избранного'
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок."""
        return self._add_to_list(
            request, pk, ShoppingCartSerializer, 'recipe', 'user'
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаление рецепта из списка покупок."""
        return self._delete_from_list(
            request, pk, ShoppingCart, 'recipe',
            'Рецепт удален из списка покупок'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = "Список покупок:\n\n"
        for item in ingredients:
            shopping_list += (
                f"- {item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}\n"
            )

        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def _add_to_list(self, request, pk, serializer_class,
                    obj_field, user_field):
        """Общий метод для добавления рецепта в список."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            obj_field: recipe.id,
            user_field: request.user.id
        }
        serializer = serializer_class(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_from_list(self, request, pk, model, obj_field, message):
        """Общий метод для удаления рецепта из списка."""
        recipe = get_object_or_404(Recipe, pk=pk)
        obj = model.objects.filter(
            **{obj_field: recipe, 'user': request.user}
        )
        if obj.exists():
            obj.delete()
            return Response(
                {'detail': message},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': 'Рецепт не найден в списке'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление для пользователей."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    permission_classes = (AllowAny,)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписка на пользователя."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscription.objects.create(user=user, author=author)
        serializer = UserWithRecipesSerializer(
            author,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Отписка от пользователя."""
        author = get_object_or_404(User, pk=pk)
        user = request.user
        subscription = Subscription.objects.filter(user=user, author=author)

        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated]
    )
    def me_avatar(self, request):
        """Добавление аватара текущему пользователю."""
        serializer = SetAvatarSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SetAvatarResponseSerializer(request.user).data,
            status=status.HTTP_200_OK
        )

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара текущего пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT) 