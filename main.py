"""
NetSpeed Pro — Android Speed Test App
Stack: Python 3.11 + Kivy 2.3.0 + Buildozer
No speedtest-cli. No requests. No KivyMD.
Pure Kivy + urllib + threading.
"""

import threading
import time
import json
import math
import socket
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import (
    Color, Ellipse, Line, Rectangle,
    RoundedRectangle
)
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import (
    NumericProperty, StringProperty,
    BooleanProperty, ListProperty
)
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# ── Цвета ──────────────────────────────────────────────
C_BG        = get_color_from_hex('#0B1220')
C_CARD      = get_color_from_hex('#151D31')
C_CYAN      = get_color_from_hex('#00D9FF')
C_GREEN     = get_color_from_hex('#00FFA3')
C_WHITE     = get_color_from_hex('#FFFFFF')
C_MUTED     = get_color_from_hex('#94A3B8')
C_ACCENT2   = get_color_from_hex('#7C3AED')
C_ERROR     = get_color_from_hex('#FF4444')
C_DARK_CARD = get_color_from_hex('#0D1526')

Window.clearcolor = C_BG

# ── Константы теста ────────────────────────────────────
PING_HOSTS = [
    ('8.8.8.8',    53),
    ('1.1.1.1',    53),
    ('208.67.222.222', 53),
]
DOWNLOAD_URLS = [
    'http://speedtest.ftp.otenet.gr/files/test1Mb.db',
    'http://ipv4.download.thinkbroadband.com/1MB.zip',
    'http://proof.ovh.net/files/1Mb.dat',
]
UPLOAD_URL   = 'https://httpbin.org/post'
DOWNLOAD_SEC = 8    # секунд на download
UPLOAD_SEC   = 6    # секунд на upload
CHUNK        = 4096

# ── IP API ─────────────────────────────────────────────
IP_APIS = [
    'https://ipwho.is/',
    'https://ipapi.co/json/',
]


# ══════════════════════════════════════════════════════
#  Утилиты сети
# ══════════════════════════════════════════════════════

def safe_fetch_json(url: str, timeout: int = 8) -> dict | None:
    """Скачать JSON без внешних библиотек. None при ошибке."""
    try:
        req = Request(url, headers={'User-Agent': 'NetSpeedPro/1.0'})
        with urlopen(req, timeout=timeout) as r:
            raw = r.read().decode('utf-8', errors='replace')
            return json.loads(raw)
    except Exception:
        return None


def fetch_ip_info() -> dict:
    """Пробуем несколько API по очереди."""
    for url in IP_APIS:
        data = safe_fetch_json(url)
        if not data:
            continue

        # Нормализуем разные форматы ответа
        ip  = (data.get('ip') or data.get('query') or '—')
        isp = (data.get('connection', {}).get('isp')
               or data.get('org')
               or data.get('isp')
               or '—')
        return {
            'ip':      ip,
            'country': data.get('country') or data.get('country_name') or '—',
            'region':  data.get('region') or '—',
            'city':    data.get('city') or '—',
            'isp':     isp,
        }
    return {'ip': '—', 'country': '—', 'region': '—',
            'city': '—', 'isp': '—'}


def measure_ping(host: str, port: int, attempts: int = 4) -> float:
    """TCP-ping. Возвращает средний ms или -1."""
    times = []
    for _ in range(attempts):
        try:
            t0 = time.perf_counter()
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            times.append((time.perf_counter() - t0) * 1000)
            time.sleep(0.05)
        except Exception:
            pass
    return round(sum(times) / len(times), 1) if times else -1.0


def best_ping() -> float:
    """Пингуем несколько хостов, берём лучший."""
    results = []
    for host, port in PING_HOSTS:
        v = measure_ping(host, port)
        if v > 0:
            results.append(v)
    return min(results) if results else -1.0


