FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Экспорт порта для хостинга
EXPOSE 8000

# Запуск единого ядра (Web-панель + Telegram Бот 24/7)
CMD ["python", "main.py"]
