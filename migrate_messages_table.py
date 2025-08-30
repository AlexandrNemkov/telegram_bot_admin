#!/usr/bin/env python3
"""
Скрипт миграции для добавления поля bot_user_id в таблицу messages
Это позволит разделить сообщения по разным ботам
"""

import sqlite3
import os
from datetime import datetime

def migrate_messages_table():
    db_path = 'data/bot.db'
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            print("🔄 Начинаем миграцию таблицы messages...")
            
            # Проверяем существующие колонки
            cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 Существующие колонки: {columns}")
            
            # Добавляем поле bot_user_id если его нет
            if 'bot_user_id' not in columns:
                print("➕ Добавляем колонку bot_user_id")
                cursor.execute('ALTER TABLE messages ADD COLUMN bot_user_id INTEGER DEFAULT 1')
                
                # Обновляем существующие сообщения, привязывая их к первому пользователю (админу)
                print("🔄 Обновляем существующие сообщения...")
                cursor.execute('UPDATE messages SET bot_user_id = 1 WHERE bot_user_id IS NULL')
                
                print("✅ Колонка bot_user_id добавлена и заполнена")
            else:
                print("✅ Колонка bot_user_id уже существует")
            
            # Проверяем финальную структуру
            cursor.execute("PRAGMA table_info(messages)")
            final_columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 Финальные колонки: {final_columns}")
            
            # Показываем статистику
            cursor.execute('SELECT COUNT(*) FROM messages')
            total_messages = cursor.fetchone()[0]
            print(f"📊 Всего сообщений в таблице: {total_messages}")
            
            cursor.execute('SELECT COUNT(DISTINCT bot_user_id) FROM messages')
            unique_bots = cursor.fetchone()[0]
            print(f"🤖 Уникальных ботов: {unique_bots}")
            
            conn.commit()
            print("✅ Миграция таблицы messages успешно завершена!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск миграции таблицы messages...")
    success = migrate_messages_table()
    if success:
        print("🎉 Миграция завершена успешно!")
    else:
        print("💥 Миграция завершилась с ошибкой!")
