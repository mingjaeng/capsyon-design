from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('stock_info'), name='home'),  # 루트 요청을 stock_info로 리디렉션
    path('stock-info/', views.stock_info, name='stock_info'),
]
