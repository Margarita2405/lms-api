import django_filters

from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    course = django_filters.NumberFilter(field_name="course_id", lookup_expr="exact")
    lesson = django_filters.NumberFilter(field_name="lesson_id", lookup_expr="exact")
    payment_method = django_filters.CharFilter(field_name="payment_method", lookup_expr="exact")

    class Meta:
        model = Payment
        fields = ["course", "lesson", "payment_method"]
