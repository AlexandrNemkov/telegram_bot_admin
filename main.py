#!/usr/bin/env python3
"""
Главный файл для запуска телеграм бота с веб-интерфейсом
"""

import os
import sys
import threading
import time
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем пути к модулям
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'bot'))
sys.path.append(os.path.join(current_dir, 'web'))

def run_web():
    """Запуск веб-интерфейса в отдельном потоке"""
    try:
        from app import app
        print("🌐 Запуск веб-интерфейса...")
        # На сервере запускаем без debug режима
        app.run(debug=False, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Ошибка запуска веб-интерфейса: {e}")

def main():
    """Главная функция"""
    print("🚀 Запуск системы телеграм бота с админ-интерфейсом...")
    
    # Проверяем наличие токена
    if not os.getenv('TELEGRAM_TOKEN'):
        print("❌ Ошибка: TELEGRAM_TOKEN не установлен!")
        print("Создайте файл .env и укажите токен бота")
        return
    
    # Создаем необходимые директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Запускаем веб-интерфейс в отдельном потоке
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Небольшая задержка для запуска веб-интерфейса
    time.sleep(2)
    
    # Запускаем бота в основном потоке
    try:
        from telegram_bot import TelegramBot
        bot = TelegramBot()
        print("🤖 Запуск телеграм бота...")
        bot.run()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        
        # Если ошибка связана с конфликтом, даем рекомендации
        if "Conflict" in str(e) or "getUpdates" in str(e):
            print("\n🔧 Рекомендации по исправлению:")
            print("1. Убедитесь, что не запущено других экземпляров бота")
            print("2. Проверьте, не запущен ли бот в другом терминале")
            print("3. Перезапустите сервер: sudo systemctl restart telegram-bot")
            print("4. Или остановите все процессы Python: sudo pkill -f python")
        
        # Продолжаем работу веб-интерфейса
        print("\n🌐 Веб-интерфейс продолжает работать...")
        try:
            # Держим основной поток живым
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n👋 Завершение работы...")

if __name__ == "__main__":
    main()
