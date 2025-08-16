#!/bin/bash

# Скрипт для настройки и запуска Telegram Bot сервиса

echo "🚀 Настройка Telegram Bot сервиса..."

# Проверяем, что мы root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен от имени root"
    echo "Используйте: sudo $0"
    exit 1
fi

# Создаем пользователя для бота
echo "👤 Создание пользователя telegram_bot_admin..."
if ! id "telegram_bot_admin" &>/dev/null; then
    useradd -m -s /bin/bash telegram_bot_admin
    echo "telegram_bot_admin:botpassword123" | chpasswd
    echo "✅ Пользователь создан"
else
    echo "ℹ️ Пользователь уже существует"
fi

# Копируем файлы сервиса
echo "📁 Копирование файлов сервиса..."
cp telegram-bot.service /etc/systemd/system/
chmod 644 /etc/systemd/system/telegram-bot.service

# Перезагружаем systemd
echo "🔄 Перезагрузка systemd..."
systemctl daemon-reload

# Включаем автозапуск сервиса
echo "🔧 Включение автозапуска сервиса..."
systemctl enable telegram-bot.service

echo "✅ Сервис настроен!"
echo ""
echo "📋 Команды для управления:"
echo "  Запуск:     sudo systemctl start telegram-bot.service"
echo "  Остановка:  sudo systemctl stop telegram-bot.service"
echo "  Статус:     sudo systemctl status telegram-bot.service"
echo "  Логи:       sudo journalctl -u telegram-bot.service -f"
echo ""
echo "🚀 Для запуска выполните: sudo systemctl start telegram-bot.service"
