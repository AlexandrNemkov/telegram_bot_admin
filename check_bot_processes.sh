#!/bin/bash

# Скрипт для проверки и остановки дублирующихся процессов Telegram бота

echo "🔍 Проверяем процессы Telegram бота..."

# Ищем все процессы Python, связанные с ботом
echo "📋 Найденные процессы Python:"
ps aux | grep -E "(python|telegram_bot|main.py)" | grep -v grep

echo ""
echo "🤖 Процессы Telegram бота:"
ps aux | grep -E "(telegram_bot|main.py)" | grep -v grep

echo ""
echo "📊 Статистика процессов:"
echo "Python процессов: $(ps aux | grep python | grep -v grep | wc -l)"
echo "Telegram бот процессов: $(ps aux | grep -E "(telegram_bot|main.py)" | grep -v grep | wc -l)"

echo ""
echo "🔧 Команды для управления:"
echo "1. Остановить все процессы Python: sudo pkill -f python"
echo "2. Остановить только бота: sudo pkill -f telegram_bot"
echo "3. Перезапустить сервис: sudo systemctl restart telegram-bot"
echo "4. Проверить статус сервиса: sudo systemctl status telegram-bot"

echo ""
echo "⚠️  ВНИМАНИЕ: Если запущено несколько экземпляров бота, это вызовет ошибку 'Conflict'"
echo "   Рекомендуется остановить все процессы и запустить заново"
