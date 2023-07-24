import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Недопустимое имя пользователя!'
        )
    invalid_symbols = re.findall(r'[^[\w.@+-]', value)
    if invalid_symbols:
        raise ValidationError(
            'Некорректные символы в username: {}'.format(
                ', '.join(invalid_symbols))
        )
    return value
