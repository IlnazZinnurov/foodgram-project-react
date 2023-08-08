import base64

from django.core.files.base import ContentFile
from django.db import transaction

from djoser.serializers import UserCreateSerializer as DjoserUserSerialiser
from djoser.serializers import UserSerializer

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

from users.models import Follow, User

# -----------------------------------------------------------------------------
#                            Приложение users
# -----------------------------------------------------------------------------


class UsersCreateSerializer(DjoserUserSerialiser):
    """
    Сериализатор для обработки запросов на создание пользователя.
    """
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class UserGetSerializer(UserSerializer):
    """
    Сериализатор для отображения информации о пользователе.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Follow.objects.filter(
                    user=request.user, author=obj
                ).exists())


class UserSubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с подписками пользователей.
    """
    class Meta:
        model = Follow
        fields = ('user', 'author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserSubscribeRepresentSerializer(
            instance.author, context={'request': request}
        ).data


# -----------------------------------------------------------------------------
#                            Приложение recipes
# -----------------------------------------------------------------------------


class Base64ImageField(serializers.ImageField):
    """
    Кастомное поле для кодирования изображения в base64.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='photo.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSubscribeRepresentSerializer(UserGetSerializer):
    """
    Сериализатор для предоставления информации
    о подписках пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        return ShortRecipeInfoSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подробного описания ингредиентов в рецепте.
    """
    name = serializers.CharField(
        source='ingredient.name', read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AddIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class FullRecipeInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения полной информации."""
    author = UserGetSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredient'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, object):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return object.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, object):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return object.shopping_cart.filter(user=request.user).exists()


class ShortRecipeInfoSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения краткой информации."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""
    ingredients = AddIngredientSerializer(
        many=True
    )
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'name',
            'text',
            'tags',
            'cooking_time',
            'image'
        )

    def validate(self, data):
        ingredients_list = []
        for ingredient in data.get('ingredients'):
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Количество не может быть меньше 1'
                )
            ingredients_list.append(ingredient.get('id'))
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        return data

    def add_ingredients(self, ingredients, recipe):
        """Метод добавления ингредиентов."""
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = ingredient.get('id')
            amount = ingredient.get('amount')
            ingredient_list.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.add_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return FullRecipeInfoSerializer(instance, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления/удаления рецепта в избранное.
    """
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен в избранное!'
            )
        ]

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShortRecipeInfoSerializer(instance.recipe, context=context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления/удаления рецепта в список покупок.
    """
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return ShortRecipeInfoSerializer(
            instance.recipe,
            context={'request': request}
        ).data
