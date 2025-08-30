import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import Config
import json
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_TOKEN
        self.subscribers = set()
        self.welcome_message = "Добро пожаловать! 👋"
        self.welcome_pdf_path = None
        self.load_data()
        
    def load_data(self):
        """Загрузка данных из файлов"""
        try:
            if os.path.exists('data/subscribers.json'):
                with open('data/subscribers.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subscribers = set(data.get('subscribers', []))
            
            if os.path.exists('data/settings.json'):
                with open('data/settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.welcome_message = settings.get('welcome_message', self.welcome_message)
                    self.welcome_pdf_path = settings.get('welcome_pdf_path')
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
    
    def save_data(self):
        """Сохранение данных в файлы"""
        try:
            # Создаем папку data если её нет
            os.makedirs('data', exist_ok=True)
            
            # Сохраняем подписчиков
            subscribers_file = 'data/subscribers.json'
            with open(subscribers_file, 'w', encoding='utf-8') as f:
                json.dump({'subscribers': list(self.subscribers)}, f, ensure_ascii=False, indent=2)
            logger.info(f"Подписчики сохранены в {subscribers_file}: {len(self.subscribers)} пользователей")
                
            # Сохраняем настройки
            settings_file = 'data/settings.json'
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'welcome_message': self.welcome_message,
                    'welcome_pdf_path': self.welcome_pdf_path
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Настройки сохранены в {settings_file}")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or f"user_{user_id}"
        
        # Добавляем пользователя в подписчики
        self.subscribers.add(user_id)
        logger.info(f"Добавлен подписчик: {user_id} ({username})")
        
        # Сохраняем данные
        self.save_data()
        logger.info(f"Данные сохранены. Всего подписчиков: {len(self.subscribers)}")
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(self.welcome_message)
        
        # Если есть PDF файл, отправляем его
        if self.welcome_pdf_path and os.path.exists(self.welcome_pdf_path):
            try:
                logger.info(f"Отправляем PDF файл пользователю {user_id}: {self.welcome_pdf_path}")
                
                # Используем прямой API для отправки документа
                success = self.send_document_to_user(user_id, self.welcome_pdf_path, "welcome.pdf", "Добро пожаловать! 📄")
                
                if success:
                    logger.info(f"PDF файл успешно отправлен пользователю {user_id}")
                else:
                    logger.error(f"Ошибка отправки PDF файла пользователю {user_id}")
                    
            except Exception as e:
                logger.error(f"Ошибка отправки PDF: {e}")
        
        # Создаем клавиатуру с основными командами
        keyboard = [
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')],
            [InlineKeyboardButton("📞 Связаться с поддержкой", callback_data='support')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def test_pdf_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Тестирование отправки PDF файла"""
        user_id = update.effective_user.id
        
        if self.welcome_pdf_path and os.path.exists(self.welcome_pdf_path):
            await update.message.reply_text("📄 Отправляю PDF файл...")
            
            success = self.send_document_to_user(user_id, self.welcome_pdf_path, "welcome.pdf", "Тестовый PDF файл 📄")
            
            if success:
                await update.message.reply_text("✅ PDF файл успешно отправлен!")
            else:
                await update.message.reply_text("❌ Ошибка отправки PDF файла")
        else:
            await update.message.reply_text("❌ PDF файл не найден. Загрузите его в настройках веб-интерфейса.")

    async def check_pdf_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка текущего PDF файла"""
        user_id = update.effective_user.id
        
        if self.welcome_pdf_path:
            if os.path.exists(self.welcome_pdf_path):
                file_size = os.path.getsize(self.welcome_pdf_path)
                filename = os.path.basename(self.welcome_pdf_path)
                
                await update.message.reply_text(
                    f"📄 Текущий PDF файл:\n"
                    f"Имя: {filename}\n"
                    f"Размер: {file_size} байт\n"
                    f"Путь: {self.welcome_pdf_path}"
                )
            else:
                await update.message.reply_text(
                    f"❌ PDF файл не найден по пути:\n{self.welcome_pdf_path}"
                )
        else:
            await update.message.reply_text("❌ PDF файл не настроен")

    async def delete_pdf_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаление PDF файла"""
        user_id = update.effective_user.id
        
        if self.welcome_pdf_path and os.path.exists(self.welcome_pdf_path):
            try:
                old_file = self.welcome_pdf_path
                old_size = os.path.getsize(old_file)
                old_filename = os.path.basename(old_file)
                
                # Удаляем файл физически
                os.remove(old_file)
                
                # Очищаем путь в настройках
                self.welcome_pdf_path = None
                self.save_data()
                
                await update.message.reply_text(
                    f"🗑️ PDF файл удален:\n"
                    f"Имя: {old_filename}\n"
                    f"Размер: {old_size} байт\n"
                    f"Путь: {old_file}"
                )
                logger.info(f"PDF файл удален пользователем {user_id}: {old_file}")
                
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка удаления файла: {e}")
                logger.error(f"Ошибка удаления PDF файла: {e}")
        else:
            await update.message.reply_text("❌ PDF файл не найден")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """
🤖 Доступные команды:
/start - Начать работу с ботом
/help - Показать эту справку
/status - Статус вашей подписки

Для получения дополнительной информации обратитесь к администратору.
        """
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        user_id = update.effective_user.id
        if user_id in self.subscribers:
            await update.message.reply_text("✅ Вы подписаны на бота!")
        else:
            await update.message.reply_text("❌ Вы не подписаны на бота. Используйте /start для подписки.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'help':
            await self.help_command(update, context)
        elif query.data == 'support':
            await query.edit_message_text("📞 Для связи с поддержкой напишите администратору.")
    
    async def broadcast_message(self, message_text: str, context: ContextTypes.DEFAULT_TYPE):
        """Отправка сообщения всем подписчикам"""
        success_count = 0
        failed_count = 0
        
        for user_id in self.subscribers:
            try:
                await context.bot.send_message(chat_id=user_id, text=message_text)
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
                failed_count += 1
        
        return success_count, failed_count
    
    def update_welcome_message(self, new_message: str):
        """Обновление приветственного сообщения"""
        self.welcome_message = new_message
        self.save_data()
    
    def update_welcome_pdf(self, pdf_path: str):
        """Обновление приветственного PDF файла"""
        try:
            logger.info(f"Обновляем путь к файлу: {pdf_path}")
            
            # Если есть старый файл, удаляем его физически
            if self.welcome_pdf_path and os.path.exists(self.welcome_pdf_path):
                try:
                    old_file = self.welcome_pdf_path
                    os.remove(old_file)
                    logger.info(f"Старый файл удален: {old_file}")
                except Exception as e:
                    logger.error(f"Ошибка удаления старого файла {old_file}: {e}")
            
            # Обновляем путь к новому файлу
            self.welcome_pdf_path = pdf_path
            file_size = os.path.getsize(pdf_path)
            
            # Сохраняем в файл
            self.save_data()
            # Сохраняем настройки в файл
            self.save_data()
            # Сохраняем настройки в файл
            self.save_data()
            
            logger.info(f"Файл успешно обновлен: {pdf_path}, размер: {file_size} байт")
            
        except Exception as e:
            logger.error(f"Ошибка обновления файла: {e}")
            raise
            raise
    
    def send_document_to_user(self, user_id: int, file_path: str, filename: str, caption: str = ""):
        """Отправка документа конкретному пользователю"""
        try:
            import requests
            
            logger.info(f"Начинаем отправку документа пользователю {user_id}")
            logger.info(f"Файл: {file_path}, размер: {os.path.getsize(file_path)} байт")
            
            url = f"https://api.telegram.org/bot{self.token}/sendDocument"
            
            # Читаем файл
            with open(file_path, 'rb') as file:
                files = {
                    'document': (filename, file, 'application/pdf')
                }
                data = {
                    'chat_id': user_id,
                    'caption': caption
                }
                
                logger.info(f"Отправляем запрос к Telegram API: {url}")
                response = requests.post(url, data=data, files=files, timeout=30)
                
                logger.info(f"Получен ответ: статус {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Ответ API: {result}")
                    
                    if result.get('ok'):
                        logger.info(f"Документ успешно отправлен пользователю {user_id}")
                        return True
                    else:
                        logger.error(f"Telegram API ошибка: {result}")
                        return False
                else:
                    logger.error(f"HTTP ошибка {response.status_code}: {response.text}")
                    return False
            
        except ImportError:
            logger.error("Модуль requests не установлен. Устанавливаем...")
            try:
                import subprocess
                subprocess.check_call(['pip', 'install', 'requests'])
                logger.info("requests установлен, повторяем отправку...")
                return self.send_document_to_user(user_id, file_path, filename, caption)
            except Exception as e:
                logger.error(f"Не удалось установить requests: {e}")
                return False
        except Exception as e:
            logger.error(f"Ошибка отправки документа пользователю {user_id}: {e}")
            return False

    def send_message_to_user(self, user_id: int, message: str):
        """Отправка сообщения конкретному пользователю"""
        try:
            import requests
            
            logger.info(f"Отправляем сообщение пользователю {user_id}: {message[:50]}...")
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Сообщение успешно отправлено пользователю {user_id}")
                    return True
                else:
                    logger.error(f"Telegram API ошибка: {result}")
                    return False
            else:
                logger.error(f"HTTP ошибка {response.status_code}: {response.text}")
                return False
                
        except ImportError:
            logger.error("Модуль requests не установлен. Устанавливаем...")
            try:
                import subprocess
                subprocess.check_call(['pip', 'install', 'requests'])
                logger.info("requests установлен, повторяем отправку...")
                return self.send_message_to_user(user_id, message)
            except Exception as e:
                logger.error(f"Не удалось установить requests: {e}")
                return False
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            return False

    def get_subscribers_count(self):
        """Получение количества подписчиков"""
        return len(self.subscribers)
    
    def get_subscribers_list(self):
        """Получение списка подписчиков"""
        return list(self.subscribers)
    
    async def run_async(self):
        """Асинхронный запуск бота"""
        if not self.token:
            logger.error("TELEGRAM_TOKEN не установлен!")
            return
        
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Добавляем обработчики
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(CommandHandler("test_pdf", self.test_pdf_command))
            application.add_handler(CommandHandler("check_pdf", self.check_pdf_command))
            application.add_handler(CommandHandler("delete_pdf", self.delete_pdf_command)) # Добавляем обработчик для удаления PDF
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Бот запущен!")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

    def run(self):
        """Запуск бота (основной метод)"""
        if not self.token:
            logger.error("TELEGRAM_TOKEN не установлен!")
            return
        
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Добавляем обработчики
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(CommandHandler("test_pdf", self.test_pdf_command))
            application.add_handler(CommandHandler("check_pdf", self.check_pdf_command))
            application.add_handler(CommandHandler("delete_pdf", self.delete_pdf_command)) # Добавляем обработчик для удаления PDF
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Бот запущен!")
            
            # Добавляем обработку ошибок
            try:
                application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            except Exception as e:
                if "Conflict" in str(e) or "getUpdates" in str(e):
                    logger.error(f"Конфликт с другим экземпляром бота: {e}")
                    logger.info("Попробуйте остановить другие экземпляры бота")
                    raise
                else:
                    logger.error(f"Ошибка запуска бота: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
