#!/bin/bash

# 🔒 Скрипт настройки безопасности сервера
# Выполнять от имени root (sudo)

set -e

echo "🛡️ Настройка безопасности сервера..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ОШИБКА]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ПРЕДУПРЕЖДЕНИЕ]${NC} $1"
}

info() {
    echo -e "${BLUE}[ИНФО]${NC} $1"
}

# Проверка на root права
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен выполняться от имени root (sudo)"
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

# Сбрасываем правила
ufw --force reset

# Устанавливаем политики по умолчанию
ufw default deny incoming
ufw default allow outgoing

# Разрешаем SSH (важно сделать это первым!)
ufw allow ssh
ufw allow 22/tcp

# Разрешаем HTTP и HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Разрешаем Telegram Bot API (если нужно)
ufw allow out 443/tcp

# Включаем файрвол
ufw --force enable

log "✅ Файрвол UFW настроен и включен"

# 3. НАСТРОЙКА SSL СЕРТИФИКАТА
log "🔐 Настройка SSL сертификата..."

# Проверяем наличие certbot
if ! command -v certbot &> /dev/null; then
    log "Установка Certbot..."
    apt install certbot python3-certbot-nginx -y
fi

# Проверяем текущий сертификат
if [ -f "/etc/letsencrypt/live/bot.tildahelp.ru/fullchain.pem" ]; then
    log "SSL сертификат уже существует"
    
    # Проверяем срок действия
    if certbot certificates | grep -q "VALID"; then
        log "✅ Сертификат действителен"
    else
        warning "Сертификат истек или недействителен"
        log "Обновление сертификата..."
        certbot renew --quiet
    fi
else
    log "Создание SSL сертификата..."
    certbot --nginx -d bot.tildahelp.ru --non-interactive --agree-tos --email admin@tildahelp.ru
fi

# 4. НАСТРОЙКА NGINX ДЛЯ CLOUDFLARE
log "🌐 Настройка Nginx для Cloudflare..."

# Создаем конфигурацию для Cloudflare
cat > /etc/nginx/sites-available/bot.tildahelp.ru.cloudflare << 'EOF'
# Конфигурация Nginx для домена bot.tildahelp.ru с Cloudflare

# HTTP -> HTTPS редирект
server {
    listen 80;
    server_name bot.tildahelp.ru;
    return 301 https://$server_name$request_uri;
}

# HTTPS сервер
server {
    listen 443 ssl http2;
    server_name bot.tildahelp.ru;
    
    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/bot.tildahelp.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.tildahelp.ru/privkey.pem;
    
    # SSL настройки (современные и безопасные)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Безопасность
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;";
    
    # Логи
    access_log /var/log/nginx/bot.tildahelp.ru.access.log;
    error_log /var/log/nginx/bot.tildahelp.ru.error.log;
    
    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Таймауты
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Буферизация
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Защита от больших запросов
        client_max_body_size 50M;
    }
    
    # Статические файлы
    location /static/ {
        alias /home/telegram_bot_admin/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }
    
    # Загруженные файлы
    location /uploads/ {
        alias /home/telegram_bot_admin/uploads/;
        expires 1d;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options nosniff;
        
        # Защита от выполнения файлов
        location ~* \.(php|pl|py|jsp|asp|sh|cgi)$ {
            deny all;
        }
    }
    
    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Защита от скрытых файлов
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Защита от вредоносных запросов
    location ~* \.(htaccess|htpasswd|ini|log|sh|sql|conf)$ {
        deny all;
    }
}

# Дополнительный сервер для Cloudflare (если нужно)
server {
    listen 80;
    server_name bot.tildahelp.ru;
    
    # Разрешаем только Cloudflare IP
    allow 173.245.48.0/20;
    allow 103.21.244.0/22;
    allow 103.22.200.0/22;
    allow 103.31.4.0/22;
    allow 141.101.64.0/18;
    allow 108.162.192.0/18;
    allow 190.93.240.0/20;
    allow 188.114.96.0/20;
    allow 197.234.240.0/22;
    allow 198.41.128.0/17;
    allow 162.158.0.0/15;
    allow 104.16.0.0/13;
    allow 104.24.0.0/14;
    allow 172.64.0.0/13;
    allow 131.0.72.0/22;
    deny all;
    
    return 301 https://$server_name$request_uri;
}
EOF

# Активируем новую конфигурацию
ln -sf /etc/nginx/sites-available/bot.tildahelp.ru.cloudflare /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/bot.tildahelp.ru

