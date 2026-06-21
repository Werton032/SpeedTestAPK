\from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
import json

KV = '''
#:import dp kivy.metrics.dp

<GlowButton>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 0.05, 0.08, 0.12, 1
    bold: True
    font_size: '18sp'
    canvas.before:
        Color:
            rgba: 0.0, 0.85, 1.0, 0.12 + self.pulse * 0.12
        RoundedRectangle:
            pos: self.x - dp(6) - self.pulse * dp(6), self.y - dp(6) - self.pulse * dp(6)
            size: self.width + dp(12) + self.pulse * dp(12), self.height + dp(12) + self.pulse * dp(12)
            radius: [dp(28),]
        Color:
            rgba: 0.0, 0.85, 1.0, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(24),]

<PulseRadar>:
    canvas:
        Color:
            rgba: 0.0, 0.85, 1.0, 0.05
        Ellipse:
            pos: self.center_x - dp(112), self.center_y - dp(112)
            size: dp(224), dp(224)

        Color:
            rgba: 0.0, 0.85, 1.0, 0.08
        Line:
            circle: (self.center_x, self.center_y, dp(92))
            width: 1.2

        Color:
            rgba: 0.0, 0.85, 1.0, 0.10
        Line:
            circle: (self.center_x, self.center_y, dp(72))
            width: 1.4

        Color:
            rgba: 0.0, 0.85, 1.0, 0.12 + self.pulse * 0.12
        Line:
            circle: (self.center_x, self.center_y, dp(56) + self.pulse * dp(16))
            width: 2

<StatCard>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(8)
    size_hint_y: None
    height: dp(112)
    opacity: 1
    canvas.before:
        Color:
            rgba: 0.10, 0.13, 0.21, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(22),]
    Label:
        text: root.title
        size_hint_y: None
        height: dp(22)
        font_size: '11sp'
        bold: True
        color: 0.53, 0.63, 0.76, 1
        text_size: self.size
        halign: 'left'
        valign: 'middle'
    Label:
        text: root.value
        font_size: '18sp'
        bold: True
        color: 1, 1, 1, 1
        text_size: self.size
        halign: 'left'
        valign: 'middle'

<RootLayout>:
    orientation: 'vertical'
    padding: dp(18)
    spacing: dp(14)

    canvas.before:
        Color:
            rgba: 0.04, 0.06, 0.10, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(58)
        spacing: dp(10)

        Label:
            text: '⚡'
            size_hint_x: None
            width: dp(40)
            font_size: '30sp'
            color: 0.0, 0.85, 1.0, 1

        BoxLayout:
            orientation: 'vertical'

            Label:
                text: 'SPEED TEST PRO'
                font_size: '24sp'
                bold: True
                color: 0.0, 0.85, 1.0, 1
                text_size: self.size
                halign: 'left'
                valign: 'middle'

            Label:
                text: 'Android edition • стиль Ookla'
                font_size: '12sp'
                color: 0.55, 0.63, 0.76, 1
                text_size: self.size
                halign: 'left'
                valign: 'middle'

    RelativeLayout:
        size_hint_y: None
        height: dp(245)

        PulseRadar:
            id: radar
            size_hint: None, None
            size: dp(250), dp(250)
            center: self.center

        Label:
            text: '⚡'
            font_size: '68sp'
            color: 0.0, 0.85, 1.0, 1
            center: self.center_x, self.center_y + dp(12)

        Label:
            text: 'LIVE NETWORK'
            font_size: '12sp'
            bold: True
            color: 0.55, 0.63, 0.76, 1
            center: self.center_x, self.center_y - dp(28)

    GridLayout:
        cols: 2
        spacing: dp(12)
        size_hint_y: None
        height: self.minimum_height

        StatCard:
            id: card_ip
            title: 'IP АДРЕС'
            value: 'Загрузка...'

        StatCard:
            id: card_country
            title: 'СТРАНА'
            value: 'Загрузка...'

        StatCard:
            id: card_city
            title: 'ГОРОД'
            value: 'Загрузка...'

        StatCard:
            id: card_isp
            title: 'ПРОВАЙДЕР'
            value: 'Загрузка...'

        StatCard:
            id: card_region
            title: 'РЕГИОН'
            value: 'Загрузка...'

        StatCard:
            id: card_state
            title: 'СТАТУС'
            value: 'Ожидание'

    Label:
        id: status_label
        text: 'Запуск...'
        size_hint_y: None
        height: dp(28)
        font_size: '14sp'
        color: 0.0, 1.0, 0.65, 1

    Label:
        id: error_label
        text: ''
        size_hint_y: None
        height: dp(42)
        font_size: '12sp'
        color: 1.0, 0.42, 0.42, 1
        text_size: self.width, None
        halign: 'center'
        valign: 'middle'

    GlowButton:
        id: start_btn
        text: 'ОТКРЫТЬ SPEED TEST'
        size_hint_y: None
        height: dp(60)
        on_release: root.open_speedtest()

    Button:
        text: 'ОБНОВИТЬ ДАННЫЕ'
        size_hint_y: None
        height: dp(48)
        background_normal: ''
        background_down: ''
        background_color: 0, 0, 0, 0
        color: 0.86, 0.91, 0.98, 1
        bold: True
        on_release: root.fetch_ip_data()
        canvas.before:
            Color:
                rgba: 0.10, 0.13, 0.21, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(20),]

    Label:
        text: 'Для точного теста скорости кнопка откроет Fast.com во внешнем браузере'
        size_hint_y: None
        height: dp(40)
        font_size: '11sp'
        color: 0.48, 0.57, 0.70, 1
        text_size: self.width, None
        halign: 'center'
        valign: 'middle'
'''


