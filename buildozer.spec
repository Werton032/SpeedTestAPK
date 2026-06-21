[app]

title = NetSpeed Pro
package.name = netspeedpro
package.domain = org.netspeed

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.2.0

# ── Зависимости ───────────────────────────────────────
# Намеренно минимальные.
# НЕТ: speedtest-cli, requests, KivyMD, plyer (ломали сборку).
# Всё через stdlib: urllib, socket, threading, json.
requirements = python3,kivy==2.3.0,hostpython3

# ── Android ───────────────────────────────────────────
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.sdk = 33
android.build_tools_version = 33.0.2
android.accept_sdk_license = True

# Одна архитектура — стабильнее и быстрее сборки
android.archs = arm64-v8a

android.allow_backup = False

# ── Orientation ───────────────────────────────────────
orientation = portrait

# ── Fullscreen ────────────────────────────────────────
fullscreen = 0

# ── Log level ─────────────────────────────────────────
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