def measure_download(cb_speed, stop_event) -> float:
    """
    Качаем чанками N секунд, считаем Mbps.
    cb_speed(mbps) вызывается каждые ~300ms.
    """
    deadline = time.perf_counter() + DOWNLOAD_SEC
    total    = 0
    window_bytes = 0
    window_t     = time.perf_counter()

    url = DOWNLOAD_URLS[0]
    try:
        req = Request(url, headers={'User-Agent': 'NetSpeedPro/1.0'})
        with urlopen(req, timeout=15) as r:
            while time.perf_counter() < deadline and not stop_event.is_set():
                chunk = r.read(CHUNK)
                if not chunk:
                    # файл закончился — качаем по новой
                    r.close()
                    req2 = Request(url, headers={'User-Agent': 'NetSpeedPro/1.0'})
                    r = urlopen(req2, timeout=15)
                    continue
                total        += len(chunk)
                window_bytes += len(chunk)
                now = time.perf_counter()
                if now - window_t >= 0.3:
                    mbps = (window_bytes * 8) / ((now - window_t) * 1_000_000)
                    cb_speed(round(mbps, 2))
                    window_bytes = 0
                    window_t     = now
    except Exception:
        pass

    elapsed = DOWNLOAD_SEC  # фиксированное окно
    if total == 0:
        return 0.0
    return round((total * 8) / (elapsed * 1_000_000), 2)


def measure_upload(cb_speed, stop_event) -> float:
    """
    Отправляем рандомные данные POST на httpbin.
    cb_speed(mbps) каждые ~300ms.
    """
    BLOCK    = 256 * 1024   # 256 KB за раз
    deadline = time.perf_counter() + UPLOAD_SEC
    total    = 0
    window_bytes = 0
    window_t     = time.perf_counter()

    payload = b'X' * BLOCK

    while time.perf_counter() < deadline and not stop_event.is_set():
        try:
            req = Request(
                UPLOAD_URL,
                data=payload,
                headers={
                    'User-Agent':    'NetSpeedPro/1.0',
                    'Content-Type':  'application/octet-stream',
                    'Content-Length': str(len(payload)),
                }
            )
            with urlopen(req, timeout=10):
                pass
            total        += len(payload)
            window_bytes += len(payload)
        except Exception:
            break

        now = time.perf_counter()
        if now - window_t >= 0.3:
            mbps = (window_bytes * 8) / ((now - window_t) * 1_000_000)
            cb_speed(round(mbps, 2))
            window_bytes = 0
            window_t     = now

    elapsed = min(time.perf_counter() - (deadline - UPLOAD_SEC), UPLOAD_SEC)
    if total == 0 or elapsed < 0.1:
        return 0.0
    return round((total * 8) / (elapsed * 1_000_000), 2)


# ══════════════════════════════════════════════════════
#  Gauge Widget
# ══════════════════════════════════════════════════════

