from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .apps import UsersConfig
from .views import PaymentListAPIView, UserCreateAPIView, UserProfileAPIView

app_name = UsersConfig.name

urlpatterns = [
    path("register/", UserCreateAPIView.as_view(), name="user_register"),
    path("profile/<int:pk>/", UserProfileAPIView.as_view(), name="user_profile"),
    path("payments/", PaymentListAPIView.as_view(), name="payment_list"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
