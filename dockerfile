# Используем официальный образ Python
FROM python:3.13-slim

# Отключаем создание .pyc и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости (нужны для psycopg2, Pillow и т.д.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями Python
COPY requirements.txt .

# Принудительно обновляем pip перед установкой
RUN pip install --no-cache-dir --upgrade pip

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаём папки для статики и медиа (чтобы не было ошибок прав)
RUN mkdir -p /app/static /app/media

# Копируем весь проект
COPY . .

# Открываем порт 8000
EXPOSE 8000

# Запускаем gunicorn (сбор статики выполняется перед запуском)
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
