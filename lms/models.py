from django.db import models

from config import settings


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название курса", help_text="Введите название курса")
    preview = models.ImageField(
        upload_to="lms/previews",
        verbose_name="Превью (картинка)",
        blank=True,
        null=True,
        help_text="Загрузите превью(картинку",
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание курса", help_text="Введите описание")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Владелец",
        blank=True,
        null=True,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Цена курса")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название урока", help_text="Введите название урока")
    description = models.TextField(verbose_name="Описание урока", blank=True, null=True, help_text="Введите описание")
    preview = models.ImageField(
        upload_to="lms/previews",
        verbose_name="Превью (картинка)",
        blank=True,
        null=True,
        help_text="Загрузите превью(картинку",
    )
    video_url = models.URLField(verbose_name="Ссылка на видео", blank=True, null=True)

    # Связь с курсом: один курс — много уроков
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Владелец",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["title"]

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="Пользователь"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="Курс")
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        # Защита от дублирующихся подписок
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} подписан на {self.course}"
