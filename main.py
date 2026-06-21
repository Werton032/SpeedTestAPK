from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
import threading
import json
import time
import socket
import urllib.request


KV = '''
MDScreen:
    md_bg_color: 15/255, 20/255, 25/255, 1

    ScrollView:
        do_scroll_x: False

        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: [dp(16), dp(25), dp(16), dp(25)]
            spacing: dp(14)

            # ===== ЗАГОЛОВОК =====
            MDLabel:
                text: "⚡ SPEED TEST PRO"
                halign: "center"
                font_style: "H4"
                bold: True
                theme_text_color: "Custom"
                text_color: 0, 0.85, 1, 1
                adaptive_height: True

            MDLabel:
                text: "Проверка скорости интернета"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.48, 0.51, 0.58, 1
                adaptive_height: True
                font_style: "Body2"

            Widget:
                size_hint_y: None
                height: dp(5)

            # ===== КАРТОЧКА ИНФОРМАЦИИ =====
            MDCard:
                orientation: "vertical"
                padding: dp(18)
                spacing: dp(8)
                adaptive_height: True
                md_bg_color: 26/255, 31/255, 46/255, 1
                radius: [dp(18)]
                elevation: 0

                MDLabel:
                    text: "🌐 Информация о соединении"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 0, 0.85, 1, 1
                    adaptive_height: True
                    font_style: "Subtitle1"

                Widget:
                    size_hint_y: None
                    height: dp(4)

                # IP
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "🔹 IP адрес:"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        size_hint_x: 0.4
                        font_style: "Body2"
                    MDLabel:
                        text: app.ip_address
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.95
                        bold: True
                        adaptive_height: True
                        size_hint_x: 0.6
                        font_style: "Body2"

                # Страна
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "🏳 Страна:"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        size_hint_x: 0.4
                        font_style: "Body2"
                    MDLabel:
                        text: app.country
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.95
                        bold: True
                        adaptive_height: True
                        size_hint_x: 0.6
                        font_style: "Body2"

                # Город
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "🏙 Город:"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        size_hint_x: 0.4
                        font_style: "Body2"
                    MDLabel:
                        text: app.city
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.95
                        bold: True
                        adaptive_height: True
                        size_hint_x: 0.6
                        font_style: "Body2"

                # Провайдер
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "📡 Провайдер:"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        size_hint_x: 0.4
                        font_style: "Body2"
                    MDLabel:
                        text: app.isp
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.95
                        bold: True
                        adaptive_height: True
                        size_hint_x: 0.6
                        font_style: "Body2"

                # Регион
                MDBoxLayout:
                    adaptive_height: True
                    MDLabel:
                        text: "📍 Регион:"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        size_hint_x: 0.4
                        font_style: "Body2"
                    MDLabel:
                        text: app.region
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.95
                        bold: True
                        adaptive_height: True
                        size_hint_x: 0.6
                        font_style: "Body2"

            # ===== КАРТОЧКИ СКОРОСТИ =====
            MDBoxLayout:
                adaptive_height: True
                spacing: dp(8)

                # Download
                MDCard:
                    orientation: "vertical"
                    padding: [dp(8), dp(15)]
                    adaptive_height: True
                    md_bg_color: 26/255, 31/255, 46/255, 1
                    radius: [dp(18)]
                    elevation: 0

                    MDLabel:
                        text: "⬇ DOWNLOAD"
                        halign: "center"
                        bold: True
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0, 1, 0.53, 1
                        adaptive_height: True

                    MDLabel:
                        text: app.download_speed
                        halign: "center"
                        font_style: "H4"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        adaptive_height: True

                    MDLabel:
                        text: "Mbps"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        font_style: "Caption"

                # Upload
                MDCard:
                    orientation: "vertical"
                    padding: [dp(8), dp(15)]
                    adaptive_height: True
                    md_bg_color: 26/255, 31/255, 46/255, 1
                    radius: [dp(18)]
                    elevation: 0

                    MDLabel:
                        text: "⬆ UPLOAD"
                        halign: "center"
                        bold: True
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 0, 0.85, 1, 1
                        adaptive_height: True

                    MDLabel:
                        text: app.upload_speed
                        halign: "center"
                        font_style: "H4"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        adaptive_height: True

                    MDLabel:
                        text: "Mbps"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        font_style: "Caption"

                # Ping
                MDCard:
                    orientation: "vertical"
                    padding: [dp(8), dp(15)]
                    adaptive_height: True
                    md_bg_color: 26/255, 31/255, 46/255, 1
                    radius: [dp(18)]
                    elevation: 0

                    MDLabel:
                        text: "📶 PING"
                        halign: "center"
                        bold: True
                        font_style: "Caption"
                        theme_text_color: "Custom"
                        text_color: 1, 0.67, 0, 1
                        adaptive_height: True

                    MDLabel:
                        text: app.ping_value
                        halign: "center"
                        font_style: "H4"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        adaptive_height: True

                    MDLabel:
                        text: "ms"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.48, 0.51, 0.58, 1
                        adaptive_height: True
                        font_style: "Caption"

            # ===== СТАТУС =====
            MDLabel:
                text: app.status_text
                halign: "center"
                bold: True
                theme_text_color: "Custom"
                text_color: 0, 0.85, 1, 1
                adaptive_height: True
                font_style: "Subtitle1"

            # ===== ПРОГРЕСС =====
            MDProgressBar:
                value: app.progress_value
                color: 0, 0.85, 1, 1
                size_hint_y: None
                height: dp(6)

            Widget:
                size_hint_y: None
                height: dp(5)

            # ===== КНОПКА СТАРТ =====
            MDRaisedButton:
                text: "🚀  НАЧАТЬ ТЕСТ"
                pos_hint: {"center_x": 0.5}
                size_hint_x: 0.85
                size_hint_y: None
                height: dp(58)
                font_size: sp(18)
                md_bg_color: 0, 0.85, 1, 1
                text_color: 15/255, 20/255, 25/255, 1
                on_release: app.start_test()
                disabled: app.is_testing
                elevation: 0

            Widget:
                size_hint_y: None
                height: dp(10)

            # ===== ФУТЕР =====
            MDLabel:
                text: "Made with ❤ in Python | v1.0"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.29, 0.32, 0.38, 1
                font_style: "Caption"
                adaptive_height: True
'''


