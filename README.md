# Telegram Bot Admin Panel

Веб-интерфейс для управления телеграм ботом с возможностью рассылки сообщений и настройки функционала.

## Возможности

- 🤖 **Telegram Bot**: Автоматические ответы на команды /start, /help, /status
- 📱 **Веб-интерфейс**: Админ-панель с авторизацией
- 📢 **Рассылки**: Отправка сообщений всем подписчикам
- 👥 **Управление подписчиками**: Просмотр списка и статистики
- ⚙️ **Настройки**: Конфигурация приветственного сообщения и PDF файла
- 📄 **PDF поддержка**: Автоматическая отправка PDF при команде /start

## Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd telegram_bot_admin
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте переменные окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл, указав ваш TELEGRAM_TOKEN
```

4. **Получите токен бота:**
- Напишите @BotFather в Telegram
- Создайте нового бота командой /newbot
- Скопируйте полученный токен в .env файл

## Запуск

### Разработка
```bash
python main.py
```

### Продакшн
```bash
gunicorn -c gunicorn_config.py web.app:app
```

## Структура проекта

```
telegram_bot_admin/
├── bot/                 # Код телеграм бота
│   └── telegram_bot.py
├── web/                 # Веб-интерфейс
│   └── app.py
├── templates/           # HTML шаблоны
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── broadcast.html
│   ├── settings.html
│   └── subscribers.html
├── static/              # Статические файлы
├── uploads/             # Загруженные файлы
├── data/                # Данные бота (создается автоматически)
├── config.py            # Конфигурация
├── main.py              # Главный файл запуска
├── requirements.txt     # Зависимости
└── README.md           # Документация
```

## Использование

1. **Запустите бота** - он будет доступен в Telegram
2. **Откройте веб-интерфейс** по адресу http://localhost:5000
3. **Войдите** используя данные из .env файла
4. **Настройте** приветственное сообщение и PDF
5. **Создавайте рассылки** для всех подписчиков

## API Endpoints

- `GET /` - Главная страница (требует авторизации)
- `GET /login` - Страница входа
- `POST /login` - Авторизация
- `GET /logout` - Выход
- `GET /broadcast` - Страница рассылки
- `POST /api/send_broadcast` - API для отправки рассылки
- `GET /settings` - Страница настроек
- `GET /subscribers` - Список подписчиков

## Настройка для продакшена

1. **Измените SECRET_KEY** в .env файле
2. **Настройте веб-сервер** (Nginx + Gunicorn)
3. **Настройте SSL** для HTTPS
4. **Настройте домен** bot.tildahelp.ru

### Nginx конфигурация
```nginx
server {
    listen 80;
    server_name bot.tildahelp.ru;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name bot.tildahelp.ru;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Безопасность

- Все маршруты (кроме /login) требуют авторизации
- Пароли хранятся в переменных окружения
- Загрузка файлов ограничена по размеру (16MB)
- Поддерживаются только PDF файлы

## Поддержка

При возникновении проблем:
1. Проверьте логи в консоли
2. Убедитесь, что все зависимости установлены
3. Проверьте правильность токена бота
4. Убедитесь, что порт 5000 свободен

## Лицензия

MIT License
