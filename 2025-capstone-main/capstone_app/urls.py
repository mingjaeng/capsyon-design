from django.urls import path
from . import views

urlpatterns = [
    path('stock-info/', views.stock_info_api, name='stock_info'),  # API 엔드포인트
]
