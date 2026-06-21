[app]
title = Speed Test Pro
package.name = speedtestpro
package.domain = org.speedtestpro
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0

# Только стабильные зависимости — без KivyMD, без pillow, без certifi
requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

# API и NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Архитектуры — только arm64, чтобы сборка была быстрее и стабильнее
android.archs = arm64-v8a

android.allow_backup = True

# Разрешаем cleartext только если нужно (на самом деле все URL уже HTTPS)
# android.manifest.extra = <uses-permission android:name="android.permission.CLEARTEXT_TRAFFIC" />

# p4a — стабильная ветка
p4a.branch = master

# Gradle
android.gradle_dependencies =

log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