class SpeedTestProApp(MDApp):
    # Свойства интерфейса
    download_speed = StringProperty("0.00")
    upload_speed = StringProperty("0.00")
    ping_value = StringProperty("0")
    ip_address = StringProperty("Загрузка...")
    country = StringProperty("Загрузка...")
    city = StringProperty("Загрузка...")
    isp = StringProperty("Загрузка...")
    region = StringProperty("Загрузка...")
    status_text = StringProperty("Готов к тестированию")
    progress_value = NumericProperty(0)
    is_testing = BooleanProperty(False)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.title = "Speed Test Pro"
        return Builder.load_string(KV)

    def on_start(self):
        threading.Thread(target=self._fetch_ip_info, daemon=True).start()

    # ---------- IP INFO ----------
    def _fetch_ip_info(self):
        try:
            req = urllib.request.urlopen(
                "http://ip-api.com/json/?lang=ru", timeout=10
            )
            data = json.loads(req.read().decode())
            Clock.schedule_once(lambda dt: self._set_ip_info(data))
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._update(status_text=f"Ошибка IP: {e}")
            )

    def _set_ip_info(self, data):
        self.ip_address = data.get("query", "?")
        self.country = data.get("country", "?")
        self.city = data.get("city", "?")
        self.isp = data.get("isp", "?")
        self.region = data.get("regionName", "?")

    # ---------- ОБНОВЛЕНИЕ UI ----------
    def _update(self, **kwargs):
        def do(dt):
            for key, val in kwargs.items():
                setattr(self, key, val)
        Clock.schedule_once(do)

    # ---------- ЗАПУСК ТЕСТА ----------
    def start_test(self):
        if self.is_testing:
            return
        self.is_testing = True
        self.download_speed = "..."
        self.upload_speed = "..."
        self.ping_value = "..."
        self.progress_value = 0
        threading.Thread(target=self._run_test, daemon=True).start()

    def _run_test(self):
        try:
            # 1. PING
            self._update(status_text="📶 Измерение пинга...")
            ping = self._test_ping()
            self._update(ping_value=str(ping), progress_value=15)
            time.sleep(0.3)

            # 2. DOWNLOAD
            self._update(status_text="⬇️ Тест загрузки...")
            dl_speed = self._test_download()
            self._update(
                download_speed=f"{dl_speed:.2f}",
                progress_value=55
            )
            time.sleep(0.3)

            # 3. UPLOAD
            self._update(status_text="⬆️ Тест отдачи...")
            ul_speed = self._test_upload()
            self._update(
                upload_speed=f"{ul_speed:.2f}",
                progress_value=100
            )

            self._update(status_text="✅ Тест завершён!")

        except Exception as e:
            self._update(status_text=f"❌ Ошибка: {e}")
        finally:
            self._update(is_testing=False)

    # ---------- PING ----------
    def _test_ping(self):
        results = []
        for _ in range(5):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                start = time.time()
                sock.connect(("8.8.8.8", 53))
                elapsed = (time.time() - start) * 1000
                sock.close()
                results.append(elapsed)
            except Exception:
                pass
        return round(min(results)) if results else 0

    # ---------- DOWNLOAD ----------
    def _test_download(self):
        test_urls = [
            "http://speedtest.tele2.net/10MB.zip",
            "http://proof.ovh.net/files/10Mb.dat",
        ]

        total_bytes = 0
        start_time = time.time()

        for url in test_urls:
            try:
                req = urllib.request.urlopen(url, timeout=25)
                while True:
                    chunk = req.read(32768)
                    if not chunk:
                        break
                    total_bytes += len(chunk)

                    # Обновляем скорость в реальном времени
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        speed = (total_bytes * 8) / (elapsed * 1_000_000)
                        progress = 15 + min(40, 40 * total_bytes / 20_000_000)
                        self._update(
                            download_speed=f"{speed:.2f}",
                            progress_value=progress
                        )
            except Exception:
                pass

        elapsed = time.time() - start_time
        if elapsed == 0 or total_bytes == 0:
            return 0.0
        return (total_bytes * 8) / (elapsed * 1_000_000)

    # ---------- UPLOAD ----------
    def _test_upload(self):
        data = b"X" * 5_000_000  # 5 МБ данных

        start_time = time.time()
        try:
            req = urllib.request.Request(
                "http://speedtest.tele2.net/upload.php",
                data=data,
                method="POST",
                headers={"Content-Type": "application/octet-stream"},
            )
            urllib.request.urlopen(req, timeout=30)
        except Exception:
            pass

        elapsed = time.time() - start_time
        if elapsed == 0:
            return 0.0
        return (len(data) * 8) / (elapsed * 1_000_000)


if __name__ == "__main__":
    SpeedTestProApp().run()