# Проверяем конфигурацию nginx
if nginx -t; then
    log "✅ Конфигурация Nginx корректна"
    systemctl reload nginx
else
    error "Ошибка в конфигурации Nginx"
    exit 1
fi

# 5. НАСТРОЙКА АВТОМАТИЧЕСКИХ ОБНОВЛЕНИЙ
log "🔄 Настройка автоматических обновлений..."

# Устанавливаем unattended-upgrades
apt install unattended-upgrades -y

# Настраиваем автоматические обновления безопасности
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
Unattended-Upgrade::SyslogEnable "true";
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

# 6. НАСТРОЙКА ЛОГИРОВАНИЯ И МОНИТОРИНГА
log "📊 Настройка логирования и мониторинга..."

# Устанавливаем fail2ban для защиты от брутфорса
apt install fail2ban -y

# Создаем конфигурацию для SSH
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

# Включаем и запускаем fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# 7. НАСТРОЙКА ПРАВ ДОСТУПА
log "🔐 Настройка прав доступа..."

# Устанавливаем правильные права для проекта
chown -R telegram_bot_admin:telegram_bot_admin /home/telegram_bot_admin/
chmod -R 755 /home/telegram_bot_admin/
chmod -R 644 /home/telegram_bot_admin/data/*.db
chmod 755 /home/telegram_bot_admin/data/

# 8. СОЗДАНИЕ CRON ЗАДАЧ
log "⏰ Настройка cron задач..."

# Создаем cron задачи для регулярных проверок
cat > /etc/cron.d/telegram_bot_security << 'EOF'
# Ежедневная проверка безопасности
0 2 * * * root /home/telegram_bot_admin/check_security.sh

# Еженедельная проверка обновлений
0 3 * * 0 root apt update && apt list --upgradable

# Ежемесячная очистка логов
0 4 1 * * root find /var/log -name "*.log" -mtime +30 -delete
EOF

# 9. СОЗДАНИЕ СКРИПТА ПРОВЕРКИ БЕЗОПАСНОСТИ
log "🔍 Создание скрипта проверки безопасности..."

cat > /home/telegram_bot_admin/check_security.sh << 'EOF'
#!/bin/bash

# Скрипт проверки безопасности
LOG_FILE="/var/log/security_check.log"

echo "$(date): Начало проверки безопасности" >> $LOG_FILE

# Проверка обновлений
if apt list --upgradable 2>/dev/null | grep -q "upgradable"; then
    echo "$(date): Доступны обновления системы" >> $LOG_FILE
fi

# Проверка SSL сертификата
if ! certbot certificates | grep -q "VALID"; then
    echo "$(date): Проблема с SSL сертификатом" >> $LOG_FILE
fi

# Проверка файрвола
if ! ufw status | grep -q "Status: active"; then
    echo "$(date): Файрвол неактивен!" >> $LOG_FILE
fi

# Проверка fail2ban
if ! systemctl is-active --quiet fail2ban; then
    echo "$(date): Fail2ban не работает!" >> $LOG_FILE
fi

echo "$(date): Проверка безопасности завершена" >> $LOG_FILE
EOF

chmod +x /home/telegram_bot_admin/check_security.sh

# 10. ФИНАЛЬНАЯ ПРОВЕРКА
log "🔍 Финальная проверка безопасности..."

# Проверяем статус всех сервисов
echo "📊 Статус сервисов безопасности:"
echo "UFW (файрвол): $(systemctl is-active ufw)"
echo "Fail2ban: $(systemctl is-active fail2ban)"
echo "Unattended-upgrades: $(systemctl is-active unattended-upgrades)"
echo "Nginx: $(systemctl is-active nginx)"

# Показываем правила файрвола
echo "🔥 Правила файрвола UFW:"
ufw status numbered

# Проверяем SSL сертификат
echo "🔐 Статус SSL сертификата:"
certbot certificates

log "✅ Настройка безопасности завершена!"
log "🛡️ Сервер защищен следующими мерами:"
echo "  - Файрвол UFW активен"
echo "  - SSL сертификат настроен"
echo "  - Автоматические обновления включены"
echo "  - Fail2ban защищает от брутфорса"
echo "  - Nginx настроен с безопасными заголовками"
echo "  - Cron задачи настроены"
echo "  - Права доступа исправлены"

warning "⚠️  РЕКОМЕНДАЦИИ:"
echo "  1. Перезагрузите сервер: sudo reboot"
echo "  2. Проверьте доступность сайта по HTTPS"
echo "  3. Настройте мониторинг в Cloudflare"
echo "  4. Регулярно проверяйте логи: sudo journalctl -f"
