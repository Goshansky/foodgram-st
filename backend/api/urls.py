from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'

# Создаем роутер для основных ресурсов
router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    # Djoser URLs для токенов
    path('auth/', include('djoser.urls.authtoken')),
    
    # Наш роутер для всех ресурсов
    path('', include(router.urls)),
] 