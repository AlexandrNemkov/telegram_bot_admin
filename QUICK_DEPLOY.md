# 🚀 Быстрое развертывание на сервере

## ⚡ Команды для быстрого запуска

### 1. Автоматическое развертывание
```bash
# Сделать скрипты исполняемыми
chmod +x deploy_server.sh setup_domain.sh maintenance.sh

# Развертывание на сервере
./deploy_server.sh [IP_СЕРВЕРА] [ПОЛЬЗОВАТЕЛЬ] bot.tildahelp.ru

# Пример:
./deploy_server.sh 192.168.1.100 botuser bot.tildahelp.ru
```

### 2. Настройка домена и SSL
```bash
# После развертывания настройте DNS записи:
# Тип: A, Имя: bot, Значение: [IP_СЕРВЕРА]

# Затем получите SSL сертификат:
./setup_domain.sh [IP_СЕРВЕРА] [ПОЛЬЗОВАТЕЛЬ] bot.tildahelp.ru
```

### 3. Запуск системы
```bash
# Подключение к серверу
ssh [ПОЛЬЗОВАТЕЛЬ]@[IP_СЕРВЕРА]

# Запуск бота
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot
```

### 4. Настройка токена
```bash
# Редактирование .env файла
nano .env

# Укажите ваш TELEGRAM_TOKEN
TELEGRAM_TOKEN=ваш_реальный_токен_здесь
```

### 5. Тестирование
```bash
# Проверка веб-интерфейса
curl -I https://bot.tildahelp.ru

# Проверка мониторинга
./monitor.sh

# Интерактивное обслуживание
./maintenance.sh
```

## 📋 Минимальные требования

- **Сервер**: Ubuntu 20.04+ / Debian 11+
- **RAM**: 1GB+
- **Диск**: 10GB+
- **Сеть**: Статический IP
- **Домен**: Настроенный DNS для bot.tildahelp.ru

## 🔑 Доступ к системе

- **Веб-интерфейс**: https://bot.tildahelp.ru
- **Логин**: BotNemkov
- **Пароль**: Nemkov&

## 🆘 Если что-то пошло не так

```bash
# Проверка логов
sudo journalctl -u telegram-bot -f

# Проверка статуса
sudo systemctl status telegram-bot nginx

# Мониторинг системы
./monitor.sh

# Полная диагностика
./maintenance.sh
```

## 📚 Подробная документация

- `SERVER_DEPLOYMENT.md` - Пошаговое развертывание
- `DNS_SETUP.md` - Настройка DNS
- `SECURITY.md` - Безопасность сервера
- `DEPLOY.md` - Инструкции по развертыванию

## 🎯 Результат

После выполнения всех команд у вас будет:
✅ Работающий Telegram бот  
✅ Веб-интерфейс на домене bot.tildahelp.ru  
✅ SSL сертификат  
✅ Система мониторинга  
✅ Автоматическое обслуживание  

**Время развертывания**: ~15-20 минут
