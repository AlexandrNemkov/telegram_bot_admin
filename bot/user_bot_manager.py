#!/usr/bin/env python3
"""
Менеджер пользовательских ботов
Управляет множественными экземплярами ботов для разных пользователей
"""

import asyncio
import logging
import threading
from typing import Dict, Optional, Tuple
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import sqlite3
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class UserBot:
    """Индивидуальный бот пользователя"""
    
    def __init__(self, user_id: int, bot_token: str, bot_username: str, welcome_message: str, start_command: str):
        self.user_id = user_id
        self.bot_token = bot_token
        self.bot_username = bot_username
        self.welcome_message = welcome_message
        self.start_command = start_command
        self.application = None
        self.is_running = False
        self.subscribers = set()
        
    async def start(self):
        """Запуск бота"""
        try:
            if not self.bot_token:
                logger.warning(f"Бот пользователя {self.user_id} не имеет токена")
                return False
                
            # Создаем приложение
            self.application = Application.builder().token(self.bot_token).build()
            
            # Добавляем обработчики
            self.application.add_handler(CommandHandler("start", self.start_command_handler))
            self.application.add_handler(CommandHandler("help", self.help_command_handler))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            
            # Запускаем бота
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.is_running = True
            logger.info(f"✅ Бот пользователя {self.user_id} (@{self.bot_username}) запущен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота пользователя {self.user_id}: {e}")
            return False
    
    async def stop(self):
        """Остановка бота"""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                self.is_running = False
                logger.info(f"🛑 Бот пользователя {self.user_id} остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота пользователя {self.user_id}: {e}")
    
    async def start_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username or "Unknown"
            first_name = update.effective_user.first_name or "User"
            
            # Добавляем пользователя в подписчики
            self.subscribers.add(user_id)
            
            # Отправляем приветственное сообщение
            await update.message.reply_text(self.welcome_message)
            
            # Отправляем приветственный файл по file_id если указан, иначе PDF по локальному пути
            from database import Database
            db = Database()
            user_settings = db.get_user_settings(self.user_id)
            if user_settings:
                welcome_file_id = user_settings.get('welcome_file_id')
                welcome_caption = user_settings.get('welcome_file_caption') or "Добро пожаловать! 📎"
                if welcome_file_id:
                    try:
                        # Пытаемся отправить как документ
                        await self.application.bot.send_document(chat_id=user_id, document=welcome_file_id, caption=welcome_caption)
                        logger.info(f"📎 Welcome file_id отправлен пользователю {user_id}")
                    except Exception as e_doc:
                        try:
                            # Если не документ — попробуем как фото
                            await self.application.bot.send_photo(chat_id=user_id, photo=welcome_file_id, caption=welcome_caption)
                            logger.info(f"🖼 Welcome photo_id отправлен пользователю {user_id}")
                        except Exception as e_photo:
                            logger.error(f"❌ Ошибка отправки welcome file_id: {e_doc} / {e_photo}")
                elif user_settings.get('welcome_pdf_path'):
                    pdf_path = user_settings['welcome_pdf_path']
                    import os
                    if os.path.exists(pdf_path):
                        try:
                            filename = os.path.basename(pdf_path)
                            await self.send_file_to_user(user_id, pdf_path, filename, "Добро пожаловать! 📄")
                            logger.info(f"📄 PDF файл отправлен пользователю {user_id}")
                        except Exception as e:
                            logger.error(f"❌ Ошибка отправки PDF пользователю {user_id}: {e}")
            
            # Сохраняем пользователя в базу данных
            self.save_user_to_db(user_id, username, first_name)
            
            logger.info(f"👋 Новый пользователь {user_id} (@{username}) в боте {self.user_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки /start в боте {self.user_id}: {e}")
    
    async def help_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        try:
            help_text = """
🤖 Доступные команды:
/start - Начать работу с ботом
/help - Показать эту справку

Для получения дополнительной информации обратитесь к администратору.
            """
            await update.message.reply_text(help_text)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки /help в боте {self.user_id}: {e}")
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            # Сохраняем сообщение в базу данных
            self.save_message_to_db(user_id, message_text, True)
            
            # НЕ отправляем автоматический ответ - администратор ответит через веб-интерфейс
            # await update.message.reply_text("Сообщение получено! Администратор скоро ответит.")
            
            logger.info(f"💬 Сообщение от {user_id} в боте {self.user_id}: {message_text[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения в боте {self.user_id}: {e}")
    
    def save_user_to_db(self, user_id: int, username: str, first_name: str):
        """Сохранение пользователя в базу данных"""
        try:
            from database import Database
            db = Database()
            db.add_user(user_id, username, first_name)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователя {user_id}: {e}")
    
    def save_message_to_db(self, user_id: int, text: str, is_from_user: bool):
        """Сохранение сообщения в базу данных"""
        try:
            from database import Database
            db = Database()
            db.add_message(user_id, text, is_from_user, self.user_id)  # Добавляем bot_user_id
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сообщения: {e}")
    
    def get_subscribers_count(self) -> int:
        """Получение количества подписчиков"""
        return len(self.subscribers)
    
    async def send_broadcast(self, message: str) -> Tuple[int, int]:
        """Отправка рассылки всем подписчикам"""
        success_count = 0
        failed_count = 0
        
        # Проверяем что бот запущен
        if not self.application or not self.is_running:
            logger.error(f"❌ Бот {self.user_id} не запущен")
            return 0, 1
        
        # Получаем подписчиков из базы данных
        from database import Database
        db = Database()
        users = db.get_users_for_bot(self.user_id)
        
        logger.info(f"📤 Начинаем рассылку для бота {self.user_id}, найдено {len(users)} подписчиков")
        
        for user in users:
            user_id = user['id']
            try:
                await self.application.bot.send_message(chat_id=user_id, text=message)
                success_count += 1
                logger.info(f"✅ Сообщение отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки сообщения пользователю {user_id}: {e}")
                failed_count += 1
        
        logger.info(f"📊 Рассылка завершена: {success_count} успешно, {failed_count} ошибок")
        return success_count, failed_count
    
    async def send_file_to_user(self, user_id: int, file_path: str, filename: str, caption: str = ""):
        """Отправка файла конкретному пользователю"""
        try:
            with open(file_path, 'rb') as file:
                await self.application.bot.send_document(
                    chat_id=user_id,
                    document=file,
                    filename=filename,
                    caption=caption
                )
            logger.info(f"✅ Файл {filename} отправлен пользователю {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки файла пользователю {user_id}: {e}")
            return False
    
    async def send_broadcast_file(self, file_path: str, filename: str, caption: str = "") -> Tuple[int, int]:
        """Отправка файла всем подписчикам"""
        success_count = 0
        failed_count = 0
        
        # Получаем подписчиков из базы данных
        from database import Database
        db = Database()
        users = db.get_users_for_bot(self.user_id)
        
        for user in users:
            user_id = user['id']
            try:
                with open(file_path, 'rb') as file:
                    await self.application.bot.send_document(
                        chat_id=user_id,
                        document=file,
                        filename=filename,
                        caption=caption
                    )
                success_count += 1
                logger.info(f"✅ Файл {filename} отправлен пользователю {user_id}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки файла пользователю {user_id}: {e}")
                failed_count += 1
        
        return success_count, failed_count

