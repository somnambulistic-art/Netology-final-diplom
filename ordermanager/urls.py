from django.urls import path

from ordermanager.views import OrderView, PartnerOrders, BasketView


app_name = 'ordermanager'

urlpatterns = [
    path('order', OrderView.as_view(), name='order'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),
    path('basket', BasketView.as_view(), name='basket'),

]
