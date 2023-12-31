from django.conf import settings
from django.contrib.admin import ModelAdmin, TabularInline, register

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class IngredientInline(TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


class TagInline(TabularInline):
    model = Recipe.tags.through
    extra = 1
    min_num = 1


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = settings.EMPTY_VALUE


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    empty_value_display = settings.EMPTY_VALUE


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    fields = (
        'author',
        'name',
        'text',
        'cooking_time',
        'image'
    )
    list_display = (
        'pk',
        'name',
        'author',
        'favorites_amount'
    )
    list_filter = ('name', 'author', 'tags')
    empty_value_display = settings.EMPTY_VALUE
    inlines = [IngredientInline,
               TagInline
               ]

    def favorites_amount(self, obj):
        return obj.favorites.count()


@register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    empty_value_display = settings.EMPTY_VALUE


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = settings.EMPTY_VALUE


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    empty_value_display = settings.EMPTY_VALUE
