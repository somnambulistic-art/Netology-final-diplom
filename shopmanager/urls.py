from django.urls import path, include
from rest_framework.routers import DefaultRouter

from shopmanager.views import CategoryView, ShopView, ProductInfoViewSet, PartnerState, PartnerUpdate


app_name = 'shopmanager'
router = DefaultRouter()
router.register(r'products', ProductInfoViewSet, basename='products')

urlpatterns = [
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('', include(router.urls)),
]
