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
    print("🚀 Запуск системы множественных телеграм ботов с админ-интерфейсом...")
    
    # Создаем необходимые директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Запускаем веб-интерфейс в отдельном потоке
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Небольшая задержка для запуска веб-интерфейса
    time.sleep(2)
    
    # Запускаем менеджер пользовательских ботов
    try:
        from bot.user_bot_manager import bot_manager
        print("🤖 Запуск менеджера пользовательских ботов...")
        
        # Загружаем и запускаем всех активных ботов из базы данных
        from database import Database
        db = Database()
        
        # Получаем всех пользователей с настройками ботов
        system_users = db.get_all_system_users()
        active_bots = 0
        
        for user in system_users:
            if user['is_active']:
                user_settings = db.get_user_settings(user['id'])
                if user_settings and user_settings.get('bot_token'):
                    print(f"🚀 Запуск бота пользователя {user['username']}...")
                    if bot_manager.add_bot(
                        user['id'],
                        user_settings['bot_token'],
                        user_settings.get('bot_username', ''),
                        user_settings.get('welcome_message', 'Добро пожаловать! 👋'),
                        user_settings.get('start_command', 'Добро пожаловать! Нажмите /help для справки.')
                    ):
                        active_bots += 1
        
        print(f"✅ Запущено {active_bots} активных ботов")
        
        # Держим основной поток живым
        try:
            while True:
                time.sleep(10)
                # Можно добавить периодическую проверку новых ботов
        except KeyboardInterrupt:
            print("\n🛑 Остановка всех ботов...")
            bot_manager.stop_all_bots()
            print("👋 Завершение работы...")
            
    except Exception as e:
        print(f"❌ Ошибка запуска менеджера ботов: {e}")
        
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
