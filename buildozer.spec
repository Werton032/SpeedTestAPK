[app]

title = SpeedTest
package.name = speedtest
package.domain = org.speedtest.app

source.dir = .
source.include_exts = py,png,jpg,kv

version = 1.0

requirements = python3,kivy,urllib3

orientation = portrait

fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

android.permissions = INTERNET,ACCESS_NETWORK_STATE

log_level = 2

[buildozer]

log_level = 2
warn_on_root = 1