class GaugeWidget(Widget):
    """
    Круговой спидометр.
    speed_val  — текущее значение (0..max_val)
    max_val    — максимум шкалы
    stage_text — PING / DOWNLOAD / UPLOAD / READY
    """
    speed_val  = NumericProperty(0.0)
    max_val    = NumericProperty(150.0)
    stage_text = StringProperty('READY')
    unit_text  = StringProperty('Mbps')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(
            speed_val=self._redraw,
            stage_text=self._redraw,
            size=self._redraw,
            pos=self._redraw,
        )

    def _redraw(self, *_):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        r  = min(self.width, self.height) * 0.42

        with self.canvas:
            # ── фоновый круг ──────────────────────────
            Color(*C_DARK_CARD)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

            # ── внешний обод ──────────────────────────
            Color(*C_CYAN[:3], 0.18)
            Line(circle=(cx, cy, r), width=dp(3))

            # ── пустая дуга (трек) ────────────────────
            Color(*C_MUTED[:3], 0.25)
            Line(
                ellipse=(cx - r + dp(8), cy - r + dp(8),
                         (r - dp(8)) * 2, (r - dp(8)) * 2,
                         225, 225 + 270),
                width=dp(10), cap='round',
            )

            # ── заполненная дуга ──────────────────────
            ratio   = min(self.speed_val / max(self.max_val, 1), 1.0)
            arc_deg = ratio * 270
            if arc_deg > 1:
                Color(*C_CYAN)
                Line(
                    ellipse=(cx - r + dp(8), cy - r + dp(8),
                             (r - dp(8)) * 2, (r - dp(8)) * 2,
                             225, 225 + arc_deg),
                    width=dp(10), cap='round',
                )

            # ── деления ───────────────────────────────
            Color(*C_MUTED[:3], 0.4)
            for i in range(11):
                angle = math.radians(225 + i * 27)
                r1 = r - dp(20)
                r2 = r - dp(28) if i % 5 == 0 else r - dp(25)
                x1 = cx + r1 * math.cos(angle)
                y1 = cy + r1 * math.sin(angle)
                x2 = cx + r2 * math.cos(angle)
                y2 = cy + r2 * math.sin(angle)
                Line(points=[x1, y1, x2, y2], width=dp(1.2))

        # Labels через canvas — используем Kivy Label внутри
        self._draw_labels(cx, cy, r, ratio)

    def _draw_labels(self, cx, cy, r, ratio):
        """Обновляем дочерние Label."""
        self.clear_widgets()

        # Скорость (большие цифры)
        speed_str = f'{self.speed_val:.1f}' if self.speed_val < 100 \
                    else f'{int(self.speed_val)}'
        spd = Label(
            text=speed_str,
            font_size=sp(38),
            bold=True,
            color=C_WHITE,
            size_hint=(None, None),
            size=(r * 1.6, dp(50)),
            pos=(cx - r * 0.8, cy),
        )
        self.add_widget(spd)

        # Единица
        unit = Label(
            text=self.unit_text,
            font_size=sp(13),
            color=C_CYAN,
            size_hint=(None, None),
            size=(r * 1.6, dp(22)),
            pos=(cx - r * 0.8, cy - dp(22)),
        )
        self.add_widget(unit)

        # Стадия
        stage_color = {
            'PING':     C_WHITE,
            'DOWNLOAD': C_CYAN,
            'UPLOAD':   C_GREEN,
            'READY':    C_MUTED,
            'DONE':     C_GREEN,
            'ERROR':    C_ERROR,
        }.get(self.stage_text, C_WHITE)

        stg = Label(
            text=self.stage_text,
            font_size=sp(12),
            color=stage_color,
            size_hint=(None, None),
            size=(r * 1.6, dp(20)),
            pos=(cx - r * 0.8, cy - dp(46)),
        )
        self.add_widget(stg)


# ══════════════════════════════════════════════════════
#  Карточка
# ══════════════════════════════════════════════════════

class InfoCard(BoxLayout):
    """Тёмная карточка с иконкой-символом, заголовком и значением."""

    def __init__(self, icon: str, title: str, value: str = '—', **kw):
        super().__init__(orientation='vertical',
                         padding=dp(12), spacing=dp(4),
                         size_hint_y=None, height=dp(72), **kw)
        self._icon_ch  = icon
        self._title_ch = title
        self.val_label = None
        self._build(value)
        self.bind(size=self._draw_bg, pos=self._draw_bg)

    def _build(self, value):
        top = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(6))
        top.add_widget(Label(
            text=self._icon_ch, font_size=sp(14),
            color=C_CYAN, size_hint_x=None, width=dp(20),
            halign='left', valign='middle',
        ))
        top.add_widget(Label(
            text=self._title_ch, font_size=sp(11),
            color=C_MUTED, halign='left', valign='middle',
        ))
        self.add_widget(top)

        self.val_label = Label(
            text=value, font_size=sp(15),
            color=C_WHITE, bold=True,
            halign='left', valign='middle',
        )
        self.val_label.bind(size=self.val_label.setter('text_size'))
        self.add_widget(self.val_label)

    def set_value(self, v: str):
        if self.val_label:
            self.val_label.text = v

    def _draw_bg(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_CARD)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])


