import math, time
from logging import getLogger
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils.translation import get_language
from rest_framework import serializers
from rest_framework.exceptions import ParseError, APIException
from project.apps.profile.v1.validators import check_phone, check_password, check_name, check_channel_name
from project.apps.profile.models import Contact, User, StreamerView
from project.apps.captcha.v1.views import PROVIDERS
from project.apps.administration.messages import MESSAGES
from project.settings import VALUES, LIST_LARGE, LIST_MEDIUM
from project.tools import get_user_ip

logger = getLogger(__name__)


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = MESSAGES['service_unavailable']['fa'] if get_language() == 'fa' else \
        MESSAGES['service_unavailable']['en']
    default_code = 'service_unavailable'


class LoginCaptchaRequired(serializers.Serializer):
    captcha_required = serializers.CharField(allow_null=True, default=None)

    def check_required(self, request):
        if VALUES['CAPTCHA_REQUIRED']:
            user_ip = get_user_ip(request)
            count_403 = 0 if cache.get(VALUES['CAPTCHA_CACHE_LOGIN_PREFIX'].format(user_ip)) is None else \
                cache.get(VALUES['CAPTCHA_CACHE_LOGIN_PREFIX'].format(user_ip))
            if count_403 + 1 == VALUES['LOGIN_MAX_REQUEST']:
                cache_time = datetime.now() + timedelta(minutes=VALUES['LOGIN_CAPTCHA_CACHE_TIME'])
                self.validated_data['captcha_required'] = math.ceil(cache_time.timestamp())


