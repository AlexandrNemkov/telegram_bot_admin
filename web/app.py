import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
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
                
                for user_id in bot.subscribers:
                    try:
                        # Используем контекст бота для отправки
                        bot.send_message_to_user(user_id, message)
                        success_count += 1
                    except Exception as e:
                        print(f"Ошибка отправки пользователю {user_id}: {e}")
                        failed_count += 1
                
                if success_count > 0:
                    flash(f'Сообщение отправлено {success_count} подписчикам!', 'success')
                if failed_count > 0:
                    flash(f'Ошибка отправки {failed_count} подписчикам', 'error')
                    
            except Exception as e:
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
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(pdf_path)
            bot.update_welcome_pdf(pdf_path)
            flash('PDF файл загружен!', 'success')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html', 
                         welcome_message=bot.welcome_message,
                         has_pdf=bool(bot.welcome_pdf_path))

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

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
