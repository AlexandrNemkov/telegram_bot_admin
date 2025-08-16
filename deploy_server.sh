#!/bin/bash

# Скрипт автоматического развертывания на сервере
# Использование: ./deploy_server.sh SERVER_IP USERNAME DOMAIN

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ $# -ne 3 ]; then
    echo -e "${RED}Ошибка: Неверное количество аргументов${NC}"
    echo "Использование: $0 94.241.141.253 alexandnemkov bot.tildahelp.ru"
    echo "Пример: $0 192.168.1.100 botuser bot.tildahelp.ru"
    exit 1
fi

SERVER_IP=$1
USERNAME=$2
DOMAIN=$3
PROJECT_DIR="/home/$USERNAME/telegram_bot_admin"

echo -e "${BLUE}🚀 Начинаем развертывание Telegram Bot Admin Panel${NC}"
echo -e "${BLUE}Сервер: ${SERVER_IP}${NC}"
echo -e "${BLUE}Пользователь: ${USERNAME}${NC}"
echo -e "${BLUE}Домен: ${DOMAIN}${NC}"
echo ""

# Проверка подключения к серверу
echo -e "${YELLOW}🔍 Проверка подключения к серверу...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $USERNAME@$SERVER_IP exit 2>/dev/null; then
    echo -e "${RED}❌ Не удается подключиться к серверу${NC}"
    echo "Проверьте:"
    echo "1. IP адрес сервера"
    echo "2. Имя пользователя"
    echo "3. SSH ключи или пароль"
    exit 1
fi
echo -e "${GREEN}✅ Подключение к серверу успешно${NC}"

# Создание архива проекта
echo -e "${YELLOW}📦 Создание архива проекта...${NC}"
tar -czf telegram_bot_admin.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='data' \
    --exclude='uploads' \
    .

echo -e "${GREEN}✅ Архив создан: telegram_bot_admin.tar.gz${NC}"

# Копирование архива на сервер
echo -e "${YELLOW}�� Копирование архива на сервер...${NC}"
scp telegram_bot_admin.tar.gz $USERNAME@$SERVER_IP:~/
echo -e "${GREEN}✅ Архив скопирован на сервер${NC}"

# Выполнение команд на сервере
echo -e "${YELLOW}🔧 Выполнение команд на сервере...${NC}"
ssh $USERNAME@$SERVER_IP << 'ENDSSH'
set -e

echo "Обновление системы..."
sudo apt update && sudo apt upgrade -y

echo "Установка необходимых пакетов..."
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl

echo "Создание директории проекта..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

echo "Распаковка архива..."
tar -xzf ~/telegram_bot_admin.tar.gz
rm ~/telegram_bot_admin.tar.gz

echo "Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

echo "Установка зависимостей..."
pip install -r requirements.txt

echo "Создание необходимых директорий..."
mkdir -p data uploads

echo "Настройка прав доступа..."
sudo chown -R $USERNAME:$USERNAME $PROJECT_DIR
chmod +x run.sh

echo "Настройка Nginx..."
sudo cp nginx-bot.tildahelp.ru.conf /etc/nginx/sites-available/$DOMAIN

# Замена путей в конфигурации Nginx
sudo sed -i "s|/path/to/telegram_bot_admin|$PROJECT_DIR|g" /etc/nginx/sites-available/$DOMAIN

sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "Проверка конфигурации Nginx..."
sudo nginx -t

echo "Перезапуск Nginx..."
sudo systemctl reload nginx

echo "Настройка systemd сервиса..."
sudo cp telegram-bot.service /etc/systemd/system/

# Замена путей в systemd сервисе
sudo sed -i "s|/path/to/telegram_bot_admin|$PROJECT_DIR|g" /etc/systemd/system/telegram-bot.service
sudo sed -i "s|www-data|$USERNAME|g" /etc/systemd/system/telegram-bot.service

echo "Перезагрузка systemd..."
sudo systemctl daemon-reload

echo "Настройка firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "Настройка fail2ban..."
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

echo "Создание .env файла..."
cat > .env << 'ENVEOF'
# Telegram Bot Token (замените на ваш)
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Админские данные для входа в веб-интерфейс
ADMIN_USERNAME=BotNemkov
ADMIN_PASSWORD=Nemkov&

# Секретный ключ для Flask
SECRET_KEY=$(openssl rand -hex 32)
ENVEOF

echo "Генерация секретного ключа..."
SECRET_KEY=$(openssl rand -hex 32)
sudo sed -i "s|your_secret_key_here|$SECRET_KEY|g" .env

echo "Настройка cron для обновления SSL..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

echo "Создание скрипта обновления..."
cat > update.sh << 'UPDATEEOF'
#!/bin/bash
cd $PROJECT_DIR
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
echo "Обновление завершено: $(date)"
UPDATEEOF

chmod +x update.sh

echo "Настройка логирования..."
sudo mkdir -p /var/log/telegram-bot
sudo chown $USERNAME:$USERNAME /var/log/telegram-bot

echo "Создание скрипта мониторинга..."
cat > monitor.sh << 'MONITOREOF'
#!/bin/bash
echo "=== Статус Telegram Bot Admin Panel ==="
echo "Время: $(date)"
echo ""

echo "1. Статус systemd сервиса:"
sudo systemctl status telegram-bot --no-pager -l

echo ""
echo "2. Статус Nginx:"
sudo systemctl status nginx --no-pager -l

echo ""
echo "3. Использование диска:"
df -h $PROJECT_DIR

echo ""
echo "4. Использование памяти:"
free -h

echo ""
echo "5. Активные соединения:"
netstat -tulpn | grep :5000

echo ""
echo "6. Последние логи бота:"
sudo journalctl -u telegram-bot -n 20 --no-pager

echo ""
echo "7. Последние логи Nginx:"
sudo tail -n 10 /var/log/nginx/access.log
MONITOREOF

chmod +x monitor.sh

echo "Настройка завершена!"
ENDSSH

echo -e "${GREEN}✅ Развертывание на сервере завершено!${NC}"

# Очистка локального архива
rm telegram_bot_admin.tar.gz

echo ""
echo -e "${BLUE}📋 Следующие шаги:${NC}"
echo "1. Настройте DNS записи для домена $DOMAIN"
echo "2. Получите SSL сертификат: ssh $USERNAME@$SERVER_IP 'sudo certbot --nginx -d $DOMAIN'"
echo "3. Запустите бота: ssh $USERNAME@$SERVER_IP 'sudo systemctl start telegram-bot'"
echo "4. Проверьте статус: ssh $USERNAME@$SERVER_IP './monitor.sh'"
echo ""
echo -e "${BLUE}🌐 Веб-интерфейс будет доступен по адресу: https://$DOMAIN${NC}"
echo -e "${BLUE}👤 Логин: BotNemkov${NC}"
echo -e "${BLUE}🔑 Пароль: Nemkov&${NC}"
echo ""
echo -e "${GREEN}🎉 Развертывание завершено успешно!${NC}"
