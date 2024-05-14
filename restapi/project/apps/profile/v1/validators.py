from re import search, match
from django.utils.translation import get_language
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from project.settings import VALUES
from project.messages import get_message


phone_regex_validator = RegexValidator(regex=r"^(?:0|98|\+98|\+980|0098|098|00980)?(9\d{9})$",
                                       message="Phone number must be entered in one of these formats: '09xxxxxxxxx',"
                                               " '989xxxxxxxxx', '+989xxxxxxxxx', '+9809xxxxxxxxx', '00989xxxxxxxxx',"
                                               "'0989xxxxxxxxx', '009809xxxxxxxxx'."
                                               " Up to 15 digits allowed.")


def check_password(value):
    if VALUES.get('PASSWORD_REGEXES'):
        for item in VALUES['PASSWORD_REGEXES']['regexes']:
            if search(rf"{item['pattern']}", value) is None:
                if get_language() == 'fa':
                    raise ValidationError(item['message']['fa'])
                raise ValidationError(item['message']['en'])


def check_name(value):
    if value is not None and len(value) < 3:
        raise ValidationError(get_message('name_wrong', flat=True))


def check_channel_name(value):
    if value is not None and len(value) < 3:
        raise ValidationError(get_message('channel_name_wrong', flat=True))
    if not match(r'^\w+$', value):
        raise ValidationError(get_message('channel_name_wrong', flat=True))
