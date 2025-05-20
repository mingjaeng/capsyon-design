from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect),  # 루트 접속 시 리다이렉트
    path('stock-info/', views.stock_info_api, name='stock_info'),
]

from . import views
urlpatterns = [
    path('detail/', views.company_detail, name='company_detail'),
]
