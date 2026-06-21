[app]
title = Speed Test Pro
package.name = speedtestpro
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.2.1,kivymd==1.2.0,pillow,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.allow_backup = True
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1