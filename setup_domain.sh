#!/bin/bash

# Скрипт настройки домена и SSL сертификата
# Использование: ./setup_domain.sh SERVER_IP USERNAME DOMAIN

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
    echo "Использование: $0 SERVER_IP USERNAME DOMAIN"
    echo "Пример: $0 192.168.1.100 botuser bot.tildahelp.ru"
    exit 1
fi

SERVER_IP=$1
USERNAME=$2
DOMAIN=$3

echo -e "${BLUE}🌐 Настройка домена $DOMAIN${NC}"
echo ""

# Проверка подключения к серверу
echo -e "${YELLOW}🔍 Проверка подключения к серверу...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $USERNAME@$SERVER_IP exit 2>/dev/null; then
    echo -e "${RED}❌ Не удается подключиться к серверу${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Подключение к серверу успешно${NC}"

# Получение SSL сертификата
echo -e "${YELLOW}🔐 Получение SSL сертификата для $DOMAIN...${NC}"
ssh $USERNAME@$SERVER_IP << 'ENDSSH'
set -e

echo "Остановка Nginx для получения сертификата..."
sudo systemctl stop nginx

echo "Получение SSL сертификата..."
sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

echo "Запуск Nginx..."
sudo systemctl start nginx

echo "Проверка SSL сертификата..."
sudo certbot certificates

echo "Настройка автоматического обновления..."
sudo crontab -l 2>/dev/null | grep -v "certbot renew" | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'"; } | sudo crontab -

echo "Проверка конфигурации Nginx..."
sudo nginx -t

echo "Перезапуск Nginx..."
sudo systemctl reload nginx

echo "Проверка статуса сервисов..."
sudo systemctl status nginx --no-pager -l
sudo systemctl status telegram-bot --no-pager -l

echo "Проверка SSL соединения..."
curl -I https://$DOMAIN

echo "Настройка завершена!"
ENDSSH

echo ""
echo -e "${GREEN}✅ Домен $DOMAIN настроен успешно!${NC}"
echo ""
echo -e "${BLUE}📋 Проверьте:${NC}"
echo "1. https://$DOMAIN - веб-интерфейс"
echo "2. SSL сертификат действителен"
echo "3. Бот работает в Telegram"
echo ""
echo -e "${BLUE}🔧 Полезные команды:${NC}"
echo "ssh $USERNAME@$SERVER_IP './monitor.sh' - мониторинг системы"
echo "ssh $USERNAME@$SERVER_IP './update.sh' - обновление бота"
echo "ssh $USERNAME@$SERVER_IP 'sudo systemctl restart telegram-bot' - перезапуск бота"
