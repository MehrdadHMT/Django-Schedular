import logging, boto3
from rgwadmin import RGWAdmin
from uuid import uuid4
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError
from project.apps.organization.permissions import IsDriveAdmin
from project.apps.profile.v1.serializers import ContactSerializer, ListContactSerializer, SyncContactResponseSer, SyncContactSerializer, \
    StreamerSerializer, GetProfileSerializer, SetProfileSerializer, CreateProfileUrlSerializer, PhoneSerializer, SearchUserQuery, ListUserSerializer
from project.apps.administration.messages import get_message
from project.settings import VALUES
from project.apps.profile.models import Contact, User
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from project.outgoing_logger import wrap_request
from operator import itemgetter
from hashlib import blake2b
from project.apps.profile.models import StreamerView
from django.db.models import Value
from django.db.models.functions import StrIndex
from django.db.models.functions.text import Length
from django.core.cache import cache
from project.authentications import StaticAuthentication, OptionalAuthentication
from drf_spectacular.types import OpenApiTypes

logger = logging.getLogger(__name__)
rgw = wrap_request('RGW', RGWAdmin, kwargs={
    'access_key': VALUES['RGW_ACCESS_KEY'], 'secret_key': VALUES['RGW_SECRET_KEY'],
    'server': VALUES['RGW_SERVER'], 'pool_connections': True})


