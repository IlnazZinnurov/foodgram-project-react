from djoser.serializers import UserSerializer
from djoser.serializers import UserCreateSerializer as DjoserUserSerialiser
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import Follow, User


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
        from api.serializers.recipes import UserSubscribeRepresentSerializer
        request = self.context.get('request')
        return UserSubscribeRepresentSerializer(
            instance.author, context={'request': request}
        ).data
