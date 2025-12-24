# -*- coding: utf-8 -*-
"""Упрощенный тест REST API без токена"""
import requests
import base64
import uuid
import time

BASE_URL = "http://127.0.0.1:5000"
DEVICE_ID = str(uuid.uuid4())

print(f"[TEST] Тестирование REST API без токена")
print(f"[INFO] Сервер: {BASE_URL}")
print(f"[INFO] Device ID: {DEVICE_ID}\n")

# 1. Регистрация устройства
print("[1] Регистрация устройства...")
try:
    r = requests.post(f"{BASE_URL}/api/device/register", data={
        "device_id": DEVICE_ID,
        "manufacturer": "Samsung",
        "model": "Galaxy S21",
        "android_version": "12",
        "sdk": 31,
        "imei": "123456789012345"
    })
    print(f"   Статус: {r.status_code}")
    print(f"   Ответ: {r.json()}")
    if r.status_code == 200:
        print("   [OK] Регистрация успешна!\n")
    else:
        print(f"   [ERROR] Ошибка регистрации\n")
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}\n")

# 2. Отправка местоположения
print("[2] Отправка местоположения...")
try:
    r = requests.post(f"{BASE_URL}/api/device/location/no-token", data={
        "device_id": DEVICE_ID,
        "lat": 55.7558,
        "lon": 37.6173,
        "accuracy": 10.5,
        "timestamp": int(time.time() * 1000)
    })
    print(f"   Статус: {r.status_code}")
    print(f"   Ответ: {r.json()}")
    if r.status_code == 200:
        print("   [OK] Местоположение отправлено!\n")
    else:
        print(f"   [ERROR] Ошибка отправки местоположения\n")
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}\n")

# 3. Отправка системной информации
print("[3] Отправка системной информации...")
try:
    r = requests.post(f"{BASE_URL}/api/device/system-info/no-token", data={
        "device_id": DEVICE_ID,
        "battery_level": 85,
        "is_charging": "false",
        "battery_temp": 25.5,
        "memory_usage": 2048,
        "storage_usage": 65.5,
        "timestamp": int(time.time() * 1000)
    })
    print(f"   Статус: {r.status_code}")
    print(f"   Ответ: {r.json()}")
    if r.status_code == 200:
        print("   [OK] Системная информация отправлена!\n")
    else:
        print(f"   [ERROR] Ошибка отправки системной информации\n")
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}\n")

# 4. Отправка информации о батарее
print("[4] Отправка информации о батарее...")
try:
    r = requests.post(f"{BASE_URL}/api/device/battery/no-token", data={
        "device_id": DEVICE_ID,
        "level": 85,
        "is_charging": "false",
        "temperature": 25.5,
        "voltage": 4200,
        "health": "good",
        "timestamp": int(time.time() * 1000)
    })
    print(f"   Статус: {r.status_code}")
    print(f"   Ответ: {r.json()}")
    if r.status_code == 200:
        print("   [OK] Информация о батарее отправлена!\n")
    else:
        print(f"   [ERROR] Ошибка отправки информации о батарее\n")
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}\n")

# 5. Проверка списка устройств
print("[5] Проверка списка устройств...")
try:
    # Логин как админ
    login_r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if login_r.status_code == 200:
        token = login_r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        devices_r = requests.get(f"{BASE_URL}/api/devices", headers=headers)
        if devices_r.status_code == 200:
            devices = devices_r.json()
            found = any(str(d.get("id")) == DEVICE_ID for d in devices)
            print(f"   [INFO] Всего устройств: {len(devices)}")
            if found:
                print(f"   [OK] Устройство найдено в списке!")
            else:
                print(f"   [WARN] Устройство не найдено в активных сессиях (но может быть в БД)")
        else:
            print(f"   [WARN] Не удалось получить список: {devices_r.status_code}")
    else:
        print(f"   [WARN] Не удалось залогиниться: {login_r.status_code}")
except Exception as e:
    print(f"   [WARN] Ошибка: {e}")

print("\n" + "="*60)
print("[OK] Тестирование завершено!")
print("="*60)

