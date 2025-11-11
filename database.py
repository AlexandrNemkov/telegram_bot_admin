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
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_message_text TEXT,
                        last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        bot_user_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (bot_user_id) REFERENCES system_users (id)
                    )
                ''')
                
                # Таблица настроек (общие для системы)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица пользователей системы
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        full_name TEXT,
                        email TEXT,
                        account_expires TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        created_by INTEGER,
                        FOREIGN KEY (created_by) REFERENCES system_users (id)
                    )
                ''')
                
                # Таблица индивидуальных настроек пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        welcome_message TEXT DEFAULT 'Добро пожаловать! 👋',
                        welcome_pdf_path TEXT DEFAULT '',
                        welcome_file_id TEXT DEFAULT '',
                        welcome_file_caption TEXT DEFAULT '',
                        bot_token TEXT DEFAULT '',
                        bot_username TEXT DEFAULT '',
                        bot_name TEXT DEFAULT 'Мой бот',
                        bot_description TEXT DEFAULT '',
                        start_command TEXT DEFAULT 'Добро пожаловать! Нажмите /help для справки.',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES system_users (id)
                    )
                ''')
                
                # ===== Дополнительные таблицы для рассылок и логов доставки =====
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS campaigns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        text TEXT,
                        photo_file_id TEXT,
                        scheduled_at TIMESTAMP,
                        status TEXT DEFAULT 'scheduled', -- scheduled, sending, sent, failed, canceled
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES system_users (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS delivery_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,         -- подписчик (получатель)
                        bot_user_id INTEGER NOT NULL,     -- владелец бота
                        campaign_id INTEGER,
                        status TEXT NOT NULL,             -- success, failed
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (bot_user_id) REFERENCES system_users (id),
                        FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                    )
                ''')
                
                # Миграции-страховки: добавляем недостающие колонки, если таблица уже была
                for alter in [
                    "ALTER TABLE user_settings ADD COLUMN welcome_file_id TEXT",
                    "ALTER TABLE user_settings ADD COLUMN welcome_file_caption TEXT",
                    "ALTER TABLE user_settings ADD COLUMN bot_token TEXT",
                    "ALTER TABLE user_settings ADD COLUMN bot_username TEXT"
                ]:
                    try:
                        cursor.execute(alter)
                    except sqlite3.OperationalError:
                        pass
                
                # Миграция: добавляем поле bot_user_id если его нет
                try:
                    cursor.execute('ALTER TABLE messages ADD COLUMN bot_user_id INTEGER')
                    logger.info("Добавлено поле bot_user_id в таблицу messages")
                except sqlite3.OperationalError:
                    # Поле уже существует
                    pass
                
                # Очищаем дублирующиеся записи пользователей
                try:
                    cursor.execute('''
                        DELETE FROM users 
                        WHERE id IN (
                            SELECT id FROM users 
                            GROUP BY id 
                            HAVING COUNT(*) > 1
                        )
                    ''')
                    logger.info("Очищены дублирующиеся записи пользователей")
                except Exception as e:
                    logger.warning(f"Ошибка очистки дублей: {e}")
                
                # Создаем индексы для быстрого поиска
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_bot_user_id ON messages(bot_user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_users_username ON system_users(username)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_users_role ON system_users(role)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_users_expires ON system_users(account_expires)')
                
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
    
    # ===== Помощники для system_users, создаваемых из Telegram (админ-бот) =====
    def upsert_system_user_from_telegram(self, telegram_user_id: int, username: str, full_name: str = None) -> int:
        """Создать или получить system_user для владельца по его Telegram ID.
        Используем telegram_user_id как первичный ключ для удобной связи."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Пытаемся получить по id
                cursor.execute('SELECT id FROM system_users WHERE id = ?', (telegram_user_id,))
                row = cursor.fetchone()
                if row:
                    return row[0]
                
                # Пытаемся получить по username
                if username:
                    cursor.execute('SELECT id FROM system_users WHERE username = ?', (username,))
                    row = cursor.fetchone()
                    if row:
                        # Проставим id если отличается (оставим как есть для целостности)
                        return row[0]
                
                # Создаём пользователя с заданным id
                password_hash = 'telegram-auth'  # маркер-заглушка
                cursor.execute('''
                    INSERT INTO system_users (id, username, password_hash, role, full_name, is_active, created_at)
                    VALUES (?, ?, ?, 'user', ?, 1, CURRENT_TIMESTAMP)
                ''', (telegram_user_id, username or f"user_{telegram_user_id}", password_hash, full_name))
                conn.commit()
                return telegram_user_id
        except Exception as e:
            logger.error(f"Ошибка upsert system_user от Telegram ID {telegram_user_id}: {e}")
            raise
    
    def add_message(self, user_id: int, text: str, is_from_user: bool = True, bot_user_id = None) -> bool:
        """Добавление сообщения"""
        try:
            logger.info(f"🔍 Database.add_message: user_id={user_id}, text='{text[:50]}...', is_from_user={is_from_user}, bot_user_id={bot_user_id}")
            # Логируем в файл
            with open('/tmp/debug.log', 'a') as f:
                f.write(f"🔍 DEBUG: Database.add_message: user_id={user_id}, text='{text[:50]}...', is_from_user={is_from_user}, bot_user_id={bot_user_id}\n")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем существует ли пользователь
                cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
                user_exists = cursor.fetchone()
                
                if not user_exists:
                    logger.warning(f"⚠️ Пользователь {user_id} не найден в БД, создаем...")
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (id, username, first_name, last_name, full_name)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, f'user_{user_id}', '', '', f'User {user_id}'))
                
                # Добавляем сообщение
                logger.info(f"💾 Добавляем сообщение в БД...")
                current_time = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO messages (user_id, text, is_from_user, timestamp, bot_user_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, text, is_from_user, current_time, bot_user_id))
                
                # Обновляем время последней активности пользователя
                cursor.execute('''
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user_id,))
                
                conn.commit()
                logger.info(f"✅ Сообщение успешно добавлено для пользователя {user_id}")
                
                # Проверяем что сообщение действительно сохранилось
                cursor.execute('''
                    SELECT COUNT(*) FROM messages 
                    WHERE user_id = ? AND bot_user_id = ?
                ''', (user_id, bot_user_id))
                count = cursor.fetchone()[0]
                logger.info(f"📊 Всего сообщений у пользователя {user_id} с ботом {bot_user_id}: {count}")
                # Логируем в файл
                with open('/tmp/debug.log', 'a') as f:
                    f.write(f"📊 DEBUG: Всего сообщений у пользователя {user_id} с ботом {bot_user_id}: {count}\n")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления сообщения для пользователя {user_id}: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
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

    # ===== МЕТОДЫ ДЛЯ СИСТЕМНЫХ ПОЛЬЗОВАТЕЛЕЙ =====
    
    def create_system_user(self, username: str, password_hash: str, role: str = 'user', 
                          full_name: str = None, email: str = None, 
                          account_expires: str = None, created_by: int = None) -> bool:
        """Создание системного пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_users (username, password_hash, role, full_name, email, 
                                            account_expires, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (username, password_hash, role, full_name, email, account_expires, created_by))
                
                conn.commit()
                logger.info(f"Создан системный пользователь: {username} с ролью {role}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка создания системного пользователя {username}: {e}")
            return False
    
    def get_system_user(self, username_or_id):
        """Получить пользователя системы по username или ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем, является ли параметр числом (ID) или строкой (username)
            if isinstance(username_or_id, int) or str(username_or_id).isdigit():
                # Поиск по ID
                cursor.execute('''
                    SELECT id, username, password_hash, role, full_name, email, 
                           account_expires, is_active, created_at, last_login, created_by
                    FROM system_users 
                    WHERE id = ?
                ''', (int(username_or_id),))
            else:
                # Поиск по username
                cursor.execute('''
                    SELECT id, username, password_hash, role, full_name, email, 
                           account_expires, is_active, created_at, last_login, created_by
                    FROM system_users 
                    WHERE username = ?
                ''', (username_or_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'password_hash': result[2],
                    'role': result[3],
                    'full_name': result[4],
                    'email': result[5],
                    'account_expires': result[6],
                    'is_active': result[7],
                    'created_at': result[8],
                    'last_login': result[9],
                    'created_by': result[10]
                }
            return None
    
    def update_system_user_password(self, username: str, new_password_hash: str) -> bool:
        """Обновление пароля системного пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE system_users SET password_hash = ? WHERE username = ?
                ''', (new_password_hash, username))
                
                conn.commit()
                logger.info(f"Пароль обновлен для пользователя {username}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления пароля для {username}: {e}")
            return False
    
    def update_system_user_expiry(self, username: str, account_expires: str) -> bool:
        """Обновление времени истечения аккаунта"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE system_users SET account_expires = ? WHERE username = ?
                ''', (account_expires, username))
                
                conn.commit()
                logger.info(f"Время истечения обновлено для пользователя {username}: {account_expires}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления времени истечения для {username}: {e}")
            return False
    
    def get_expired_accounts(self) -> List[Dict]:
        """Получение списка истекших аккаунтов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, full_name, email, account_expires, created_at
                    FROM system_users 
                    WHERE account_expires < datetime('now') AND is_active = 1
                    ORDER BY account_expires ASC
                ''')
                
                expired_accounts = []
                for row in cursor.fetchall():
                    expired_accounts.append({
                        'id': row[0],
                        'username': row[1],
                        'full_name': row[2],
                        'email': row[3],
                        'account_expires': row[4],
                        'created_at': row[5]
                    })
                
                return expired_accounts
                
        except Exception as e:
            logger.error(f"Ошибка получения истекших аккаунтов: {e}")
            return []
    
    def deactivate_expired_accounts(self) -> int:
        """Деактивация истекших аккаунтов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE system_users 
                    SET is_active = 0 
                    WHERE account_expires < datetime('now') AND is_active = 1
                ''')
                
                deactivated_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Деактивировано {deactivated_count} истекших аккаунтов")
                return deactivated_count
                
        except Exception as e:
            logger.error(f"Ошибка деактивации истекших аккаунтов: {e}")
            return 0
    
    def get_all_system_users(self) -> List[Dict]:
        """Получение всех системных пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, role, full_name, email, account_expires, 
                           is_active, created_at, last_login, created_by
                    FROM system_users 
                    ORDER BY created_at DESC
                ''')
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'id': row[0],
                        'username': row[1],
                        'role': row[2],
                        'full_name': row[3],
                        'email': row[4],
                        'account_expires': row[5],
                        'is_active': bool(row[6]),
                        'created_at': row[7],
                        'last_login': row[8],
                        'created_by': row[9]
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Ошибка получения системных пользователей: {e}")
            return []
    
    def update_last_login(self, username: str) -> bool:
        """Обновление времени последнего входа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE system_users SET last_login = CURRENT_TIMESTAMP WHERE username = ?
                ''', (username,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления времени входа для {username}: {e}")
            return False

    def get_user_settings(self, user_id):
        """Получить настройки пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT welcome_message, welcome_pdf_path, bot_token, bot_username, bot_name, bot_description, start_command, created_at, updated_at,
                       welcome_file_id, welcome_file_caption
                FROM user_settings 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'welcome_message': result[0],
                    'welcome_pdf_path': result[1],
                    'bot_token': result[2],
                    'bot_username': result[3],
                    'bot_name': result[4],
                    'bot_description': result[5],
                    'start_command': result[6],
                    'created_at': result[7],
                    'updated_at': result[8],
                    'welcome_file_id': result[9] if len(result) > 9 else '',
                    'welcome_file_caption': result[10] if len(result) > 10 else ''
                }
            else:
                # Создать настройки по умолчанию для пользователя
                cursor.execute('''
                    INSERT INTO user_settings (user_id, welcome_message, welcome_pdf_path, bot_token, bot_username, bot_name, bot_description, start_command, welcome_file_id, welcome_file_caption)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, 'Добро пожаловать! 👋', '', '', '', 'Мой бот', '', 'Добро пожаловать! Нажмите /help для справки.', '', ''))
                conn.commit()
                
                return {
                    'welcome_message': 'Добро пожаловать! 👋',
                    'welcome_pdf_path': '',
                    'bot_token': '',
                    'bot_username': '',
                    'bot_name': 'Мой бот',
                    'bot_description': '',
                    'start_command': 'Добро пожаловать! Нажмите /help для справки.',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'welcome_file_id': '',
                    'welcome_file_caption': ''
                }

    def update_user_welcome_message(self, user_id, message):
        """Обновить приветственное сообщение пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_settings 
                SET welcome_message = ?, updated_at = ?
                WHERE user_id = ?
            ''', (message, datetime.now().isoformat(), user_id))
            conn.commit()
            return True

    def update_user_welcome_pdf(self, user_id, pdf_path):
        """Обновить путь к PDF файлу пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_settings 
                SET welcome_pdf_path = ?, updated_at = ?
                WHERE user_id = ?
            ''', (pdf_path, datetime.now().isoformat(), user_id))
            conn.commit()
            return True
    
    def update_user_welcome_file_id(self, user_id, file_id: str, caption: str = ''):
        """Сохранить file_id и подпись для приветственного файла"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_settings 
                SET welcome_file_id = ?, welcome_file_caption = ?, updated_at = ?
                WHERE user_id = ?
            ''', (file_id, caption, datetime.now().isoformat(), user_id))
            conn.commit()
            return True

    def update_user_bot_settings(self, user_id, bot_name, bot_description, start_command):
        """Обновить настройки бота пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_settings 
                SET bot_name = ?, bot_description = ?, start_command = ?, updated_at = ?
                WHERE user_id = ?
            ''', (bot_name, bot_description, start_command, datetime.now().isoformat(), user_id))
            conn.commit()
            return True

    def update_user_bot_token(self, user_id, bot_token, bot_username):
        """Обновить токен и username бота пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE user_settings 
                SET bot_token = ?, bot_username = ?, updated_at = ?
                WHERE user_id = ?
            ''', (bot_token, bot_username, datetime.now().isoformat(), user_id))
            conn.commit()
            return True
    
    # ===== Кампании (рассылки) и логи =====
    def create_campaign(self, owner_user_id: int, text: str = None, photo_file_id: str = None, scheduled_at: str = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO campaigns (user_id, text, photo_file_id, scheduled_at, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'scheduled', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (owner_user_id, text, photo_file_id, scheduled_at))
            conn.commit()
            return cursor.lastrowid
    
    def list_campaigns(self, owner_user_id: int, limit: int = 50):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, text, photo_file_id, scheduled_at, status, created_at
                FROM campaigns
                WHERE user_id = ?
                ORDER BY 
                    CASE WHEN scheduled_at IS NULL THEN 1 ELSE 0 END,
                    COALESCE(scheduled_at, created_at) DESC
                LIMIT ?
            ''', (owner_user_id, limit))
            rows = cursor.fetchall()
            return [
                {
                    'id': r[0],
                    'text': r[1],
                    'photo_file_id': r[2],
                    'scheduled_at': r[3],
                    'status': r[4],
                    'created_at': r[5],
                } for r in rows
            ]
    
    def get_due_campaigns(self):
        """Кампании к отправке сейчас"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, text, photo_file_id
                FROM campaigns
                WHERE status = 'scheduled' AND (scheduled_at IS NULL OR scheduled_at <= CURRENT_TIMESTAMP)
                ORDER BY COALESCE(scheduled_at, created_at) ASC
            ''')
            return [{'id': r[0], 'user_id': r[1], 'text': r[2], 'photo_file_id': r[3]} for r in cursor.fetchall()]
    
    def mark_campaign_status(self, campaign_id: int, status: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE campaigns SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (status, campaign_id))
            conn.commit()
            return True
    
    def log_delivery(self, recipient_user_id: int, owner_user_id: int, campaign_id: int, status: str, error: str = None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO delivery_logs (user_id, bot_user_id, campaign_id, status, error, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (recipient_user_id, owner_user_id, campaign_id, status, error))
            conn.commit()
            return True
    
    def get_broadcast_stats(self, owner_user_id: int, since: str = None):
        """Статистика по доставкам кампаний"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if since:
                cursor.execute('''
                    SELECT status, COUNT(*) FROM delivery_logs
                    WHERE bot_user_id = ? AND created_at >= ?
                    GROUP BY status
                ''', (owner_user_id, since))
            else:
                cursor.execute('''
                    SELECT status, COUNT(*) FROM delivery_logs
                    WHERE bot_user_id = ?
                    GROUP BY status
                ''', (owner_user_id,))
            rows = cursor.fetchall()
            return {r[0]: r[1] for r in rows}

    def get_users_for_bot(self, bot_user_id):
        """Получить пользователей, которые общались с конкретным ботом"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT u.id, u.username, u.first_name, u.last_name, u.created_at,
                       m.text as last_message_text, m.timestamp as last_message_time
                FROM users u
                INNER JOIN (
                    SELECT user_id, text, timestamp,
                           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp DESC) as rn
                    FROM messages
                    WHERE bot_user_id = ?
                ) m ON u.id = m.user_id AND m.rn = 1
                ORDER BY u.created_at DESC
            ''', (bot_user_id,))
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'created_at': row[4],
                    'last_message_text': row[5],
                    'last_message_time': row[6]
                })
            return users

    def get_messages_between_users(self, user_id, bot_user_id):
        """Получить сообщения между пользователем и конкретным ботом"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, text, timestamp, is_from_user
                FROM messages
                WHERE user_id = ? AND bot_user_id = ?
                ORDER BY timestamp ASC
            ''', (user_id, bot_user_id))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],
                    'text': row[1],
                    'timestamp': row[2],
                    'is_from_user': bool(row[3])
                })
            
            logger.info(f"📊 Получено {len(messages)} сообщений для пользователя {user_id} с ботом {bot_user_id}")
            # Логируем в файл
            with open('/tmp/debug.log', 'a') as f:
                f.write(f"📊 DEBUG: Получено {len(messages)} сообщений для пользователя {user_id} с ботом {bot_user_id}\n")
            return messages

    def get_last_message_for_user(self, user_id, bot_user_id):
        """Получить последнее сообщение для пользователя от конкретного бота"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, text, timestamp, is_from_user
                FROM messages
                WHERE user_id = ? AND bot_user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id, bot_user_id))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'text': row[1],
                    'timestamp': row[2],
                    'is_from_user': bool(row[3])
                }
            return None


    def get_active_subscribers_count(self, bot_user_id, since_date):
        """Получить количество активных подписчиков с определенной даты"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM messages 
                WHERE bot_user_id = ? AND timestamp >= ? AND is_from_user = 1
            ''', (bot_user_id, since_date))
            return cursor.fetchone()[0] or 0

    def get_new_subscribers_count(self, bot_user_id, since_date):
        """Получить количество новых подписчиков с определенной даты"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM messages 
                WHERE bot_user_id = ? AND timestamp >= ? AND is_from_user = 1
                AND user_id NOT IN (
                    SELECT DISTINCT user_id 
                    FROM messages 
                    WHERE bot_user_id = ? AND timestamp < ? AND is_from_user = 1
                )
            ''', (bot_user_id, since_date, bot_user_id, since_date))
            return cursor.fetchone()[0] or 0

    def get_total_subscribers_count(self, bot_user_id):
        """Получить общее количество подписчиков бота"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) 
                FROM messages 
                WHERE bot_user_id = ? AND is_from_user = 1
            ''', (bot_user_id,))
            return cursor.fetchone()[0] or 0

    def get_messages_count_24h(self, bot_user_id, since_date):
        """Получить количество сообщений за последние 24 часа"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) 
                FROM messages 
                WHERE bot_user_id = ? AND timestamp >= ?
            ''', (bot_user_id, since_date))
            return cursor.fetchone()[0] or 0
