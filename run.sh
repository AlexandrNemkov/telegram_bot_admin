#!/bin/bash

# Скрипт запуска телеграм бота с админ-панелью

echo "🚀 Запуск Telegram Bot Admin Panel..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Скопируйте .env.example в .env и настройте переменные"
    cp .env.example .env
    echo "📝 Файл .env создан. Отредактируйте его и запустите скрипт снова."
    exit 1
fi

# Проверяем токен бота
if ! grep -q "TELEGRAM_TOKEN=" .env || grep -q "your_telegram_bot_token_here" .env; then
    echo "❌ TELEGRAM_TOKEN не настроен в .env файле!"
    echo "Получите токен у @BotFather и укажите его в .env файле"
    exit 1
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p data uploads

# Запускаем бота
echo "🤖 Запуск бота и веб-интерфейса..."
python3 main.py
