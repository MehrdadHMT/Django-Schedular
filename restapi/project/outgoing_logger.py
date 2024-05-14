import logging
import time
from rest_framework import status
from project.tools import mask_sensitive_args


def key_parser(key, json):
    keys = key.split('.')
    value = json
    for key in keys:
        value = value[key]
    return value


def log_external_requests(provider, action, run_time, response, body, masked_args, masked_kwargs, request_id):
    logger = logging.getLogger('provider_logger')
    log_data = {
        'request_id': request_id,
        'provider': provider,
        'action': action,
        'run_time': run_time,
        'response_status': response.get('status'),
        'masked_args': str(masked_args),
        'masked_kwargs': str(masked_kwargs),
    }
    if body and response.get('status') == status.HTTP_200_OK:
        response_status = dict()
        for key in body:
            keyword = key.split('.')[-1]
            data = key_parser(key, response.get('body', {}))
            response_status[keyword] = data
        log_data['response_data'] = response_status
    log_data['response_data'] = log_data.get('response_data', {}) | response.get('body', {}) if isinstance(response.get('body', {}), dict) else {}
    logger.info('', extra=log_data)


def wrap_request(provider, func, args=[], kwargs={}, body=None, request_id=None, action=None):
    start_time = time.time()
    response = {'status': 200, 'body': {}}
    try:
        result = func(*args, **kwargs)
        try:
            response = {'status': result.status_code, 'body': result.json()}
        except Exception:
            response = {'status': getattr(result, 'status_code', None), 'body': result}
    except Exception as exception:
        response = {'status': 500, 'body': {'exception_message': str(exception)}}
        raise
    finally:
        finish_time = time.time()
        run_time = finish_time - start_time
        action = action or func.__name__
        masked_args = mask_sensitive_args([*args])
        masked_kwargs = mask_sensitive_args({**kwargs})
        log_external_requests(provider, action, run_time, response, body, masked_args, masked_kwargs, request_id)
    return result
