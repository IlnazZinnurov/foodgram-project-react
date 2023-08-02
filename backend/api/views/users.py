from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.serializers.recipes import (UserSubscribeRepresentSerializer,
                                     UserSubscribeSerializer)

from users.models import Follow, User


class UserSubscriptionsViewSet(viewsets.GenericViewSet):
    """
    Вьюсет управления подписками
    """

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        serializer = UserSubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if not Follow.objects.filter(
                user=request.user,
                author=author
        ).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.get(
            user=request.user.id,
            author=pk
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def subscriptions(self, request):
        authors = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(authors)
        serializer = UserSubscribeRepresentSerializer(
            page,
            many=True, context={
                'request': request})
        return self.get_paginated_response(serializer.data)
