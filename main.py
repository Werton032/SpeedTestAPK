from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

import threading
import json
import traceback
from urllib.request import urlopen, Request

Window.clearcolor = (0.06, 0.08, 0.12, 1)


class SpeedTestLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 12

        self.title_label = Label(
            text="SPEED TEST PRO",
            font_size="24sp",
            size_hint_y=None,
            height=60,
            color=(0, 0.85, 1, 1)
        )
        self.add_widget(self.title_label)

        self.info_label = Label(
            text="Информация о соединении",
            font_size="16sp",
            size_hint_y=None,
            height=35,
            color=(0.8, 0.85, 0.9, 1)
        )
        self.add_widget(self.info_label)

        self.ip_label = Label(text="IP: загрузка...")
        self.country_label = Label(text="Страна: загрузка...")
        self.city_label = Label(text="Город: загрузка...")
        self.isp_label = Label(text="Провайдер: загрузка...")
        self.region_label = Label(text="Регион: загрузка...")

        self.add_widget(self.ip_label)
        self.add_widget(self.country_label)
        self.add_widget(self.city_label)
        self.add_widget(self.isp_label)
        self.add_widget(self.region_label)

        self.status_label = Label(
            text="Запуск...",
            size_hint_y=None,
            height=40,
            color=(0.3, 1, 0.5, 1)
        )
        self.add_widget(self.status_label)

        self.error_label = Label(
            text="",
            font_size="12sp",
            color=(1, 0.4, 0.4, 1)
        )
        self.add_widget(self.error_label)

        self.refresh_button = Button(
            text="ОБНОВИТЬ ИНФОРМАЦИЮ",
            size_hint_y=None,
            height=55,
            background_color=(0.0, 0.7, 1.0, 1)
        )
        self.refresh_button.bind(on_press=self.load_info)
        self.add_widget(self.refresh_button)

        self.speed_button = Button(
            text="ОТКРЫТЬ FAST.COM",
            size_hint_y=None,
            height=60,
            background_color=(0.0, 0.9, 0.5, 1)
        )
        self.speed_button.bind(on_press=self.open_speedtest)
        self.add_widget(self.speed_button)

        Clock.schedule_once(lambda dt: self.load_info(), 0.5)

    def load_info(self, *args):
        self.status_label.text = "Получаем данные..."
        self.error_label.text = ""
        threading.Thread(target=self._load_info_thread, daemon=True).start()

    def _load_info_thread(self):
        try:
            req = Request(
                "https://ipapi.co/json/",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            Clock.schedule_once(lambda dt: self.update_info(data))
        except Exception:
            error_text = traceback.format_exc()
            Clock.schedule_once(lambda dt: self.show_error(error_text))

    def update_info(self, data):
        self.ip_label.text = f"IP: {data.get('ip', 'N/A')}"
        self.country_label.text = f"Страна: {data.get('country_name', 'N/A')}"
        self.city_label.text = f"Город: {data.get('city', 'N/A')}"
        self.isp_label.text = f"Провайдер: {data.get('org', 'N/A')}"
        self.region_label.text = f"Регион: {data.get('region', 'N/A')}"
        self.status_label.text = "Готово"

    def show_error(self, error_text):
        self.status_label.text = "Ошибка загрузки"
        self.error_label.text = error_text[:400]

    def open_speedtest(self, *args):
        try:
            if platform == "android":
                from jnius import autoclass, cast
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")

                intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://fast.com"))
                currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
                currentActivity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open("https://fast.com")

            self.status_label.text = "Открываю fast.com..."
        except Exception:
            error_text = traceback.format_exc()
            self.show_error(error_text)


class SpeedTestApp(App):
    def build(self):
        return SpeedTestLayout()


if __name__ == "__main__":
    SpeedTestApp().run()
