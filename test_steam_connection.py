#!/usr/bin/env python3
"""
Тестовый скрипт для диагностики проблем с подключением к Steam
"""
import requests
import sys

print("="*60)
print("  Диагностика подключения к Steam")
print("="*60)
print()

# 1. Проверка подключения к Steam Community
print("[1/4] Проверка доступности Steam Community...")
try:
    response = requests.get("https://steamcommunity.com", timeout=10)
    if response.status_code == 200:
        print("✓ Steam Community доступен (200 OK)")
    else:
        print(f"⚠️ Steam Community вернул код: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"✗ Ошибка подключения к Steam Community: {e}")
    sys.exit(1)

print()

# 2. Проверка Steam Store API
print("[2/4] Проверка Steam Store API...")
try:
    response = requests.get("https://store.steampowered.com/api/featured/", timeout=10)
    if response.status_code == 200:
        print("✓ Steam Store API доступен")
    else:
        print(f"⚠️ Steam Store API вернул код: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"✗ Ошибка подключения к Steam Store API: {e}")

print()

# 3. Проверка Steam login API
print("[3/4] Проверка Steam Login API...")
try:
    response = requests.get("https://steamcommunity.com/login/home/", timeout=10)
    if response.status_code == 200:
        print("✓ Steam Login доступен")
    else:
        print(f"⚠️ Steam Login вернул код: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"✗ Ошибка подключения к Steam Login: {e}")

print()

# 4. Проверка версии библиотеки steampy
print("[4/4] Проверка установленной библиотеки steampy...")
try:
    import steampy
    print(f"✓ steampy установлен")

    # Проверяем версию если доступна
    if hasattr(steampy, '__version__'):
        print(f"  Версия: {steampy.__version__}")

except ImportError:
    print("✗ steampy не установлен!")
    print("  Установите: pip install steampy")

print()
print("="*60)
print("  Дополнительная информация")
print("="*60)
print()

# Проверяем IP адрес
print("Проверка вашего IP адреса...")
try:
    response = requests.get("https://api.ipify.org?format=json", timeout=5)
    if response.status_code == 200:
        ip_data = response.json()
        print(f"Ваш IP: {ip_data.get('ip', 'Неизвестно')}")
except:
    print("Не удалось определить IP адрес")

print()

# Рекомендации
print("="*60)
print("  Рекомендации")
print("="*60)
print()
print("Если все проверки прошли успешно, но авторизация не работает:")
print()
print("1. Steam может временно ограничивать API")
print("   → Подождите 15-30 минут и попробуйте снова")
print()
print("2. Ваш IP может быть заблокирован Steam")
print("   → Попробуйте использовать VPN")
print()
print("3. Библиотека steampy может быть несовместима")
print("   → Попробуйте обновить: pip install --upgrade steampy")
print()
print("4. Аккаунт может требовать дополнительную проверку")
print("   → Войдите в аккаунт через браузер и пройдите проверку")
print()
print("5. Проверьте статус Steam:")
print("   → https://steamstat.us/")
print()
