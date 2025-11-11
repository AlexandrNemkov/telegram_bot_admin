#!/bin/bash
set -euo pipefail

# Устанавливает/обновляет все systemd-сервисы: веб/панель (если нужна), админ-бот, менеджер пользовательских ботов

if [ "$EUID" -ne 0 ]; then
  echo "❌ Запустите скрипт от root: sudo $0"
  exit 1
fi

PROJECT_USER="telegram_bot_admin"
PROJECT_GROUP="telegram_bot_admin"
PROJECT_HOME="/home/${PROJECT_USER}"
VENV_DIR="${PROJECT_HOME}/venv"
SYSTEMD_DIR="/etc/systemd/system"

echo "👤 Проверка пользователя ${PROJECT_USER}..."
if ! id "${PROJECT_USER}" &>/dev/null; then
  useradd -m -s /bin/bash "${PROJECT_USER}"
  echo "${PROJECT_USER}:botpassword123" | chpasswd
fi

echo "📦 Директории и права..."
chown -R "${PROJECT_USER}:${PROJECT_GROUP}" "${PROJECT_HOME}" || true
mkdir -p "${PROJECT_HOME}/logs" "${PROJECT_HOME}/data" "${PROJECT_HOME}/uploads"
chown -R "${PROJECT_USER}:${PROJECT_GROUP}" "${PROJECT_HOME}/logs" "${PROJECT_HOME}/data" "${PROJECT_HOME}/uploads"

echo "🐍 Виртуальное окружение..."
if [ ! -d "${VENV_DIR}" ]; then
  su - "${PROJECT_USER}" -c "cd ${PROJECT_HOME} && python3 -m venv venv"
fi
su - "${PROJECT_USER}" -c "source ${VENV_DIR}/bin/activate && pip install --upgrade pip && pip install -r ${PROJECT_HOME}/requirements.txt"

echo "🗂 Копирование unit-файлов..."
install -m 0644 telegram-bot.service "${SYSTEMD_DIR}/" || true
install -m 0644 admin-bot.service "${SYSTEMD_DIR}/"
install -m 0644 user-bots.service "${SYSTEMD_DIR}/"

echo "🔄 Перезагрузка systemd..."
systemctl daemon-reload

echo "🔧 Включение автозапуска..."
systemctl enable admin-bot.service
systemctl enable user-bots.service
# Веб-сервис оставляем опциональным:
if [ -f "${SYSTEMD_DIR}/telegram-bot.service" ]; then
  systemctl enable telegram-bot.service || true
fi

echo "🚀 Запуск сервисов..."
systemctl restart admin-bot.service
systemctl restart user-bots.service
# Не трогаем веб, так как веб-версия заморожена

echo "✅ Готово. Проверьте статусы:"
echo "  journalctl -u admin-bot.service -f"
echo "  journalctl -u user-bots.service -f"


