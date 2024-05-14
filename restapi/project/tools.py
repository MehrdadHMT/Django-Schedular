from copy import deepcopy
from datetime import timedelta
from logging import getLogger
from re import compile, match, IGNORECASE
from django.conf import settings
from django.db.transaction import on_commit

logger = getLogger(__name__)


def size_parser(size, response_unit="b"):
    value, unit = size.split()
    result = {'b': 1, 'k': 1024, 'm': pow(1024, 2), 'g': pow(1024, 3)}[unit[0].lower()]
    result *= int(value)
    if response_unit != 'b':
        divide = {'k': 1024, 'm': pow(1024, 2), 'g': pow(1024, 3)}[response_unit[0].lower()]
        result //= divide
    return str(result)


def time_parser(time, response_unit="s"):
    time_responses = {'w': 7 * 24 * 60 * 60, 'd': 24 * 60 * 60, 'h': 60 * 60, 'm': 60, 's': 1}
    regex = compile(
        r'((?P<weeks>\d+?)w\s?)?((?P<days>\d+?)d\s?)?((?P<hours>\d+?)h\s?)?((?P<minutes>\d+?)m\s?)?((?P<seconds>\d+?)s\s?)?')
    parts = regex.match(time)
    if not parts:
        raise ValueError("Invalid time.")
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    timedelta_temp = timedelta(**time_params)
    seconds = int(timedelta_temp.total_seconds())
    if seconds % time_responses[response_unit] != 0:
        raise ValueError("Invalid response unit.")
    return seconds / time_responses[response_unit]


def get_user_ip(request):
    return request.headers.get(settings.VALUES['USER_FORWARDED_IP'], request.META.get('REMOTE_ADDR'))


def message_maker(message, message_source=None, dict_key='detail', flat=False, extra={}):
    if flat:
        return message_source.get(message)
    msg_dict = {
                   dict_key: message_source.get(message) if message_source else message
               } | extra
    return msg_dict


def with_commit(func):
    def wrapper(*args, **kwargs):
        instance = deepcopy(kwargs.get('instance'))

        def do_on_commit():
            if instance:
                kwargs['instance'] = instance
            func(*args, **kwargs)

        on_commit(do_on_commit)

    return wrapper


def mask_sensitive_args(data):
    patterns = [r'.*password.*', r'.*refresh.*', r'.*code.*', r'.*token.*', r'.*secret.*']
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                mask_sensitive_args(value)  # Recursive call for nested dictionaries or arrays
            elif any([match(pattern, str(key), flags=IGNORECASE) for pattern in patterns]):
                data[key] = "*******"
    elif isinstance(data, list):
        for item in data:
            mask_sensitive_args(item)  # Recursive call for nested dictionaries or arrays
    return data