@extend_schema(
    tags=['profile'],
    request=ContactSerializer,
    responses={
        200: OpenApiResponse(response=ListContactSerializer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
        404: OpenApiResponse(description=VALUES[404]),
        406: OpenApiResponse(description=VALUES[406]),
        409: OpenApiResponse(description=VALUES[409]),
    },
    description='This API will add contact for users.',
)
class CreateContactView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = ContactSerializer
    res_serializer_class = ListContactSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone, name = serializer.validated_data['phone'], serializer.validated_data['name']
        if str(user) == phone:
            return Response(data=get_message('contact_yourself_406'), status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            contact_user = User.objects.get(phone=phone, searchable=True)
            contact = Contact.objects.create(user=user, contact=contact_user, name=name)
            return Response(data=self.res_serializer_class(contact).data, status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            logger.warning(e)
            return Response(data=get_message('user_not_exist'), status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.warning(e)
            return Response(data=get_message('create_contact_conflict'), status=status.HTTP_409_CONFLICT)


@extend_schema(
    tags=['profile'],
    request=PhoneSerializer,
    responses={
        200: OpenApiResponse(description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
        404: OpenApiResponse(description=VALUES[404]),
        409: OpenApiResponse(description=VALUES[409]),
    },
    description='This API will remove a contact for users contact list.<br>This Api receive data in json format like: <b>{"phone":"09127278546"}</b> but we cant show you this request body or enable <b>\"try it out\"</b> due to an issue in updated library we use :) feel free to use postman or some other tools to test this API.',
)
class DeleteContactView(generics.DestroyAPIView):
    serializer_class = PhoneSerializer

    def delete(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user.contact_user_set.get(contact=User.objects.get(phone=serializer.validated_data['phone']).id).delete()
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist as e:
            logger.warning(e)
            return Response(data=get_message('user_not_exist'), status=status.HTTP_404_NOT_FOUND)
        except Contact.DoesNotExist as e:
            logger.warning(e)
            return Response(data=get_message('user_not_exist'), status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.warning(e)
            return Response(data=get_message('delete_contact_409'), status=status.HTTP_409_CONFLICT)


@extend_schema(
    tags=['profile'],
    responses={
        200: OpenApiResponse(response=ListContactSerializer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
    },
    description="Return list of user contacts",
)
class ListContactView(generics.ListAPIView):
    serializer_class = ListContactSerializer

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)



@extend_schema(
    tags=['profile'],
    responses={
        200: OpenApiResponse(response=SyncContactResponseSer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
        406: OpenApiResponse(description=VALUES[406]),
    },
    description='An API to sync the contacts of current user with special parameters.',
)
class SyncContactView(generics.GenericAPIView):
    serializer_class = SyncContactSerializer

    def post(self, request, *args, **kwargs):
        if not request.data.get('paginate', False):
            serializer = SyncContactSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            response_ser = SyncContactResponseSer(data={})
            response_ser.is_valid()
            contacts = serializer.validated_data.get("contacts")
            if serializer.data.get('page_id', None) is not None:
                contacts += cache.get(serializer.data.get('page_id'), [])
            contacts_dict = {item['phone']: {'name': item['name']} for item in contacts}
            exist_users = User.objects.filter(phone__in=list(map(itemgetter('phone'), contacts)), searchable=True).values_list('id', 'phone')
            exist_users_dict = {item[0]: {'phone': item[1]} for item in exist_users}
            user_contacts = request.user.contact_user_set.all().values_list('id', 'contact', 'name')
            user_contacts_dict = {item[1]: {'id': item[0], 'name': item[2]} for item in user_contacts}
            intersect_contact_ids = set(user_contacts_dict.keys()).intersection(exist_users_dict.keys())
            updates = []
            for id in intersect_contact_ids:
                if user_contacts_dict[id]['name'] != contacts_dict[exist_users_dict[id]['phone']]['name']:
                    updates.append(Contact(id=user_contacts_dict[id]['id'], contact_id=id,
                                           name=contacts_dict[exist_users_dict[id]['phone']]['name']))
            Contact.objects.bulk_update(updates, ['name'])
            if request.user.id in exist_users_dict.keys():
                return Response(data=get_message('contact_yourself_406'), status=status.HTTP_406_NOT_ACCEPTABLE)
            if serializer.data.get("is_transactional"):
                if serializer.data.get("fail_on_no_regs"):
                    if len(exist_users) != len(contacts):
                        return Response(data=get_message('sync_contact_406'), status=status.HTTP_406_NOT_ACCEPTABLE)
                if serializer.data.get("add_extra"):
                    extra_ids = exist_users_dict.keys() - user_contacts_dict.keys()
                    creates = []
                    for id in extra_ids:
                        creates.append(Contact(user=request.user, contact_id=id,
                                               name=contacts_dict[exist_users_dict[id]['phone']]['name']))
                    Contact.objects.bulk_create(creates)
                if serializer.data.get("delete_missing"):
                    missing_ids = user_contacts_dict.keys() - exist_users_dict.keys()
                    Contact.objects.filter(user=request.user, contact_id__in=missing_ids).delete()
                return Response(response_ser.data, status=status.HTTP_200_OK)
            else:
                if serializer.data.get("add_extra"):
                    if request.user in exist_users:
                        del exist_users_dict[request.user.id]
                    extra_ids = exist_users_dict.keys() - user_contacts_dict.keys()
                    creates = []
                    for id in extra_ids:
                        creates.append(Contact(user=request.user, contact_id=id, name=contacts_dict[exist_users_dict[id]['phone']]['name']))
                    Contact.objects.bulk_create(creates)
                if serializer.data.get("delete_missing"):
                    missing_ids = user_contacts_dict.keys() - exist_users_dict.keys()
                    Contact.objects.filter(user=request.user, contact_id__in=missing_ids).delete()
                return Response(response_ser.data, status=status.HTTP_200_OK)
        else:
            serializer = SyncContactSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if serializer.validated_data.get('page_id', None):
                cache_key = serializer.validated_data['page_id']
                list_contacts = cache.get(cache_key, None)
                if list_contacts is None:
                    return Response(get_message(404), status=status.HTTP_404_NOT_FOUND)
            else:
                cache_key = uuid4()
                list_contacts = list()
            list_contacts += serializer.validated_data.get('contacts', [])
            cache.set(cache_key, self.remove_dup(list_contacts), 5 * 60)
            response_ser = SyncContactResponseSer(data={'page_id': cache_key})
            response_ser.is_valid()
            return Response(response_ser.data, status=status.HTTP_200_OK)

    @staticmethod
    def remove_dup(lst):
        added = list()
        result = list()
        for dic in lst[::-1]:
            if dic['phone'] not in added:
                result.append(dic)
                added.append(dic['phone'])

        return result



@extend_schema(
    tags=['profile'],
    description="Return user's information by channel name.",
    responses={
        200: OpenApiResponse(response=StreamerSerializer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        404: OpenApiResponse(description=VALUES[404]),
    },
)
class GetUserView(generics.RetrieveAPIView):
    authentication_classes = ()
    serializer_class = StreamerSerializer

    def get_object(self):
        try:
            return StreamerView.objects.get(channel_name=self.kwargs['channel_name'])
        except StreamerView.DoesNotExist as exception:
            logger.warning(exception)
            raise NotFound(get_message(status.HTTP_404_NOT_FOUND))



@extend_schema(
    tags=['profile'],
    description="Return user's information by channel name.",
    responses={
        200: OpenApiResponse(response=StreamerSerializer(many=True), description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
    },
)
class ListUserView(APIView):
    authentication_classes = ()
    serializer_class = ListUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get('ids')
        users = StreamerView.objects.filter(id__in=ids)
        return Response(StreamerSerializer(users, many=True).data, status=status.HTTP_200_OK)


@extend_schema(
        tags=['profile'],
        description="Return user's information with given id (Just permm for drive admin).",
        responses={
            200: OpenApiResponse(response=GetProfileSerializer, description=VALUES[200]),
            401: OpenApiResponse(description=VALUES[401]),
            403: OpenApiResponse(description=VALUES[403]),
            404: OpenApiResponse(description=VALUES[404]),
        },
        parameters=[
            OpenApiParameter(
                name='auth-token',
                location=OpenApiParameter.HEADER,
                type=OpenApiTypes.STR,
                description='(static authentication token)',
            ),
        ],
    )
class GetUserById(generics.RetrieveAPIView):
    authentication_classes = (OptionalAuthentication,)
    permission_classes = [IsDriveAdmin | StaticAuthentication]
    queryset = User.objects.all()
    serializer_class = GetProfileSerializer


@extend_schema(
    tags=['profile'],
    request=SetProfileSerializer,
    responses={
        200: OpenApiResponse(description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
        409: OpenApiResponse(description=VALUES[409]),
        503: OpenApiResponse(description=VALUES[503]),
    },
    description='Change user\'s name or profile image(or remove profile photo).',
)
class SetProfileView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SetProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        picture_key, keys, data_keys = 'picture', ['name', 'channel_name', 'description', 'banner_url', 'searchable'], request.data.keys()

        if not any(key in data_keys for key in ([picture_key] + keys)):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        for key in keys:
            if key in serializer.validated_data:
                setattr(user, key, serializer.validated_data[key])
        if picture_key in serializer.validated_data:
            if picture := serializer.validated_data[picture_key]:
                try:
                    user.picture and user.picture != picture and SetProfileView.s3_delete_object(
                        VALUES["PUBLIC_BUCKET"], user.picture)
                except Exception as e:
                    logger.exception(e)
                    return Response(data=get_message(503), status=status.HTTP_503_SERVICE_UNAVAILABLE)

                object_key = f'/{VALUES["PROFILE_FOLDER"]}/{VALUES["USER_PROFILE_PREFIX"].format(user.id)}/{picture}'
                user.picture = object_key
            else:
                user.picture = None
                profile_image = User.objects.get(pk=user.id).picture
                if profile_image is not None:
                    try:
                        SetProfileView.s3_delete_object(VALUES["PUBLIC_BUCKET"], profile_image)
                    except Exception as e:
                        logger.exception(e)
                        return Response(data=get_message(503), status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            user.save()
        except IntegrityError as e:
            logger.warning(e)
            return Response(data=get_message('channel_name_409'), status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_200_OK)

    @staticmethod
    def s3_delete_object(bucket, profile_image):
        try:
            s3_client = wrap_request('S3', boto3.client, args=['s3'], kwargs={'aws_access_key_id': VALUES['RGW_ACCESS_KEY'],
                                                                              'aws_secret_access_key': VALUES['RGW_SECRET_KEY'],
                                                                              'endpoint_url': 'https://{}'.format(VALUES['RGW_SERVER'])})
            wrap_request('S3', s3_client.delete_object, kwargs={'Bucket': bucket, 'Key': profile_image})
            return True
        except Exception as e:
            logger.exception(e)
            return False


@extend_schema(
    tags=['profile'],
    responses={
        200: OpenApiResponse(response=CreateProfileUrlSerializer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
        503: OpenApiResponse(description=VALUES[503]),
    },
    description='Create a put temp-url to upload the profile picture.',
)
class CreateProfileUrlView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        pic_name_hashed = blake2b(f'{VALUES["OBJECT_KEY_PREFIX"]}{user_id}-{get_random_string(5)}'.encode()).hexdigest()
        object_key = f'/{VALUES["PROFILE_FOLDER"]}/{VALUES["USER_PROFILE_PREFIX"].format(user_id)}/{pic_name_hashed}'
        try:
            url = CreateProfileUrlView.s3_generate_presigned_url(object_key)
        except Exception as e:
            logger.exception(e)
            return Response(data=get_message(503), status=status.HTTP_503_SERVICE_UNAVAILABLE)
        serializer = CreateProfileUrlSerializer(data={'url': url, 'image_name': pic_name_hashed})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def s3_generate_presigned_url(object_key):
        s3_client = wrap_request('S3', boto3.client, args=['s3'], kwargs={'aws_access_key_id': VALUES['RGW_ACCESS_KEY'],
                                                                          'aws_secret_access_key': VALUES['RGW_SECRET_KEY'],
                                                                          'endpoint_url': 'https://{}'.format(VALUES['RGW_SERVER'])})
        url = wrap_request('S3', s3_client.generate_presigned_url, kwargs={
            'ClientMethod': 'put_object', 'Params': {'Bucket': VALUES['PUBLIC_BUCKET'], 'Key': object_key},
            'ExpiresIn': VALUES['PROFILE_URL_EXPIRATION_TIME']})
        return VALUES['NGINX_HOST'] + url.split(f"/{VALUES['PUBLIC_BUCKET']}/")[-1]


@extend_schema(
    tags=['profile'],
    responses={
        200: OpenApiResponse(response=ListContactSerializer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
        401: OpenApiResponse(description=VALUES[401]),
        404: OpenApiResponse(description=VALUES[404]),
    },
    description='get contact by user id',
)
class GetContactView(generics.RetrieveAPIView):
    serializer_class = ListContactSerializer
    lookup_field = 'user_id'

    def get_object(self):
        try:
            return Contact.objects.get(user=self.request.user, contact_id=self.kwargs.get(self.lookup_field, None))
        except Contact.DoesNotExist as exception:
            logger.warning(exception)
            raise NotFound(get_message(status.HTTP_404_NOT_FOUND))



@extend_schema(
    tags=['profile'],
    description='list of searching results.',
    responses={
        200: OpenApiResponse(response=StreamerSerializer, description=VALUES[200]),
        400: OpenApiResponse(description=VALUES[400]),
    },
    parameters=[
        OpenApiParameter(
            name='channel_name',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True
        ),
    ],
)
class SearchUser(generics.ListAPIView):
    authentication_classes = ()
    serializer_class = StreamerSerializer
    query_serializer_class = SearchUserQuery

    def get_queryset(self):
        query_serializer = self.query_serializer_class(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        channel_name = query_serializer.validated_data.get('channel_name')
        queryset = StreamerView.objects.filter(channel_name__icontains=channel_name).annotate(length=Length('channel_name'), idx=StrIndex('channel_name', Value(channel_name))).order_by('length', 'idx')
        return queryset
