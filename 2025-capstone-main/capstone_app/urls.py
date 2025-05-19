from django.urls import path
from . import views

urlpatterns = [
    path('stock-info/', views.stock_info_api, name='stock_info'),  # ✅ 올바른 함수 이름
]
