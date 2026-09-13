import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from lms.models import Course, Lesson
from users.models import CustomUser, Payment


class Command(BaseCommand):
    help = "Fill payments with random data"

    def handle(self, *args, **options):
        # Получаем существующие объекты из базы (преобразуем QuerySet в список для использования random.choice())
        users = list(CustomUser.objects.all())
        courses = list(Course.objects.all())
        lessons = list(Lesson.objects.all())

        # Проверка на наличие пользователей
        if not users:
            self.stdout.write(self.style.ERROR("No users found"))
            return

        # Создаём пустой список платежей
        payments = []
        for _ in range(20):
            # Выбор случайного пользователя
            user = random.choice(users)
            # Генерация случайной суммы
            amount = Decimal(random.randint(500, 10000)) / 100
            # Случайный способ оплаты
            method = random.choice(["cash", "transfer"])
            # С вероятностью 50% – за курс, иначе – за урок
            if random.choice([True, False]) and courses:
                course = random.choice(courses)
                lesson = None
            else:
                course = None
                lesson = random.choice(lessons) if lessons else None

            # Создание объекта Payment
            payments.append(Payment(user=user, amount=amount, payment_method=method, course=course, lesson=lesson))

        # Сохраняем все объекты из списка за один запрос к базе данных
        Payment.objects.bulk_create(payments)
        # Вывод сообщения об успехе
        self.stdout.write(self.style.SUCCESS(f"Created {len(payments)} payments"))
