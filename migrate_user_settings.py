#!/usr/bin/env python3
"""
Скрипт миграции для добавления новых колонок в таблицу user_settings
Добавляет поля: bot_name, bot_description, start_command
"""

import sqlite3
import os
from datetime import datetime

def migrate_user_settings():
    """Миграция таблицы user_settings"""
    db_path = 'data/bot.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🔄 Начинаем миграцию таблицы user_settings...")
            
            # Проверяем существующие колонки
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 Существующие колонки: {columns}")
            
            # Добавляем новые колонки если их нет
            new_columns = [
                ('bot_name', 'TEXT DEFAULT "Мой бот"'),
                ('bot_description', 'TEXT DEFAULT ""'),
                ('start_command', 'TEXT DEFAULT "Добро пожаловать! Нажмите /help для справки."')
            ]
            
            for column_name, column_def in new_columns:
                if column_name not in columns:
                    print(f"➕ Добавляем колонку: {column_name}")
                    cursor.execute(f'ALTER TABLE user_settings ADD COLUMN {column_name} {column_def}')
                else:
                    print(f"✅ Колонка {column_name} уже существует")
            
            # Обновляем существующие записи значениями по умолчанию
            print("🔄 Обновляем существующие записи...")
            cursor.execute('''
                UPDATE user_settings 
                SET bot_name = COALESCE(bot_name, 'Мой бот'),
                    bot_description = COALESCE(bot_description, ''),
                    start_command = COALESCE(start_command, 'Добро пожаловать! Нажмите /help для справки.')
                WHERE bot_name IS NULL OR bot_description IS NULL OR start_command IS NULL
            ''')
            
            # Проверяем результат
            cursor.execute("PRAGMA table_info(user_settings)")
            final_columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 Финальные колонки: {final_columns}")
            
            # Показываем количество обновленных записей
            cursor.execute('SELECT COUNT(*) FROM user_settings')
            count = cursor.fetchone()[0]
            print(f"📊 Всего записей в таблице: {count}")
            
            conn.commit()
            print("✅ Миграция успешно завершена!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск миграции user_settings...")
    success = migrate_user_settings()
    if success:
        print("🎉 Миграция завершена успешно!")
    else:
        print("💥 Миграция завершилась с ошибкой!")
