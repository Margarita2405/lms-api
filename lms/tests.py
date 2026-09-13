from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription

User = get_user_model()


class LmsBasicTests(APITestCase):
    def setUp(self):
        # Обычный пользователь (владелец)
        self.user = User.objects.create_user(email="user@test.com", password="testpass")
        # Модератор
        self.moderator = User.objects.create_user(email="moder@test.com", password="testpass")
        group, _ = Group.objects.get_or_create(name="moderators")
        self.moderator.groups.add(group)

        # Курс, созданный self.user
        self.course = Course.objects.create(title="Курс для тестов", owner=self.user)
        # Урок, созданный self.user
        self.lesson = Lesson.objects.create(
            title="Урок 1", video_url="https://www.youtube.com/watch?v=abc", course=self.course, owner=self.user
        )

        # URL-ы
        self.lesson_list_url = reverse("lms:lesson_list")
        self.lesson_create_url = reverse("lms:lesson_create")
        self.lesson_detail_url = lambda pk: reverse("lms:lesson_get", args=[pk])
        self.lesson_update_url = lambda pk: reverse("lms:lesson_update", args=[pk])
        self.lesson_delete_url = lambda pk: reverse("lms:lesson_delete", args=[pk])
        self.subscribe_url = reverse("lms:course_subscribe")
        self.course_detail_url = lambda pk: reverse("lms:course-detail", args=[pk])

    # Создание урока
    def test_create_lesson_owner_success(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "Новый урок", "video_url": "https://www.youtube.com/watch?v=xyz", "course": self.course.id}
        response = self.client.post(self.lesson_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.last().owner, self.user)

    def test_create_lesson_moderator_forbidden(self):
        self.client.force_authenticate(user=self.moderator)
        data = {"title": "Урок модератора", "course": self.course.id}
        response = self.client.post(self.lesson_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_lesson_invalid_url(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "Плохой урок", "video_url": "https://vimeo.com/123", "course": self.course.id}
        response = self.client.post(self.lesson_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("youtube.com", str(response.data))

    # Список уроков (пагинация не проверяется явно, но пагинатор есть)
    def test_list_lessons_owner_only_own(self):
        self.client.force_authenticate(user=self.user)
        # Создаём чужой урок другим пользователем
        other = User.objects.create_user(email="other@test.com", password="pass")
        Lesson.objects.create(title="Чужой урок", course=self.course, owner=other)
        response = self.client.get(self.lesson_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)  # только свой

    # Просмотр урока
    def test_retrieve_lesson_owner_ok(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.lesson_detail_url(self.lesson.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_lesson_other_user_404(self):
        other = User.objects.create_user(email="other@test.com", password="pass")
        self.client.force_authenticate(user=other)
        response = self.client.get(self.lesson_detail_url(self.lesson.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_lesson_moderator_ok(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(self.lesson_detail_url(self.lesson.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Обновление урока
    def test_update_lesson_owner_ok(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "Обновлено"}
        response = self.client.patch(self.lesson_update_url(self.lesson.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Обновлено")

    def test_update_lesson_other_user_404(self):
        other = User.objects.create_user(email="other@test.com", password="pass")
        self.client.force_authenticate(user=other)
        response = self.client.patch(self.lesson_update_url(self.lesson.id), {"title": "Взлом"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_lesson_moderator_ok(self):
        self.client.force_authenticate(user=self.moderator)
        data = {"title": "Отредактировано модератором"}
        response = self.client.patch(self.lesson_update_url(self.lesson.id), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Удаление урока
    def test_delete_lesson_owner_ok(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.lesson_delete_url(self.lesson.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_delete_lesson_other_user_404(self):
        other = User.objects.create_user(email="other@test.com", password="pass")
        self.client.force_authenticate(user=other)
        response = self.client.delete(self.lesson_delete_url(self.lesson.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_lesson_moderator_403(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.lesson_delete_url(self.lesson.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Подписка на курс
    def test_subscribe_and_unsubscribe(self):
        self.client.force_authenticate(user=self.user)
        # Подписаться
        response = self.client.post(self.subscribe_url, {"course_id": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "подписка добавлена")
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        # Отписаться
        response = self.client.post(self.subscribe_url, {"course_id": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "подписка удалена")
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_is_subscribed_field(self):
        self.client.force_authenticate(user=self.user)
        url = self.course_detail_url(self.course.id)
        # Изначально не подписан
        response = self.client.get(url)
        self.assertFalse(response.data["is_subscribed"])

        # Подписываемся
        self.client.post(self.subscribe_url, {"course_id": self.course.id})
        response = self.client.get(url)
        self.assertTrue(response.data["is_subscribed"])
