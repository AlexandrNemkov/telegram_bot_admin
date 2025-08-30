#!/bin/bash
echo "🔍 ПРОВЕРКА СТАТУСА БОТОВ И СЕРВИСА"
echo "======================================"

echo ""
echo "📊 Статус сервиса telegram-bot:"
systemctl status telegram-bot.service --no-pager -l

echo ""
echo "🐍 Процессы Python:"
ps aux | grep python | grep -v grep

echo ""
echo "📁 Файлы логов:"
if [ -f "/var/log/telegram-bot.log" ]; then
    echo "Последние 20 строк лога:"
    tail -20 /var/log/telegram-bot.log
else
    echo "Лог файл не найден"
fi

echo ""
echo "🗄️ База данных:"
if [ -f "/home/telegram_bot_admin/data/bot.db" ]; then
    echo "База данных существует"
    sqlite3 /home/telegram_bot_admin/data/bot.db "SELECT COUNT(*) as total_users FROM system_users;"
    sqlite3 /home/telegram_bot_admin/data/bot.db "SELECT COUNT(*) as total_settings FROM user_settings;"
    sqlite3 /home/telegram_bot_admin/data/bot.db "SELECT user_id, bot_username, bot_token FROM user_settings WHERE bot_token != '';"
else
    echo "База данных не найдена"
fi

echo ""
echo "🌐 Веб-сервер:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5000

echo ""
echo "🔑 Переменные окружения:"
if [ -f "/home/telegram_bot_admin/.env" ]; then
    echo "Файл .env существует"
    cat /home/telegram_bot_admin/.env | grep -v "TOKEN\|PASSWORD\|SECRET"
else
    echo "Файл .env не найден"
fi
