from django.urls import path
from . import views

urlpatterns = [
    path('stock-info/', views.get_stock_info, name='stock_info'),  # ✅ 함수 이름 맞춤
]