class LoginCaptchaResponse(serializers.Serializer):
    def __init__(self, throttle=[], request=None, view=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.throttle_ins = throttle[0] if len(throttle) > 0 else None
        self.request = request
        self.view = view

    captcha_id = serializers.UUIDField(required=False)
    captcha_value = serializers.CharField(min_length=4, required=False)
    captcha_provider = serializers.CharField(required=False, max_length=50)

    def validate(self, attrs):
        user_ip = get_user_ip(self.request)
        id, value, provider = attrs.get('captcha_id'), attrs.get('captcha_value'), attrs.get('captcha_provider')
        if VALUES['CAPTCHA_REQUIRED']:
            count_403 = 1 if cache.get(VALUES['CAPTCHA_CACHE_LOGIN_PREFIX'].format(user_ip)) is None else \
                cache.get(VALUES['CAPTCHA_CACHE_LOGIN_PREFIX'].format(user_ip))
            captcha_expire = cache.ttl(VALUES['CAPTCHA_CACHE_LOGIN_PREFIX'].format(user_ip))
            captcha_expire = math.ceil(time.time() + captcha_expire)
            if count_403 >= VALUES['LOGIN_MAX_REQUEST']:
                if all(i is not None for i in [id, value, provider]):
                    verify = None
                    for pr in PROVIDERS:
                        if provider == pr.PROVIDER:
                            verify = pr().verify_captcha(id, value)
                            if verify.get('result') is None:
                                details = {'detail': verify.get('detail'), 'captcha_required': captcha_expire}
                                raise ServiceUnavailable(details)
                            if not verify.get('result'):
                                details = {'detail': verify.get('detail'), 'captcha_required': captcha_expire}
                                raise ParseError(details)
                    if verify is None:
                        details = {'detail': MESSAGES['captcha_invalid']['en'], 'captcha_required': captcha_expire}
                        if get_language() == 'fa':
                            details = {'detail': MESSAGES['captcha_invalid']['fa'], 'captcha_required': captcha_expire}
                        raise ParseError(details)
                    cache.delete(VALUES['CAPTCHA_CACHE_LOGIN_PREFIX'].format(user_ip))
                    if self.throttle_ins is not None:
                        throttle_cache_key = self.throttle_ins.get_cache_key(self.request, self.view)
                        cache.delete(throttle_cache_key)
                else:
                    details = {'detail': MESSAGES['captcha_required']['en'], 'captcha_required': captcha_expire}
                    if get_language() == 'fa':
                        details = {'detail': MESSAGES['captcha_required']['fa'], 'captcha_required': captcha_expire}
                    raise ParseError(details)
        return attrs


class GenerateCodeCaptchaResponse(serializers.Serializer):
    def __init__(self, throttle=[], request=None, view=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.throttle_ins = throttle[0] if len(throttle) > 0 else None
        self.request = request
        self.view = view

    captcha_id = serializers.UUIDField(required=False)
    captcha_value = serializers.CharField(min_length=4, required=False)
    captcha_provider = serializers.CharField(required=False, max_length=50)

    def validate(self, attrs):
        user_ip = get_user_ip(self.request)
        id, value, provider = attrs.get('captcha_id'), attrs.get('captcha_value'), attrs.get('captcha_provider')
        if VALUES['CAPTCHA_REQUIRED']:
            count_200 = 0 if cache.get(VALUES['CAPTCHA_CACHE_CODE_PREFIX'].format(user_ip)) is None else \
                cache.get(VALUES['CAPTCHA_CACHE_CODE_PREFIX'].format(user_ip))
            captcha_expire = cache.ttl(VALUES['CAPTCHA_CACHE_CODE_PREFIX'].format(user_ip))
            captcha_expire = math.ceil(time.time() + captcha_expire)
            if count_200 >= VALUES['CODE_MAX_REQUEST']:
                if all(i is not None for i in [id, value, provider]):
                    verify = None
                    for pr in PROVIDERS:
                        if provider == pr.PROVIDER:
                            verify = pr().verify_captcha(id, value)
                            if verify.get('result') is None:
                                details = {'detail': verify.get('detail'), 'captcha_required': captcha_expire}
                                raise ServiceUnavailable(details)
                            if not verify.get('result'):
                                details = {'detail': verify.get('detail'), 'captcha_required': captcha_expire}
                                raise ParseError(details)
                    if verify is None:
                        details = {'detail': MESSAGES['captcha_invalid']['en'], 'captcha_required': captcha_expire}
                        if get_language() == 'fa':
                            details = {'detail': MESSAGES['captcha_invalid']['fa'], 'captcha_required': captcha_expire}
                        raise ParseError(details)
                    cache.delete(VALUES['CAPTCHA_CACHE_CODE_PREFIX'].format(user_ip))
                    if self.throttle_ins is not None:
                        throttle_cache_key = self.throttle_ins.get_cache_key(self.request, self.view)
                        cache.delete(throttle_cache_key)

                else:
                    details = {'detail': MESSAGES['captcha_required']['en'], 'captcha_required': captcha_expire}
                    if get_language() == 'fa':
                        details = {'detail': MESSAGES['captcha_required']['fa'], 'captcha_required': captcha_expire}
                    raise ParseError(details)
        return attrs


class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(min_length=11, max_length=11, validators=[check_phone])



class GenerateCodeSerializer(PhoneSerializer, GenerateCodeCaptchaResponse):
    pass


class TokenSerializer(serializers.Serializer):
    jwt_access_token = serializers.CharField(max_length=400, required=False, allow_null=True)
    jwt_refresh_token = serializers.CharField(max_length=400, required=False, allow_null=True)
    bucket_name = serializers.CharField(max_length=200, required=False, allow_null=True)
    trash_bucket_name = serializers.CharField(max_length=200, required=False, allow_null=True)


class LoginSerializer(PhoneSerializer, LoginCaptchaResponse):
    name = serializers.CharField(min_length=1, max_length=200, required=False,
                                 allow_blank=True, allow_null=True, validators=[check_name])
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=80)
    code = serializers.IntegerField(min_value=100000, max_value=999999, required=False, allow_null=True)


class LoginResponseSerializer(TokenSerializer, LoginCaptchaRequired):
    pass


class LogoutSerializer(serializers.Serializer):
    jwt_refresh_token = serializers.CharField(max_length=400)


class ChangePasswordSerializer(serializers.Serializer):
    code = serializers.IntegerField(min_value=100000, max_value=999999, required=False, allow_null=True)
    old_password = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    new_password = serializers.CharField(validators=[check_password])
    refresh_token = serializers.CharField()


class ContactSerializer(PhoneSerializer):
    name = serializers.CharField(max_length=128, allow_null=False)


class ListContactSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(min_length=11, max_length=11, validators=[check_phone], source='contact')
    contact_id = serializers.IntegerField(min_value=1, help_text='Id of contact', source='contact.id')
    rsa_pub = serializers.CharField(help_text='rsa_pub of contact', source='contact.rsa_pub')

    class Meta:
        model = Contact
        fields = ['contact_id', 'phone', 'name', 'picture_url', 'rsa_pub']


class SyncContactSerializer(serializers.Serializer):
    contacts = serializers.ListField(
        child=ContactSerializer(), max_length=LIST_LARGE
    )
    paginate = serializers.BooleanField(default=False, required=False)
    page_id = serializers.UUIDField(required=False)
    is_transactional = serializers.BooleanField(default=False)
    fail_on_no_regs = serializers.BooleanField(default=False)
    add_extra = serializers.BooleanField(default=True)
    delete_missing = serializers.BooleanField(default=True)


class SyncContactResponseSer(serializers.Serializer):
    page_id = serializers.UUIDField(allow_null=True, default=None)


class GetProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200, required=True)
    picture_url = serializers.CharField(max_length=1000)

    class Meta:
        model = User
        fields = ('id', 'phone', 'name', 'picture_url', 'channel_name')


class ListUserSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), min_length=1, max_length=LIST_MEDIUM, help_text='Include user ids.')


class StreamerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamerView
        fields = ('id', 'name', 'picture_url', 'channel_name', 'banner_url', 'description')


class SetProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, allow_null=False, required=False, validators=[check_name])
    picture = serializers.CharField(max_length=250, allow_null=True, required=False)
    description = serializers.CharField(max_length=1000, allow_null=True, required=False)
    banner_url = serializers.CharField(max_length=1000, allow_null=True, required=False)
    channel_name = serializers.CharField(max_length=200, allow_null=True, required=False, validators=[check_channel_name])
    searchable = serializers.BooleanField(default=True)



class CreateProfileUrlSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=500)
    image_name = serializers.CharField(max_length=250)


class SearchUserQuery(serializers.Serializer):
    channel_name = serializers.CharField(max_length=255)
