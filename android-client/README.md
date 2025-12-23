# Android WebRTC Stream Client

Android приложение для стриминга видео с камеры на FastAPI сервер.

## Возможности

- ✅ Захват видео с камеры устройства
- ✅ Отправка кадров на сервер в режиме реального времени
- ✅ Автоматическое сжатие и оптимизация кадров
- ✅ Настраиваемый FPS (по умолчанию 10 FPS)
- ✅ Превью камеры на экране
- ✅ Простой UI с кнопками старт/стоп

## Установка

### 1. Создайте новый Android проект в Android Studio

1. Откройте Android Studio
2. File → New → New Project
3. Выберите "Empty Activity"
4. Name: `WebRTCStream`
5. Package name: `com.example.webrtcstream`
6. Language: Kotlin
7. Minimum SDK: API 24

### 2. Скопируйте файлы

Скопируйте содержимое файлов из этой папки:

- `MainActivity.kt` → `app/src/main/java/com/example/webrtcstream/MainActivity.kt`
- `activity_main.xml` → `app/src/main/res/layout/activity_main.xml`
- `build.gradle.kts` → `app/build.gradle.kts`
- `AndroidManifest.xml` → `app/src/main/AndroidManifest.xml`

### 3. Sync Gradle

Нажмите "Sync Now" когда Android Studio предложит синхронизировать проект.

## Настройка

### Изменить адрес сервера

В `MainActivity.kt` найдите строку:

```kotlin
private val serverUrl = "https://kelyastream.duckdns.org"
```

Замените на ваш сервер, если нужно.

### Настроить FPS и качество

В `MainActivity.kt`:

```kotlin
// FPS (кадров в секунду)
private val frameInterval = 100L // 100мс = 10 FPS

// Качество JPEG (0-100)
bitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream)

// Разрешение видео
val scaledBitmap = Bitmap.createScaledBitmap(
    bitmap, 
    640,  // ширина (можно изменить)
    480,  // высота (можно изменить)
    true
)
```

## Использование

1. **Установите приложение** на Android устройство
2. **Разрешите доступ к камере** при первом запуске
3. **Нажмите "Начать стрим"** для начала трансляции
4. **Откройте в браузере** `https://kelyastream.duckdns.org` для просмотра
5. **Нажмите "Остановить"** для завершения трансляции

## Архитектура

```
[Android Device]
     ↓ Камера
[CameraX] → захват кадров
     ↓
[FrameAnalyzer] → обработка кадров
     ↓
[Bitmap] → конвертация в JPEG
     ↓
[Base64] → кодирование
     ↓
[OkHttp] → отправка HTTP POST
     ↓
[FastAPI Server] → обработка на сервере
     ↓
[MJPEG Stream] → трансляция в браузер
```

## API Endpoints

Приложение использует следующие endpoints:

### 1. Проверка подключения
```http
GET /api/stats
```

### 2. Отправка кадра
```http
POST /api/process-frame
Content-Type: application/json

{
  "frame": {
    "type": "video",
    "data": "<base64_encoded_jpeg>",
    "width": 640,
    "height": 480,
    "timestamp": 1703348764000
  }
}
```

## Оптимизация

### Уменьшить использование трафика

1. **Снизить FPS:**
```kotlin
private val frameInterval = 200L // 5 FPS вместо 10
```

2. **Уменьшить разрешение:**
```kotlin
val scaledBitmap = Bitmap.createScaledBitmap(bitmap, 320, 240, true)
```

3. **Снизить качество JPEG:**
```kotlin
bitmap.compress(Bitmap.CompressFormat.JPEG, 60, outputStream)
```

### Улучшить качество

1. **Увеличить FPS:**
```kotlin
private val frameInterval = 50L // 20 FPS
```

2. **Увеличить разрешение:**
```kotlin
val scaledBitmap = Bitmap.createScaledBitmap(bitmap, 1280, 720, true)
```

3. **Повысить качество JPEG:**
```kotlin
bitmap.compress(Bitmap.CompressFormat.JPEG, 90, outputStream)
```

## Troubleshooting

### Камера не работает
- Проверьте разрешения в настройках телефона
- Перезапустите приложение

### Кадры не отправляются
- Проверьте подключение к интернету
- Убедитесь что сервер доступен: `https://kelyastream.duckdns.org/api/stats`
- Проверьте логи: `adb logcat | grep WebRTCStream`

### Низкий FPS
- Уменьшите разрешение кадров
- Снизьте качество JPEG
- Проверьте скорость интернета

### Приложение крашится
- Проверьте логи: `adb logcat | grep AndroidRuntime`
- Убедитесь что все разрешения предоставлены
- Проверьте что устройство поддерживает CameraX

## Требования

- **Android**: 7.0 (API 24) или выше
- **Камера**: Задняя камера с автофокусом
- **Интернет**: Wi-Fi или мобильный интернет
- **Разрешения**: Camera, Internet

## Лицензия

MIT License

