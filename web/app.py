import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from translit import transliterate_russian
from config import Config
import sys
import os

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

# Инициализация бота
bot = TelegramBot()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == Config.ADMIN_USERNAME:
        return User(user_id, Config.ADMIN_USERNAME)
    return None

def check_auth(username, password):
    return username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD

@app.route('/')
@login_required
def dashboard():
    subscribers_count = bot.get_subscribers_count()
    return render_template('dashboard.html', subscribers_count=subscribers_count)

@app.route('/login', methods=['GET', 'POST'])
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
    if request.method == 'POST':
        welcome_message = request.form.get('welcome_message')
        pdf_file = request.files.get('welcome_pdf')
        
        if welcome_message:
            bot.update_welcome_message(welcome_message)
            flash('Приветственное сообщение обновлено!', 'success')
        
        if pdf_file and pdf_file.filename:
            try:
                print(f"Начинаем загрузку файла: {pdf_file.filename}")
                
                # Проверяем размер файла
                if pdf_file.content_length and pdf_file.content_length > app.config['MAX_CONTENT_LENGTH']:
                    flash(f'Файл слишком большой! Максимальный размер: {app.config["MAX_CONTENT_LENGTH_STR"]}', 'error')
                    return redirect(url_for('settings'))
                
                # Проверяем расширение файла
                filename = secure_filename(pdf_file.filename).replace("-", "_").replace(" ", "_")
                # Транслитерация русских символов
                
                filename = transliterate_russian(secure_filename(pdf_file.filename)).replace("-", "_").replace(" ", "_")
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    flash(f'Неподдерживаемый тип файла! Разрешены: {", ".join(app.config["UPLOAD_EXTENSIONS"])}', 'error')
                    return redirect(url_for('settings'))
                
                # Создаем папку uploads если её нет
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Проверяем, есть ли уже загруженный файл
                old_file_info = ""
                if bot.welcome_pdf_path and os.path.exists(bot.welcome_pdf_path):
                    old_size = os.path.getsize(bot.welcome_pdf_path)
                    old_filename = os.path.basename(bot.welcome_pdf_path)
                    old_file_info = f" (заменяет {old_filename}, {old_size} байт)"
                
                # Сохраняем файл
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pdf_file.save(pdf_path)
                
                print(f"Файл сохранен: {pdf_path}")
                print(f"Размер файла: {os.path.getsize(pdf_path)} байт")
                
                # Обновляем путь к файлу в боте
                try:
                    # Просто обновляем путь - если файл физически загружен, значит все ок
                    bot.update_welcome_pdf(pdf_path)
                    
                    flash(f'Файл {filename} успешно загружен и сохранен!{old_file_info}', 'success')
                    print(f"Файл успешно обновлен в боте: {bot.welcome_pdf_path}")
                    
                except Exception as e:
                    # Если произошла ошибка при обновлении настроек
                    flash(f'Файл {filename} загружен, но не удалось обновить настройки бота. Ошибка: {e}', 'error')
                    print(f"Ошибка обновления настроек бота: {e}")
                    
            except Exception as e:
                flash(f'Ошибка загрузки файла: {e}', 'error')
                print(f"Ошибка загрузки файла: {e}")
        
        return redirect(url_for('settings'))
    
    # Показываем информацию о лимитах
    max_file_size = app.config.get('MAX_CONTENT_LENGTH_STR', '50MB')
    allowed_extensions = ', '.join(app.config.get('UPLOAD_EXTENSIONS', []))
    
    return render_template('settings.html', 
                         welcome_message=bot.welcome_message,
                         has_pdf=bool(bot.welcome_pdf_path),
                         max_file_size=max_file_size,
                         allowed_extensions=allowed_extensions)

@app.route('/subscribers')
@login_required
def subscribers():
    subscribers_list = bot.get_subscribers_list()
    return render_template('subscribers.html', subscribers=subscribers_list)

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
        
        messages = bot.get_user_messages(user_id)
        logger.info(f"Получено {len(messages)} сообщений для пользователя {user_id}")
        
        # Форматируем сообщения для фронтенда
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg['id'],
                'text': msg['text'],
                'timestamp': msg['timestamp'],
                'is_from_user': msg['is_from_user']
            })
        
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

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
