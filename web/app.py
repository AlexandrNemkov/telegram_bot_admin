import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from translit import transliterate_russian
from config import Config
import sys
from datetime import datetime
from functools import wraps
import time

# Добавляем путь к модулю бота
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bot'))
from telegram_bot import TelegramBot

# Получаем путь к корневой папке проекта (где находится папка templates)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_dir = os.path.join(project_root, 'templates')
static_dir = os.path.join(project_root, 'static')

app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
app.config.from_object(Config)

# Увеличиваем лимит загрузки файлов
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['MAX_CONTENT_LENGTH_STR'] = '50MB'
app.config['UPLOAD_EXTENSIONS'] = {'.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png'}
app.config['UPLOAD_MAX_FILES'] = 5

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Словарь для отслеживания попыток входа
login_attempts = {}

def rate_limit(max_attempts=5, window=300):
    """Декоратор для ограничения попыток входа"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            
            # Очищаем старые попытки
            if ip in login_attempts:
                login_attempts[ip] = [t for t in login_attempts[ip] if now - t < window]
            
            # Проверяем количество попыток
            if ip in login_attempts and len(login_attempts[ip]) >= max_attempts:
                return jsonify({'error': 'Слишком много попыток входа. Попробуйте позже.'}), 429
            
            # Добавляем текущую попытку
            if ip not in login_attempts:
                login_attempts[ip] = []
            login_attempts[ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Инициализация бота
bot = TelegramBot()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя из базы данных"""
    try:
        from database import Database
        db = Database()
        user = db.get_system_user(user_id)
        
        if user and user['is_active']:
            return User(user['id'], user['username'])
        
        return None
        
    except Exception as e:
        print(f"Ошибка загрузки пользователя: {e}")
        # Fallback на старую систему
        if user_id == Config.ADMIN_USERNAME:
            return User(user_id, Config.ADMIN_USERNAME)
        return None

def check_auth(username, password):
    """Проверка аутентификации через базу данных"""
    try:
        from database import Database
        import hashlib
        
        db = Database()
        user = db.get_system_user(username)
        
        if not user:
            return False
        
        # Проверяем активность аккаунта
        if not user['is_active']:
            return False
        
        # Проверяем время истечения
        if user['account_expires'] and user['account_expires'] < datetime.now().isoformat():
            return False
        
        # Проверяем пароль безопасно
        if check_password_hash(user['password_hash'], password):
            # Обновляем время последнего входа
            db.update_last_login(username)
            return True
        
        return False
        
    except Exception as e:
        print(f"Ошибка аутентификации: {e}")
        # Fallback на старую систему
        return username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD

