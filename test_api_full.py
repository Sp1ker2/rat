# -*- coding: utf-8 -*-
"""Полный тест REST API без токена (с тестом камеры)"""
import requests
import base64
import uuid
import time
from io import BytesIO

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("⚠️ Pillow не установлен, тест камеры будет пропущен")
    print("   Установите: pip install Pillow\n")

BASE_URL = "http://127.0.0.1:5000"
DEVICE_ID = str(uuid.uuid4())

print(f"🧪 Полное тестирование REST API без токена")
print(f"📍 Сервер: {BASE_URL}")
print(f"📱 Device ID: {DEVICE_ID}\n")

# ============================================================================
# 1. Тест регистрации устройства
# ============================================================================
print("1️⃣ Тестирую регистрацию устройства...")
try:
    response = requests.post(
        f"{BASE_URL}/api/device/register",
        data={
            "device_id": DEVICE_ID,
            "manufacturer": "Samsung",
            "model": "Galaxy S21",
            "android_version": "12",
            "sdk": 31,
            "imei": "123456789012345"
        }
    )
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 200, "Регистрация не удалась!"
    print("   ✅ Регистрация успешна!\n")
except Exception as e:
    print(f"   ❌ Ошибка: {e}\n")

# ============================================================================
# 2. Тест отправки кадра камеры (Base64)
# ============================================================================
if HAS_PIL:
    print("2️⃣ Тестирую отправку кадра камеры (Base64)...")
    try:
        # Создаем тестовое изображение
        img = Image.new('RGB', (1920, 1080), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        
        response = requests.post(
            f"{BASE_URL}/api/device/camera/base64/no-token",
            data={
                "device_id": DEVICE_ID,
                "camera": "back",
                "image_base64": img_base64,
                "width": 1920,
                "height": 1080,
                "timestamp": int(time.time() * 1000)
            }
        )
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.json()}")
        assert response.status_code == 200, "Отправка кадра не удалась!"
        print("   ✅ Кадр камеры отправлен!\n")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}\n")
else:
    print("2️⃣ Пропускаю тест камеры (Pillow не установлен)\n")

# ============================================================================
# 3. Тест отправки местоположения
# ============================================================================
print("3️⃣ Тестирую отправку местоположения...")
try:
    response = requests.post(
        f"{BASE_URL}/api/device/location/no-token",
        data={
            "device_id": DEVICE_ID,
            "lat": 55.7558,  # Москва
            "lon": 37.6173,
            "accuracy": 10.5,
            "timestamp": int(time.time() * 1000)
        }
    )
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 200, "Отправка местоположения не удалась!"
    print("   ✅ Местоположение отправлено!\n")
except Exception as e:
    print(f"   ❌ Ошибка: {e}\n")

# ============================================================================
# 4. Тест отправки системной информации
# ============================================================================
print("4️⃣ Тестирую отправку системной информации...")
try:
    response = requests.post(
        f"{BASE_URL}/api/device/system-info/no-token",
        data={
            "device_id": DEVICE_ID,
            "battery_level": 85,
            "is_charging": False,
            "battery_temp": 25.5,
            "memory_usage": 2048,
            "storage_usage": 65.5,
            "timestamp": int(time.time() * 1000)
        }
    )
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 200, "Отправка системной информации не удалась!"
    print("   ✅ Системная информация отправлена!\n")
except Exception as e:
    print(f"   ❌ Ошибка: {e}\n")

# ============================================================================
# 5. Тест отправки информации о батарее
# ============================================================================
print("5️⃣ Тестирую отправку информации о батарее...")
try:
    response = requests.post(
        f"{BASE_URL}/api/device/battery/no-token",
        data={
            "device_id": DEVICE_ID,
            "level": 85,
            "is_charging": False,
            "temperature": 25.5,
            "voltage": 4200,
            "health": "good",
            "timestamp": int(time.time() * 1000)
        }
    )
    print(f"   Статус: {response.status_code}")
    print(f"   Ответ: {response.json()}")
    assert response.status_code == 200, "Отправка информации о батарее не удалась!"
    print("   ✅ Информация о батарее отправлена!\n")
except Exception as e:
    print(f"   ❌ Ошибка: {e}\n")

# ============================================================================
# 6. Проверка, что устройство появилось в списке
# ============================================================================
print("6️⃣ Проверяю, что устройство появилось в списке...")
try:
    # Сначала нужно залогиниться как админ
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        devices_response = requests.get(
            f"{BASE_URL}/api/devices",
            headers=headers
        )
        if devices_response.status_code == 200:
            devices = devices_response.json()
            found = any(str(d.get("id")) == DEVICE_ID for d in devices)
            print(f"   📊 Всего устройств: {len(devices)}")
            if found:
                print(f"   ✅ Устройство найдено в списке!")
            else:
                print(f"   ⚠️ Устройство не найдено в активных сессиях (но может быть в БД)")
        else:
            print(f"   ⚠️ Не удалось получить список устройств: {devices_response.status_code}")
    else:
        print(f"   ⚠️ Не удалось залогиниться: {login_response.status_code}")
except Exception as e:
    print(f"   ⚠️ Ошибка при проверке списка: {e}")

print("\n" + "="*60)
print("✅ Тестирование завершено!")
print("="*60)

