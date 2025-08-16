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
            os.makedirs('data', exist_ok=True)
            
            with open('data/subscribers.json', 'w', encoding='utf-8') as f:
                json.dump({'subscribers': list(self.subscribers)}, f, ensure_ascii=False, indent=2)
                
            with open('data/settings.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'welcome_message': self.welcome_message,
                    'welcome_pdf_path': self.welcome_pdf_path
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or f"user_{user_id}"
        
        # Добавляем пользователя в подписчики
        self.subscribers.add(user_id)
        self.save_data()
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(self.welcome_message)
        
        # Если есть PDF файл, отправляем его
        if self.welcome_pdf_path and os.path.exists(self.welcome_pdf_path):
            try:
                with open(self.welcome_pdf_path, 'rb') as pdf_file:
                    await update.message.reply_document(
                        document=pdf_file,
                        filename='welcome.pdf',
                        caption='Добро пожаловать! 📄'
                    )
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
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Бот запущен!")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

    def run(self):
        """Запуск бота (для обратной совместимости)"""
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
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Запускаем бота
            logger.info("Бот запущен!")
            # Запускаем в текущем event loop
            asyncio.run(application.run_polling(allowed_updates=Update.ALL_TYPES))
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
