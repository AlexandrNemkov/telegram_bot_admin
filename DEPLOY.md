# Инструкция по развертыванию на сервере

## Подготовка сервера

### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка необходимых пакетов
```bash
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git
```

### 3. Создание пользователя для приложения
```bash
sudo adduser --disabled-password --gecos "" botuser
sudo usermod -aG sudo botuser
```

## Развертывание приложения

### 1. Клонирование репозитория
```bash
sudo -u botuser git clone <repository-url> /home/botuser/telegram_bot_admin
cd /home/botuser/telegram_bot_admin
```

### 2. Создание виртуального окружения
```bash
sudo -u botuser python3 -m venv venv
sudo -u botuser /home/botuser/telegram_bot_admin/venv/bin/pip install -r requirements.txt
```

### 3. Настройка переменных окружения
```bash
sudo -u botuser cp .env.example .env
sudo -u botuser nano .env
# Укажите ваш TELEGRAM_TOKEN и другие настройки
```

### 4. Создание необходимых директорий
```bash
sudo -u botuser mkdir -p data uploads
```

## Настройка Nginx

### 1. Копирование конфигурации
```bash
sudo cp nginx-bot.tildahelp.ru.conf /etc/nginx/sites-available/bot.tildahelp.ru
```

### 2. Редактирование путей
```bash
sudo nano /etc/nginx/sites-available/bot.tildahelp.ru
# Замените /path/to/telegram_bot_admin на /home/botuser/telegram_bot_admin
```

### 3. Активация сайта
```bash
sudo ln -s /etc/nginx/sites-available/bot.tildahelp.ru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Настройка SSL сертификата

### 1. Получение сертификата Let's Encrypt
```bash
sudo certbot --nginx -d bot.tildahelp.ru
```

### 2. Автоматическое обновление
```bash
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## Настройка systemd сервиса

### 1. Копирование файла сервиса
```bash
sudo cp telegram-bot.service /etc/systemd/system/
```

### 2. Редактирование путей
```bash
sudo nano /etc/systemd/system/telegram-bot.service
# Замените /path/to/telegram_bot_admin на /home/botuser/telegram_bot_admin
# Замените www-data на botuser
```

### 3. Активация сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Проверка работы

### 1. Проверка бота
- Отправьте /start в Telegram
- Проверьте логи: `sudo journalctl -u telegram-bot -f`

### 2. Проверка веб-интерфейса
- Откройте https://bot.tildahelp.ru
- Войдите используя данные из .env

### 3. Проверка Nginx
```bash
sudo nginx -t
sudo systemctl status nginx
```

## Мониторинг и логи

### 1. Логи приложения
```bash
sudo journalctl -u telegram-bot -f
```

### 2. Логи Nginx
```bash
sudo tail -f /var/log/nginx/bot.tildahelp.ru.access.log
sudo tail -f /var/log/nginx/bot.tildahelp.ru.error.log
```

### 3. Статус сервисов
```bash
sudo systemctl status telegram-bot
sudo systemctl status nginx
```

## Обновление приложения

### 1. Остановка сервиса
```bash
sudo systemctl stop telegram-bot
```

### 2. Обновление кода
```bash
cd /home/botuser/telegram_bot_admin
sudo -u botuser git pull origin main
sudo -u botuser /home/botuser/telegram_bot_admin/venv/bin/pip install -r requirements.txt
```

### 3. Запуск сервиса
```bash
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Резервное копирование

### 1. Создание бэкапа
```bash
sudo -u botuser tar -czf backup-$(date +%Y%m%d).tar.gz data/ uploads/ .env
```

### 2. Восстановление из бэкапа
```bash
cd /home/botuser/telegram_bot_admin
sudo -u botuser tar -xzf backup-YYYYMMDD.tar.gz
sudo systemctl restart telegram-bot
```

## Устранение неполадок

### 1. Бот не отвечает
```bash
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f
# Проверьте TELEGRAM_TOKEN в .env
```

### 2. Веб-интерфейс недоступен
```bash
sudo systemctl status nginx
sudo nginx -t
# Проверьте конфигурацию Nginx
```

### 3. Проблемы с SSL
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

## Безопасность

### 1. Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Обновления
```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

### 3. Мониторинг
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```
