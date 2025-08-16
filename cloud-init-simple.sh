#!/bin/bash

# Cloud-init скрипт для автоматической настройки Telegram Bot Admin Panel
# Вставьте этот скрипт в поле Cloud-init при создании VM

set -e

# Логирование
exec > >(tee /var/log/cloud-init-setup.log) 2>&1
echo "=== Начало автоматической настройки $(date) ==="

# Обновление системы
echo "Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
echo "Установка пакетов..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    unzip \
    ufw \
    fail2ban

# Создание пользователя для приложения
echo "Создание пользователя botadmin..."
useradd -m -s /bin/bash botadmin
usermod -aG sudo botadmin

# Клонирование проекта из GitHub
echo "Клонирование проекта..."
cd /home/botadmin
sudo -u botadmin git clone https://github.com/YOUR_USERNAME/telegram_bot_admin.git
cd telegram_bot_admin

# Создание виртуального окружения
echo "Настройка Python окружения..."
sudo -u botadmin python3 -m venv venv
sudo -u botadmin venv/bin/pip install --upgrade pip setuptools wheel

# Установка зависимостей
echo "Установка зависимостей..."
sudo -u botadmin venv/bin/pip install -r requirements.txt

# Создание необходимых директорий
sudo -u botadmin mkdir -p data uploads logs

# Настройка .env файла
echo "Настройка конфигурации..."
sudo -u botadmin cat > .env << 'ENVEOF'
# Telegram Bot Token (замените на ваш)
TELEGRAM_TOKEN=YOUR_TELEGRAM_TOKEN_HERE

# Админские данные для входа в веб-интерфейс
ADMIN_USERNAME=BotNemkov
ADMIN_PASSWORD=Nemkov&

# Секретный ключ для Flask
SECRET_KEY=GENERATED_SECRET_KEY_HERE
ENVEOF

# Генерация секретного ключа
SECRET_KEY=$(openssl rand -hex 32)
sudo -u botadmin sed -i "s|GENERATED_SECRET_KEY_HERE|$SECRET_KEY|g" .env

# Настройка Nginx
echo "Настройка Nginx..."
cp nginx-bot.tildahelp.ru.conf /etc/nginx/sites-available/bot.tildahelp.ru
sed -i "s|/path/to/telegram_bot_admin|/home/botadmin/telegram_bot_admin|g" /etc/nginx/sites-available/bot.tildahelp.ru

ln -sf /etc/nginx/sites-available/bot.tildahelp.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Настройка systemd сервиса
echo "Настройка systemd сервиса..."
cp telegram-bot.service /etc/systemd/system/
sed -i "s|/path/to/telegram_bot_admin|/home/botadmin/telegram_bot_admin|g" /etc/systemd/system/telegram-bot.service
sed -i "s|www-data|botadmin|g" /etc/systemd/system/telegram-bot.service

systemctl daemon-reload

# Настройка firewall
echo "Настройка firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Настройка fail2ban
echo "Настройка fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Перезапуск Nginx
echo "Перезапуск Nginx..."
systemctl reload nginx

# Запуск бота
echo "Запуск Telegram бота..."
systemctl start telegram-bot
systemctl enable telegram-bot

# Создание финального скрипта настройки
echo "Создание финального скрипта настройки..."
cat > /home/botadmin/final_setup.sh << 'FINALEOF'
#!/bin/bash

echo "=== Финальная настройка Telegram Bot Admin Panel ==="
echo ""

echo "1. Настройте DNS записи для домена bot.tildahelp.ru:"
echo "   Тип: A, Имя: bot, Значение: $(curl -s ifconfig.me)"
echo ""

echo "2. Получите SSL сертификат:"
echo "   sudo certbot --nginx -d bot.tildahelp.ru"
echo ""

echo "3. Настройте TELEGRAM_TOKEN в .env файле:"
echo "   nano .env"
echo ""

echo "4. Проверьте статус системы:"
echo "   ./monitor.sh"
echo ""

echo "5. Веб-интерфейс будет доступен по адресу:"
echo "   https://bot.tildahelp.ru"
echo "   Логин: BotNemkov"
echo "   Пароль: Nemkov&"
echo ""

echo "=== Настройка завершена! ==="
FINALEOF

chmod +x /home/botadmin/final_setup.sh
chown botadmin:botadmin /home/botadmin/final_setup.sh

echo "=== Автоматическая настройка завершена $(date) ==="
echo "Сервер готов к использованию!"
echo "Выполните: sudo -u botadmin /home/botadmin/final_setup.sh"
