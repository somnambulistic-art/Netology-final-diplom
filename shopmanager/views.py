from distutils.util import strtobool
from yaml import load as load_yaml, Loader
from requests import get

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Q
from django.http import JsonResponse
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from shopmanager.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter
from shopmanager.serializers import CategorySerializer, ShopSerializer, ProductInfoSerializer


class CategoryView(ListAPIView):
    """ Класс для просмотра категорий. """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    @extend_schema(request=CategorySerializer, responses={200: CategorySerializer})
    def get(self, request):
        """ Метод возвращает список категорий. """

        category_list = super().get(request)
        return category_list


class ShopView(ListAPIView):
    """ Класс для просмотра списка магазинов. """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoViewSet(ModelViewSet):
    """ Класс для поиска товаров. """

    throttle_scope = 'anon'
    serializer_class = ProductInfoSerializer
    permission_classes = [IsAuthenticated]
    ordering = ('product')

    @extend_schema(request=ProductInfoSerializer, responses={200: ProductInfoSerializer})
    def get(self):
        """
        Метод принимает в качестве аргументов параметры для поиска
        и возвращает соответствующие им товары.
        """

        query = Q(shop__state=True)
        shop_id = self.request.query_params.get('shop_id')
        category_id = self.request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        return queryset


class PartnerUpdate(APIView):
    """ Класс для обновления прайса от поставщика. """

    throttle_scope = 'user'

    def post(self, request, *args, **kwargs):
        """
        Метод post проверяет авторизацию пользователя, его тип (требуется тип 'shop'),
        после чего создает обновленный прайс-лист.
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False,
                                 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('user_register_url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False,
                                     'Error': str(e)})
            else:
                stream = get(url).content
                data = load_yaml(stream, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})


class PartnerState(APIView):
    """ Класс для работы со статусом поставщика. """

    throttle_scope = 'user'

    def get(self, request, *args, **kwargs):
        """
        Метод post проверяет авторизацию пользователя, его тип (требуется тип 'shop'),
        после чего возвращает информацию о текущем статусе пользователя-магазина.
        """

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Метод проверяет авторизацию и тип пользователя (для работы требуется тип 'shop'),
        после чего обновляет информацию о текущем пользователя-магазина.
        """

        if not request.user.is_authenticated:
            return JsonResponse({'Status': False,
                                 'Error': 'Log in required'},
                                status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False,
                                 'Error': 'Только для магазинов'},
                                status=403)

        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False,
                                     'Errors': str(error)})

        return JsonResponse({'Status': False,
                             'Errors': 'Не указаны все необходимые аргументы'})
