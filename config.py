import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    MAX_CONTENT_LENGTH_STR = '50MB'
    
    # Дополнительные настройки для загрузки
    UPLOAD_EXTENSIONS = {
        # Документы
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        # Изображения
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        # Видео (популярные форматы)
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm',
        # Аудио
        '.mp3', '.wav', '.ogg', '.m4a',
        # Архивы
        '.zip', '.rar', '.7z'
    }
    UPLOAD_MAX_FILES = 5
