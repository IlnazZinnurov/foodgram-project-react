from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.recipes import IngredientViewSet, RecipeViewSet, TagViewSet
from api.views.users import UserSubscriptionsViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', UserSubscriptionsViewSet, basename='users')
urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
