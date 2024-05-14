from logging import getLogger

from rest_framework import status
from rest_framework.exceptions import APIException

from project.messages import MainMessages
from project.tools import message_maker

logger = getLogger(__name__)


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = message_maker(status.HTTP_503_SERVICE_UNAVAILABLE, message_source=MainMessages)
    default_code = 'service_unavailable'


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = message_maker(status.HTTP_409_CONFLICT, message_source=MainMessages)
    default_code = 'conflict'


class RequestEntityTooLarge(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = message_maker(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, message_source=MainMessages)
    default_code = 'request_entity_too_large'


class Locked(APIException):
    status_code = status.HTTP_423_LOCKED
    default_detail = message_maker(status.HTTP_423_LOCKED, message_source=MainMessages)
    default_code = 'locked'


def raise_rest_exception(func, exception=ServiceUnavailable, detail: str = None):
    """
    'raise_exception' argument is required for decorated function .
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            if kwargs.get('raise_exception', False):
                raise exception(detail) if detail else exception()
            return

    return wrapper
