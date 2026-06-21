[app]
title = Speed Test Pro
package.name = speedtestpro
package.domain = org.speedtestpro
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0

requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Явно фиксируем build-tools — buildozer по умолчанию берёт 37 у которой проблемы с лицензией
android.build_tools_version = 33.0.2

android.archs = arm64-v8a
android.allow_backup = True

p4a.branch = master

log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