@app.route('/')
@login_required
def dashboard():
    subscribers_count = bot.get_subscribers_count()
    return render_template('dashboard.html', subscribers_count=subscribers_count)

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_attempts=5, window=300)
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if check_auth(username, password):
            user = User(username, username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные учетные данные!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast():
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            try:
                # Отправляем сообщение всем подписчикам
                success_count = 0
                failed_count = 0
                
                print(f"Начинаем рассылку сообщения: {message}")
                print(f"Всего подписчиков: {len(bot.subscribers)}")
                
                for user_id in bot.subscribers:
                    try:
                        print(f"Отправляем сообщение пользователю {user_id}")
                        result = bot.send_message_to_user(user_id, message)
                        if result:
                            success_count += 1
                            print(f"✅ Сообщение отправлено пользователю {user_id}")
                        else:
                            failed_count += 1
                            print(f"❌ Ошибка отправки пользователю {user_id}")
                    except Exception as e:
                        failed_count += 1
                        print(f"❌ Исключение при отправке пользователю {user_id}: {e}")
                
                print(f"Рассылка завершена: {success_count} успешно, {failed_count} ошибок")
                
                if success_count > 0:
                    flash(f'Сообщение отправлено {success_count} подписчикам!', 'success')
                if failed_count > 0:
                    flash(f'Ошибка отправки {failed_count} подписчикам', 'error')
                    
            except Exception as e:
                print(f"Общая ошибка рассылки: {e}")
                flash(f'Ошибка рассылки: {e}', 'error')
            
            return redirect(url_for('broadcast'))
        else:
            flash('Введите текст сообщения!', 'error')
    
    return render_template('broadcast.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Страница настроек (индивидуальная для каждого пользователя)"""
    try:
        from database import Database
        db = Database()
        
        if request.method == 'POST':
            welcome_message = request.form.get('welcome_message')
            pdf_file = request.files.get('welcome_pdf')
            
            if welcome_message:
                if db.update_user_welcome_message(current_user.id, welcome_message):
                    flash('Приветственное сообщение обновлено!', 'success')
                else:
                    flash('Ошибка обновления сообщения!', 'error')
            
            if pdf_file and pdf_file.filename:
                try:
                    print(f"Начинаем загрузку файла: {pdf_file.filename}")
                    
                    # Проверяем размер файла
                    if pdf_file.content_length and pdf_file.content_length > app.config['MAX_CONTENT_LENGTH']:
                        flash(f'Файл слишком большой! Максимальный размер: {app.config["MAX_CONTENT_LENGTH_STR"]}', 'error')
                        return redirect(url_for('settings'))
                    
                    # Проверяем расширение файла
                    filename = secure_filename(pdf_file.filename)
                    filename = transliterate_russian(filename).replace("-", "_").replace(" ", "_")
                    file_ext = os.path.splitext(filename)[1].lower()
                    
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        flash(f'Неподдерживаемый тип файла! Разрешены: {", ".join(app.config["UPLOAD_EXTENSIONS"])}', 'error')
                        return redirect(url_for('settings'))
                    
                    # Создаем папку uploads если её нет
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Сохраняем файл
                    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    pdf_file.save(pdf_path)
                    
                    # Обновляем путь к файлу в базе данных
                    if db.update_user_welcome_pdf(current_user.id, pdf_path):
                        flash(f'Файл {filename} успешно загружен!', 'success')
                    else:
                        flash('Ошибка обновления пути к файлу!', 'error')
                        
                except Exception as e:
                    flash(f'Ошибка загрузки файла: {e}', 'error')
            
            return redirect(url_for('settings'))
        
        # GET запрос - показать настройки
        user_settings = db.get_user_settings(current_user.id)
        
        # Показываем информацию о лимитах
        max_file_size = app.config.get('MAX_CONTENT_LENGTH_STR', '50MB')
        allowed_extensions = ', '.join(app.config.get('UPLOAD_EXTENSIONS', []))
        
        return render_template('settings.html', 
                             settings=user_settings,
                             max_file_size=max_file_size,
                             allowed_extensions=allowed_extensions)
                             
    except Exception as e:
        flash(f'Ошибка загрузки настроек: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/subscribers')
@login_required
def subscribers():
    try:
        from bot.telegram_bot import TelegramBot
        bot = TelegramBot()
        
        # Получаем подробную информацию о пользователях
        users = bot.get_users_info()
        
        return render_template('subscribers.html', subscribers=users)
    except Exception as e:
        flash(f'Ошибка загрузки подписчиков: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/send_broadcast', methods=['POST'])
@login_required
def send_broadcast():
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    try:
        # Отправляем сообщение всем подписчикам
        success_count = 0
        failed_count = 0
        
        for user_id in bot.subscribers:
            try:
                bot.send_message_to_user(user_id, message)
                success_count += 1
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")
                failed_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Сообщение отправлено {success_count} подписчикам',
            'success_count': success_count,
            'failed_count': failed_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users')
@login_required
def users():
    """Страница управления пользователями системы"""
    try:
        from database import Database
        db = Database()
        
        # Получаем всех пользователей системы
        system_users = db.get_all_system_users()
        
        return render_template('users.html', users=system_users)
    except Exception as e:
        flash(f'Ошибка загрузки пользователей: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/dialogs')
@login_required
def dialogs():
    """Страница диалогов с пользователями"""
    try:
        from bot.telegram_bot import TelegramBot
        bot = TelegramBot()
        
        # Получаем подробную информацию о пользователях
        users = bot.get_users_info()
        
        # Добавляем время последнего сообщения (пока не реализовано)
        for user in users:
            user['last_message_time'] = None
        
        return render_template('dialogs.html', users=users)
    except Exception as e:
        flash(f'Ошибка загрузки диалогов: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/messages/<int:user_id>')
@login_required
def get_messages(user_id):
    """Получение сообщений для конкретного пользователя"""
    try:
        from bot.telegram_bot import TelegramBot
        import logging
        logger = logging.getLogger(__name__)
        
        bot = TelegramBot()
        logger.info(f"Запрашиваем сообщения для пользователя {user_id}")
        
        # Проверяем доступ к базе данных
        try:
            messages = bot.get_user_messages(user_id)
            logger.info(f"Получено {len(messages)} сообщений для пользователя {user_id}")
        except Exception as db_error:
            logger.error(f"Ошибка доступа к базе данных: {db_error}")
            return jsonify({'success': False, 'error': f'Ошибка БД: {str(db_error)}'})
        
        # Форматируем сообщения для фронтенда
        formatted_messages = []
        for msg in messages:
            try:
                formatted_messages.append({
                    'id': msg['id'],
                    'text': msg['text'],
                    'timestamp': msg['timestamp'],
                    'is_from_user': msg['is_from_user']
                })
            except KeyError as key_error:
                logger.error(f"Ошибка форматирования сообщения: {key_error}, сообщение: {msg}")
                continue
        
        logger.info(f"Отправляем {len(formatted_messages)} отформатированных сообщений")
        return jsonify({'success': True, 'messages': formatted_messages})
    except Exception as e:
        logger.error(f"Ошибка получения сообщений для пользователя {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send_message', methods=['POST'])
@login_required
def send_message():
    """Отправка сообщения пользователю"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return jsonify({'success': False, 'error': 'Неверные параметры'})
        
        from bot.telegram_bot import TelegramBot
        bot = TelegramBot()
        
        # Отправляем сообщение
        result = bot.send_message_to_user(user_id, message)
        
        if result:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Ошибка отправки'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ===== API ДЛЯ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ =====

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    """Создание нового пользователя"""
    try:
        from database import Database
        import hashlib
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        full_name = data.get('full_name')
        email = data.get('email')
        account_expires = data.get('account_expires')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username и пароль обязательны'})
        
        db = Database()
        
        # Проверяем что пользователь не существует
        existing_user = db.get_system_user(username)
        if existing_user:
            return jsonify({'success': False, 'error': 'Пользователь с таким username уже существует'})
        
        # Хешируем пароль безопасно
        password_hash = generate_password_hash(password)
        
        # Создаем пользователя
        if db.create_system_user(username, password_hash, role, full_name, email, account_expires, current_user.id):
            return jsonify({'success': True, 'message': 'Пользователь создан успешно'})
        else:
            return jsonify({'success': False, 'error': 'Ошибка создания пользователя'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/users/<username>/password', methods=['PUT'])
@login_required
def update_user_password(username):
    """Обновление пароля пользователя"""
    try:
        from database import Database
        import hashlib
        
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'success': False, 'error': 'Новый пароль обязателен'})
        
        db = Database()
        
        # Хешируем новый пароль безопасно
        password_hash = generate_password_hash(new_password)
        
        # Обновляем пароль
        if db.update_system_user_password(username, password_hash):
            return jsonify({'success': True, 'message': 'Пароль обновлен успешно'})
        else:
            return jsonify({'success': False, 'error': 'Ошибка обновления пароля'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/users/<username>/expiry', methods=['PUT'])
@login_required
def update_user_expiry(username):
    """Обновление времени истечения аккаунта"""
    try:
        from database import Database
        
        data = request.get_json()
        account_expires = data.get('account_expires')
        
        db = Database()
        
        # Обновляем время истечения
        if db.update_system_user_expiry(username, account_expires):
            return jsonify({'success': True, 'message': 'Время истечения обновлено успешно'})
        else:
            return jsonify({'success': False, 'error': 'Ошибка обновления времени истечения'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
