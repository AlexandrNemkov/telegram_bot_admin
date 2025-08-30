#!/usr/bin/env python3
"""
Скрипт для обновления информации о пользователях из Telegram API
"""

import os
import sys
import requests
from database import Database
from config import Config

def update_user_info():
    """Обновление информации о пользователях из Telegram API"""
    # Проверяем токен
    if not hasattr(Config, 'TELEGRAM_TOKEN') or not Config.TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN не найден в config.py")
        return
    
    token = Config.TELEGRAM_TOKEN
    db = Database()
    
    print("🔍 Получаем список пользователей из БД...")
    users = db.get_all_users()
    
    if not users:
        print("❌ Пользователи не найдены в БД")
        return
    
    print(f"👥 Найдено {len(users)} пользователей")
    
    updated_count = 0
    error_count = 0
    
    for user in users:
        user_id = user['id']
        print(f"\n🔄 Обновляем информацию для пользователя {user_id}...")
        
        try:
            # Получаем информацию из Telegram API
            url = f"https://api.telegram.org/bot{token}/getChat"
            data = {'chat_id': user_id}
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    user_data = result['result']
                    
                    username = user_data.get('username')
                    first_name = user_data.get('first_name', '')
                    last_name = user_data.get('last_name', '')
                    
                    # Обновляем в БД
                    if db.add_user(user_id, username, first_name, last_name):
                        print(f"✅ Обновлен: {first_name} {last_name} (@{username})")
                        updated_count += 1
                    else:
                        print(f"❌ Ошибка обновления в БД")
                        error_count += 1
                else:
                    print(f"❌ API ошибка: {result.get('description', 'Unknown error')}")
                    error_count += 1
            else:
                print(f"❌ HTTP ошибка: {response.status_code}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            error_count += 1
    
    print(f"\n🎯 Результат:")
    print(f"✅ Обновлено: {updated_count}")
    print(f"❌ Ошибок: {error_count}")
    
    if updated_count > 0:
        print("\n🔍 Проверяем результат...")
        users_after = db.get_all_users()
        for user in users_after[:3]:  # Показываем первые 3
            print(f"  ID: {user['id']}, Name: {user['full_name'] or 'N/A'}, Username: @{user['username'] or 'N/A'}")

if __name__ == "__main__":
    update_user_info()
