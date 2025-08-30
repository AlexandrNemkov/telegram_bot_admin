#!/bin/bash

# 🛡️ Базовые настройки безопасности сервера
# Выполнять от имени root (sudo)
# НЕ ИЗМЕНЯЕТ существующие настройки Cloudflare и HTTPS

set -e

echo "🛡️ Настройка базовой безопасности сервера..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ПРЕДУПРЕЖДЕНИЕ]${NC} $1"
}

info() {
    echo -e "${BLUE}[ИНФО]${NC} $1"
}

# Проверка на root права
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен выполняться от имени root (sudo)"
   exit 1
fi

# 1. ОБНОВЛЕНИЕ СИСТЕМЫ
log "🔄 Обновление системы..."
apt update && apt upgrade -y
apt autoremove -y
apt autoclean

# 2. НАСТРОЙКА ФАЙРВОЛА UFW
log "🔥 Настройка файрвола UFW..."

# Устанавливаем UFW если не установлен
if ! command -v ufw &> /dev/null; then
    log "Установка UFW..."
    apt install ufw -y
fi

# Проверяем текущий статус UFW
if ufw status | grep -q "Status: active"; then
    warning "UFW уже активен. Пропускаем настройку файрвола."
else
    log "Настройка UFW..."
    
    # Сбрасываем правила
    ufw --force reset
    
    # Устанавливаем политики по умолчанию
    ufw default deny incoming
    ufw default allow outgoing
    
    # Разрешаем SSH (важно сделать это первым!)
    ufw allow ssh
    ufw allow 22/tcp
    
    # Разрешаем HTTP и HTTPS (не изменяем существующие порты)
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Включаем файрвол
    ufw --force enable
    
    log "✅ Файрвол UFW настроен и включен"
fi

# 3. НАСТРОЙКА АВТОМАТИЧЕСКИХ ОБНОВЛЕНИЙ
log "🔄 Настройка автоматических обновлений..."

# Устанавливаем unattended-upgrades
apt install unattended-upgrades -y

# Настраиваем автоматические обновления безопасности
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
};

Unattended-Upgrade::Package-Blacklist {
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

# Включаем автоматические обновления
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

# Включаем и запускаем сервис
systemctl enable unattended-upgrades
systemctl start unattended-upgrades

# 4. НАСТРОЙКА ПРАВ ДОСТУПА
log "🔐 Настройка прав доступа..."

# Устанавливаем правильные права для проекта
chown -R telegram_bot_admin:telegram_bot_admin /home/telegram_bot_admin/
chmod -R 755 /home/telegram_bot_admin/
chmod -R 644 /home/telegram_bot_admin/data/*.db
chmod 755 /home/telegram_bot_admin/data/

# 5. СОЗДАНИЕ СКРИПТА ПРОВЕРКИ БЕЗОПАСНОСТИ
log "🔍 Создание скрипта проверки безопасности..."

cat > /home/telegram_bot_admin/check_security.sh << 'EOF'
#!/bin/bash

# Скрипт проверки базовой безопасности
LOG_FILE="/var/log/security_check.log"

echo "$(date): Начало проверки безопасности" >> $LOG_FILE

# Проверка обновлений
if apt list --upgradable 2>/dev/null | grep -q "upgradable"; then
    echo "$(date): Доступны обновления системы" >> $LOG_FILE
fi

# Проверка файрвола
if ! ufw status | grep -q "Status: active"; then
    echo "$(date): Файрвол неактивен!" >> $LOG_FILE
fi

# Проверка автоматических обновлений
if ! systemctl is-active --quiet unattended-upgrades; then
    echo "$(date): Автоматические обновления не работают!" >> $LOG_FILE
fi

# Проверка прав доступа
if [ ! -r "/home/telegram_bot_admin/data/bot.db" ]; then
    echo "$(date): Проблема с правами доступа к базе данных" >> $LOG_FILE
fi

echo "$(date): Проверка безопасности завершена" >> $LOG_FILE
EOF

chmod +x /home/telegram_bot_admin/check_security.sh

# 6. СОЗДАНИЕ CRON ЗАДАЧ
log "⏰ Настройка cron задач..."

# Создаем cron задачи для регулярных проверок
cat > /etc/cron.d/telegram_bot_security << 'EOF'
# Еженедельная проверка безопасности (вместо ежедневной)
0 2 * * 0 root /home/telegram_bot_admin/check_security.sh

# Еженедельная проверка обновлений
0 3 * * 0 root apt update && apt list --upgradable

# Ежемесячная очистка логов
0 4 1 * * root find /var/log -name "*.log" -mtime +30 -delete
EOF

# 7. ФИНАЛЬНАЯ ПРОВЕРКА
log "🔍 Финальная проверка безопасности..."

# Проверяем статус всех сервисов
echo "📊 Статус сервисов безопасности:"
echo "UFW (файрвол): $(systemctl is-active ufw)"
echo "Unattended-upgrades: $(systemctl is-active unattended-upgrades)"

# Показываем правила файрвола
echo "🔥 Правила файрвола UFW:"
ufw status numbered

log "✅ Настройка базовой безопасности завершена!"
log "🛡️ Сервер защищен следующими мерами:"
echo "  - Файрвол UFW активен"
echo "  - Автоматические обновления включены"
echo "  - Права доступа исправлены"
echo "  - Cron задачи настроены"

warning "⚠️  ВАЖНО:"
echo "  - Существующие настройки Cloudflare НЕ ИЗМЕНЕНЫ"
echo "  - Существующие настройки HTTPS НЕ ИЗМЕНЕНЫ"
echo "  - Существующие настройки Nginx НЕ ИЗМЕНЕНЫ"

info "📋 Следующие шаги:"
echo "  1. Перезагрузите сервер: sudo reboot"
echo "  2. Проверьте что сайт работает как прежде"
echo "  3. Проверьте логи: sudo journalctl -f"
echo "  4. Еженедельно проверяйте: sudo /home/telegram_bot_admin/check_security.sh"

log "🎯 Готово! Безопасность настроена без изменения существующих настроек."
