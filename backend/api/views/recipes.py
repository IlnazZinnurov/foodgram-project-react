from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (FavoriteSerializer,
                                     FullRecipeInfoSerializer,
                                     IngredientSerializer, RecipeSerializer,
                                     ShoppingCartSerializer, TagSerializer)
from api.utils import create_shopping_cart_file
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class ModelFunctionality:
    def create_model(self, request, instance, serializer_name):
        """Метод для добавления модели."""
        serializer = serializer_name(
            data={'user': request.user.id, 'recipe': instance.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_model(self, request, model_name, instance, error_message):
        """Метод для удаления модели."""
        if not model_name.objects.filter(
                user=request.user, recipe=instance).exists():
            return Response(
                {'errors': error_message}, status=status.HTTP_400_BAD_REQUEST)
        model_name.objects.filter(user=request.user, recipe=instance).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для обработки запросов на получение ингредиентов.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для обработки запросов на получение тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )
    pagination_class = None


class RecipeViewSet(ModelFunctionality, viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами.
    Обработка запросов создания/получения/редактирования/удаления рецептов
    Добавление/удаление рецепта в избранное и список покупок.
    """

    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination
    http_method_names = [
        'get',
        'post',
        'patch',
        'delete'
    ]

    def get_queryset(self):
        qs = Recipe.objects.select_related('author').prefetch_related(
            'ingredients', 'tags'
        )
        if self.request.user.is_authenticated:
            qs = qs.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipe_id=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user,
                        recipe_id=OuterRef('pk')
                    )
                )
            )

        return qs

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return FullRecipeInfoSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        """
        Добавление в избранное.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        return self.create_model(
            request,
            recipe,
            FavoriteSerializer
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """
        Удаление из избранного.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        error_message = 'Такого рецепта нет в избранном.'
        return self.delete_model(
            request,
            Favorite,
            recipe,
            error_message
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        """
        Добавление в список покупок.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        return self.create_model(
            request,
            recipe,
            ShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """
        Удаление из списка покупок.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        error_message = 'Такого рецепта нет в списке покупок.'
        return self.delete_model(
            request,
            ShoppingCart,
            recipe,
            error_message
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, ]
    )
    def download_shopping_cart(self, request):
        """
        Скачивание файла со списком покупок.
        """
        response = create_shopping_cart_file(request.user)
        return response
