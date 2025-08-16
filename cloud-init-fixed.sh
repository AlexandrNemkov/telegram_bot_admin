#cloud-config
# Автоматическая настройка Telegram Bot Admin Panel при создании VM

runcmd:
  # Обновление системы
  - apt update && apt upgrade -y
  
  # Установка пакетов
  - apt install -y python3 python3-pip python3-venv python3-dev build-essential nginx certbot python3-certbot-nginx git curl wget unzip ufw fail2ban
  
  # Создание пользователя
  - useradd -m -s /bin/bash botadmin
  - usermod -aG sudo botadmin
  
  # Клонирование проекта
  - cd /home/botadmin
  - sudo -u botadmin git clone https://github.com/YOUR_USERNAME/telegram_bot_admin.git
  - cd telegram_bot_admin
  
  # Python окружение
  - sudo -u botadmin python3 -m venv venv
  - sudo -u botadmin venv/bin/pip install --upgrade pip setuptools wheel
  - sudo -u botadmin venv/bin/pip install -r requirements.txt
  
  # Создание директорий
  - sudo -u botadmin mkdir -p data uploads logs
  
  # Настройка .env
  - sudo -u botadmin bash -c 'cat > .env << "ENVEOF"
TELEGRAM_TOKEN=YOUR_TELEGRAM_TOKEN_HERE
ADMIN_USERNAME=BotNemkov
ADMIN_PASSWORD=Nemkov&
SECRET_KEY=$(openssl rand -hex 32)
ENVEOF'
  
  # Настройка Nginx
  - cp nginx-bot.tildahelp.ru.conf /etc/nginx/sites-available/bot.tildahelp.ru
  - sed -i "s|/path/to/telegram_bot_admin|/home/botadmin/telegram_bot_admin|g" /etc/nginx/sites-available/bot.tildahelp.ru
  - ln -sf /etc/nginx/sites-available/bot.tildahelp.ru /etc/nginx/sites-enabled/
  - rm -f /etc/nginx/sites-enabled/default
  
  # Systemd сервис
  - cp telegram-bot.service /etc/systemd/system/
  - sed -i "s|/path/to/telegram_bot_admin|/home/botadmin/telegram_bot_admin|g" /etc/systemd/system/telegram-bot.service
  - sed -i "s|www-data|botadmin|g" /etc/systemd/system/telegram-bot.service
  - systemctl daemon-reload
  
  # Firewall
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw allow 443/tcp
  - ufw --force enable
  
  # Fail2ban
  - systemctl enable fail2ban
  - systemctl start fail2ban
  
  # Запуск сервисов
  - systemctl reload nginx
  - systemctl start telegram-bot
  - systemctl enable telegram-bot
  
  # Права доступа
  - chown -R botadmin:botadmin /home/botadmin/telegram_bot_admin

final_message: "Telegram Bot Admin Panel настроен! Выполните: sudo -u botadmin /home/botadmin/final_setup.sh"
