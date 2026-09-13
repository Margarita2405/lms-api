import re

from rest_framework.serializers import ValidationError


class YoutubeOnlyValidator:
    """Валидатор проверяет отсутствие в материалах ссылок на сторонние ресурсы, кроме youtube.com."""

    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        # Получаем текст или URL из тестируемого поля
        text_content = value.get(self.field)

        if not text_content:
            return

        # Регулярное выражение для поиска любых URL-адресов в тексте
        url_pattern = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

        # Находим все ссылки внутри поля
        found_urls = url_pattern.findall(str(text_content))

        # Проверяем каждую найденную ссылку
        for url in found_urls:
            if "youtube.com" not in url:
                raise ValidationError(
                    {self.field: "Запрещено добавлять ссылки на сторонние ресурсы, кроме youtube.com."}
                )
