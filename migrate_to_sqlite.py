#!/usr/bin/env python3
"""
Скрипт для миграции данных из JSON файлов в SQLite базу данных
"""

import json
import os
import logging
from database import Database

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data():
    """Миграция данных из JSON в SQLite"""
    db = Database()
    
    # Миграция подписчиков
    if os.path.exists('data/subscribers.json'):
        try:
            with open('data/subscribers.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                subscribers = data.get('subscribers', [])
                
            logger.info(f"Найдено {len(subscribers)} подписчиков в JSON")
            
            # Добавляем подписчиков в БД (с базовой информацией)
            for user_id in subscribers:
                db.add_user(user_id, f"user_{user_id}")
            
            logger.info("Подписчики мигрированы в SQLite")
            
        except Exception as e:
            logger.error(f"Ошибка миграции подписчиков: {e}")
    
    # Миграция настроек
    if os.path.exists('data/settings.json'):
        try:
            with open('data/settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            logger.info("Настройки найдены в JSON")
            
            # Мигрируем настройки
            if 'welcome_message' in settings:
                db.set_setting('welcome_message', settings['welcome_message'])
            
            if 'welcome_pdf_path' in settings:
                db.set_setting('welcome_pdf_path', settings['welcome_pdf_path'])
            
            logger.info("Настройки мигрированы в SQLite")
            
        except Exception as e:
            logger.error(f"Ошибка миграции настроек: {e}")
    
    # Миграция сообщений (если есть)
    if os.path.exists('data/messages.json'):
        try:
            with open('data/messages.json', 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
            
            logger.info(f"Найдено {len(messages_data)} пользователей с сообщениями в JSON")
            
            # Мигрируем сообщения
            total_messages = 0
            for user_id_str, messages in messages_data.items():
                try:
                    user_id = int(user_id_str)
                    
                    # Добавляем пользователя если его нет
                    db.add_user(user_id, f"user_{user_id}")
                    
                    # Добавляем сообщения
                    for msg in messages:
                        db.add_message(user_id, msg['text'], msg['is_from_user'])
                        total_messages += 1
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Пропускаем некорректные данные для пользователя {user_id_str}: {e}")
                    continue
            
            logger.info(f"Мигрировано {total_messages} сообщений в SQLite")
            
        except Exception as e:
            logger.error(f"Ошибка миграции сообщений: {e}")
    
    logger.info("Миграция завершена!")
    
    # Показываем статистику
    users_count = db.get_subscribers_count()
    logger.info(f"Всего пользователей в БД: {users_count}")

if __name__ == "__main__":
    migrate_data()
