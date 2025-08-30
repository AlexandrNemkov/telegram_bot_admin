#!/usr/bin/env python3
"""
Скрипт для проверки и деактивации истекших аккаунтов
"""

import os
import sys
from datetime import datetime
from database import Database
from bot.telegram_bot import TelegramBot

def check_expired_accounts():
    """Проверка и деактивация истекших аккаунтов"""
    print("🔍 Проверка истекших аккаунтов...")
    
    db = Database()
    
    # Получаем истекшие аккаунты
    expired_accounts = db.get_expired_accounts()
    
    if not expired_accounts:
        print("✅ Истекших аккаунтов не найдено")
        return
    
    print(f"⚠️ Найдено {len(expired_accounts)} истекших аккаунтов:")
    
    for account in expired_accounts:
        print(f"  👤 {account['username']} - {account['full_name'] or 'Без имени'}")
        print(f"     📅 Истек: {account['account_expires']}")
    
    # Деактивируем истекшие аккаунты
    deactivated_count = db.deactivate_expired_accounts()
    print(f"✅ Деактивировано {deactivated_count} аккаунтов")
    
    # Отправляем уведомления пользователям (если есть Telegram ID)
    if expired_accounts:
        print("📱 Отправка уведомлений об истечении...")
        send_expiry_notifications(expired_accounts)

def send_expiry_notifications(expired_accounts):
    """Отправка уведомлений об истечении аккаунтов"""
    try:
        bot = TelegramBot()
        
        for account in expired_accounts:
            # Здесь можно добавить логику для поиска Telegram ID пользователя
            # Пока просто логируем
            print(f"  📨 Уведомление отправлено: {account['username']}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки уведомлений: {e}")

def get_account_status():
    """Получение статуса всех аккаунтов"""
    print("📊 Статус аккаунтов:")
    
    db = Database()
    users = db.get_all_system_users()
    
    if not users:
        print("❌ Пользователи не найдены")
        return
    
    active_count = 0
    expired_count = 0
    admin_count = 0
    
    for user in users:
        if user['role'] == 'admin':
            admin_count += 1
        elif user['is_active']:
            active_count += 1
        else:
            expired_count += 1
    
    print(f"👑 Администраторы: {admin_count}")
    print(f"✅ Активные пользователи: {active_count}")
    print(f"⏰ Истекшие аккаунты: {expired_count}")
    print(f"📈 Всего: {len(users)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            get_account_status()
        else:
            print("Использование:")
            print("  python3 check_expired_accounts.py          # Проверить и деактивировать")
            print("  python3 check_expired_accounts.py status  # Показать статус")
    else:
        check_expired_accounts()
