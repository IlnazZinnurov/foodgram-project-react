import io

from django.db.models import Sum
from django.http import FileResponse

from recipes.models import RecipeIngredient


def create_shopping_cart_file(user):
    ingredients = RecipeIngredient.objects.filter(
        recipe__shopping_cart__user=user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(ingredient_amount=Sum('amount'))

    shopping_cart = ['Список покупок:\n']
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['ingredient_amount']
        shopping_cart.append(f'\n{name} - {amount}, {unit}')

    file_content = '\n'.join(shopping_cart)
    file_name = 'shopping_cart.txt'
    file = io.BytesIO(file_content.encode())
    response = FileResponse(file, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    return response
