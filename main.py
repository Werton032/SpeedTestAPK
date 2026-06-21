"""
Speed Test Pro — чистый Kivy, без KivyMD.
Совместим с Android через Buildozer + python-for-android.
"""

import threading
import json
import time
import socket
import urllib.request
import ssl
import math

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import (
    Color, RoundedRectangle, Ellipse, Line,
    PushMatrix, PopMatrix, Rotate, Translate,
)
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.lang import Builder


# ──────────────────────────────────────────────
# Цветовая палитра
# ──────────────────────────────────────────────
BG       = (11/255, 18/255, 32/255, 1)
CARD     = (21/255, 29/255, 49/255, 1)
CYAN     = (0, 0.85, 1, 1)
GREEN    = (0, 1, 0.64, 1)
WHITE    = (1, 1, 1, 1)
MUTED    = (0.57, 0.64, 0.73, 1)
BTN_TEXT = (11/255, 18/255, 32/255, 1)
ORANGE   = (1, 0.6, 0.1, 1)

# ──────────────────────────────────────────────
# Speed-test endpoints
# ──────────────────────────────────────────────
DOWNLOAD_URLS = [
    "https://speed.hetzner.de/10MB.bin",
    "https://speedtest.tele2.net/10MB.zip",
]
UPLOAD_URL = "https://httpbin.org/post"
IP_API_PRIMARY   = "https://ipwho.is/"
IP_API_SECONDARY = "https://ipapi.co/json/"


# ══════════════════════════════════════════════
# Вспомогательный виджет: карточка (RoundedRect)
# ══════════════════════════════════════════════
class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(16), dp(14), dp(16), dp(14)]
        self.spacing = dp(6)
        with self.canvas.before:
            Color(*CARD)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(20)]
            )
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size


# ══════════════════════════════════════════════
# Gauge — круговой спидометр (canvas)
# ══════════════════════════════════════════════
class SpeedGauge(Widget):
    speed_value  = NumericProperty(0)   # текущее значение для дуги
    display_text = StringProperty("0.00")
    unit_text    = StringProperty("Mbps")
    stage_text   = StringProperty("")

    MAX_SPEED = 200.0   # максимум шкалы
    ARC_START = 220     # угол начала дуги (градусы CCW от +X)
    ARC_SWEEP = 280     # общий диапазон дуги

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw, size=self._redraw,
            speed_value=self._redraw,
            display_text=self._redraw,
            unit_text=self._redraw,
            stage_text=self._redraw,
        )

    def _redraw(self, *_):
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        r  = min(self.width, self.height) / 2 * 0.78

        with self.canvas:
            # --- фон дуги ---
            Color(1, 1, 1, 0.07)
            Line(
                circle=(cx, cy, r,
                        -(self.ARC_START),
                        -(self.ARC_START - self.ARC_SWEEP)),
                width=dp(10), cap="round",
            )

            # --- заполненная дуга ---
            ratio = min(max(self.speed_value / self.MAX_SPEED, 0), 1)
            sweep = self.ARC_SWEEP * ratio
            if sweep > 0:
                # Цвет зависит от скорости
                if ratio < 0.4:
                    Color(*CYAN)
                elif ratio < 0.75:
                    Color(*GREEN)
                else:
                    Color(*ORANGE)
                Line(
                    circle=(cx, cy, r,
                            -(self.ARC_START),
                            -(self.ARC_START - sweep)),
                    width=dp(10), cap="round",
                )

            # --- центральный текст: число ---
            # Рисуется через Label — оверлей
        # Label'ы добавляем программно (обновляем)
        self._update_labels(cx, cy, r)

    def _update_labels(self, cx, cy, r):
        # Удаляем старые лейблы
        for child in list(self.children):
            self.remove_widget(child)

        # Значение скорости
        lbl_val = Label(
            text=self.display_text,
            font_size=sp(36),
            bold=True,
            color=WHITE,
            size_hint=(None, None),
        )
        lbl_val.texture_update()
        lbl_val.size = lbl_val.texture_size
        lbl_val.pos  = (cx - lbl_val.width / 2, cy - lbl_val.height / 2 + dp(8))
        self.add_widget(lbl_val)

        # Единица
        lbl_unit = Label(
            text=self.unit_text,
            font_size=sp(13),
            color=MUTED,
            size_hint=(None, None),
        )
        lbl_unit.texture_update()
        lbl_unit.size = lbl_unit.texture_size
        lbl_unit.pos  = (cx - lbl_unit.width / 2, cy - lbl_val.height / 2 - dp(6))
        self.add_widget(lbl_unit)

        # Стадия
        if self.stage_text:
            lbl_stage = Label(
                text=self.stage_text,
                font_size=sp(12),
                bold=True,
                color=CYAN,
                size_hint=(None, None),
            )
            lbl_stage.texture_update()
            lbl_stage.size = lbl_stage.texture_size
            lbl_stage.pos  = (cx - lbl_stage.width / 2, cy + r * 0.55)
            self.add_widget(lbl_stage)

    def animate_to(self, target_speed, display_text=None, unit="Mbps", stage=""):
        Animation.cancel_all(self, "speed_value")
        anim = Animation(speed_value=target_speed, duration=0.45, t="out_quad")
        anim.start(self)
        self.unit_text    = unit
        self.stage_text   = stage
        if display_text is not None:
            self.display_text = display_text

    def reset(self):
        Animation.cancel_all(self, "speed_value")
        self.speed_value  = 0
        self.display_text = "0.00"
        self.unit_text    = "Mbps"
        self.stage_text   = ""


