from rest_framework import serializers

from lms.models import Course, Lesson, Subscription

from .validators import YoutubeOnlyValidator


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "preview", "video_url", "course", "owner"]

        # Защищаем и ссылку на видео, и описание урока
        validators = [YoutubeOnlyValidator(field="video_url"), YoutubeOnlyValidator(field="description")]


class CourseSerializer(serializers.ModelSerializer):
    # Добавляем вложенный список уроков, которые принадлежат курсу (благодаря related_name="lessons")
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    # Поле для отображения статуса подписки текущего пользователя
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "lessons", "lessons_count", "is_subscribed", "owner"]

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    # Интегрируем класс-валидатор в class Meta для проверки курса
    validators = [YoutubeOnlyValidator(field="description")]

    def get_is_subscribed(self, obj):
        # Извлекаем объект запроса из контекста сериализатора
        request = self.context.get("request")

        # Если запрос пустой или пользователь не авторизован — возвращаем False
        if not request or not request.user or request.user.is_anonymous:
            return False

        # Возвращает True, если подписка существует, и False, если её нет
        return Subscription.objects.filter(user=request.user, course=obj).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["id", "user", "course", "subscribed_at"]
        read_only_fields = ["user"]
