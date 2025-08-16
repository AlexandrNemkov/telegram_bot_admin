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
        self.welcome_pdf_path = pdf_path
        self.save_data()
    
    def send_document_to_user(self, user_id: int, file_path: str, filename: str, caption: str = ""):
        """Отправка документа конкретному пользователю"""
        try:
            import aiohttp
            import asyncio
            
            # Создаем временный event loop для отправки
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def send_document():
                async with aiohttp.ClientSession() as session:
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
                        
                        async with session.post(url, data=data, files=files) as response:
                            if response.status == 200:
                                result = await response.json()
                                if result.get('ok'):
                                    logger.info(f"Документ отправлен пользователю {user_id}")
                                    return True
                                else:
                                    logger.error(f"Telegram API ошибка при отправке документа: {result}")
                                    return False
                            else:
                                logger.error(f"HTTP ошибка при отправке документа: {response.status}")
                                return False
            
            # Запускаем отправку
            result = loop.run_until_complete(send_document())
            loop.close()
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки документа пользователю {user_id}: {e}")
            return False

    def send_message_to_user(self, user_id: int, message: str):
        """Отправка сообщения конкретному пользователю"""
        try:
            import aiohttp
            import asyncio
            
            # Создаем временный event loop для отправки
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def send_message():
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('ok'):
                                logger.info(f"Сообщение отправлено пользователю {user_id}")
                                return True
                            else:
                                logger.error(f"Telegram API ошибка: {result}")
                                return False
                        else:
                            logger.error(f"HTTP ошибка: {response.status}")
                            return False
            
            # Запускаем отправку
            result = loop.run_until_complete(send_message())
            loop.close()
            return result
            
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
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Бот запущен!")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
