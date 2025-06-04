from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(FilterSet):
    author = filters.NumberFilter(field_name="author__id")
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
