from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    # Добавил для тестов в postman
    name = filters.CharFilter(method="filter_name")

    class Meta:
        model = Ingredient
        fields = ("name",)

    # Добавил для тестов в postman
    def filter_name(self, queryset, name, value):
        exact_matches = queryset.filter(name=value)
        if exact_matches.exists():
            return exact_matches

        startswith_matches = queryset.filter(name__startswith=value)
        if startswith_matches.exists():
            return startswith_matches

        return queryset.filter(name__istartswith=value)


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method="filter_favorites")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("author", "is_favorited", "is_in_shopping_cart")

    def filter_favorites(self, queryset, name, value):
        user = self._get_user()
        if not user or not value:
            return queryset
        return queryset.filter(favorites__user=user)

    def filter_shopping_cart(self, queryset, name, value):
        user = self._get_user()
        if not user or not value:
            return queryset
        return queryset.filter(shopping_cart__user=user)

    def _get_user(self):
        if not self.request or not hasattr(self.request, "user"):
            return None
        user = self.request.user
        if not user.is_authenticated:
            return None
        return user
