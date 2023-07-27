from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтр ингредиентов по названию"""
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Фильтр рецептов по тегу/подписке/наличию в списке покупок"""
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        conjoined=False,
        lookup_expr='exact'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited_and_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            filter_parameters = {}
            if value:
                filter_parameters['favorites__user'] = self.request.user
                filter_parameters['shopping_cart__user'] = self.request.user
            return queryset.filter(**filter_parameters)
        return queryset
