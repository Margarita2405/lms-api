from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Email", help_text="Укажите email")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="Имя", help_text="Введите имя")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Фамилия", help_text="Введите фамилию")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон", help_text="Укажите телефон")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Город", help_text="Укажите город")
    avatar = models.ImageField(
        upload_to="users/avatars", blank=True, null=True, verbose_name="Аватарка", help_text="Загрузите аватарку"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Payment(models.Model):
    PAYMENT_METHODS = (
        ("cash", "Наличные"),
        ("transfer", "Перевод на счет"),
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="payments", verbose_name="Пользователь"
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплаты")
    course = models.ForeignKey(
        "lms.Course", on_delete=models.CASCADE, null=True, blank=True, verbose_name="Оплаченный курс"
    )
    lesson = models.ForeignKey(
        "lms.Lesson", on_delete=models.CASCADE, null=True, blank=True, verbose_name="Оплаченный урок"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма оплаты")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="Способ оплаты")
    # Поля для интеграции со Stripe
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID продукта в Stripe")
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID цены в Stripe")
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID сессии Stripe")
    payment_link = models.URLField(max_length=500, blank=True, null=True, verbose_name="Ссылка на оплату")
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[("pending", "Ожидание"), ("paid", "Оплачено"), ("failed", "Ошибка")],
        verbose_name="Статус платежа",
    )

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.user.email} - {self.amount} ({self.payment_date})"
