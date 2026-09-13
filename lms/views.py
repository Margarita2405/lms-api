from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.models import Course, Lesson, Subscription
from lms.paginators import LmsPagination
from lms.serializers import CourseSerializer, LessonSerializer
from lms.services import create_checkout_session, create_stripe_price, create_stripe_product, retrieve_session_status
from users.models import Payment
from users.permissions import IsNotModerator, IsOwner


# CRUD для Курсов через ViewSet
class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    pagination_class = LmsPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Course.objects.none()
        if user.groups.filter(name="moderators").exists():
            return Course.objects.all().order_by("id")  # Добавили сортировку
        return Course.objects.filter(owner=user).order_by("id")  # Добавили сортировку

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [IsAuthenticated, IsNotModerator]
        elif self.action in ["destroy", "update", "partial_update"]:
            self.permission_classes = [IsAuthenticated, IsNotModerator, IsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # Обновление курса
    def perform_update(self, serializer, send_course_update_email=None):
        course = serializer.save()
        subscribers = Subscription.objects.filter(course=course).select_related('user')
        emails = [sub.user.email for sub in subscribers if sub.user.email]
        if emails:
            send_course_update_email.delay(course.id, emails)


# CRUD для Уроков через Generics
class LessonListAPIView(generics.ListAPIView):
    serializer_class = LessonSerializer
    pagination_class = LmsPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Lesson.objects.none()
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all().order_by("id")  # Добавили сортировку
        return Lesson.objects.filter(owner=user).order_by("id")  # Добавили сортировку


class LessonCreateAPIView(generics.CreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsNotModerator]  # только не модераторы

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Lesson.objects.none()
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonUpdateAPIView(generics.UpdateAPIView):
    serializer_class = LessonSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Lesson.objects.none()
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonDestroyAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsNotModerator]  # только не модераторы

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Lesson.objects.none()
        return Lesson.objects.filter(owner=user)


# Класс для добавления и удаления подписки у пользователя
class SubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Получаем пользователя
        user = request.user
        # Получаем id курса из тела запроса (data)
        course_id = request.data.get("course_id")

        # Проверяем, существует ли курс вообще
        course_item = get_object_or_404(Course, id=course_id)

        # Ищем подписку этого пользователя на этот курс
        subs_item = Subscription.objects.filter(user=user, course=course_item)

        # Если подписка у пользователя на этот курс есть - удаляем ее
        if subs_item.exists():
            subs_item.delete()
            message = "подписка удалена"

        # Если подписки у пользователя на этот курс нет - создаем ее
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = "подписка добавлена"

        # Возвращаем ответ в API
        return Response({"message": message}, status=status.HTTP_200_OK)


# Эндпоинт для оплаты курса
class CreateCoursePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Создаёт платёжную сессию Stripe для оплаты курса",
        responses={
            200: openapi.Response(
                description="Ссылка на оплату",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "payment_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "payment_url": openapi.Schema(type=openapi.TYPE_STRING),
                        "session_id": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            )
        },
    )
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = request.user

        # Создаём продукт и цену в Stripe
        product_id = create_stripe_product(course)
        price_id = create_stripe_price(product_id, course.price)

        # Определяем URL для возврата после оплаты (можно сделать статическими или из запроса)
        base_url = request.build_absolute_uri("/")
        success_url = f"{base_url}payment/success/"
        cancel_url = f"{base_url}payment/cancel/"

        # Создаём сессию оплаты
        session_id, payment_url = create_checkout_session(price_id, success_url, cancel_url)

        # Сохраняем платёж в базе данных
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=course.price,
            stripe_product_id=product_id,
            stripe_price_id=price_id,
            stripe_session_id=session_id,
            payment_link=payment_url,
            status="pending",
            payment_method="card",  # или другой метод, например, 'stripe'
        )

        # 5. Возвращаем клиенту ссылку на оплату
        return Response({"payment_id": payment.id, "payment_url": payment_url, "session_id": session_id})


# Эндпоинт для проверки статуса оплаты (дополнительное задание)
class CheckPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Проверка статуса оплаты по ID платежа",
        responses={
            200: openapi.Response(
                description="Статус платежа",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "status": openapi.Schema(type=openapi.TYPE_STRING, enum=["pending", "paid", "failed"]),
                    },
                ),
            )
        },
    )
    def get(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        if not payment.stripe_session_id:
            return Response({"error": "No Stripe session ID"}, status=400)

        status = retrieve_session_status(payment.stripe_session_id)
        if status == "paid" and payment.status != "paid":
            payment.status = "paid"
            payment.save()
        return Response({"status": payment.status})