class GlowButton(Button):
    pulse = NumericProperty(0)


class PulseRadar(Widget):
    pulse = NumericProperty(0)


class StatCard(BoxLayout):
    title = StringProperty("")
    value = StringProperty("—")


class RootLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apis = [
            "https://ipwho.is/",
            "https://ipapi.co/json/"
        ]
        self._loading_event = None
        Clock.schedule_once(self.start_animations, 0.2)
        Clock.schedule_once(lambda dt: self.fetch_ip_data(), 0.7)

    def start_animations(self, *args):
        Animation.cancel_all(self.ids.radar)
        radar_anim = Animation(pulse=1, duration=1.3, t='out_quad') + Animation(pulse=0, duration=1.3, t='in_out_quad')
        radar_anim.repeat = True
        radar_anim.start(self.ids.radar)

        Animation.cancel_all(self.ids.start_btn)
        btn_anim = Animation(pulse=1, duration=1.0, t='out_quad') + Animation(pulse=0, duration=1.0, t='in_out_quad')
        btn_anim.repeat = True
        btn_anim.start(self.ids.start_btn)

    def start_loading_text(self):
        self.stop_loading_text()
        self._dots = 0
        self._loading_event = Clock.schedule_interval(self._animate_loading_text, 0.45)

    def stop_loading_text(self):
        if self._loading_event:
            self._loading_event.cancel()
            self._loading_event = None

    def _animate_loading_text(self, dt):
        self._dots = (self._dots + 1) % 4
        dots = "." * self._dots
        self.ids.status_label.text = f"Получаю данные{dots}"
        self.ids.card_state.value = "Загрузка"

    def fetch_ip_data(self, *args):
        self.ids.error_label.text = ""
        self.ids.status_label.text = "Подключаюсь..."
        self.start_loading_text()
        self._request_api(0)

    def _request_api(self, index):
        url = self.apis[index]
        headers = {
            "User-Agent": "Mozilla/5.0 SpeedTestPro"
        }

        UrlRequest(
            url,
            req_headers=headers,
            timeout=12,
            verify=False,
            on_success=lambda req, result: self._on_success(index, result),
            on_error=lambda req, err: self._on_fail(index, err),
            on_failure=lambda req, err: self._on_fail(index, err)
        )

    def _on_success(self, index, result):
        try:
            if isinstance(result, bytes):
                result = result.decode("utf-8", "ignore")
            if isinstance(result, str):
                result = json.loads(result)

            data = self._normalize_result(result)
            self._apply_data(data)
        except Exception as e:
            self._on_fail(index, e)

    def _on_fail(self, index, error):
        if index + 1 < len(self.apis):
            self._request_api(index + 1)
            return

        self.stop_loading_text()
        self.ids.status_label.text = "Не удалось получить данные"
        self.ids.error_label.text = "Проверь интернет или попробуй ещё раз через кнопку «Обновить данные»"
        self.ids.card_state.value = "Ошибка сети"

    def _normalize_result(self, result):
        if not isinstance(result, dict):
            raise ValueError("Некорректный ответ сервера")

        # Формат ipwho.is
        if "success" in result:
            if result.get("success") is False:
                raise ValueError(result.get("message", "Сервис вернул ошибку"))

            connection = result.get("connection") or {}
            return {
                "ip": result.get("ip", "—"),
                "country": result.get("country", "—"),
                "city": result.get("city", "—"),
                "region": result.get("region", "—"),
                "isp": connection.get("isp") or connection.get("org") or "—"
            }

        # Формат ipapi.co
        return {
            "ip": result.get("ip", "—"),
            "country": result.get("country_name", "—"),
            "city": result.get("city", "—"),
            "region": result.get("region", "—"),
            "isp": result.get("org") or result.get("isp") or "—"
        }

    def _apply_data(self, data):
        self.stop_loading_text()

        self.ids.card_ip.value = str(data.get("ip", "—"))
        self.ids.card_country.value = str(data.get("country", "—"))
        self.ids.card_city.value = str(data.get("city", "—"))
        self.ids.card_region.value = str(data.get("region", "—"))
        self.ids.card_isp.value = str(data.get("isp", "—"))
        self.ids.card_state.value = "Готово"

        self.ids.status_label.text = "Соединение успешно определено"
        self.ids.error_label.text = ""

        for widget in [
            self.ids.card_ip,
            self.ids.card_country,
            self.ids.card_city,
            self.ids.card_isp,
            self.ids.card_region,
            self.ids.card_state
        ]:
            widget.opacity = 0

        delay = 0
        for widget in [
            self.ids.card_ip,
            self.ids.card_country,
            self.ids.card_city,
            self.ids.card_isp,
            self.ids.card_region,
            self.ids.card_state
        ]:
            anim = Animation(opacity=1, duration=0.25, t='out_quad')
            Clock.schedule_once(lambda dt, w=widget, a=anim: a.start(w), delay)
            delay += 0.05

    def open_speedtest(self):
        try:
            self.ids.status_label.text = "Открываю Fast.com..."
            self.ids.card_state.value = "Запуск теста"

            if platform == "android":
                from jnius import autoclass, cast
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")

                currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
                intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://fast.com"))
                currentActivity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open("https://fast.com")
        except Exception:
            self.ids.status_label.text = "Не удалось открыть браузер"
            self.ids.card_state.value = "Ошибка запуска"
            self.ids.error_label.text = "Браузер не открылся. Попробуй установить Chrome или другой браузер."


Builder.load_string(KV)


class SpeedTestApp(App):
    def build(self):
        return RootLayout()


if __name__ == "__main__":
    SpeedTestApp().run()
