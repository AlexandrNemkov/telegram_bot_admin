#!/bin/bash

# Скрипт для настройки GitHub репозитория

echo "�� Настройка GitHub репозитория для Telegram Bot Admin Panel"
echo ""

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите git и попробуйте снова."
    exit 1
fi

# Проверка инициализации git
if [ ! -d ".git" ]; then
    echo "📁 Инициализация Git репозитория..."
    git init
    echo "✅ Git репозиторий инициализирован"
else
    echo "✅ Git репозиторий уже существует"
fi

# Создание .gitignore если не существует
if [ ! -f ".gitignore" ]; then
    echo "📝 Создание .gitignore..."
    cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# Environment variables
.env
.env.local
.env.production

# Data files
data/
uploads/
*.db
*.sqlite

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
GITIGNORE
    echo "✅ .gitignore создан"
fi

# Добавление всех файлов
echo "📦 Добавление файлов в Git..."
git add .

# Первый коммит
echo "💾 Создание первого коммита..."
git commit -m "Initial commit: Telegram Bot Admin Panel

- Telegram Bot с командами /start, /help, /status
- Веб-интерфейс на Flask с Bootstrap
- Система рассылок и управления подписчиками
- Загрузка PDF файлов
- Настройки приветственного сообщения
- Nginx конфигурация для домена
- Systemd сервис для автозапуска
- Cloud-init скрипт для автоматического развертывания
- Полная документация и скрипты развертывания"

echo ""
echo "🌐 Теперь создайте репозиторий на GitHub:"
echo "1. Перейдите на https://github.com/new"
echo "2. Введите имя репозитория: telegram_bot_admin"
echo "3. Сделайте репозиторий публичным"
echo "4. НЕ инициализируйте с README, .gitignore или лицензией"
echo "5. Нажмите 'Create repository'"
echo ""

read -p "После создания репозитория нажмите Enter для продолжения..."

echo ""
echo "📤 Настройка удаленного репозитория..."
echo "Введите ваше имя пользователя на GitHub:"
read -p "GitHub username: " github_username

# Добавление удаленного репозитория
git remote add origin https://github.com/$github_username/telegram_bot_admin.git

# Отправка в GitHub
echo "🚀 Отправка проекта в GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Проект успешно загружен в GitHub!"
echo "🌐 URL: https://github.com/$github_username/telegram_bot_admin"
echo ""
echo "📋 Теперь вы можете:"
echo "1. Вставить cloud-init скрипт при создании VM"
echo "2. Заменить YOUR_USERNAME на $github_username в скрипте"
echo "3. Заменить YOUR_TELEGRAM_TOKEN на ваш токен"
echo "4. Создать VM - все настроится автоматически!"
echo ""
echo "🎉 Готово к автоматическому развертыванию!"
