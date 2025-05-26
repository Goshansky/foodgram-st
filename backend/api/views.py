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
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeListSerializer
        
    def perform_create(self, serializer):
        """Создание рецепта с указанием автора."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user
            
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            favorite = Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError:
            return Response(
                {'errors': 'Неверный формат идентификатора рецепта'},
                status=status.HTTP_404_NOT_FOUND
            )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            
            if not favorite.exists():
                return Response(
                    {'errors': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {'errors': 'Неверный формат идентификатора рецепта'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок."""
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user
            
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен в список покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            shopping_cart = ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError:
            return Response(
                {'errors': 'Неверный формат идентификатора рецепта'},
                status=status.HTTP_404_NOT_FOUND
            )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаление рецепта из списка покупок."""
        try:
            recipe = get_object_or_404(Recipe, pk=pk)
            user = request.user
            shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            
            if not shopping_cart.exists():
                return Response(
                    {'errors': 'Рецепт не найден в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {'errors': 'Неверный формат идентификатора рецепта'},
                status=status.HTTP_404_NOT_FOUND
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




class UserViewSet(viewsets.ModelViewSet):
    """Представление для пользователей."""
    queryset = User.objects.all()
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'delete']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            # Используем сериализатор из djoser для создания пользователя
            from djoser.serializers import UserCreateSerializer
            return UserCreateSerializer
        return CustomUserSerializer
    
    def get_permissions(self):
        """Определение прав доступа для различных действий."""
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['me', 'me_avatar', 'delete_avatar', 'subscriptions', 'subscribe', 'unsubscribe', 'set_password']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = CustomUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        subscriptions = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(subscriptions)
        
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, 
                many=True, 
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = UserWithRecipesSerializer(
            subscriptions, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписка на пользователя."""
        try:
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
        except ValueError:
            return Response(
                {'errors': 'Неверный формат идентификатора пользователя'},
                status=status.HTTP_404_NOT_FOUND
            )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Отписка от пользователя."""
        try:
            author = get_object_or_404(User, pk=pk)
            user = request.user
            subscription = get_object_or_404(
                Subscription, 
                user=user, 
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {'errors': 'Неверный формат идентификатора пользователя'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=False,
        methods=['put', 'post'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        """Установка аватара пользователя."""
        serializer = SetAvatarSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            response_serializer = SetAvatarResponseSerializer(request.user)
            return Response(response_serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @me_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        """Изменение пароля пользователя."""
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password or not new_password:
            return Response(
                {'errors': 'Необходимо указать текущий и новый пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(current_password):
            return Response(
                {'current_password': ['Неправильный пароль']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT) 