from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import HttpResponse

schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version="v1",
        description="Your API description",
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def payment_success(request):
    return HttpResponse("✅ Оплата прошла успешно! Спасибо за покупку.")


def payment_cancel(request):
    return HttpResponse("❌ Оплата отменена. Вы можете вернуться и попробовать снова.")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("lms/", include("lms.urls", namespace="lms")),
    path("users/", include("users.urls", namespace="users")),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("payment/success/", payment_success, name="payment_success"),
    path("payment/cancel/", payment_cancel, name="payment_cancel"),
]