# ══════════════════════════════════════════════════════
#  Карточка результата теста
# ══════════════════════════════════════════════════════

class ResultCard(BoxLayout):
    def __init__(self, icon, title, **kw):
        super().__init__(orientation='vertical',
                         padding=dp(10), spacing=dp(2),
                         size_hint_y=None, height=dp(80), **kw)
        self.val_label = None
        self._build(icon, title)
        self.bind(size=self._draw_bg, pos=self._draw_bg)

    def _build(self, icon, title):
        self.add_widget(Label(
            text=icon, font_size=sp(20), color=C_CYAN,
            size_hint_y=None, height=dp(26),
        ))
        self.val_label = Label(
            text='—', font_size=sp(20), bold=True, color=C_WHITE,
            size_hint_y=None, height=dp(28),
        )
        self.add_widget(self.val_label)
        self.add_widget(Label(
            text=title, font_size=sp(10), color=C_MUTED,
            size_hint_y=None, height=dp(16),
        ))

    def set_value(self, v: str):
        if self.val_label:
            self.val_label.text = v

    def _draw_bg(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_CARD)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])


# ══════════════════════════════════════════════════════
#  Кнопка Start
# ══════════════════════════════════════════════════════

class StartButton(Widget):
    active = BooleanProperty(True)

    def __init__(self, on_press_cb, **kw):
        super().__init__(size_hint=(None, None),
                         size=(dp(130), dp(130)), **kw)
        self._cb       = on_press_cb
        self._glow_a   = 1.0
        self._glow_dir = -1
        self._pulse    = None
        self.bind(size=self._draw, pos=self._draw, active=self._draw)
        Clock.schedule_once(self._start_pulse, 0.5)

    def _start_pulse(self, *_):
        self._pulse = Clock.schedule_interval(self._update_pulse, 0.05)

    def _update_pulse(self, *_):
        if not self.active:
            return
        self._glow_a += self._glow_dir * 0.03
        if self._glow_a <= 0.3:
            self._glow_dir = 1
        elif self._glow_a >= 1.0:
            self._glow_dir = -1
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r = dp(55)
        with self.canvas:
            # glow
            if self.active:
                Color(*C_CYAN[:3], self._glow_a * 0.3)
                Ellipse(pos=(cx - r - dp(12), cy - r - dp(12)),
                        size=((r + dp(12)) * 2, (r + dp(12)) * 2))
            # circle
            col = C_CYAN if self.active else C_MUTED
            Color(*col)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
            # inner
            Color(*C_BG)
            ir = r - dp(4)
            Ellipse(pos=(cx - ir, cy - ir), size=(ir * 2, ir * 2))

        self.clear_widgets()
        txt  = 'START' if self.active else '...'
        tclr = C_CYAN  if self.active else C_MUTED
        lbl = Label(
            text=txt, font_size=sp(16), bold=True, color=tclr,
            size_hint=(None, None), size=(dp(130), dp(30)),
            pos=(cx - dp(65), cy - dp(15)),
        )
        self.add_widget(lbl)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and self.active:
            self._cb()
            return True
        return super().on_touch_down(touch)


# ══════════════════════════════════════════════════════
#  Главный экран
# ══════════════════════════════════════════════════════

