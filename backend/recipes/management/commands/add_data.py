import logging
import sys
from csv import DictReader

from django.core.management import BaseCommand
from recipes.models import Ingredient, Tag

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)


class Command(BaseCommand):
    help = 'Загрузка данных в БД'

    def handle(self, *args, **options):
        logger.info('Удаление данных в таблице Ингридиенты')
        Ingredient.objects.all().delete()

        logger.info('Загрузка ингридиентов в БД')
        ingredients = []
        for row in DictReader(
            open('./data/ingredients.csv', encoding='utf-8'),
            ['name', 'measurement_unit']
        ):
            ingredients.append(
                Ingredient(
                    name=row['name'],
                    measurement_unit=row['measurement_unit'],
                )
            )

        Ingredient.objects.bulk_create(ingredients)

        logger.info('Загрузка ингридиентов в БД завершена')

        logger.info('Удаление данных в таблице Теги')
        Tag.objects.all().delete()

        logger.info('Загрузка тегов в БД')
        tags = []
        for row in DictReader(
            open('./data/tags.csv', encoding='utf-8'),
            ['name', 'color', 'slug']
        ):
            tags.append(
                Tag(
                    name=row['name'],
                    color=row['color'],
                    slug=row['slug'],
                )
            )

        Tag.objects.bulk_create(tags)

        logger.info('Загрузка тегов в БД завершена')
