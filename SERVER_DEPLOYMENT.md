# 🚀 Пошаговое развертывание на сервере

## 📋 Подготовка

### 1. Требования к серверу
- **ОС**: Ubuntu 20.04+ или Debian 11+
- **RAM**: Минимум 1GB, рекомендуется 2GB+
- **Диск**: Минимум 10GB свободного места
- **Сеть**: Статический IP адрес
- **Домен**: Настроенный DNS для bot.tildahelp.ru

### 2. Необходимые данные
- IP адрес сервера
- Имя пользователя на сервере
- SSH ключи или пароль
- Telegram Bot Token

## 🔧 Этап 1: Подготовка локальной машины

### 1.1 Проверка SSH подключения
```bash
# Тест подключения
ssh USERNAME@SERVER_IP

# Если используете SSH ключи, убедитесь что они настроены
ssh-copy-id USERNAME@SERVER_IP
```

### 1.2 Клонирование проекта
```bash
git clone <repository-url>
cd telegram_bot_admin
```

## 🚀 Этап 2: Автоматическое развертывание

### 2.1 Запуск скрипта развертывания
```bash
# Сделать скрипт исполняемым
chmod +x deploy_server.sh

# Запуск развертывания
./deploy_server.sh SERVER_IP USERNAME bot.tildahelp.ru

# Пример:
./deploy_server.sh 192.168.1.100 botuser bot.tildahelp.ru
```

### 2.2 Что делает скрипт
- ✅ Обновляет систему
- ✅ Устанавливает необходимые пакеты
- ✅ Настраивает Python окружение
- ✅ Копирует проект на сервер
- ✅ Настраивает Nginx
- ✅ Создает systemd сервис
- ✅ Настраивает firewall
- ✅ Устанавливает fail2ban

## 🌐 Этап 3: Настройка DNS

### 3.1 Создание A записи
```
Тип: A
Имя: bot
Значение: [IP_АДРЕС_СЕРВЕРА]
TTL: 300
```

### 3.2 Проверка DNS
```bash
# Проверка через dig
dig bot.tildahelp.ru A

# Проверка через nslookup
nslookup bot.tildahelp.ru

# Ожидаемый результат:
# bot.tildahelp.ru.    300    IN    A    [ВАШ_IP]
```

## 🔐 Этап 4: Получение SSL сертификата

### 4.1 Автоматическая настройка
```bash
# Запуск скрипта настройки домена
./setup_domain.sh SERVER_IP USERNAME bot.tildahelp.ru

# Пример:
./setup_domain.sh 192.168.1.100 botuser bot.tildahelp.ru
```

### 4.2 Ручная настройка
```bash
# Подключение к серверу
ssh USERNAME@SERVER_IP

# Остановка Nginx
sudo systemctl stop nginx

# Получение сертификата
sudo certbot certonly --standalone -d bot.tildahelp.ru

# Запуск Nginx
sudo systemctl start nginx

# Проверка сертификата
sudo certbot certificates
```

## 🚀 Этап 5: Запуск системы

### 5.1 Запуск бота
```bash
# Подключение к серверу
ssh USERNAME@SERVER_IP

# Запуск systemd сервиса
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot
```

### 5.2 Проверка работы
```bash
# Проверка веб-интерфейса
curl -I https://bot.tildahelp.ru

# Проверка логов
sudo journalctl -u telegram-bot -f

# Проверка мониторинга
./monitor.sh
```

## 🔧 Этап 6: Настройка и тестирование

### 6.1 Настройка .env файла
```bash
# Подключение к серверу
ssh USERNAME@SERVER_IP

# Редактирование .env
nano .env

# Указать ваш TELEGRAM_TOKEN
TELEGRAM_TOKEN=your_actual_token_here
```

### 6.2 Тестирование бота
1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Проверьте ответ бота
4. Проверьте веб-интерфейс по адресу https://bot.tildahelp.ru

### 6.3 Тестирование админки
1. Откройте https://bot.tildahelp.ru
2. Войдите с логином `BotNemkov` и паролем `Nemkov&`
3. Проверьте все разделы: Дашборд, Рассылка, Настройки, Подписчики

## 📊 Этап 7: Мониторинг и обслуживание

### 7.1 Запуск мониторинга
```bash
# Подключение к серверу
ssh USERNAME@SERVER_IP

# Запуск интерактивного мониторинга
./maintenance.sh

# Или прямой запуск мониторинга
./monitor.sh
```

### 7.2 Автоматические задачи
```bash
# Проверка cron задач
crontab -l

# Должны быть строки:
# 0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'
```

## 🆘 Устранение проблем

### Проблема: Бот не отвечает
```bash
# Проверка статуса
sudo systemctl status telegram-bot

# Проверка логов
sudo journalctl -u telegram-bot -f

# Проверка токена
cat .env | grep TELEGRAM_TOKEN
```

### Проблема: Веб-интерфейс недоступен
```bash
# Проверка Nginx
sudo systemctl status nginx
sudo nginx -t

# Проверка портов
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

### Проблема: SSL сертификат не работает
```bash
# Проверка сертификата
sudo certbot certificates

# Обновление сертификата
sudo certbot renew --dry-run

# Проверка конфигурации Nginx
sudo nginx -t
```

## 📋 Чек-лист развертывания

### Подготовка
- [ ] Сервер готов и доступен
- [ ] SSH подключение настроено
- [ ] DNS записи настроены
- [ ] Проект склонирован локально

### Развертывание
- [ ] Скрипт deploy_server.sh выполнен
- [ ] Все пакеты установлены
- [ ] Nginx настроен
- [ ] Systemd сервис создан

### Настройка
- [ ] DNS записи распространились
- [ ] SSL сертификат получен
- [ ] Telegram Bot Token указан
- [ ] Бот запущен и работает

### Тестирование
- [ ] Веб-интерфейс доступен по HTTPS
- [ ] Бот отвечает в Telegram
- [ ] Админка работает корректно
- [ ] Все функции протестированы

### Безопасность
- [ ] Firewall настроен
- [ ] Fail2ban активен
- [ ] SSH настроен безопасно
- [ ] Система обновлена

## 🎯 Финальная проверка

### Команда полной проверки
```bash
# Подключение к серверу
ssh USERNAME@SERVER_IP

# Полная проверка системы
./monitor.sh

# Проверка статуса сервисов
sudo systemctl status telegram-bot nginx

# Проверка SSL
sudo certbot certificates

# Проверка доступности
curl -I https://bot.tildahelp.ru
```

### Ожидаемый результат
- ✅ Веб-интерфейс доступен по https://bot.tildahelp.ru
- ✅ Бот отвечает в Telegram
- ✅ Все сервисы работают
- ✅ SSL сертификат действителен
- ✅ Система безопасна

## 🎉 Готово!

После выполнения всех этапов у вас будет:
- 🌐 Работающий веб-интерфейс на домене bot.tildahelp.ru
- 🤖 Функционирующий Telegram бот
- 🔐 Безопасная система с SSL
- 📊 Мониторинг и администрирование
- 🚀 Автоматическое обновление и обслуживание

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u telegram-bot -f`
2. Используйте мониторинг: `./monitor.sh`
3. Проверьте статус сервисов: `sudo systemctl status`
4. Обратитесь к документации в проекте
