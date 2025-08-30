#!/usr/bin/env python3
"""
Скрипт для инициализации первого администратора системы
"""

import hashlib
import os
import sys
from database import Database

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_admin():
    """Инициализация первого администратора"""
    print("🔐 Инициализация системы ролей...")
    
    db = Database()
    
    # Проверяем есть ли уже администраторы
    admin_users = [u for u in db.get_all_system_users() if u['role'] == 'admin']
    
    if admin_users:
        print(f"✅ Администраторы уже существуют ({len(admin_users)}):")
        for admin in admin_users:
            print(f"  👤 {admin['username']} - {admin['full_name'] or 'Без имени'}")
        return
    
    print("📝 Создание первого администратора...")
    
    # Запрашиваем данные администратора
    username = input("Введите username администратора: ").strip()
    if not username:
        print("❌ Username не может быть пустым")
        return
    
    password = input("Введите пароль: ").strip()
    if not password:
        print("❌ Пароль не может быть пустым")
        return
    
    confirm_password = input("Подтвердите пароль: ").strip()
    if password != confirm_password:
        print("❌ Пароли не совпадают")
        return
    
    full_name = input("Введите полное имя (необязательно): ").strip()
    email = input("Введите email (необязательно): ").strip()
    
    # Создаем администратора
    password_hash = hash_password(password)
    
    if db.create_system_user(
        username=username,
        password_hash=password_hash,
        role='admin',
        full_name=full_name if full_name else None,
        email=email if email else None,
        account_expires=None,  # Админ без ограничений по времени
        created_by=None
    ):
        print(f"✅ Администратор {username} успешно создан!")
        print(f"🔑 Роль: admin")
        print(f"👤 Имя: {full_name or 'Не указано'}")
        print(f"📧 Email: {email or 'Не указан'}")
        print(f"⏰ Ограничения по времени: Нет")
    else:
        print("❌ Ошибка создания администратора")

if __name__ == "__main__":
    init_admin()
