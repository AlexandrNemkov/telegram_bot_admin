#!/bin/bash

# Скрипт установки и настройки Telegram Bot как systemd сервиса

echo "🚀 Установка Telegram Bot как systemd сервиса..."

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

# Создаем виртуальное окружение если его нет
echo "🐍 Проверка виртуального окружения..."
if [ ! -d "/home/telegram_bot_admin/venv" ]; then
    echo "Создание виртуального окружения..."
    su - telegram_bot_admin << 'EOF'
    cd /home/telegram_bot_admin
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
EOF
    echo "✅ Виртуальное окружение создано"
else
    echo "ℹ️ Виртуальное окружение уже существует"
fi

# Копируем файлы сервиса
echo "📁 Настройка systemd сервиса..."
cp telegram-bot.service /etc/systemd/system/
chmod 644 /etc/systemd/system/telegram-bot.service

# Перезагружаем systemd
echo "🔄 Перезагрузка systemd..."
systemctl daemon-reload

# Включаем автозапуск сервиса
echo "🔧 Включение автозапуска сервиса..."
systemctl enable telegram-bot.service

# Настраиваем права доступа
echo "🔐 Настройка прав доступа..."
chown -R telegram_bot_admin:telegram_bot_admin /home/telegram_bot_admin

# Создаем папки если их нет
echo "📁 Создание необходимых папок..."
su - telegram_bot_admin << 'EOF'
cd /home/telegram_bot_admin
mkdir -p data uploads logs
EOF

echo ""
echo "✅ Сервис установлен и настроен!"
echo ""
echo "📋 Команды для управления:"
echo "  Запуск:     sudo systemctl start telegram-bot.service"
echo "  Остановка:  sudo systemctl stop telegram-bot.service"
echo "  Перезапуск: sudo systemctl restart telegram-bot.service"
echo "  Статус:     sudo systemctl status telegram-bot.service"
echo "  Логи:       sudo journalctl -u telegram-bot.service -f"
echo "  Автозапуск: sudo systemctl enable telegram-bot.service"
echo "  Отключить:  sudo systemctl disable telegram-bot.service"
echo ""
echo "🚀 Для запуска выполните: sudo systemctl start telegram-bot.service"
echo "🌐 Веб-интерфейс будет доступен по адресу: http://YOUR_SERVER_IP:5000"
