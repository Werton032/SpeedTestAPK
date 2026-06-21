[app]
title = Speed Test Pro
package.name = speedtestpro
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas
version = 1.3

requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
