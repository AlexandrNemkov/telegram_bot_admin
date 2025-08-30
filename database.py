import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = 'data/bot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        full_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица сообщений
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        is_from_user BOOLEAN NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # Таблица настроек
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создаем индексы для быстрого поиска
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                
                conn.commit()
                logger.info("База данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Добавление или обновление пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                full_name = f"{first_name or ''} {last_name or ''}".strip()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO users (id, username, first_name, last_name, full_name, last_activity)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name, last_name, full_name))
                
                conn.commit()
                logger.info(f"Пользователь {user_id} добавлен/обновлен в БД")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, first_name, last_name, full_name, created_at, last_activity
                    FROM users WHERE id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'full_name': row[4],
                        'created_at': row[5],
                        'last_activity': row[6]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT u.id, u.username, u.first_name, u.last_name, u.full_name, 
                           u.created_at, u.last_activity,
                           m.text as last_message_text, m.timestamp as last_message_time
                    FROM users u
                    LEFT JOIN (
                        SELECT user_id, text, timestamp,
                               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp DESC) as rn
                        FROM messages
                    ) m ON u.id = m.user_id AND m.rn = 1
                    ORDER BY u.last_activity DESC
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'full_name': row[4],
                        'created_at': row[5],
                        'last_activity': row[6],
                        'last_message_text': row[7],
                        'last_message_time': row[8]
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []
    
    def add_message(self, user_id: int, text: str, is_from_user: bool = True) -> bool:
        """Добавление сообщения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Добавляем сообщение
                cursor.execute('''
                    INSERT INTO messages (user_id, text, is_from_user, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, text, is_from_user))
                
                # Обновляем время последней активности пользователя
                cursor.execute('''
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user_id,))
                
                conn.commit()
                logger.info(f"Сообщение добавлено для пользователя {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения для пользователя {user_id}: {e}")
            return False
    
    def get_user_messages(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Получение сообщений пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, text, is_from_user, timestamp
                    FROM messages 
                    WHERE user_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                ''', (user_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'id': row[0],
                        'text': row[1],
                        'is_from_user': bool(row[2]),
                        'timestamp': row[3]
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Ошибка получения сообщений пользователя {user_id}: {e}")
            return []
    
    def get_setting(self, key: str) -> Optional[str]:
        """Получение настройки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
                row = cursor.fetchone()
                
                return row[0] if row else None
                
        except Exception as e:
            logger.error(f"Ошибка получения настройки {key}: {e}")
            return None
    
    def set_setting(self, key: str, value: str) -> bool:
        """Установка настройки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка установки настройки {key}: {e}")
            return False
    
    def get_subscribers_count(self) -> int:
        """Получение количества подписчиков"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM users')
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Ошибка получения количества подписчиков: {e}")
            return 0
    
    def cleanup_old_messages(self, days: int = 30) -> int:
        """Очистка старых сообщений"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Удалено {deleted_count} старых сообщений")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Ошибка очистки старых сообщений: {e}")
            return 0
