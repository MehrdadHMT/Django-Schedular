import json
from django.core.cache import cache
from project.base_test import CustomBaseTest, JWTAuthorizedTest, PaginatedTest
from project.apps.profile.v1 import views
from django.conf import settings
from project.settings import VALUES
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from project.apps.profile.models import Contact,User
from hashlib import blake2b


views.CreateContactView.throttle_classes = ()
views.DeleteContactView.throttle_classes = ()
views.ListContactView.throttle_classes = ()
views.SyncContactView.throttle_classes = ()


class LoginTest(CustomBaseTest):
    API_NAME = 'profile:login'
    METHOD = 'POST'

    @patch('project.apps.profile.views.s3_create_buckets', lambda x: None)
    def test_ok(self):
        user_pass = 'Test109010000000'
        data = json.dumps({'phone': str(self.user1.phone), 'password': user_pass})
        response1 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.registration_code(self.user1.phone)
        data = json.dumps({'phone': str(self.user1.phone), 'code': 111111})
        response2 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.registration_code(self.user1.phone)
        data = json.dumps({'phone': str(self.user1.phone), 'code': 111111, 'password': user_pass})
        response3 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.registration_code(self.user1.phone)
        data = json.dumps({'phone': str(self.user1.phone), 'code': 111111, 'password': ''})
        response4 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response4.status_code, status.HTTP_200_OK)
        data = json.dumps({'phone': str(self.user1.phone), 'code': None, 'password': user_pass})
        response5 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response5.status_code, status.HTTP_200_OK)
        self.registration_code('09000000000')
        data = json.dumps({'phone': '09000000000', 'name': 'Test', 'code': 111111})
        response6 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response6.status_code, status.HTTP_200_OK)
        created_user = User.objects.get(phone='09000000000')
        self.assertEqual(created_user.name, 'Test')
        self.assertEqual(created_user.phone, '09000000000')

        # login with captcha
        VALUES['CAPTCHA_REQUIRED'] = True
        cache.clear()
        user2_pass = 'Test209020000000'
        wrong_pass = 'wrong pass'
        for _ in range(VALUES['LOGIN_MAX_REQUEST'] - 1):
            data = json.dumps({'phone': str(self.user2.phone), 'password': wrong_pass})
            self.client.post(reverse('profile:login'), data, content_type='application/json')
        data = json.dumps({'phone': str(self.user2.phone), 'password': user2_pass})
        response7 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response7.status_code, status.HTTP_200_OK)
        self.assertIsNone(response7.json().get('captcha_required'))
        cache.clear()

        for _ in range(VALUES['LOGIN_MAX_REQUEST']):
            data = json.dumps({'phone': str(self.user2.phone), 'password': wrong_pass})
            self.client.post(reverse('profile:login'), data, content_type='application/json')
        data = json.dumps({'phone': str(self.user2.phone), 'password': user2_pass})
        response8 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response8.status_code, status.HTTP_400_BAD_REQUEST)
        VALUES['CAPTCHA_REQUIRED'] = False

    @patch('project.apps.profile.views.s3_create_buckets', lambda x: None)
    def test_bad_request(self):
        data = json.dumps({'phone': int(self.user1.phone), 'password': int(self.user1.phone)})
        response1 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        response2 = self.client.post(reverse('profile:login'))
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': str(self.user1.phone), 'code': '', 'password': ''})
        response3 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'code': 111111, 'password': ''})
        response4 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response4.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': str(self.user1.phone), 'code': ''})
        response5 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response5.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': str(self.user1.phone), 'password': ''})
        response6 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response6.status_code, status.HTTP_400_BAD_REQUEST)
        self.registration_code('09111111111')
        data = json.dumps({'phone': '09111111111', 'name': 0})
        response7 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response7.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': '09111111111', 'name': 'ab'})
        response8 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response8.status_code, status.HTTP_400_BAD_REQUEST)

    def test_forbidden(self):
        # login with wrong password
        user_pass = '123456'
        data = json.dumps({'phone': str(self.user1.phone), 'password': user_pass})
        response1 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_403_FORBIDDEN)
        # login with wrong generate code
        self.registration_code(self.user1.phone)
        data = json.dumps({'phone': str(self.user1.phone), 'code': 222222})
        response2 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)
        self.registration_code(self.user1.phone)
        self.registration_code(self.user1.phone)
        data = json.dumps({'phone': str(self.user1.phone), 'code': 111111, 'password': user_pass})
        response3 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response3.status_code, status.HTTP_403_FORBIDDEN)
        cache.clear()

        # login with captcha
        VALUES['CAPTCHA_REQUIRED'] = True
        wrong_pass = 'wrong pass'
        for _ in range(VALUES['LOGIN_MAX_REQUEST'] - 2):
            data = json.dumps({'phone': str(self.user2.phone), 'password': wrong_pass})
            self.client.post(reverse('profile:login'), data, content_type='application/json')
        data = json.dumps({'phone': str(self.user2.phone), 'password': wrong_pass})
        response4 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response4.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsNone(response4.json().get('captcha_required'))
        cache.clear()

        for _ in range(VALUES['LOGIN_MAX_REQUEST']):
            data = json.dumps({'phone': str(self.user2.phone), 'password': wrong_pass})
            self.client.post(reverse('profile:login'), data, content_type='application/json')
        data = json.dumps({'phone': str(self.user2.phone), 'password': wrong_pass})
        response5 = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response5.status_code, status.HTTP_400_BAD_REQUEST)
        VALUES['CAPTCHA_REQUIRED'] = False

    def test_not_acceptable(self):
        self.registration_code(self.user2.phone)
        for _ in range(int(settings.MAX_REFRESH_TOKENS)):
            data = json.dumps({'phone': str(self.user2.phone), 'code': 111111})
            self.client.post(reverse('profile:login'), data, content_type='application/json')
        data = json.dumps({'phone': str(self.user2.phone), 'code': 111111})
        response = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CodeGeneratorTest(CustomBaseTest):
    API_NAME = 'profile:code_generator'
    METHOD = 'POST'

    @patch('project.apps.profile.sms_providers.SmsServer.send_otp', lambda x, y, z: True)
    def test_ok(self):
        VALUES['CAPTCHA_REQUIRED'] = True
        cache.clear()
        data = json.dumps({'phone': str(self.user1.phone)})
        response = self.client.post(reverse('profile:code_generator'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.json().get('captcha_required'))
        VALUES['CAPTCHA_REQUIRED'] = False

    @patch('project.apps.profile.sms_providers.SmsServer.send_otp', lambda x, y, z: True)
    def test_bad_request(self):
        data= json.dumps({'phone': '02111111111'})
        response1 = self.client.post(reverse('profile:code_generator'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': '0912111'})
        response2 = self.client.post(reverse('profile:code_generator'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        response3 = self.client.post(reverse('profile:code_generator'))
        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)

        # generate code with captcha
        VALUES['CAPTCHA_REQUIRED'] = True
        for _ in range(VALUES['CODE_MAX_REQUEST']):
            data = json.dumps({'phone': '09000000000'})
            self.client.post(reverse('profile:code_generator'), data, content_type='application/json')
        data = json.dumps({'phone': '09000000000'})
        response4 = self.client.post(reverse('profile:code_generator'), data, content_type='application/json')
        self.assertEqual(response4.status_code, status.HTTP_400_BAD_REQUEST)
        VALUES['CAPTCHA_REQUIRED'] = False


class LogoutTestJWT(JWTAuthorizedTest):
    API_NAME = 'profile:logout'
    METHOD = 'POST'

    def test_ok(self):
        data = json.dumps({'jwt_refresh_token': self.refresh_token})
        response = self.client.post(reverse('profile:logout'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bad_request(self):
        self.login()
        response1 = self.client.post(reverse('profile:logout'))
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'jwt_refresh_token': ''})
        response2 = self.client.post(reverse('profile:logout'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordTestJWT(JWTAuthorizedTest):
    API_NAME = 'profile:change_password'
    METHOD = 'POST'

    def test_ok(self):
        sample_pass = 'Test209010000000'
        old_pass = 'Test109010000000'
        data = json.dumps({
            'old_password': old_pass,
            'new_password': sample_pass,
            'refresh_token': self.refresh_token
        })
        response1 = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response1.json()['jwt_access_token'])
        self.registration_code(self.user1.phone)
        data = json.dumps({
            'code': 111111,
            'new_password': old_pass,
            'refresh_token': response1.json()['jwt_refresh_token']
        })
        response2 = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.login()
        self.registration_code(self.user1.phone)
        data = json.dumps({
            'code': 123456,
            'old_password': old_pass,
            'new_password': sample_pass,
            'refresh_token': self.refresh_token
        })
        response3 = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response3.json()['jwt_access_token'])

    def test_bad_request(self):
        self.login()
        data = json.dumps({
            'code': 111111,
            'old_password': self.user1.phone,
        })
        response = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.registration_code(self.user1.phone)
        data = json.dumps({
            'code': 111111,
            'old_password': self.user1.phone,
            'refresh_token': self.refresh_token
        })
        response = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.registration_code(self.user1.phone)
        data = json.dumps({
            'code': 111111,
            'old_password': self.user1.phone,
            'new_password': 123456,
        })
        response = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_forbidden(self):
        old_pass = 'test'
        new_pass = '123456Test'
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.authorization_header)
        data = json.dumps({
            'old_password': old_pass,
            'new_password': new_pass,
            'refresh_token': self.refresh_token
        })
        response1 = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_403_FORBIDDEN)
        data = json.dumps({
            'code': 222222,
            'new_password': new_pass,
            'refresh_token': self.refresh_token
        })
        response2 = self.client.post(reverse('profile:change_password'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)


class RefreshTokenTest(CustomBaseTest):
    API_NAME = 'profile:refresh_token'
    METHOD = 'POST'

    def setUp(self):
        user_pass = 'Test109010000000'
        super().setUp()
        data = json.dumps({'phone': '09010000000', 'password': user_pass})
        response = self.client.post(reverse('profile:login'), data, content_type='application/json')
        self.refresh_token = response.json().get("jwt_refresh_token")
        self.access_token = response.json().get("jwt_access_token")

    def test_ok(self):
        data = json.dumps({'refresh': self.refresh_token})
        response = self.client.post(reverse('profile:refresh_token'), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['access'])

    def test_bad_request(self):
        response = self.client.post(reverse('profile:refresh_token'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized(self):
        data = json.dumps({'refresh': self.access_token})
        response1 = self.client.post(reverse('profile:refresh_token'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_401_UNAUTHORIZED)
        data = json.dumps({'refresh': 'self.refresh_token'})
        response2 = self.client.post(reverse('profile:refresh_token'), data, content_type='application/json')
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)


class GetProfileTestJWT(JWTAuthorizedTest):
    API_NAME = 'profile:get_profile'
    METHOD = 'GET'

    def test_ok(self):
        response = self.client.get(reverse('profile:get_profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(phone=self.user1.phone)
        self.assertEqual(response.json().get('name'), user.name)
        self.assertEqual(response.json().get('picture'), user.picture)
        self.assertEqual(response.json().get('phone'), user.phone)


class SetProfileTestJWT(JWTAuthorizedTest):
    API_NAME = 'profile:set_profile'
    METHOD = 'POST'

    @patch('project.apps.profile.views.SetProfileView.s3_delete_object', lambda x, y: None)
    def test_ok(self):
        data = json.dumps({'name': 'new test name1'})
        response1 = self.client.post(reverse('profile:set_profile'), data, content_type='application/json')
        user = User.objects.get(id=self.user1.id)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(user.name, 'new test name1')
        picture = f'/{VALUES["PROFILE_FOLDER"]}/{VALUES["USER_PROFILE_PREFIX"].format(self.user1.id)}/' + \
                  blake2b(f'{VALUES["OBJECT_KEY_PREFIX"]}{user.id}'.encode()).hexdigest()
        data = json.dumps({'picture': True})
        response2 = self.client.post(reverse('profile:set_profile'), data, content_type='application/json')
        user_picture = User.objects.get(id=self.user1.id).picture
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(user_picture, picture)
        picture = f'/{VALUES["PROFILE_FOLDER"]}/{VALUES["USER_PROFILE_PREFIX"].format(self.user1.id)}/' + \
                  blake2b(f'{VALUES["OBJECT_KEY_PREFIX"]}{user.id}'.encode()).hexdigest()
        data = json.dumps({'name': 'new test name2', 'picture': True})
        response3 = self.client.post(reverse('profile:set_profile'), data, content_type='application/json')
        user = User.objects.get(id=self.user1.id)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(user.name, 'new test name2')
        self.assertEqual(user.picture, picture)
        data = json.dumps({'name': 'new test name3', 'picture': False})
        response4 = self.client.post(reverse('profile:set_profile'), data, content_type='application/json')
        user = User.objects.get(id=self.user1.id)
        self.assertEqual(response4.status_code, status.HTTP_200_OK)
        self.assertEqual(user.name, 'new test name3')
        self.assertEqual(user.picture, None)

    def test_bad_request(self):
        data = json.dumps({'name': "a"*300})
        response1 = self.client.post(reverse('profile:set_profile'), data, content_type='application/json')
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'picture': None})
        response3 = self.client.post(reverse('profile:set_profile'), data, content_type='application/json')
        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)


def error_function(user_id):
    raise NotImplementedError


class CreateProfileUrlTestJWT(JWTAuthorizedTest):
    API_NAME = 'profile:create_profile_url'
    METHOD = 'GET'

    @patch('project.apps.profile.views.CreateProfileUrlView.s3_generate_presigned_url',
           lambda x: f'https://{VALUES["RGW_SERVER"]}/...' + 'Expires=123456')
    def test_ok(self):
        response = self.client.get(reverse('profile:create_profile_url'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('url'))
        self.assertTrue(response.json().get('url').startswith(f'https://{VALUES["RGW_SERVER"]}'))
        self.assertIn('Expires', response.json().get('url'))

    @patch('project.apps.profile.views.CreateProfileUrlView.s3_generate_presigned_url', error_function)
    def test_service_unavailable(self):
        response = self.client.get(reverse('profile:create_profile_url'))
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class CreateContactTests(JWTAuthorizedTest):
    API_NAME = 'profile:create_contact'
    METHOD = 'POST'

    def test_ok(self):
        data = json.dumps({'phone': self.user2.phone, 'name': 'test'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(list(Contact.objects.filter(user=self.user1, contact=self.user2).values_list('name', flat=True)), ['test'])
        data = json.dumps({'phone': self.user3.phone, 'name': 'تست'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(list(Contact.objects.filter(user=self.user1, contact=self.user3).values_list('name', flat=True)), ['تست'])

    def test_bad_request(self):
        data = json.dumps({'phone': '09121234567'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': '09121234567', 'nam': 'test'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': '0912123', 'name': 'test'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': '0912123456789', 'name': 'test'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_found(self):
        data = json.dumps({'phone': '09129999999', 'name': 'test'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_not_acceptable(self):
        Contact(user=self.user1, contact=self.user2, name='test1').save()
        data = json.dumps({'phone': self.user2.phone, 'name': 'test2'})
        response = self.client.post(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class DeleteContactTests(JWTAuthorizedTest):
    API_NAME = 'profile:delete_contact'
    METHOD = 'DELETE'

    def setUp(self):
        super().setUp()
        contacts = [Contact(user=self.user1, contact=self.user2, name='test1'), Contact(user=self.user1, contact=self.user3, name='test2')]
        Contact.objects.bulk_create(contacts)

    def test_ok(self):
        data = json.dumps({'phone': self.user2.phone})
        response = self.client.delete(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(list(Contact.objects.filter(user=self.user1, contact=self.user2).values_list('name', flat=True)), [])

    def test_bad_request(self):
        data = json.dumps({'phone': '0912123'})
        response = self.client.delete(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phone': '0912123456789'})
        response = self.client.delete(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({'phon': '09121234567'})
        response = self.client.delete(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.dumps({})
        response = self.client.delete(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_found(self):
        data = json.dumps({'phone': '09121234567'})
        response = self.client.delete(reverse(self.API_NAME), data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ListContactTests(JWTAuthorizedTest, PaginatedTest):
    API_NAME = 'profile:list_contact'
    METHOD = 'GET'

    def setUp(self):
        super().setUp()
        contacts = [Contact(user=self.user1, contact=self.user2, name='test1'), Contact(user=self.user1, contact=self.user3, name='test2')]
        Contact.objects.bulk_create(contacts)

    def test_ok(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.authorization_header)
        response = self.client.get(reverse(self.API_NAME))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.json()['results'], [{'phone': self.user2.phone, 'name': 'test1','picture_url':None }, {'phone': self.user3.phone, 'name': 'test2','picture_url':None}])


class SynContactTests(JWTAuthorizedTest):
    API_NAME = 'profile:sync_contact'
    METHOD = 'POST'

    def test_ok(self):
        data = {'contacts': [], 'is_transact': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'contacts':[{'phone': self.user2.phone, 'name': 'test1'}], 'is_transactional': True, 'fail_on_no_regs': True, 'add_extra': False, 'delete_missing': False}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [])

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}, {'phone': self.user3.phone, 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': True, 'add_extra': True, 'delete_missing': False}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user2.id, self.user3.id])

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}], 'is_transactional': True, 'fail_on_no_regs': True, 'add_extra': False, 'delete_missing': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user2.id])

        data = {'contacts': [{'phone': self.user3.phone, 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': True, 'add_extra': True, 'delete_missing': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user3.id])
        Contact.objects.all().delete()

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}, {'phone': '09121234567', 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': False, 'add_extra': False, 'delete_missing': False}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [])

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}, {'phone': self.user3.phone, 'name': 'test2'}, {'phone': '09121234567', 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': False, 'add_extra': True, 'delete_missing': False}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user2.id, self.user3.id])

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}, {'phone': '09121234567', 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': False, 'add_extra': False, 'delete_missing': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user2.id])

        data = {'contacts': [{'phone': self.user3.phone, 'name': 'test2'}, {'phone': '09121234567', 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': False, 'add_extra': True, 'delete_missing': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user3.id])

        data = {'contacts': [], 'is_transactional': False, 'add_extra': False, 'delete_missing': False}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}], 'is_transactional': False, 'add_extra': True, 'delete_missing': False}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user2.id, self.user3.id])

        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}], 'is_transactional': False, 'add_extra': False, 'delete_missing': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user2.id])

        data = {'contacts': [{'phone': self.user3.phone, 'name': 'test1'}], 'is_transactional': False, 'add_extra': True, 'delete_missing': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contact_ids = list(Contact.objects.filter(user=self.user1).values_list('contact', flat=True))
        contact_ids.sort()
        self.assertListEqual(contact_ids, [self.user3.id])

    def test_bad_request(self):
        data = {}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': 'abcd'}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'contacts': [], 'is_transactional': 'abcd'}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [], 'is_transactional': 1234}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '09121234567'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'name': 'abcd'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'pho': '09121234567', 'name': 'abcd'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '091212345', 'name': 'abcd'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '0912123456789', 'name': 'abcd'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '09121234567', 'name': 'abcd'}, {'phone': '09127654321'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '09121234567', 'name': 'abcd'}, {'name': 'dcba'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '09121234567', 'name': 'abcd'}, {'pho': '09127654321', 'name': 'dcba'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '09121234567', 'name': 'abcd'}, {'phone': '091276543', 'name': 'dcba'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'contacts': [{'phone': '09121234567', 'name': 'abcd'}, {'phone': '091287654321', 'name': 'dcba'}]}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_acceptable(self):
        data = {'contacts': [{'phone': self.user2.phone, 'name': 'test1'}, {'phone': '09121234567', 'name': 'test2'}], 'is_transactional': True, 'fail_on_no_regs': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        data = {'contacts': [{'phone': self.user1.phone, 'name': 'test1'},
                             {'phone': self.user2.phone, 'name': 'test2'}], 'is_transactional': True, 'add_extra': True}
        response = self.client.post(reverse(self.API_NAME), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CheckChannelNameTest(CustomBaseTest):
    API_NAME = 'profile:check_channel_name'
    METHOD = 'GET'

    def setUp(self):
        super().setUp()
        self.user1.channel_name = f'channel{self.user1.id}'
        self.user1.save()

    def test_ok(self):
        response = self.client.get(reverse(self.API_NAME, kwargs={'channel_name': 'Never_Used'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_conflict(self):
        response = self.client.get(reverse(self.API_NAME, kwargs={'channel_name':  f'channel{self.user1.id}'}))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_bad_request(self):
        response1 = self.client.get(reverse(self.API_NAME, kwargs={'channel_name':  't'}))
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)
        response2 = self.client.get(reverse(self.API_NAME, kwargs={'channel_name':  'te'}))
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        response3 = self.client.get(reverse(self.API_NAME, kwargs={'channel_name':  'test'*100}))
        self.assertEqual(response3.status_code, status.HTTP_400_BAD_REQUEST)
