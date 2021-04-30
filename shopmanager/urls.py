from django.urls import path

from shopmanager.views import CategoryView, ShopView, ProductInfoView, PartnerState, PartnerUpdate


app_name = 'shopmanager'

urlpatterns = [
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductInfoView.as_view(), name='shops'),
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),

]
