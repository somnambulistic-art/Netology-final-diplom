from copy import deepcopy

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from usermanager.models import User


class UserManagerAPITests(APITestCase):
    """
    Класс для тестирования работы контроллеров из приложения usermanager.
    """

    user_register_url = reverse('usermanager:user-register')
    user_login_url = reverse('usermanager:user-login')
    user_details_url = reverse('usermanager:user-details')

    data = {
        'first_name': 'TestFirstName',
        'last_name': 'TestLastName',
        'email': 'test@gmail.com',
        'password': 'TestPassword123',
        'company': 'TestCompany',
        'position': 'TestPosition',
        'contacts': []
    }

    def setUp(self):
        return super().setUp()

    def create_test_user(self):
        data = deepcopy(self.data)
        data.pop('contacts', [])
        password = data.pop('password')

        user = User.objects.create(**data, type='buyer')
        user.is_active = True
        user.set_password(password)
        user.save()

    def test_new_user_registration(self):
        """
        Проверка корректной работы контроллера RegisterAccount,
        а именно кода HTTP-статуса и наличия статуса True в данных ответа.
        """

        response = self.client.post(self.user_register_url, self.data)

        assert response.status_code == 201
        assert response.data['Status'] is True

    def test_new_user_registration_missed_field(self):
        """
        Проверка корректной работы контроллера RegisterAccount в случае,
        когда при регистрации нового пользователя были заполнены не все поля.
        """

        data = deepcopy(self.data)
        data.pop('email')

        response = self.client.post(self.user_register_url, data)

        assert 'Errors' in response.data
        assert response.data['Errors'] == 'Не указаны все необходимые аргументы'
        assert response.status_code == 401

    def test_new_user_registration_validation_error(self):
        """
        Проверка корректной работы контроллера RegisterAccount в случае,
        когда при регистрации нового пользователя параметр не прошёл валидацию.
        """

        data = deepcopy(self.data)
        data['email'] = ''

        response = self.client.post(self.user_register_url, data)

        assert response.status_code == 422
        assert response.data['Status'] is False
        assert 'Errors' in response.data

    def test_new_user_registration_password_error(self):
        """
        Проверка корректной работы контроллера RegisterAccount в случае,
        когда при регистрации нового пользователя указан неподходящий пароль.
        """

        data = deepcopy(self.data)
        data['password'] = ''
        response = self.client.post(self.user_register_url, data)

        assert response.status_code == 403
        assert response.data['Status'] is False
        assert 'Errors' in response.data

    def test_account_login(self):
        """
        Проверка корректной работы контроллера LoginAccount,
        а именно кода HTTP-статуса и наличия статуса True в данных ответа
        (при успешной авторизации).
        """

        self.create_test_user()
        email = self.data['email']
        password = self.data['password']
        login_data = dict(email=email, password=password)
        response = self.client.post(self.user_login_url, login_data)

        assert response.status_code is 200
        assert 'Status' in response.data
        assert response.data['Status'] is True

    def test_account_login_missed_field(self):
        """
        Проверка корректной работы контроллера LoginAccount в случае,
        когда при авторизации были указаны не все параметры.
        """

        self.create_test_user()
        email = self.data['email']
        password = self.data['password']
        login_data = dict(email=email, password=password)
        login_data.pop('email')

        response = self.client.post(self.user_login_url, login_data)

        assert self.failureException == AssertionError
        assert response.status_code == 401

    def test_contact_get_method(self):
        """ Проверка корректной работы метода get у контроллера ContactView,
        а именно кода HTTP-статуса и отсутствия параметра 'Errors' в данных ответа.
        """

        url_contact = reverse('usermanager:user-contact')

        self.create_test_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(url_contact, format='json')

        assert response.status_code == 200
        assert 'Errors' not in response.data

    def test_contact_get_method_unauthorized(self):
        """ Проверка корректной работы метода get у контроллера ContactView в случае,
        когда запрос был выполнен неавторизованным пользователем.
        Проверяет код HTTP-статуса, наличие статуса False в данных ответа,
        наличие параметра 'Errors' в ответе.
        """

        url_contact = reverse('usermanager:user-contact')
        response = self.client.get(url_contact, format='json')

        assert response.status_code == 403
        assert response.data['Status'] is False
        assert 'Error' in response.data

    def test_contact_post_method(self):
        """ Проверка корректной работы метода post у контроллера ContactView.
        Проверяет код HTTP-статуса, наличие статуса True в данных ответа,
        отсутствие параметра 'Errors' в данных ответа.
        """

        url_contact = reverse('usermanager:user-contact')

        self.create_test_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {
            "city": "Test-City",
            "street": "Test Street",
            "house": "23",
            "structure": "2",
            "building": "3",
            "apartment": "23",
            "phone": "8-999-666-23-93"
        }

        response = self.client.post(url_contact, data=data)

        assert response.status_code == 201
        assert response.data['Status'] is True
        assert 'Error' not in response.data

    def test_contact_post_method_missed_field(self):
        """ Проверка корректной работы метода post у контроллера ContactView в случае,
        когда были указаны не все поля.
        Проверяет код HTTP-статуса, наличие статуса False в данных ответа,
        отсутствие параметра 'Errors' в данных ответа.
        """

        url_contact = reverse('usermanager:user-contact')

        self.create_test_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {
            "city": "Test-City",
            "structure": "2",
            "building": "3",
            "apartment": "23",
            "phone": "8-999-666-23-93"
        }

        response = self.client.post(url_contact, data=data, format='json')

        assert response.status_code == 401
        assert response.data['Status'] is False
        assert 'Error' not in response.data

    def test_contact_delete_method(self):
        """ Проверка корректной работы метода delete у контроллера ContactView.
        Проверяет код HTTP-статуса и наличие статуса True в данных ответа.
        """

        url_contact = reverse('usermanager:user-contact')

        self.create_test_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {"items": "10"}

        response = self.client.delete(url_contact, data=data, format='json')

        assert response.status_code == 200
        assert response.data['Status'] is True

    def test_contact_delete_method_missed_field(self):
        """ Проверка корректной работы метода delete у контроллера ContactView в случае,
        когда были указаны не все поля.
        Проверяет код HTTP-статуса и наличие статуса False в данных ответа.
        """

        url_contact = reverse('usermanager:user-contact')

        self.create_test_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {"items": ''}

        response = self.client.delete(url_contact, data=data, format='json')

        assert response.status_code == 400
        assert response.data['Status'] is False
