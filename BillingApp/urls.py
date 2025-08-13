from django.urls import path
from . import views

app_name = 'BillingApp'

urlpatterns = [
    path('', views.billing_form, name='billing_form'),
    path('bill/<uuid:purchase_id>/', views.bill_detail, name='bill_detail'),
    path('history/', views.purchase_history, name='purchase_history'),
    path('api/product-info/', views.get_product_info, name='get_product_info'),
]