# ══════════════════════════════════════════════
# Прогресс-бар
# ══════════════════════════════════════════════
class NeonProgressBar(Widget):
    value = NumericProperty(0)  # 0..100

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, value=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            # Фон
            Color(1, 1, 1, 0.07)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            # Заполнение
            if self.value > 0:
                Color(*CYAN)
                fill_w = self.width * self.value / 100
                RoundedRectangle(
                    pos=self.pos,
                    size=(fill_w, self.height),
                    radius=[dp(4)],
                )

    def animate_to(self, val):
        Animation.cancel_all(self, "value")
        Animation(value=val, duration=0.4, t="out_quad").start(self)


# ══════════════════════════════════════════════
# Строка информации (метка + значение)
# ══════════════════════════════════════════════
class InfoRow(BoxLayout):
    def __init__(self, icon, title, value_prop, app, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
            spacing=dp(8),
            **kwargs,
        )
        lbl_title = Label(
            text=f"{icon}  {title}",
            color=MUTED,
            font_size=sp(13),
            size_hint_x=0.38,
            halign="left",
            valign="middle",
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        self.add_widget(lbl_title)

        self._val_label = Label(
            text=getattr(app, value_prop),
            color=WHITE,
            font_size=sp(13),
            bold=True,
            size_hint_x=0.62,
            halign="left",
            valign="middle",
        )
        self._val_label.bind(size=self._val_label.setter("text_size"))
        self.add_widget(self._val_label)

        # Подписка на изменение свойства
        app.bind(**{value_prop: self._on_prop})

    def _on_prop(self, _, value):
        self._val_label.text = value


# ══════════════════════════════════════════════
# Мини-карточка результата (Download / Upload / Ping)
# ══════════════════════════════════════════════
class ResultCard(Card):
    def __init__(self, icon, title, title_color, value_prop, unit, app, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(90)

        lbl_icon = Label(
            text=f"{icon} {title}",
            color=title_color,
            font_size=sp(11),
            bold=True,
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle",
        )
        lbl_icon.bind(size=lbl_icon.setter("text_size"))
        self.add_widget(lbl_icon)

        self._val = Label(
            text=getattr(app, value_prop),
            color=WHITE,
            font_size=sp(26),
            bold=True,
            size_hint_y=None,
            height=dp(36),
            halign="center",
            valign="middle",
        )
        self._val.bind(size=self._val.setter("text_size"))
        self.add_widget(self._val)

        lbl_unit = Label(
            text=unit,
            color=MUTED,
            font_size=sp(11),
            size_hint_y=None,
            height=dp(16),
            halign="center",
            valign="middle",
        )
        lbl_unit.bind(size=lbl_unit.setter("text_size"))
        self.add_widget(lbl_unit)

        app.bind(**{value_prop: self._on_prop})

    def _on_prop(self, _, value):
        self._val.text = value


# ══════════════════════════════════════════════
# Кнопка Start
# ══════════════════════════════════════════════
class StartButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal  = ""
        self.background_color   = (0, 0, 0, 0)
        self.color              = BTN_TEXT
        self.font_size          = sp(17)
        self.bold               = True
        self.size_hint          = (0.85, None)
        self.height             = dp(58)
        with self.canvas.before:
            self._btn_color = Color(*CYAN)
            self._btn_rect  = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(30)]
            )
        self.bind(pos=self._upd, size=self._upd, disabled=self._upd_color)

    def _upd(self, *_):
        self._btn_rect.pos  = self.pos
        self._btn_rect.size = self.size

    def _upd_color(self, _, disabled):
        if disabled:
            self._btn_color.rgba = (0.3, 0.3, 0.3, 0.6)
        else:
            self._btn_color.rgba = CYAN


