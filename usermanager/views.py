from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from api_diplom_final.celery import send_email
from usermanager.models import Contact, ConfirmEmailToken
from usermanager.serializers import UserSerializer, ContactSerializer


class RegisterAccount(APIView):
    """
    Класс для регистрации покупателей.
    """

    throttle_scope = 'register'

    def post(self, request, *args, **kwargs):
        """
        Метод проверяет наличие обязательных полей, сложность пароля,
        уникальность имени пользователя, после чего сохраняет пользователя в системе.
        """

        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return Response({'Status': False, 'Errors': {'password': error_array}}, status=403)
            else:
                request.data._mutable = True
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()

                    # Отправка письма с подтверждением почты.
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    title = f'Подтверждение регистрации пользователя: {token.user.email}'
                    message = f'Токен: {token.key}'
                    email = token.user.email
                    send_email(title, message, email)

                    return Response({'Status': True}, status=201)
                else:
                    return Response({'Status': False,
                                     'Errors': user_serializer.errors}, status=422)

        return Response({'Status': False,
                         'Errors': 'Не указаны все необходимые аргументы'}, status=401)


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса.
    """

    throttle_scope = 'anon'

    def post(self, request, *args, **kwargs):
        """
        Метод проверяет наличие обязательных полей, статус токена и адреса почты,
        после чего подтверждает регистрацию пользователя в системе.
        """
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'Status': True})
            else:
                return Response({'Status': False,
                                 'Errors': 'Неправильно указан токен или email'})

        return Response({'Status': False,
                         'Errors': 'Не указаны все необходимые аргументы'})


class AccountDetails(APIView):
    """
    Класс для работы данными пользователя.
    """

    throttle_scope = 'user'

    def get(self, request, *args, **kwargs):
        """
        Метод позволяет получить данные о пользователе.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False,
                             'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей.
    """

    throttle_scope = 'anon'

    def post(self, request, *args, **kwargs):
        """
        Метод позволяет произвести авторизацию пользователя.
        Проверяет обязательные поля (пароль и email), после чего создает токен для пользователя.
        """
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({'Status': True, 'Token': token.key}, status=200)

            return Response({'Status': False,
                             'Errors': 'Не удалось авторизовать'}, status=403)

        return Response({'Status': False,
                         'Errors': 'Не указаны все необходимые аргументы'}, status=401)


class ContactView(APIView):
    """ Класс для работы с контактами покупателей. """

    throttle_scope = 'user'

    def get(self, request, *args, **kwargs):
        """
        Метод проверяет авторизацию,
        после чего выдает информацию о контактных данных покупателя.
        """

        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Метод проверяет авторизацию,
        после чего добавляет информацию о новых контактных данных покупателя.
        """

        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({'Status': True}, status=201)
            else:
                Response({'Status': False,
                          'Errors': serializer.errors})

        return Response({'Status': False,
                         'Errors': 'Не указаны все необходимые аргументы'}, status=401)

    def put(self, request, *args, **kwargs):
        """
        Метод проверяет авторизацию,
        после чего обновляет информацию о контактных данных покупателя.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                print(contact)
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({'Status': True})
                    else:
                        Response({'Status': False,
                                  'Errors': serializer.errors})

        return Response({'Status': False,
                         'Errors': 'Не указаны все необходимые аргументы'}, status=400)

    def delete(self, request, *args, **kwargs):
        """
        Метод проверяет авторизацию,
        после чего удаляет информацию о контактных дынных покупателя.
        """

        if not request.user.is_authenticated:
            return Response({'Status': False,
                             'Error': 'Log in required'},
                            status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response({'Status': True,
                                 'Удалено объектов': deleted_count},
                                status=200)
        return Response({'Status': False,
                         'Errors': 'Не указаны все необходимые аргументы'},
                        status=400)
