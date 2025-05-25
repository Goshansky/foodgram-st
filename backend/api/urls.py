from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'

# Основной роутер для рецептов, тегов и ингредиентов
router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

# Роутер для пользовательского ViewSet с уникальным базовым путем
user_router = DefaultRouter()
user_router.register('profiles', UserViewSet, basename='profiles')

urlpatterns = [
    # URL Djoser для регистрации, авторизации и т.д.
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    
    # URL из основного роутера
    path('', include(router.urls)),
    
    # URL пользовательского ViewSet с уникальным базовым путем
    path('', include(user_router.urls)),
] 