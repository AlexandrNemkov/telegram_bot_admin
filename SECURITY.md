# 🔒 Безопасность сервера

## 🛡️ Основные меры безопасности

### 1. Обновление системы
```bash
# Регулярное обновление
sudo apt update && sudo apt upgrade -y

# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 2. Firewall (UFW)
```bash
# Установка UFW
sudo apt install ufw

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешенные порты
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Активация
sudo ufw enable
sudo ufw status verbose
```

### 3. Fail2ban
```bash
# Установка
sudo apt install fail2ban

# Конфигурация
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Настройка SSH защиты
sudo nano /etc/fail2ban/jail.local
```

**Содержимое jail.local:**
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
```

### 4. SSH безопасность
```bash
# Редактирование конфигурации SSH
sudo nano /etc/ssh/sshd_config
```

**Рекомендуемые настройки:**
```bash
# Отключение root входа
PermitRootLogin no

# Отключение парольной аутентификации
PasswordAuthentication no

# Использование только SSH ключей
PubkeyAuthentication yes

# Изменение порта SSH (опционально)
Port 2222

# Ограничение пользователей
AllowUsers $USERNAME

# Максимальные попытки входа
MaxAuthTries 3

# Таймаут неактивности
ClientAliveInterval 300
ClientAliveCountMax 2
```

## 🔐 SSH ключи

### 1. Генерация ключей на локальной машине
```bash
# Генерация пары ключей
ssh-keygen -t ed25519 -C "your_email@example.com"

# Копирование публичного ключа на сервер
ssh-copy-id -i ~/.ssh/id_ed25519.pub $USERNAME@$SERVER_IP
```

### 2. Настройка на сервере
```bash
# Создание директории .ssh
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Создание authorized_keys
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Добавление публичного ключа
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
```

### 3. Тестирование
```bash
# Тест подключения по ключу
ssh $USERNAME@$SERVER_IP

# Отключение парольной аутентификации
sudo systemctl restart ssh
```

## 🚪 Порты и сервисы

### 1. Проверка открытых портов
```bash
# Установка netstat
sudo apt install net-tools

# Просмотр открытых портов
sudo netstat -tulpn

# Установка nmap
sudo apt install nmap

# Сканирование портов
sudo nmap -sT -O localhost
```

### 2. Отключение ненужных сервисов
```bash
# Проверка активных сервисов
sudo systemctl list-units --type=service --state=active

# Отключение ненужных сервисов
sudo systemctl stop service_name
sudo systemctl disable service_name
```

## 📊 Мониторинг безопасности

### 1. Логи системы
```bash
# Просмотр логов авторизации
sudo tail -f /var/log/auth.log

# Просмотр логов fail2ban
sudo tail -f /var/log/fail2ban.log

# Просмотр логов SSH
sudo journalctl -u ssh --since "1 hour ago"
```

### 2. Скрипт мониторинга безопасности
```bash
#!/bin/bash
echo "=== Проверка безопасности ==="
echo "Время: $(date)"
echo ""

echo "1. Статус UFW:"
sudo ufw status

echo ""
echo "2. Статус Fail2ban:"
sudo systemctl status fail2ban

echo ""
echo "3. Последние неудачные попытки входа:"
sudo grep "Failed password" /var/log/auth.log | tail -5

echo ""
echo "4. Активные SSH соединения:"
sudo netstat -tulpn | grep :22

echo ""
echo "5. Проверка открытых портов:"
sudo netstat -tulpn | grep LISTEN
```

## 🔍 Аудит безопасности

### 1. Проверка уязвимостей
```bash
# Установка инструментов аудита
sudo apt install lynis chkrootkit rkhunter

# Проверка системы
sudo lynis audit system

# Проверка на rootkit
sudo chkrootkit

# Проверка на вредоносное ПО
sudo rkhunter --check
```

### 2. Проверка прав доступа
```bash
# Проверка критических файлов
sudo find /etc -type f -perm -o+w

# Проверка SUID файлов
sudo find / -type f -perm -4000 -ls

# Проверка SGID файлов
sudo find / -type f -perm -2000 -ls
```

## 🚨 Инциденты безопасности

### 1. Подозрительная активность
```bash
# Проверка активных процессов
ps aux | grep -v grep | grep -E "(nc|netcat|wget|curl)"

# Проверка сетевых соединений
sudo netstat -tulpn | grep -E "(nc|netcat|wget|curl)"

# Проверка cron задач
crontab -l
sudo crontab -l
```

### 2. Блокировка подозрительных IP
```bash
# Ручная блокировка IP
sudo ufw deny from IP_ADDRESS

# Проверка заблокированных IP
sudo ufw status numbered
```

## 📋 Чек-лист безопасности

### Система
- [ ] Система обновлена до последней версии
- [ ] UFW настроен и активен
- [ ] Fail2ban установлен и настроен
- [ ] SSH настроен безопасно
- [ ] Используются SSH ключи

### Порты
- [ ] Открыты только необходимые порты (22, 80, 443)
- [ ] Закрыты все остальные порты
- [ ] Проверены активные сервисы

### Мониторинг
- [ ] Настроено логирование
- [ ] Настроен мониторинг безопасности
- [ ] Регулярные проверки системы

### Резервное копирование
- [ ] Настроено автоматическое резервное копирование
- [ ] Тестирование восстановления
- [ ] Хранение бэкапов в безопасном месте

## 🔧 Автоматизация безопасности

### 1. Скрипт ежедневной проверки
```bash
#!/bin/bash
# Добавить в crontab: 0 2 * * * /path/to/security_check.sh

echo "=== Ежедневная проверка безопасности ==="
echo "Дата: $(date)"

# Проверка обновлений
sudo apt update
UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
echo "Доступно обновлений: $((UPDATES - 1))"

# Проверка статуса сервисов
echo "Статус UFW: $(sudo ufw status | grep Status)"
echo "Статус Fail2ban: $(sudo systemctl is-active fail2ban)"

# Проверка дискового пространства
df -h | grep -E "(/$|/home)"

# Проверка логов
echo "Неудачные попытки входа за последние 24 часа:"
sudo grep "Failed password" /var/log/auth.log | grep "$(date '+%b %d')" | wc -l
```

### 2. Настройка crontab
```bash
# Редактирование crontab
crontab -e

# Добавить строки:
0 2 * * * /path/to/security_check.sh
0 3 * * 0 /path/to/weekly_security_audit.sh
```

## 📚 Дополнительные ресурсы

### Полезные ссылки
- [Ubuntu Security](https://ubuntu.com/security)
- [Fail2ban Documentation](https://www.fail2ban.org/wiki/index.php/Main_Page)
- [UFW Documentation](https://help.ubuntu.com/community/UFW)

### Рекомендуемые инструменты
- **Lynis** - аудит безопасности
- **Chkrootkit** - проверка на rootkit
- **Rkhunter** - проверка на вредоносное ПО
- **ClamAV** - антивирус
- **Logwatch** - анализ логов

## ✅ Итоговая проверка

После настройки всех мер безопасности выполните:

```bash
# Полная проверка системы
sudo lynis audit system

# Проверка открытых портов
sudo nmap -sT -O localhost

# Проверка статуса сервисов
sudo systemctl status ufw fail2ban ssh

# Тест подключения
ssh $USERNAME@$SERVER_IP
```

Система считается безопасной, если:
- UFW активен и настроен
- Fail2ban работает
- SSH доступен только по ключам
- Открыты только необходимые порты
- Система регулярно обновляется
- Настроен мониторинг безопасности
