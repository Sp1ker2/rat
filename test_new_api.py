# -*- coding: utf-8 -*-
"""Тест нового API с device_id в пути и Bearer token"""
import requests
import base64
import uuid
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BASE_URL = "http://127.0.0.1:5000"
DEVICE_ID = str(uuid.uuid4())

print(f"[TEST] Тестирование нового API (device_id в пути, Bearer token)")
print(f"[INFO] Сервер: {BASE_URL}")
print(f"[INFO] Device ID: {DEVICE_ID}\n")

# Сначала регистрируем устройство и получаем токен
print("[SETUP] Регистрация устройства...")
try:
    register_r = requests.post(f"{BASE_URL}/api/device/register", data={
        "device_id": DEVICE_ID,
        "manufacturer": "Samsung",
        "model": "Galaxy S21",
        "android_version": "12",
        "sdk": 31,
        "imei": "123456789012345"
    })
    if register_r.status_code != 200:
        print(f"   [ERROR] Регистрация не удалась: {register_r.status_code}")
        print(f"   Ответ: {register_r.text}")
        exit(1)
    print("   [OK] Устройство зарегистрировано\n")
except Exception as e:
    print(f"   [ERROR] Ошибка регистрации: {e}\n")
    exit(1)

# Получаем токен устройства
print("[SETUP] Получение токена устройства...")
try:
    # Логинимся как админ
    login_r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if login_r.status_code != 200:
        print(f"   [ERROR] Логин не удался: {login_r.status_code}")
        exit(1)
    
    admin_token = login_r.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Получаем токен устройства
    token_r = requests.get(f"{BASE_URL}/api/devices/{DEVICE_ID}/token", headers=headers)
    if token_r.status_code != 200:
        print(f"   [ERROR] Не удалось получить токен: {token_r.status_code}")
        print(f"   Ответ: {token_r.text}")
        exit(1)
    
    device_token = token_r.json()["token"]
    device_headers = {"Authorization": f"Bearer {device_token}", "Content-Type": "application/json"}
    print(f"   [OK] Токен получен: {device_token[:20]}...\n")
except Exception as e:
    print(f"   [ERROR] Ошибка получения токена: {e}\n")
    exit(1)

# Теперь тестируем endpoints
test_results = []

# 1. Battery
print("[1] Тест POST /api/devices/{device_id}/battery...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/battery",
        headers=device_headers,
        json={
            "level": 85,
            "is_charging": True,
            "temperature": 32.5,
            "voltage": 4.2,
            "health": "good",
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("battery", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("battery", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("battery", False))

# 2. Device Info
print("\n[2] Тест POST /api/devices/{device_id}/device-info...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/device-info",
        headers=device_headers,
        json={
            "manufacturer": "Samsung",
            "model": "Galaxy S21 Ultra",
            "android_version": "13",
            "sdk_version": 33,
            "serial_number": "ABC123",
            "imei": "123456789012345",
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("device-info", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("device-info", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("device-info", False))

# 3. Location
print("\n[3] Тест POST /api/devices/{device_id}/location...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/location",
        headers=device_headers,
        json={
            "latitude": 48.4647,
            "longitude": 35.0462,
            "accuracy": 10.5,
            "altitude": 150.0,
            "speed": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("location", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("location", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("location", False))

# 4. Camera Frame
print("\n[4] Тест POST /api/devices/{device_id}/camera-frame...")
try:
    if HAS_PIL:
        # Создаем тестовое изображение
        img = Image.new('RGB', (1920, 1080), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    else:
        # Простой тестовый base64 (1x1 красный пиксель)
        img_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
    
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/camera-frame",
        headers=device_headers,
        json={
            "camera": "back",
            "image_base64": img_base64,
            "width": 1920,
            "height": 1080,
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("camera-frame", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("camera-frame", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("camera-frame", False))

# 5. Logs
print("\n[5] Тест POST /api/devices/{device_id}/logs...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/logs",
        headers=device_headers,
        json={
            "logs": [
                {
                    "level": "info",
                    "message": "App started",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "level": "error",
                    "message": "Connection failed",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("logs", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("logs", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("logs", False))

# 6. System Stats
print("\n[6] Тест POST /api/devices/{device_id}/system-stats...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/system-stats",
        headers=device_headers,
        json={
            "ram_total": 8192,
            "ram_used": 4096,
            "ram_free": 4096,
            "cpu_usage": 45.2,
            "storage_total": 128000,
            "storage_used": 64000,
            "storage_free": 64000,
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("system-stats", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("system-stats", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("system-stats", False))

# 7. Apps
print("\n[7] Тест POST /api/devices/{device_id}/apps...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/apps",
        headers=device_headers,
        json={
            "apps": [
                {
                    "package_name": "com.example.app",
                    "app_name": "Example App",
                    "version": "1.0.0",
                    "install_time": datetime.now().isoformat()
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("apps", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("apps", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("apps", False))

# 8. Contacts
print("\n[8] Тест POST /api/devices/{device_id}/contacts...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/contacts",
        headers=device_headers,
        json={
            "contacts": [
                {
                    "name": "John Doe",
                    "phone": "+380123456789",
                    "email": "john@example.com"
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("contacts", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("contacts", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("contacts", False))

# 9. SMS
print("\n[9] Тест POST /api/devices/{device_id}/sms...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/sms",
        headers=device_headers,
        json={
            "messages": [
                {
                    "sender": "+380123456789",
                    "body": "Hello",
                    "timestamp": datetime.now().isoformat(),
                    "is_read": True
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("sms", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("sms", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("sms", False))

# 10. Call Logs
print("\n[10] Тест POST /api/devices/{device_id}/call-logs...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/call-logs",
        headers=device_headers,
        json={
            "calls": [
                {
                    "number": "+380123456789",
                    "type": "incoming",
                    "duration": 120,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("call-logs", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("call-logs", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("call-logs", False))

# 11. Heartbeat
print("\n[11] Тест POST /api/devices/{device_id}/heartbeat...")
try:
    r = requests.post(
        f"{BASE_URL}/api/devices/{DEVICE_ID}/heartbeat",
        headers=device_headers,
        json={
            "status": "online",
            "timestamp": datetime.now().isoformat()
        }
    )
    if r.status_code == 200:
        print(f"   [OK] Успешно: {r.json()}")
        test_results.append(("heartbeat", True))
    else:
        print(f"   [ERROR] Статус: {r.status_code}, Ответ: {r.text[:200]}")
        test_results.append(("heartbeat", False))
except Exception as e:
    print(f"   [ERROR] Ошибка: {e}")
    test_results.append(("heartbeat", False))

# Итоги
print("\n" + "="*60)
print("[RESULTS] Результаты тестирования:")
print("="*60)
passed = sum(1 for _, result in test_results if result)
total = len(test_results)
for name, result in test_results:
    status = "[OK]" if result else "[FAIL]"
    print(f"  {status} {name}")
print("="*60)
print(f"[SUMMARY] Пройдено: {passed}/{total}")
if passed == total:
    print("[OK] Все тесты пройдены успешно!")
else:
    print(f"[WARN] Не пройдено: {total - passed} тестов")
print("="*60)

