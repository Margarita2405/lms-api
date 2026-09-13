from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.permissions import IsAuthenticated

from .filters import PaymentFilter
from .models import CustomUser, Payment
from .permissions import IsOwnerProfile
from .serializers import PaymentSerializer, UserCreateSerializer, UserProfileSerializer, UserPublicProfileSerializer


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        # Если запрашиваем свой профиль, используем полный сериализатор
        if self.request.user == self.get_object():
            return UserProfileSerializer
        # Для чужого профиля – публичный сериализатор (без фамилии, без платежей)
        return UserPublicProfileSerializer

    def get_permissions(self):
        # Для GET (просмотр) – разрешаем всем авторизованным
        if self.request.method == "GET":
            self.permission_classes = [IsAuthenticated]
        # Для PUT/PATCH – разрешаем только владельцу
        else:
            self.permission_classes = [IsAuthenticated, IsOwnerProfile]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        # переопределяем retrieve, чтобы проверить доступ к чужому профилю (но он разрешён)
        return super().retrieve(request, *args, **kwargs)


class PaymentListAPIView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["payment_date"]
    ordering = ["-payment_date"]  # по умолчанию сначала новые


class UserCreateAPIView(generics.CreateAPIView):
    """Регистрация нового пользователя. Доступен без аутентификации."""

    queryset = CustomUser.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]  # открытый доступ