# ══════════════════════════════════════════════
# Главный экран
# ══════════════════════════════════════════════
class MainScreen(ScrollView):
    pass


# ══════════════════════════════════════════════
# Приложение
# ══════════════════════════════════════════════
class SpeedTestProApp(App):
    # Данные
    ip_address     = StringProperty("Загрузка...")
    country        = StringProperty("Загрузка...")
    city           = StringProperty("Загрузка...")
    isp            = StringProperty("Загрузка...")
    region         = StringProperty("Загрузка...")
    status_text    = StringProperty("Готов к тестированию")
    download_speed = StringProperty("—")
    upload_speed   = StringProperty("—")
    ping_value     = StringProperty("—")
    is_testing     = BooleanProperty(False)

    def build(self):
        Window.clearcolor = BG
        self.title = "Speed Test Pro"
        return self._build_ui()

    # ──────────────────────────────
    # Построение UI
    # ──────────────────────────────
    def _build_ui(self):
        root = ScrollView(do_scroll_x=False)

        outer = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(16), dp(30), dp(16), dp(30)],
            spacing=dp(14),
        )
        outer.bind(minimum_height=outer.setter("height"))
        root.add_widget(outer)

        # --- Заголовок ---
        lbl_title = Label(
            text="⚡ SPEED TEST PRO",
            font_size=sp(26),
            bold=True,
            color=CYAN,
            size_hint_y=None,
            height=dp(40),
            halign="center",
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        outer.add_widget(lbl_title)

        lbl_sub = Label(
            text="Проверка скорости интернета",
            font_size=sp(13),
            color=MUTED,
            size_hint_y=None,
            height=dp(22),
            halign="center",
        )
        lbl_sub.bind(size=lbl_sub.setter("text_size"))
        outer.add_widget(lbl_sub)

        # --- Gauge ---
        self.gauge = SpeedGauge(size_hint_y=None, height=dp(210))
        outer.add_widget(self.gauge)

        # --- Статус ---
        self._status_lbl = Label(
            text=self.status_text,
            font_size=sp(14),
            bold=True,
            color=CYAN,
            size_hint_y=None,
            height=dp(26),
            halign="center",
        )
        self._status_lbl.bind(size=self._status_lbl.setter("text_size"))
        outer.add_widget(self._status_lbl)
        self.bind(status_text=lambda _, v: setattr(self._status_lbl, "text", v))

        # --- Progress bar ---
        self.progress = NeonProgressBar(size_hint_y=None, height=dp(6))
        outer.add_widget(self.progress)

        outer.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # --- Карточки результатов ---
        row_cards = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(90),
            spacing=dp(8),
        )
        row_cards.add_widget(
            ResultCard("⬇", "DOWNLOAD", GREEN,  "download_speed", "Mbps", self)
        )
        row_cards.add_widget(
            ResultCard("⬆", "UPLOAD",   CYAN,   "upload_speed",   "Mbps", self)
        )
        row_cards.add_widget(
            ResultCard("📶", "PING",    ORANGE, "ping_value",     "ms",   self)
        )
        outer.add_widget(row_cards)

        # --- Кнопка ---
        btn = StartButton(text="🚀  НАЧАТЬ ТЕСТ")
        btn.pos_hint = {"center_x": 0.5}
        btn.bind(on_release=lambda _: self.start_test())
        self.bind(is_testing=lambda _, v: setattr(btn, "disabled", v))
        outer.add_widget(btn)

        outer.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # --- Карточка IP-информации ---
        ip_card = Card(size_hint_y=None, height=dp(170))
        ip_title = Label(
            text="🌐  Информация о соединении",
            font_size=sp(14),
            bold=True,
            color=CYAN,
            size_hint_y=None,
            height=dp(22),
            halign="left",
        )
        ip_title.bind(size=ip_title.setter("text_size"))
        ip_card.add_widget(ip_title)
        ip_card.add_widget(Widget(size_hint_y=None, height=dp(4)))

        for icon, title, prop in [
            ("🔹", "IP адрес",  "ip_address"),
            ("🏳", "Страна",    "country"),
            ("🏙", "Город",     "city"),
            ("📡", "Провайдер", "isp"),
            ("📍", "Регион",    "region"),
        ]:
            ip_card.add_widget(InfoRow(icon, title, prop, self))

        outer.add_widget(ip_card)

        # --- Футер ---
        lbl_footer = Label(
            text="Made with ❤  in Python | v2.0",
            font_size=sp(11),
            color=(0.3, 0.35, 0.42, 1),
            size_hint_y=None,
            height=dp(20),
            halign="center",
        )
        lbl_footer.bind(size=lbl_footer.setter("text_size"))
        outer.add_widget(lbl_footer)

        return root

    def on_start(self):
        threading.Thread(target=self._fetch_ip_info, daemon=True).start()

    # ──────────────────────────────
    # IP Info
    # ──────────────────────────────
    def _fetch_ip_info(self):
        data = self._try_fetch_json(IP_API_PRIMARY)
        if data and data.get("ip"):
            Clock.schedule_once(lambda dt: self._apply_ip(data, "primary"))
            return
        data = self._try_fetch_json(IP_API_SECONDARY)
        if data and data.get("ip"):
            Clock.schedule_once(lambda dt: self._apply_ip(data, "secondary"))
            return
        Clock.schedule_once(
            lambda dt: self._safe_set(
                ip_address="Нет соединения",
                country="—", city="—", isp="—", region="—",
            )
        )

    def _try_fetch_json(self, url):
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.urlopen(url, timeout=10, context=ctx)
            return json.loads(req.read().decode("utf-8", errors="replace"))
        except Exception:
            return None

    def _apply_ip(self, data, source):
        if source == "primary":   # ipwho.is
            self._safe_set(
                ip_address = data.get("ip", "—"),
                country    = data.get("country", "—"),
                city       = data.get("city", "—"),
                isp        = data.get("connection", {}).get("org", "—"),
                region     = data.get("region", "—"),
            )
        else:                     # ipapi.co
            self._safe_set(
                ip_address = data.get("ip", "—"),
                country    = data.get("country_name", "—"),
                city       = data.get("city", "—"),
                isp        = data.get("org", "—"),
                region     = data.get("region", "—"),
            )

    # ──────────────────────────────
    # Speed test
    # ──────────────────────────────
    def start_test(self):
        if self.is_testing:
            return
        self.is_testing = True
        self._safe_set(
            download_speed="...",
            upload_speed="...",
            ping_value="...",
            status_text="Подготовка...",
        )
        self.gauge.reset()
        self.progress.value = 0
        threading.Thread(target=self._run_test, daemon=True).start()

    def _run_test(self):
        try:
            # 1. PING
            self._ui(status_text="📶  Измерение пинга...")
            ping = self._test_ping()
            ping_str = str(ping) if ping > 0 else "—"
            self._ui(ping_value=ping_str)
            Clock.schedule_once(lambda dt: self.gauge.animate_to(
                min(ping, 200), display_text=ping_str, unit="ms", stage="PING"
            ))
            Clock.schedule_once(lambda dt: self.progress.animate_to(20))
            time.sleep(0.6)

            # 2. DOWNLOAD
            self._ui(status_text="⬇  Загрузка...")
            Clock.schedule_once(lambda dt: self.gauge.animate_to(
                0, display_text="0.00", unit="Mbps", stage="DOWNLOAD"
            ))
            dl = self._test_download()
            dl_str = f"{dl:.2f}"
            self._ui(download_speed=dl_str)
            Clock.schedule_once(lambda dt: self.gauge.animate_to(
                dl, display_text=dl_str, unit="Mbps", stage="DOWNLOAD ✓"
            ))
            Clock.schedule_once(lambda dt: self.progress.animate_to(60))
            time.sleep(0.6)

            # 3. UPLOAD
            self._ui(status_text="⬆  Отдача...")
            Clock.schedule_once(lambda dt: self.gauge.animate_to(
                0, display_text="0.00", unit="Mbps", stage="UPLOAD"
            ))
            ul = self._test_upload()
            ul_str = f"{ul:.2f}"
            self._ui(upload_speed=ul_str)
            Clock.schedule_once(lambda dt: self.gauge.animate_to(
                ul, display_text=ul_str, unit="Mbps", stage="UPLOAD ✓"
            ))
            Clock.schedule_once(lambda dt: self.progress.animate_to(100))

            self._ui(status_text="✅  Тест завершён!")

        except Exception as exc:
            import traceback
            traceback.print_exc()   # только в лог
            self._ui(status_text="❌  Ошибка теста. Попробуйте снова.")
        finally:
            self._ui(is_testing=False)

    # ──────────────────────────────
    # Ping
    # ──────────────────────────────
    def _test_ping(self):
        results = []
        for _ in range(5):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4)
                t0 = time.time()
                sock.connect(("8.8.8.8", 53))
                results.append((time.time() - t0) * 1000)
                sock.close()
            except Exception:
                pass
        return round(min(results)) if results else 0

    # ──────────────────────────────
    # Download — реальный, с live-обновлением
    # ──────────────────────────────
    def _test_download(self):
        total_bytes = 0
        start_time  = time.time()
        limit_secs  = 10        # максимальная длительность
        limit_bytes = 20 * 1024 * 1024  # 20 МБ

        for url in DOWNLOAD_URLS:
            if time.time() - start_time > limit_secs:
                break
            try:
                ctx = ssl.create_default_context()
                resp = urllib.request.urlopen(url, timeout=12, context=ctx)
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        speed = (total_bytes * 8) / (elapsed * 1_000_000)
                        spd_str = f"{speed:.2f}"
                        # live gauge
                        def _upd_dl(dt, s=speed, ss=spd_str):
                            self.gauge.animate_to(
                                s, display_text=ss, unit="Mbps", stage="DOWNLOAD"
                            )
                            # прогресс 20→60
                            frac = min(elapsed / limit_secs, 1)
                            self.progress.animate_to(20 + 40 * frac)
                        Clock.schedule_once(_upd_dl)
                    if total_bytes >= limit_bytes:
                        break
                    if time.time() - start_time > limit_secs:
                        break
            except Exception:
                pass

        elapsed = time.time() - start_time
        if elapsed == 0 or total_bytes == 0:
            return 0.0
        return (total_bytes * 8) / (elapsed * 1_000_000)

    # ──────────────────────────────
    # Upload — POST на httpbin.org (реальный TCP upload)
    # ──────────────────────────────
    def _test_upload(self):
        data_size = 3 * 1024 * 1024   # 3 МБ — баланс скорости и времени
        payload   = b"\x00" * data_size
        start     = time.time()
        success   = False
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                UPLOAD_URL,
                data=payload,
                method="POST",
                headers={"Content-Type": "application/octet-stream"},
            )
            urllib.request.urlopen(req, timeout=20, context=ctx)
            success = True
        except Exception:
            pass

        elapsed = time.time() - start
        if not success or elapsed == 0:
            return 0.0
        return (data_size * 8) / (elapsed * 1_000_000)

    # ──────────────────────────────
    # Helpers
    # ──────────────────────────────
    def _ui(self, **kwargs):
        """Безопасное обновление свойств из потока."""
        def _do(dt):
            for k, v in kwargs.items():
                setattr(self, k, v)
        Clock.schedule_once(_do)

    def _safe_set(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


if __name__ == "__main__":
    SpeedTestProApp().run()
