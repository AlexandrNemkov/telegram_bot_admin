#!/bin/bash

# Скрипт обслуживания и мониторинга системы
# Использование: ./maintenance.sh SERVER_IP USERNAME

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ $# -ne 2 ]; then
    echo -e "${RED}Ошибка: Неверное количество аргументов${NC}"
    echo "Использование: $0 SERVER_IP USERNAME"
    echo "Пример: $0 192.168.1.100 botuser"
    exit 1
fi

SERVER_IP=$1
USERNAME=$2

echo -e "${BLUE}🔧 Обслуживание системы Telegram Bot Admin Panel${NC}"
echo ""

# Проверка подключения к серверу
echo -e "${YELLOW}🔍 Проверка подключения к серверу...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $USERNAME@$SERVER_IP exit 2>/dev/null; then
    echo -e "${RED}❌ Не удается подключиться к серверу${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Подключение к серверу успешно${NC}"

# Меню выбора действий
show_menu() {
    echo ""
    echo -e "${BLUE}📋 Выберите действие:${NC}"
    echo "1. 📊 Мониторинг системы"
    echo "2. 🔄 Обновление бота"
    echo "3. 🚀 Перезапуск сервисов"
    echo "4. 📝 Просмотр логов"
    echo "5. 💾 Создание резервной копии"
    echo "6. 🔐 Проверка SSL сертификата"
    echo "7. 🧹 Очистка системы"
    echo "8. 📈 Статистика использования"
    echo "9. 🆘 Проверка здоровья системы"
    echo "0. ❌ Выход"
    echo ""
    read -p "Введите номер действия: " choice
}

# Функции для каждого действия
monitor_system() {
    echo -e "${YELLOW}📊 Мониторинг системы...${NC}"
    ssh $USERNAME@$SERVER_IP './monitor.sh'
}

update_bot() {
    echo -e "${YELLOW}🔄 Обновление бота...${NC}"
    ssh $USERNAME@$SERVER_IP './update.sh'
}

restart_services() {
    echo -e "${YELLOW}🚀 Перезапуск сервисов...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    echo "Перезапуск Telegram Bot..."
    sudo systemctl restart telegram-bot
    
    echo "Перезапуск Nginx..."
    sudo systemctl reload nginx
    
    echo "Проверка статуса..."
    sudo systemctl status telegram-bot --no-pager -l
    sudo systemctl status nginx --no-pager -l
ENDSSH
}

view_logs() {
    echo -e "${YELLOW}📝 Просмотр логов...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    echo "=== Логи Telegram Bot ==="
    sudo journalctl -u telegram-bot -n 50 --no-pager
    
    echo ""
    echo "=== Логи Nginx ==="
    sudo tail -n 50 /var/log/nginx/error.log
ENDSSH
}

create_backup() {
    echo -e "${YELLOW}💾 Создание резервной копии...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    cd /home/$USERNAME/telegram_bot_admin
    BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf $BACKUP_FILE data/ uploads/ .env
    echo "Резервная копия создана: $BACKUP_FILE"
    ls -la *.tar.gz | tail -5
ENDSSH
}

check_ssl() {
    echo -e "${YELLOW}🔐 Проверка SSL сертификата...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    echo "Информация о сертификатах:"
    sudo certbot certificates
    
    echo ""
    echo "Проверка обновления:"
    sudo certbot renew --dry-run
ENDSSH
}

cleanup_system() {
    echo -e "${YELLOW}🧹 Очистка системы...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    echo "Очистка старых логов..."
    sudo journalctl --vacuum-time=7d
    
    echo "Очистка старых резервных копий..."
    cd /home/$USERNAME/telegram_bot_admin
    find . -name "backup-*.tar.gz" -mtime +30 -delete
    
    echo "Очистка кэша apt..."
    sudo apt autoremove -y
    sudo apt autoclean
    
    echo "Проверка свободного места..."
    df -h
ENDSSH
}

system_stats() {
    echo -e "${YELLOW}📈 Статистика использования...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    echo "=== Использование диска ==="
    df -h
    
    echo ""
    echo "=== Использование памяти ==="
    free -h
    
    echo ""
    echo "=== Использование CPU ==="
    top -bn1 | grep "Cpu(s)"
    
    echo ""
    echo "=== Активные процессы ==="
    ps aux | grep -E "(telegram|nginx|gunicorn)" | grep -v grep
    
    echo ""
    echo "=== Сетевые соединения ==="
    netstat -tulpn | grep -E ":(80|443|5000)"
ENDSSH
}

health_check() {
    echo -e "${YELLOW}🆘 Проверка здоровья системы...${NC}"
    ssh $USERNAME@$SERVER_IP << 'ENDSSH'
    echo "=== Проверка сервисов ==="
    echo "1. Telegram Bot:"
    sudo systemctl is-active telegram-bot
    
    echo "2. Nginx:"
    sudo systemctl is-active nginx
    
    echo ""
    echo "=== Проверка портов ==="
    echo "Порт 80 (HTTP):"
    netstat -tulpn | grep :80 || echo "Порт 80 не слушается"
    
    echo "Порт 443 (HTTPS):"
    netstat -tulpn | grep :443 || echo "Порт 443 не слушается"
    
    echo "Порт 5000 (Bot):"
    netstat -tulpn | grep :5000 || echo "Порт 5000 не слушается"
    
    echo ""
    echo "=== Проверка SSL ==="
    if [ -f /etc/letsencrypt/live/*/fullchain.pem ]; then
        echo "SSL сертификат найден"
        openssl x509 -in /etc/letsencrypt/live/*/fullchain.pem -text -noout | grep "Not After"
    else
        echo "SSL сертификат не найден"
    fi
    
    echo ""
    echo "=== Проверка файлов ==="
    cd /home/$USERNAME/telegram_bot_admin
    echo "Размер проекта: $(du -sh .)"
    echo "Количество файлов: $(find . -type f | wc -l)"
ENDSSH
}

# Основной цикл
while true; do
    show_menu
    
    case $choice in
        1) monitor_system ;;
        2) update_bot ;;
        3) restart_services ;;
        4) view_logs ;;
        5) create_backup ;;
        6) check_ssl ;;
        7) cleanup_system ;;
        8) system_stats ;;
        9) health_check ;;
        0) echo -e "${GREEN}👋 До свидания!${NC}"; exit 0 ;;
        *) echo -e "${RED}❌ Неверный выбор${NC}" ;;
    esac
    
    echo ""
    read -p "Нажмите Enter для продолжения..."
done
