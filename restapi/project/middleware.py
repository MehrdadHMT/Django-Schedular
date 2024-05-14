import json, logging, socket, time

from django.urls import resolve
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseServerError
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from project import settings
from project.settings import VALUES
import uuid
from project.tools import mask_sensitive_args

logger = logging.getLogger(__name__)
requests_logger = logging.getLogger('requests_logger')


class ResponseLogMiddleware(MiddlewareMixin):
    """Response Logging Middleware."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.body = None
        self.get_params = None
        self.start_time = None

    def process_request(self, request):
        request.exception_message = ""
        request.request_id = str(uuid.uuid4().hex)
        self.start_time = time.time()
        self.body = {}
        self.get_params = {}
        """Set Request Start Time to measure time taken to service request."""
        if request.method in ['POST', 'PUT', 'DELETE']:
            try:
                body_unicode = request.body.decode('utf-8')
                body = json.loads(body_unicode)
            except Exception:
                body = dict(request.POST)
            self.body = body
        if request.method == 'GET':
            self.get_params = request.GET

    def extract_log_info(self, request, response=None, exception=None):
        """Extract appropriate log info from requests/responses/exceptions."""
        log_data = {
            'request_id': request.request_id,
            'request_method': request.method,
            'remote_address': request.META['REMOTE_ADDR'],
            'server_hostname': socket.gethostname(),
            'request_path': request.get_full_path(),
            'request_user': str(request.user.id) if request.user else None,
            'route_name': resolve(request.path_info).url_name,
            'run_time': time.time() - self.start_time,
            'response_status': response.status_code,
            'request_body': self.body,
            'params': self.get_params,
            'device': request.headers.get('user-device', 'unknown')
        }
        if VALUES['HEADER_LOGGER_ENABLE']:
            log_data |= {'HEADERS': request.headers}
        return log_data

    def process_response(self, request, response):
        """Log data using logger."""
        log_data = self.extract_log_info(request=request, response=response)
        log_data = mask_sensitive_args(log_data)
        requests_logger.info(msg=request.exception_message, extra=log_data)

        return response

    def process_exception(self, request, exception):
        request.exception_message = exception
        """Log Exceptions."""
        try:
            raise exception
        except Exception as e:
            cache.set(f'{VALUES["EXCEPTION_METRICS_PREFIX"]}-{now().timestamp()}', 1, VALUES['EXCEPTION_METRICS_TTL'])
            logger.exception(msg=e)
        raise


class ResponseHeaderMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        """ remove invalid headers from allow head. """
        if response.headers.get('Allow', False):
            headers = response.headers.get('Allow').split(',')
            checked_headers = [header for header in headers if header not in [' HEAD', ' OPTIONS']]
            response.headers['Allow'] = ','.join(checked_headers)
        return response


class HealthCheckMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET":
            if request.path == "/readiness/":
                return self.readiness(request)
            elif request.path == "/liveness/":
                return self.liveness(request)
        return self.get_response(request)

    def liveness(self, request):
        """
        Returns that the server is alive.
        """
        return HttpResponse("OK")

    def readiness(self, request):

        try:
            from django.db import connections
            for name in connections:
                cursor = connections[name].cursor()
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if row is None:
                    return HttpResponseServerError("db: invalid response")
        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError("db: cannot connect to database.")
        try:

            from django_redis import get_redis_connection
            if settings.CACHES.get("default").get("BACKEND") == "django_redis.cache.RedisCache" :
                get_redis_connection('default')
            else:
                cache.set("Cache_Health", "Healthy", 1)
                if cache.get("Cache_Health") != "Healthy" :
                    return HttpResponseServerError("cache: cannot connect to cache.")

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError("cache: cannot connect to cache.")

        try:

            from kafka import KafkaProducer
            from json import dumps
            from socket import gethostname

            KAFKA_PRODUCER = KafkaProducer(
                bootstrap_servers=VALUES['KAFKA_BOOTSTRAP_SERVER'],
                value_serializer=lambda value: dumps(value).encode('utf-8'),
                client_id=gethostname(),
            )
            if not bool(KAFKA_PRODUCER.metrics()):
                raise

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError("kafka: cannot connect to kafka.")

        return HttpResponse("OK")
