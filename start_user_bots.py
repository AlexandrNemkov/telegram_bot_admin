#!/usr/bin/env python3
"""
Скрипт для запуска пользовательских ботов
Запускает все настроенные боты из базы данных
"""

import os
import sys
import asyncio
import logging
import time
from datetime import datetime

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/telegram-bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Главная функция запуска ботов"""
    try:
        print("🚀 Запуск системы множественных ботов...")
        
        # Добавляем пути к модулям
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(os.path.join(current_dir, 'bot'))
        sys.path.append(os.path.join(current_dir, 'web'))
        
        # Импортируем менеджер ботов
        from bot.user_bot_manager import bot_manager
        from database import Database
        
        print("✅ Менеджер ботов загружен")
        
        # Получаем всех пользователей с настройками ботов
        db = Database()
        system_users = db.get_all_system_users()
        
        print(f"📊 Найдено {len(system_users)} пользователей в системе")
        
        active_bots = 0
        failed_bots = 0
        
        for user in system_users:
            if user['is_active']:
                print(f"\n🔍 Проверяем пользователя: {user['username']} (ID: {user['id']})")
                
                user_settings = db.get_user_settings(user['id'])
                if user_settings and user_settings.get('bot_token'):
                    print(f"🤖 Найден токен бота для {user['username']}")
                    print(f"   Username: @{user_settings.get('bot_username', 'Не указан')}")
                    
                    # Запускаем бота
                    if bot_manager.add_bot(
                        user['id'],
                        user_settings['bot_token'],
                        user_settings.get('bot_username', ''),
                        user_settings.get('welcome_message', 'Добро пожаловать! 👋'),
                        user_settings.get('start_command', 'Добро пожаловать! Нажмите /help для справки.')
                    ):
                        active_bots += 1
                        print(f"✅ Бот пользователя {user['username']} успешно запущен")
                    else:
                        failed_bots += 1
                        print(f"❌ Ошибка запуска бота пользователя {user['username']}")
                else:
                    print(f"⚠️ У пользователя {user['username']} нет настроек бота")
        
        print(f"\n🎯 РЕЗУЛЬТАТ:")
        print(f"✅ Успешно запущено: {active_bots} ботов")
        print(f"❌ Ошибок запуска: {failed_bots} ботов")
        
        if active_bots > 0:
            print(f"\n🤖 Всего активных ботов: {len(bot_manager.get_all_bots())}")
            print(f"📱 Общее количество подписчиков: {bot_manager.get_total_subscribers()}")
            
            # Держим скрипт запущенным
            print("\n🔄 Система работает. Нажмите Ctrl+C для остановки...")
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\n🛑 Остановка всех ботов...")
                bot_manager.stop_all_bots()
                print("👋 Завершение работы...")
        else:
            print("\n⚠️ Нет активных ботов для запуска")
            print("Проверьте настройки пользователей в базе данных")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
