from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
import json


Window.clearcolor = (0.04, 0.07, 0.12, 1)


class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=20, **kwargs)

        self.status = Label(
            text="Нажмите кнопку для определения IP",
            color=(1, 1, 1, 1),
            font_size=18
        )

        self.result = Label(
            text="",
            color=(0, 0.85, 1, 1),
            font_size=16
        )

        self.btn = Button(
            text="Определить IP",
            size_hint=(1, 0.2),
            background_color=(0, 0.8, 1, 1)
        )
        self.btn.bind(on_release=self.get_ip)

        self.add_widget(self.status)
        self.add_widget(self.result)
        self.add_widget(self.btn)

    def get_ip(self, instance):
        self.status.text = "Загрузка..."
        self.btn.disabled = True

        UrlRequest(
            "https://ipwho.is/",
            on_success=self.success,
            on_error=self.error,
            on_failure=self.error,
            timeout=10
        )

    def success(self, req, result):
        try:
            data = result
            if isinstance(result, str):
                data = json.loads(result)

            text = (
                f"IP: {data.get('ip')}\n"
                f"Страна: {data.get('country')}\n"
                f"Город: {data.get('city')}\n"
                f"Регион: {data.get('region')}\n"
                f"Провайдер: {data.get('connection', {}).get('isp')}"
            )

            self.result.text = text
            self.status.text = "Соединение определено"
        except Exception:
            self.status.text = "Ошибка обработки данных"

        self.btn.disabled = False

    def error(self, *args):
        self.status.text = "Ошибка соединения"
        self.btn.disabled = False


class SpeedTestApp(App):
    def build(self):
        return Root()


if __name__ == "__main__":
    SpeedTestApp().run()
