from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "favorites_count")
    list_filter = ("author", "name")
    search_fields = ("name", "author__username")
    inlines = (RecipeIngredientInline,)

    def favorites_count(self, obj):
        return obj.favorites.count()

    favorites_count.short_description = "В избранном"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    list_filter = ("user",)
    search_fields = ("user__username", "recipe__name")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    list_filter = ("user",)
    search_fields = ("user__username", "recipe__name")