class MainScreen(FloatLayout):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._stop_event = threading.Event()
        self._testing    = False
        self._results    = {'ping': None, 'dl': None, 'ul': None}
        self._build_ui()
        Clock.schedule_once(self._load_ip_info, 0.8)

    # ── Построение UI ─────────────────────────────────

    def _build_ui(self):
        with self.canvas.before:
            Color(*C_BG)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._upd_bg, pos=self._upd_bg)

        root = BoxLayout(
            orientation='vertical',
            padding=dp(16), spacing=dp(12),
            size_hint=(1, 1),
        )

        # ── заголовок ─────────────────────────────────
        title = Label(
            text='[b]NetSpeed[/b] [color=#00D9FF]Pro[/color]',
            markup=True,
            font_size=sp(22),
            color=C_WHITE,
            size_hint_y=None, height=dp(40),
        )
        root.add_widget(title)

        # ── Gauge + кнопка ────────────────────────────
        gauge_box = FloatLayout(size_hint_y=None, height=dp(230))

        self.gauge = GaugeWidget(
            size_hint=(None, None), size=(dp(210), dp(210)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )
        gauge_box.add_widget(self.gauge)

        self.start_btn = StartButton(
            on_press_cb=self._on_start,
            pos_hint={'center_x': 0.5, 'y': 0.02},
        )
        # Кнопка будет снизу gauge_box — делаем отдельно
        root.add_widget(gauge_box)

        # ── Кнопка Start ──────────────────────────────
        btn_wrap = FloatLayout(size_hint_y=None, height=dp(140))
        self.start_btn = StartButton(
            on_press_cb=self._on_start,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )
        btn_wrap.add_widget(self.start_btn)
        root.add_widget(btn_wrap)

        # ── Статус ────────────────────────────────────
        self.status_lbl = Label(
            text='Нажмите START для начала теста',
            font_size=sp(12), color=C_MUTED,
            size_hint_y=None, height=dp(22),
        )
        root.add_widget(self.status_lbl)

        # ── Результаты ping/dl/ul ─────────────────────
        res_row = BoxLayout(
            orientation='horizontal',
            spacing=dp(8),
            size_hint_y=None, height=dp(90),
        )
        self.card_ping = ResultCard('◎', 'PING  ms')
        self.card_dl   = ResultCard('↓', 'DOWNLOAD Mbps')
        self.card_ul   = ResultCard('↑', 'UPLOAD Mbps')
        res_row.add_widget(self.card_ping)
        res_row.add_widget(self.card_dl)
        res_row.add_widget(self.card_ul)
        root.add_widget(res_row)

        # ── IP-инфо карточки ──────────────────────────
        self.ip_lbl      = InfoCard('◉', 'IP-адрес',   'Загрузка...')
        self.country_lbl = InfoCard('⚑', 'Страна',     'Загрузка...')
        self.city_lbl    = InfoCard('⌖', 'Город',      'Загрузка...')
        self.isp_lbl     = InfoCard('◈', 'Провайдер',  'Загрузка...')

        for card in [self.ip_lbl, self.country_lbl,
                     self.city_lbl, self.isp_lbl]:
            root.add_widget(card)

        self.add_widget(root)

    def _upd_bg(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    # ── IP-инфо ───────────────────────────────────────

    def _load_ip_info(self, *_):
        self._set_status('Определяем IP и местоположение...')
        threading.Thread(target=self._thread_ip, daemon=True).start()

    def _thread_ip(self):
        info = fetch_ip_info()
        Clock.schedule_once(lambda dt: self._apply_ip(info), 0)

    def _apply_ip(self, info: dict):
        self.ip_lbl.set_value(info['ip'])
        self.country_lbl.set_value(
            f"{info['country']}  {info['region']}")
        self.city_lbl.set_value(info['city'])
        self.isp_lbl.set_value(info['isp'])
        if info['ip'] == '—':
            self._set_status('Не удалось получить данные. Проверьте интернет.')
        else:
            self._set_status('Нажмите START для начала теста')

    # ── Speed test ────────────────────────────────────

    def _on_start(self):
        if self._testing:
            return
        self._testing = True
        self._stop_event.clear()
        self.start_btn.active = False
        self._results = {'ping': None, 'dl': None, 'ul': None}
        self.card_ping.set_value('—')
        self.card_dl.set_value('—')
        self.card_ul.set_value('—')
        self.gauge.speed_val  = 0
        self.gauge.stage_text = 'PING'
        self.gauge.unit_text  = 'ms'
        self._set_status('Измерение Ping...')
        threading.Thread(target=self._thread_test, daemon=True).start()

    def _thread_test(self):
        # ── 1. PING ───────────────────────────────────
        ping_ms = best_ping()
        self._results['ping'] = ping_ms
        Clock.schedule_once(lambda dt: self._on_ping_done(ping_ms), 0)

        # ── 2. DOWNLOAD ───────────────────────────────
        Clock.schedule_once(lambda dt: self._pre_download(), 0)
        time.sleep(0.15)

        dl_mbps = measure_download(
            cb_speed=lambda v: Clock.schedule_once(
                lambda dt, vv=v: self._upd_gauge(vv, 'DOWNLOAD', 'Mbps'), 0),
            stop_event=self._stop_event,
        )
        self._results['dl'] = dl_mbps
        Clock.schedule_once(lambda dt: self._on_dl_done(dl_mbps), 0)

        # ── 3. UPLOAD ─────────────────────────────────
        Clock.schedule_once(lambda dt: self._pre_upload(), 0)
        time.sleep(0.15)

        ul_mbps = measure_upload(
            cb_speed=lambda v: Clock.schedule_once(
                lambda dt, vv=v: self._upd_gauge(vv, 'UPLOAD', 'Mbps'), 0),
            stop_event=self._stop_event,
        )
        self._results['ul'] = ul_mbps
        Clock.schedule_once(lambda dt: self._on_done(), 0)

    # ── UI callbacks (main thread) ────────────────────

    def _on_ping_done(self, ms: float):
        txt = f'{ms:.0f}' if ms > 0 else '—'
        self.card_ping.set_value(txt)
        self.gauge.stage_text = 'PING'
        self.gauge.unit_text  = 'ms'
        self.gauge.max_val    = 300
        if ms > 0:
            anim = Animation(speed_val=ms, duration=0.5)
            anim.start(self.gauge)

    def _pre_download(self):
        self._set_status('Измерение скорости загрузки...')
        self.gauge.speed_val  = 0
        self.gauge.stage_text = 'DOWNLOAD'
        self.gauge.unit_text  = 'Mbps'
        self.gauge.max_val    = 150

    def _on_dl_done(self, mbps: float):
        txt = f'{mbps:.1f}' if mbps > 0 else '—'
        self.card_dl.set_value(txt)

    def _pre_upload(self):
        self._set_status('Измерение скорости отдачи...')
        self.gauge.speed_val  = 0
        self.gauge.stage_text = 'UPLOAD'
        self.gauge.unit_text  = 'Mbps'
        self.gauge.max_val    = 100

    def _on_done(self):
        self._testing = False
        self.start_btn.active = True
        self.gauge.stage_text = 'DONE'

        p  = self._results['ping']
        dl = self._results['dl']
        ul = self._results['ul']

        if dl is not None and dl > 0:
            anim = Animation(speed_val=dl, duration=0.6)
            anim.start(self.gauge)
            self.card_dl.set_value(f'{dl:.1f}')
        if ul is not None:
            self.card_ul.set_value(f'{ul:.1f}' if ul > 0 else '—')

        ok = any(v and v > 0 for v in [p, dl, ul])
        if ok:
            self._set_status('Тест завершён ✓')
        else:
            self.gauge.stage_text = 'ERROR'
            self._set_status('Не удалось выполнить тест. Проверьте интернет.')

    def _upd_gauge(self, val: float, stage: str, unit: str):
        self.gauge.stage_text = stage
        self.gauge.unit_text  = unit
        anim = Animation(speed_val=val, duration=0.25)
        anim.start(self.gauge)

    def _set_status(self, text: str):
        self.status_lbl.text = text


# ══════════════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════════════

class NetSpeedApp(App):
    def build(self):
        self.title = 'NetSpeed Pro'
        return MainScreen()

    def on_stop(self):
        # Останавливаем поток при закрытии
        screen = self.root
        if hasattr(screen, '_stop_event'):
            screen._stop_event.set()


if __name__ == '__main__':
    NetSpeedApp().run()
