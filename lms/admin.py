from django.contrib import admin

from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "price")
    search_fields = ("title", "description")
    list_filter = ("price",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "video_url")
    list_filter = ("course",)
    search_fields = ("title", "description")
