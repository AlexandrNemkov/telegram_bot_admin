# 🧪 Тестирование системы

## Локальное тестирование

### 1. Проверка зависимостей
```bash
pip3 install -r requirements.txt
pip3 list | grep -E "(telegram|Flask|gunicorn)"
```

### 2. Проверка конфигурации
```bash
python3 -c "from config import Config; print('Config OK')"
```

### 3. Тест импорта модулей
```bash
python3 -c "from bot.telegram_bot import TelegramBot; print('Bot module OK')"
python3 -c "from web.app import app; print('Web module OK')"
```

### 4. Запуск тестового режима
```bash
python3 main.py
```

## Проверка функционала

### Telegram Bot
- ✅ Отправьте /start - должно прийти приветствие
- ✅ Отправьте /help - должна прийти справка
- ✅ Отправьте /status - должен показаться статус подписки

### Веб-интерфейс
- ✅ Откройте http://localhost:5000
- ✅ Войдите с логином BotNemkov и паролем Nemkov&
- ✅ Проверьте все страницы: Дашборд, Рассылка, Настройки, Подписчики

### Функции админки
- ✅ Измените приветственное сообщение в настройках
- ✅ Загрузите PDF файл
- ✅ Создайте тестовую рассылку
- ✅ Проверьте список подписчиков

## Проверка логов

### Консольные логи
```bash
# При запуске должны быть сообщения:
# 🚀 Запуск системы телеграм бота с админ-панелью...
# 🤖 Запуск телеграм бота...
# 🌐 Запуск веб-интерфейса...
```

### Логи бота
- Проверьте, что бот отвечает на команды
- Проверьте, что новые пользователи добавляются в список

### Логи веб-интерфейса
- Проверьте доступность всех страниц
- Проверьте работу форм

## Проверка безопасности

### Авторизация
- ✅ Попытка доступа к защищенным страницам без входа
- ✅ Проверка работы logout
- ✅ Проверка сессий

### Валидация данных
- ✅ Отправка пустых форм
- ✅ Отправка форм с некорректными данными
- ✅ Загрузка файлов неправильного формата

## Проверка производительности

### Нагрузочное тестирование
```bash
# Установка Apache Bench
sudo apt install apache2-utils

# Тест веб-интерфейса
ab -n 100 -c 10 http://localhost:5000/

# Тест API
ab -n 100 -c 10 -p test_data.json -T application/json http://localhost:5000/api/send_broadcast
```

### Мониторинг ресурсов
```bash
# Мониторинг CPU и памяти
top -p $(pgrep -f "python3 main.py")

# Мониторинг сетевых соединений
netstat -tulpn | grep :5000
```

## Автоматизированное тестирование

### Создание тестового скрипта
```python
# test_bot.py
import requests
import json

def test_web_interface():
    base_url = "http://localhost:5000"
    
    # Тест страницы входа
    response = requests.get(f"{base_url}/login")
    assert response.status_code == 200
    
    # Тест авторизации
    login_data = {
        "username": "BotNemkov",
        "password": "Nemkov&"
    }
    response = requests.post(f"{base_url}/login", data=login_data)
    assert response.status_code == 302  # Редирект после входа
    
    print("✅ Веб-интерфейс работает корректно")

if __name__ == "__main__":
    test_web_interface()
```

### Запуск тестов
```bash
python3 test_bot.py
```

## Проверка развертывания

### Проверка файлов
```bash
# Проверка структуры
find . -type f -name "*.py" | wc -l
find . -type f -name "*.html" | wc -l

# Проверка прав доступа
ls -la run.sh
ls -la .env
```

### Проверка конфигурации
```bash
# Проверка .env
grep -E "TELEGRAM_TOKEN|ADMIN_USERNAME|ADMIN_PASSWORD" .env

# Проверка requirements.txt
wc -l requirements.txt
```

## Устранение проблем

### Частые ошибки

1. **ModuleNotFoundError**
   - Проверьте установку зависимостей
   - Проверьте виртуальное окружение

2. **TELEGRAM_TOKEN не установлен**
   - Проверьте файл .env
   - Проверьте переменные окружения

3. **Порт 5000 занят**
   - Измените порт в config.py
   - Остановите другие сервисы

4. **Ошибки авторизации**
   - Проверьте логин/пароль в .env
   - Проверьте настройки Flask-Login

### Логи ошибок
```bash
# Подробные логи Python
python3 -u main.py 2>&1 | tee bot.log

# Логи с отладкой
FLASK_DEBUG=1 python3 main.py
```

## Готовность к продакшену

### Чек-лист
- [ ] Все зависимости установлены
- [ ] Конфигурация настроена
- [ ] Тесты пройдены
- [ ] Логи проверены
- [ ] Безопасность протестирована
- [ ] Производительность проверена
- [ ] Документация готова

### Финальная проверка
```bash
# Полный тест системы
./run.sh &
sleep 10
curl -s http://localhost:5000/login | grep -q "Bot Admin" && echo "✅ Система готова" || echo "❌ Проблемы"
```
