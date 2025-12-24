# REST API без токена - Простая отправка данных

## Что сделано

✅ **REST API endpoints БЕЗ токена** - Android приложение может просто отправлять данные по `device_id`, токен не нужен.

## Как это работает

1. **Приложение устанавливается** на телефон
2. **При первом запросе** устройство автоматически регистрируется на сервере
3. **Все данные сохраняются в БД** (PostgreSQL)
4. **Админка видит устройство** с версией телефона и всеми данными

## Endpoints без токена

### 1. Регистрация устройства
```
POST /api/device/register
```
**Параметры (Form):**
- `device_id` (обязательно) - UUID устройства
- `manufacturer` (опционально) - Производитель
- `model` (опционально) - Модель
- `android_version` (опционально) - Версия Android
- `sdk` (опционально) - SDK версия
- `imei` (опционально) - IMEI

**Пример:**
```bash
curl -X POST "http://your-server/api/device/register" \
  -F "device_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "manufacturer=Samsung" \
  -F "model=Galaxy S21" \
  -F "android_version=12"
```

### 2. Отправка кадра камеры (файл)
```
POST /api/device/camera/no-token
```
**Параметры (Form):**
- `device_id` (обязательно) - UUID устройства
- `camera` (обязательно) - "front" или "back"
- `image` (обязательно) - JPEG файл
- `width` (обязательно) - Ширина в пикселях
- `height` (обязательно) - Высота в пикселях
- `timestamp` (обязательно) - Unix timestamp в миллисекундах

### 3. Отправка кадра камеры (Base64)
```
POST /api/device/camera/base64/no-token
```
**Параметры (Form):**
- `device_id` (обязательно) - UUID устройства
- `camera` (обязательно) - "front" или "back"
- `image_base64` (обязательно) - Base64 строка JPEG
- `width` (обязательно) - Ширина в пикселях
- `height` (обязательно) - Высота в пикселях
- `timestamp` (обязательно) - Unix timestamp в миллисекундах

### 4. Отправка местоположения
```
POST /api/device/location/no-token
```
**Параметры (Form):**
- `device_id` (обязательно) - UUID устройства
- `lat` (обязательно) - Широта (-90 до 90)
- `lon` (обязательно) - Долгота (-180 до 180)
- `accuracy` (опционально) - Точность в метрах
- `timestamp` (обязательно) - Unix timestamp в миллисекундах

### 5. Отправка системной информации
```
POST /api/device/system-info/no-token
```
**Параметры (Form):**
- `device_id` (обязательно) - UUID устройства
- `battery_level` (опционально) - Уровень батареи (0-100)
- `is_charging` (опционально) - Заряжается ли устройство
- `battery_temp` (опционально) - Температура батареи
- `memory_usage` (опционально) - Использование памяти в MB
- `storage_usage` (опционально) - Использование хранилища в процентах
- `timestamp` (обязательно) - Unix timestamp в миллисекундах

### 6. Отправка информации о батарее
```
POST /api/device/battery/no-token
```
**Параметры (Form):**
- `device_id` (обязательно) - UUID устройства
- `level` (обязательно) - Уровень батареи (0-100)
- `is_charging` (обязательно) - Заряжается ли устройство
- `temperature` (опционально) - Температура батареи
- `voltage` (опционально) - Напряжение в mV
- `health` (опционально) - Статус здоровья батареи
- `timestamp` (обязательно) - Unix timestamp в миллисекундах

## Пример использования (Kotlin)

```kotlin
// 1. Регистрация при первом запуске
fun registerDevice(deviceId: String) {
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("device_id", deviceId)
        .addFormDataPart("manufacturer", Build.MANUFACTURER)
        .addFormDataPart("model", Build.MODEL)
        .addFormDataPart("android_version", Build.VERSION.RELEASE)
        .addFormDataPart("sdk", Build.VERSION.SDK_INT.toString())
        .build()
    
    val request = Request.Builder()
        .url("http://your-server/api/device/register")
        .post(requestBody)
        .build()
    
    // Отправить запрос
}

// 2. Отправка кадра камеры
fun sendCameraFrame(deviceId: String, imageFile: File, camera: String) {
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("device_id", deviceId)
        .addFormDataPart("camera", camera) // "front" или "back"
        .addFormDataPart("image", "image.jpg",
            imageFile.asRequestBody("image/jpeg".toMediaType()))
        .addFormDataPart("width", "1920")
        .addFormDataPart("height", "1080")
        .addFormDataPart("timestamp", System.currentTimeMillis().toString())
        .build()
    
    val request = Request.Builder()
        .url("http://your-server/api/device/camera/no-token")
        .post(requestBody)
        .build()
    
    // Отправить запрос
}

// 3. Отправка местоположения
fun sendLocation(deviceId: String, lat: Double, lon: Double) {
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("device_id", deviceId)
        .addFormDataPart("lat", lat.toString())
        .addFormDataPart("lon", lon.toString())
        .addFormDataPart("timestamp", System.currentTimeMillis().toString())
        .build()
    
    val request = Request.Builder()
        .url("http://your-server/api/device/location/no-token")
        .post(requestBody)
        .build()
    
    // Отправить запрос
}

// 4. Отправка системной информации
fun sendSystemInfo(deviceId: String) {
    val requestBody = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("device_id", deviceId)
        .addFormDataPart("battery_level", getBatteryLevel().toString())
        .addFormDataPart("is_charging", isCharging().toString())
        .addFormDataPart("memory_usage", getMemoryUsage().toString())
        .addFormDataPart("timestamp", System.currentTimeMillis().toString())
        .build()
    
    val request = Request.Builder()
        .url("http://your-server/api/device/system-info/no-token")
        .post(requestBody)
        .build()
    
    // Отправить запрос
}
```

## Что происходит на сервере

1. **Получен запрос** с `device_id`
2. **Проверка:** есть ли устройство в БД?
   - Если **есть** → обновляется `last_seen`, данные сохраняются
   - Если **нет** → автоматически создается новое устройство с именем из manufacturer + model
3. **Все данные сохраняются** в PostgreSQL:
   - Кадры камеры → таблица `camera_frames`
   - Местоположение → таблица `location_history`
   - Системная информация → таблица `device_events`
4. **Админка видит** все устройства и данные в реальном времени

## Преимущества

✅ **Простота** - не нужен токен, только `device_id`  
✅ **Автоматическая регистрация** - устройство регистрируется при первом запросе  
✅ **Все данные в БД** - кадры, местоположение, системная информация  
✅ **Работает без WebSocket** - можно использовать только REST API  
✅ **Обратная совместимость** - старые endpoints с токеном тоже работают  

## Отличие от WebSocket

- **WebSocket** - постоянное соединение, real-time двусторонняя связь
- **REST API** - простые HTTP запросы, отправка данных по требованию

Оба способа работают параллельно, можно использовать любой или оба сразу.

