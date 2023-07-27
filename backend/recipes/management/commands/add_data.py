import csv
import logging
import os
import sys

from django.conf import settings
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

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Загрузка данных в БД'

    def add_arguments(self, parser):
        parser.add_argument('ingredients_file', type=str)
        parser.add_argument('tags_file', type=str)

    def handle(self, ingredients_file, tags_file, *args, **options):

        to_elaborate = [
            {'model': Ingredient,
             'file_name': ingredients_file,
             'verbose_name': "Ингредиенты"},
            {'model': Tag,
             'file_name': tags_file,
             'verbose_name': "Теги"
             },
        ]

        for element in to_elaborate:
            model = element['model']
            file_name = element['file_name']
            verbose_name = element['verbose_name']

            logger.info(f'Удаление данных в таблице {verbose_name}')
            model.objects.all().delete()

            logger.info(f'Началась загрузка таблицу {verbose_name}')
            items = []
            with open(os.path.join(DATA_ROOT, file_name),
                      encoding='utf-8') as theFile:
                reader = csv.DictReader(theFile)
                for line in reader:
                    items.append(
                        model(
                            **line
                        )
                    )

            model.objects.bulk_create(items)
            logger.info(f'Закончилась загрузка в таблицу {verbose_name}')
