#!/bin/bash

# Скрипт управления Telegram Bot сервисом

SERVICE_NAME="telegram-bot.service"

show_help() {
    echo "🤖 Управление Telegram Bot сервисом"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить бота"
    echo "  stop      - Остановить бота"
    echo "  restart   - Перезапустить бота"
    echo "  status    - Показать статус"
    echo "  logs      - Показать логи"
    echo "  enable    - Включить автозапуск"
    echo "  disable   - Отключить автозапуск"
    echo "  install   - Установить сервис"
    echo "  uninstall - Удалить сервис"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start    # Запустить бота"
    echo "  $0 status   # Проверить статус"
    echo "  $0 logs     # Посмотреть логи"
}

check_service() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo "❌ Сервис $SERVICE_NAME не установлен!"
        echo "Установите его командой: $0 install"
        exit 1
    fi
}

case "$1" in
    start)
        echo "🚀 Запуск Telegram Bot..."
        check_service
        sudo systemctl start $SERVICE_NAME
        echo "✅ Бот запущен!"
        ;;
    stop)
        echo "🛑 Остановка Telegram Bot..."
        check_service
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Бот остановлен!"
        ;;
    restart)
        echo "🔄 Перезапуск Telegram Bot..."
        check_service
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Бот перезапущен!"
        ;;
    status)
        echo "📊 Статус Telegram Bot..."
        check_service
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    logs)
        echo "📝 Логи Telegram Bot..."
        check_service
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo "🔧 Включение автозапуска..."
        check_service
        sudo systemctl enable $SERVICE_NAME
        echo "✅ Автозапуск включен!"
        ;;
    disable)
        echo "🔧 Отключение автозапуска..."
        check_service
        sudo systemctl disable $SERVICE_NAME
        echo "✅ Автозапуск отключен!"
        ;;
    install)
        echo "📦 Установка сервиса..."
        if [ "$EUID" -ne 0 ]; then
            echo "❌ Для установки нужны права root"
            echo "Используйте: sudo $0 install"
            exit 1
        fi
        ./install_service.sh
        ;;
    uninstall)
        echo "🗑️ Удаление сервиса..."
        if [ "$EUID" -ne 0 ]; then
            echo "❌ Для удаления нужны права root"
            echo "Используйте: sudo $0 uninstall"
            exit 1
        fi
        sudo systemctl stop $SERVICE_NAME
        sudo systemctl disable $SERVICE_NAME
        sudo rm /etc/systemd/system/$SERVICE_NAME
        sudo systemctl daemon-reload
        echo "✅ Сервис удален!"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