class UserBotManager:
    """Менеджер всех пользовательских ботов"""
    
    def __init__(self):
        self.user_bots: Dict[int, UserBot] = {}
        self.lock = threading.Lock()
        
    def add_bot(self, user_id: int, bot_token: str, bot_username: str, welcome_message: str, start_command: str) -> bool:
        """Добавление нового бота"""
        try:
            with self.lock:
                # Останавливаем существующий бот если есть
                if user_id in self.user_bots:
                    self.stop_bot(user_id)
                
                # Создаем новый бот
                user_bot = UserBot(user_id, bot_token, bot_username, welcome_message, start_command)
                self.user_bots[user_id] = user_bot
                
                # Запускаем бота в отдельном потоке
                threading.Thread(target=self._run_bot, args=(user_id,), daemon=True).start()
                
                logger.info(f"✅ Бот пользователя {user_id} добавлен в менеджер")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления бота пользователя {user_id}: {e}")
            return False
    
    def _run_bot(self, user_id: int):
        """Запуск бота в отдельном потоке"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            user_bot = self.user_bots.get(user_id)
            if user_bot:
                loop.run_until_complete(user_bot.start())
                loop.run_forever()
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота пользователя {user_id}: {e}")
    
    def stop_bot(self, user_id: int) -> bool:
        """Остановка бота пользователя"""
        try:
            with self.lock:
                if user_id in self.user_bots:
                    user_bot = self.user_bots[user_id]
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(user_bot.stop())
                    loop.close()
                    
                    del self.user_bots[user_id]
                    logger.info(f"🛑 Бот пользователя {user_id} остановлен")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота пользователя {user_id}: {e}")
            return False
    
    def get_bot(self, user_id: int) -> Optional[UserBot]:
        """Получение бота пользователя"""
        return self.user_bots.get(user_id)
    
    def get_all_bots(self) -> Dict[int, UserBot]:
        """Получение всех ботов"""
        return self.user_bots.copy()
    
    def get_total_subscribers(self) -> int:
        """Общее количество подписчиков всех ботов"""
        total = 0
        for bot in self.user_bots.values():
            total += bot.get_subscribers_count()
        return total
    
    def reload_bot(self, user_id: int) -> bool:
        """Перезагрузка бота пользователя"""
        try:
            # Получаем настройки из базы данных
            from database import Database
            db = Database()
            user_settings = db.get_user_settings(user_id)
            
            if user_settings and user_settings.get('bot_token'):
                # Останавливаем старый бот
                self.stop_bot(user_id)
                
                # Запускаем новый с обновленными настройками
                return self.add_bot(
                    user_id,
                    user_settings['bot_token'],
                    user_settings.get('bot_username', ''),
                    user_settings.get('welcome_message', 'Добро пожаловать! 👋'),
                    user_settings.get('start_command', 'Добро пожаловать! Нажмите /help для справки.')
                )
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка перезагрузки бота пользователя {user_id}: {e}")
            return False
    
    def stop_all_bots(self):
        """Остановка всех ботов"""
        try:
            user_ids = list(self.user_bots.keys())
            for user_id in user_ids:
                self.stop_bot(user_id)
            logger.info("🛑 Все боты остановлены")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки всех ботов: {e}")

# Глобальный экземпляр менеджера
bot_manager = UserBotManager()
