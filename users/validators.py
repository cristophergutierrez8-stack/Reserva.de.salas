import re

from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    def validate(self, password, user=None):
        requirements = (
            (r'[A-Z]', 'una letra mayúscula'),
            (r'[a-z]', 'una letra minúscula'),
            (r'\d', 'un número'),
            (r'[^A-Za-z0-9\s]', 'un carácter especial'),
        )
        missing = [label for pattern, label in requirements if not re.search(pattern, password)]
        if missing:
            raise ValidationError(
                'La contraseña debe incluir al menos ' + ', '.join(missing) + '.',
                code='password_complexity',
            )

    def get_help_text(self):
        return (
            'Incluya al menos una letra mayúscula, una minúscula, '
            'un número y un carácter especial.'
        )
