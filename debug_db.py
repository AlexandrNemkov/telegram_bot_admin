#!/usr/bin/env python3
"""
Скрипт для диагностики базы данных
"""

import sqlite3
import os
from database import Database

def debug_database():
    """Диагностика базы данных"""
    db_path = 'data/bot.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    print("🔍 Диагностика базы данных...")
    
    # Подключаемся к БД напрямую
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Таблицы в БД: {[t[0] for t in tables]}")
        
        # Проверяем пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        print(f"👥 Пользователей в БД: {users_count}")
        
        if users_count > 0:
            cursor.execute("SELECT id, username, first_name, last_name, full_name FROM users LIMIT 5")
            users = cursor.fetchall()
            print("📝 Примеры пользователей:")
            for user in users:
                print(f"  ID: {user[0]}, Username: {user[1]}, First: {user[2]}, Last: {user[3]}, Full: {user[4]}")
        
        # Проверяем сообщения
        cursor.execute("SELECT COUNT(*) FROM messages")
        messages_count = cursor.fetchone()[0]
        print(f"💬 Сообщений в БД: {messages_count}")
        
        if messages_count > 0:
            cursor.execute("SELECT user_id, text, is_from_user, timestamp FROM messages LIMIT 5")
            messages = cursor.fetchall()
            print("📨 Примеры сообщений:")
            for msg in messages:
                print(f"  User: {msg[0]}, Text: {msg[1][:50]}..., From User: {msg[2]}, Time: {msg[3]}")
        
        # Проверяем настройки
        cursor.execute("SELECT COUNT(*) FROM settings")
        settings_count = cursor.fetchone()[0]
        print(f"⚙️ Настроек в БД: {settings_count}")
        
        if settings_count > 0:
            cursor.execute("SELECT key, value FROM settings")
            settings = cursor.fetchall()
            print("🔧 Настройки:")
            for setting in settings:
                print(f"  {setting[0]}: {setting[1]}")
    
    print("\n🔍 Тестируем класс Database...")
    
    try:
        db = Database()
        
        # Тестируем получение пользователей
        users = db.get_all_users()
        print(f"📊 get_all_users() вернул {len(users)} пользователей")
        
        if users:
            print("📝 Первый пользователь:")
            user = users[0]
            for key, value in user.items():
                print(f"  {key}: {value}")
        
        # Тестируем получение сообщений
        if users:
            user_id = users[0]['id']
            messages = db.get_user_messages(user_id)
            print(f"💬 get_user_messages({user_id}) вернул {len(messages)} сообщений")
            
            if messages:
                print("📨 Первое сообщение:")
                msg = messages[0]
                for key, value in msg.items():
                    print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании Database: {e}")

if __name__ == "__main__":
    debug_database()
