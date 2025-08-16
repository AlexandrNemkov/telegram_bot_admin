#!/bin/bash

# Быстрое развертывание Telegram Bot на сервере

echo "🚀 Быстрое развертывание Telegram Bot на сервере..."

# Проверяем, что мы root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен быть запущен от имени root"
    echo "Используйте: sudo $0"
    exit 1
fi

# Обновляем систему
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
echo "🔧 Установка необходимых пакетов..."
apt install -y python3 python3-pip python3-venv nginx git curl

# Создаем пользователя для бота
echo "👤 Создание пользователя telegram_bot_admin..."
if ! id "telegram_bot_admin" &>/dev/null; then
    useradd -m -s /bin/bash telegram_bot_admin
    echo "telegram_bot_admin:botpassword123" | chpasswd
    echo "✅ Пользователь создан"
else
    echo "ℹ️ Пользователь уже существует"
fi

# Переключаемся на пользователя бота
echo "🔄 Настройка окружения для пользователя..."
su - telegram_bot_admin << 'EOF'
cd /home/telegram_bot_admin

# Создаем виртуальное окружение
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
pip install -r requirements.txt

# Создаем необходимые директории
mkdir -p data uploads logs

# Создаем файл .env если его нет
if [ ! -f .env ]; then
    echo "📝 Создание файла .env..."
    cat > .env << 'ENVEOF'
# Telegram Bot Token
TELEGRAM_TOKEN=your_bot_token_here

# Admin Panel Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Secret Key for Flask
SECRET_KEY=your-secret-key-change-this-in-production

# Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
ENVEOF
    echo "⚠️  ВАЖНО: Отредактируйте файл .env и укажите ваш TELEGRAM_TOKEN!"
fi

echo "✅ Окружение настроено!"
EOF

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

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте файл .env и укажите ваш TELEGRAM_TOKEN"
echo "2. Запустите сервис: sudo systemctl start telegram-bot.service"
echo "3. Проверьте статус: sudo systemctl status telegram-bot.service"
echo "4. Посмотрите логи: sudo journalctl -u telegram-bot.service -f"
echo ""
echo "🌐 Веб-интерфейс будет доступен по адресу: http://YOUR_SERVER_IP:5000"
echo "👤 Логин: admin, Пароль: admin123"
