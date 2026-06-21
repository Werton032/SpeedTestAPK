from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
import threading
import requests
from plyer import browser

Window.clearcolor = (0.05, 0.08, 0.12, 1)


class SpeedTestLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 15

        self.title = Label(
            text="SPEED TEST PRO",
            font_size="26sp",
            bold=True,
            color=(0, 0.85, 1, 1),
            size_hint_y=None,
            height=60
        )
        self.add_widget(self.title)

        self.subtitle = Label(
            text="Информация о соединении",
            font_size="16sp",
            color=(0.7, 0.75, 0.8, 1),
            size_hint_y=None,
            height=35
        )
        self.add_widget(self.subtitle)

        self.ip_label = Label(text="IP: загрузка...", font_size="16sp")
        self.country_label = Label(text="Страна: загрузка...", font_size="16sp")
        self.city_label = Label(text="Город: загрузка...", font_size="16sp")
        self.isp_label = Label(text="Провайдер: загрузка...", font_size="16sp")
        self.region_label = Label(text="Регион: загрузка...", font_size="16sp")

        self.add_widget(self.ip_label)
        self.add_widget(self.country_label)
        self.add_widget(self.city_label)
        self.add_widget(self.isp_label)
        self.add_widget(self.region_label)

        self.status = Label(
            text="Загрузка данных...",
            font_size="14sp",
            color=(0.4, 1, 0.6, 1),
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.status)

        self.refresh_btn = Button(
            text="ОБНОВИТЬ ИНФО",
            size_hint_y=None,
            height=55,
            font_size="18sp",
            bold=True,
            background_color=(0.0, 0.75, 1.0, 1)
        )
        self.refresh_btn.bind(on_press=self.load_info)
        self.add_widget(self.refresh_btn)

        self.speed_btn = Button(
            text="ПРОВЕРИТЬ СКОРОСТЬ",
            size_hint_y=None,
            height=60,
            font_size="20sp",
            bold=True,
            background_color=(0.0, 0.9, 0.5, 1)
        )
        self.speed_btn.bind(on_press=self.open_speed_test)
        self.add_widget(self.speed_btn)

        Clock.schedule_once(lambda dt: self.load_info(), 0.5)

    def load_info(self, *args):
        self.status.text = "Получаем данные..."
        threading.Thread(target=self._load_info_thread, daemon=True).start()

    def _load_info_thread(self):
        try:
            data = requests.get("https://ipapi.co/json/", timeout=10).json()
            Clock.schedule_once(lambda dt: self.update_info(data))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_error(str(e)))

    def update_info(self, data):
        self.ip_label.text = f"IP: {data.get('ip', 'N/A')}"
        self.country_label.text = f"Страна: {data.get('country_name', 'N/A')}"
        self.city_label.text = f"Город: {data.get('city', 'N/A')}"
        self.isp_label.text = f"Провайдер: {data.get('org', 'N/A')}"
        self.region_label.text = f"Регион: {data.get('region', 'N/A')}"
        self.status.text = "Готово"

    def set_error(self, error_text):
        self.status.text = f"Ошибка: {error_text}"

    def open_speed_test(self, instance):
        browser.open("https://fast.com/")


class SpeedTestApp(App):
    def build(self):
        self.title = "Speed Test Pro"
        return SpeedTestLayout()


if __name__ == "__main__":
    SpeedTestApp().run()
