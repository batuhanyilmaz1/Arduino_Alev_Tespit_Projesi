"""
Ana dashboard: üst çubuk, sol kontrol, orta radar, sağ kartlar, alt log.
"""
from __future__ import annotations

import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Union

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config import DEFAULT_ENV_PATH, ROOT_DIR, AppConfig, load_config, normalize_serial_port
from serial_handler import AlarmMessage, SerialBridge, StateMessage
from services.log_service import EventType, FilterKind, LogService
from services.mock_bridge import MockDataBridge
from services.notification_service import AlarmPayload, NotificationService
from ui.control_panel import ControlPanel
from ui.radar_widget import RadarWidget, region_label, region_status_text
from ui.styles import APP_STYLESHEET, COL_DANGER, COL_OK, COL_WARN, alarm_stylesheet


IoBridge = Union[SerialBridge, MockDataBridge]


class MainWindow(QMainWindow):
    def __init__(self, cfg: AppConfig, *, mock_mode: bool = False) -> None:
        super().__init__()
        self._cfg = cfg
        self._mock_mode = mock_mode
        self._logs = LogService()
        self._notify = NotificationService(cfg)

        self._io: Optional[IoBridge] = None
        self._connected = False

        self._last_angle = 0
        self._last_fire = False
        self._scanning = True
        self._alarm_latched = False
        self._alarm_angle: Optional[int] = None
        self._last_snap_ts = 0.0
        self._last_notify_str = "—"
        self._last_hw_monotonic = 0.0
        self._demo_angle = 40.0
        self._demo_dir = 1.0

        self.setWindowTitle("Güvenli Hat — Yangın Takip Merkezi")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 680)

        self._build_ui()
        self.setStyleSheet(APP_STYLESHEET)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

        self._alarm_blink = QTimer(self)
        self._alarm_blink.setInterval(500)
        self._alarm_blink.timeout.connect(self._toggle_alarm_topbar)
        self._alarm_blink_on = False

        if mock_mode:
            self._io = MockDataBridge()
            self._wire_io(self._io)
            self.controls.set_mock_mode(True)
            self.controls.port_edit.setText(cfg.serial_port)
        else:
            self._io = SerialBridge()
            self._wire_io(self._io)
            self.controls.set_mock_mode(False)
            self.controls.port_edit.setText(cfg.serial_port)
            self.controls.baud_spin.setValue(cfg.baud_rate)

        self._log_db(
            EventType.SYSTEM,
            "Uygulama başlatıldı."
            + (" (Mock mod)" if mock_mode else ""),
        )
        if cfg.telegram_enabled:
            self._log_db(EventType.SYSTEM, "Telegram bildirimi: .env ile yapılandırıldı.")

        self._viz_timer = QTimer(self)
        self._viz_timer.timeout.connect(self._refresh_radar_display)
        self._viz_timer.start(45)
        self._refresh_radar_display()

        self._apply_control_states()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("TopBar")
        self.top_bar.setFixedHeight(56)
        tb = QHBoxLayout(self.top_bar)
        brand = QLabel("GÜVENLİ HAT — Yangın Takip")
        brand.setObjectName("Brand")
        tb.addWidget(brand)
        tb.addStretch(1)
        self.status_pill = QLabel("Bağlantı yok")
        self.status_pill.setObjectName("StatusPill")
        tb.addWidget(self.status_pill)
        self.clock_lbl = QLabel()
        self.clock_lbl.setObjectName("Clock")
        tb.addWidget(self.clock_lbl)
        root.addWidget(self.top_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.controls = ControlPanel()
        self.controls.connect_clicked.connect(self._on_connect)
        self.controls.disconnect_clicked.connect(self._on_disconnect)
        self.controls.telegram_test_clicked.connect(self._on_telegram_test)

        center = QWidget()
        center.setObjectName("CenterPanel")
        cv = QVBoxLayout(center)
        cv.setContentsMargins(12, 12, 12, 12)
        cv.setSpacing(12)
        self.radar = RadarWidget()
        self.summary_card = QFrame()
        self.summary_card.setObjectName("SummaryCard")
        summary_layout = QVBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(16, 14, 16, 14)
        summary_layout.setSpacing(4)
        self.lbl_angle = QLabel("Tarama açısı: —")
        self.lbl_angle.setObjectName("SummaryTitle")
        self.lbl_region = QLabel("Bağlantı bekleniyor.")
        self.lbl_region.setObjectName("SummaryText")
        self.lbl_region.setWordWrap(True)
        summary_layout.addWidget(self.lbl_angle)
        summary_layout.addWidget(self.lbl_region)
        cv.addWidget(self.radar, 1)
        cv.addWidget(self.summary_card)

        right = QWidget()
        right.setObjectName("RightPanel")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(8, 12, 12, 12)
        rv.setSpacing(10)
        self.card_sys, self.val_sys = self._make_card("Sistem durumu")
        self.card_link, self.val_link = self._make_card("Bağlantı")
        self.card_servo, self.val_servo = self._make_card("Tarama durumu")
        self.card_angle, self.val_angle = self._make_card("Bölge analizi")
        self.card_alarm, self.val_alarm = self._make_card("Alarm özeti")
        self.card_notify, self.val_notify = self._make_card("Son bildirim")
        for card in (
            self.card_sys,
            self.card_link,
            self.card_servo,
            self.card_angle,
            self.card_alarm,
            self.card_notify,
        ):
            rv.addWidget(card)
        rv.addStretch(1)

        splitter.addWidget(self.controls)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([300, 700, 260])

        root.addWidget(splitter, 1)

        log_frame = QFrame()
        log_frame.setObjectName("LogDock")
        lv = QVBoxLayout(log_frame)
        lv.setContentsMargins(12, 8, 12, 12)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Olay günlüğü"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tüm olaylar", "Sadece alarmlar", "Sadece sistem"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        bar.addWidget(self.filter_combo)
        bar.addStretch(1)
        self.btn_clear_log = QPushButton("Günlüğü temizle")
        self.btn_export = QPushButton("CSV dışa aktar")
        self.btn_clear_log.clicked.connect(self._on_clear_log)
        self.btn_export.clicked.connect(self._on_export)
        bar.addWidget(self.btn_clear_log)
        bar.addWidget(self.btn_export)
        lv.addLayout(bar)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(4000)
        self.log_text.setMinimumHeight(160)
        lv.addWidget(self.log_text)
        root.addWidget(log_frame)

        self.val_sys.setText("Hazır")
        self.val_link.setText("Kapalı")
        self.val_servo.setText("—")
        self.val_angle.setText("—")
        self.val_alarm.setText("Alarm yok")
        self.val_notify.setText("—")

    def _make_card(self, title: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("Card")
        v = QVBoxLayout(card)
        t = QLabel(title)
        t.setObjectName("CardTitle")
        val = QLabel("—")
        val.setObjectName("CardValue")
        val.setWordWrap(True)
        v.addWidget(t)
        v.addWidget(val)
        return card, val

    @staticmethod
    def _angle_region_summary(angle: int) -> str:
        return f"{angle}° • {region_label(angle)}"

    def _set_live_region_summary(self, angle: int) -> None:
        self.val_angle.setText(self._angle_region_summary(angle))
        self.lbl_angle.setText(f"Tarama açısı: {angle}°")
        self.lbl_region.setText(region_status_text(angle, alarm=False))

    def _set_alarm_region_summary(self, angle: int) -> None:
        message = region_status_text(angle, alarm=True)
        self.val_angle.setText(self._angle_region_summary(angle))
        self.val_alarm.setText(message)
        self.lbl_angle.setText(f"Alev tespit açısı: {angle}°")
        self.lbl_region.setText(message)

    def _wire_io(self, bridge: IoBridge) -> None:
        bridge.state_update.connect(self._on_state, Qt.ConnectionType.QueuedConnection)
        bridge.alarm_event.connect(self._on_alarm, Qt.ConnectionType.QueuedConnection)
        bridge.clear_event.connect(self._on_clear, Qt.ConnectionType.QueuedConnection)
        bridge.link_changed.connect(
            self._on_link, Qt.ConnectionType.QueuedConnection
        )
        bridge.io_error.connect(self._on_io_err, Qt.ConnectionType.QueuedConnection)

    def _filter_kind(self) -> FilterKind:
        i = self.filter_combo.currentIndex()
        if i == 1:
            return "alarms"
        if i == 2:
            return "system"
        return "all"

    def _on_filter_changed(self, _i: int) -> None:
        self._refresh_log_view()

    def _refresh_log_view(self) -> None:
        self.log_text.clear()
        rows = self._logs.fetch(self._filter_kind(), limit=800)
        for r in rows:
            ts = datetime.fromtimestamp(r.ts_unix).strftime("%H:%M:%S")
            ang = f"{r.angle}°" if r.angle is not None else "—"
            line = f"[{ts}] {r.event_type} | açı={ang} | {r.message}"
            self.log_text.appendPlainText(line)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    @staticmethod
    def _event_type_str(event_type: str | EventType) -> str:
        if isinstance(event_type, Enum):
            return str(event_type.value)
        return str(event_type)

    def _log_db(
        self,
        event_type: str | EventType,
        message: str,
        *,
        angle: Optional[int] = None,
        alarm_active: bool = False,
    ) -> None:
        et = self._event_type_str(event_type)
        self._logs.add(
            et,
            message,
            angle=angle,
            alarm_active=alarm_active,
        )
        if self._filter_allows_event(et):
            ts = datetime.now().strftime("%H:%M:%S")
            ang = f"{angle}°" if angle is not None else "—"
            self.log_text.appendPlainText(
                f"[{ts}] {et} | açı={ang} | {message}"
            )

    def _filter_allows_event(self, event_type: str | EventType) -> bool:
        et = self._event_type_str(event_type)
        fk = self._filter_kind()
        if fk == "all":
            return True
        if fk == "alarms":
            return et in (EventType.ALARM.value, EventType.CLEAR.value)
        return et in (
            EventType.SYSTEM.value,
            EventType.ERROR.value,
            EventType.COMMAND.value,
            EventType.SERIAL.value,
            EventType.STATE_SNAPSHOT.value,
        )

    def _on_connect(self) -> None:
        if self._io is None:
            return
        if self._mock_mode:
            assert isinstance(self._io, MockDataBridge)
            self._io.start()
            self._connected = True
            self._log_db(EventType.SYSTEM, "Mock veri akışı başlatıldı.")
        else:
            assert isinstance(self._io, SerialBridge)
            raw = self.controls.port_edit.text().strip() or self._cfg.serial_port
            port = normalize_serial_port(raw)
            if port != raw:
                self.controls.port_edit.setText(port)
            baud = int(self.controls.baud_spin.value())
            self._io.connect_port(port, baud)
        self._apply_control_states()

    def _on_disconnect(self) -> None:
        if self._io is None:
            return
        if self._mock_mode:
            assert isinstance(self._io, MockDataBridge)
            self._io.stop()
        else:
            assert isinstance(self._io, SerialBridge)
            self._io.disconnect_port()
        self._apply_control_states()

    def _on_link(self, ok: bool, msg: str) -> None:
        self._connected = ok
        self.status_pill.setText(msg)
        self.val_link.setText("Aktif" if ok else "Kapalı")
        color = COL_OK if ok else COL_WARN
        self.status_pill.setStyleSheet(
            f"background-color: #1a1d26; border: 1px solid {color}; "
            f"border-radius: 12px; padding: 4px 12px; color: {color};"
        )
        if ok:
            self._log_db(EventType.SYSTEM, msg)
            self.val_servo.setText("Tarama verisi bekleniyor…")
            self.val_angle.setText("—")
            self.lbl_angle.setText("Tarama açısı: —")
            self.lbl_region.setText("Bağlantı kuruldu, veri bekleniyor.")
        else:
            benign = (
                "kapalı" in msg.lower()
                or "durduruldu" in msg.lower()
                or "mock" in msg.lower()
            )
            self._log_db(
                EventType.SYSTEM if benign else EventType.ERROR,
                msg,
            )
            if not self._alarm_latched:
                self.lbl_angle.setText("Tarama açısı: —")
                self.lbl_region.setText("Bağlantı yok. Sistem izleme beklemesinde.")
        self._apply_control_states()

    def _on_io_err(self, err: str) -> None:
        self._log_db(EventType.ERROR, f"Seri I/O: {err}")

    def _on_telegram_test(self) -> None:
        self._cfg = load_config(DEFAULT_ENV_PATH)
        self._notify = NotificationService(self._cfg)
        ok, info = self._notify.send_test("Telegram bağlantı testi")
        self._last_notify_str = datetime.now().strftime("%H:%M:%S")
        self.val_notify.setText(self._last_notify_str)
        self._log_db(
            EventType.COMMAND,
            f"Telegram test: {info}",
        )
        if not ok:
            tip = (
                f"{info}\n\n"
                "Token ve chat id: proje kökündeki .env dosyasında olmalıdır "
                "(TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID boş bırakılmamalı)."
            )
            QMessageBox.warning(self, "Bildirim", tip)

    def _refresh_radar_display(self) -> None:
        """Seri veri yoksa veya kesintide sahte tarama; varsa gerçek açı."""
        now = time.monotonic()
        age = now - self._last_hw_monotonic
        if self._alarm_latched and self._alarm_angle is not None:
            disp = self._alarm_angle
        elif self._connected and age < 1.0:
            disp = self._last_angle
        else:
            self._demo_angle += self._demo_dir * 3.0
            if self._demo_angle >= 180.0:
                self._demo_angle = 180.0
                self._demo_dir = -1.0
            elif self._demo_angle <= 0.0:
                self._demo_angle = 0.0
                self._demo_dir = 1.0
            disp = int(self._demo_angle)

        self.radar.set_state(
            disp,
            self._alarm_angle if self._alarm_latched else None,
            self._alarm_latched,
        )

    def _on_state(self, msg: object) -> None:
        if not isinstance(msg, StateMessage):
            return

        self._last_hw_monotonic = time.monotonic()
        self._last_angle = msg.angle

        # Kenar algılama: sadece STATE ile çalışan firmware
        if msg.fire and not self._last_fire and not self._alarm_latched:
            self._raise_alarm(msg.angle, source="STATE")
        if not msg.fire and self._last_fire and self._alarm_latched:
            self._clear_alarm(source="STATE")

        self._last_fire = msg.fire
        self._scanning = msg.scanning

        if msg.fire:
            self.val_servo.setText(
                f"Servo alarm noktasında sabit: {msg.angle}°"
            )
        elif msg.scanning:
            self.val_servo.setText(f"Tarama sürüyor: {msg.angle}°")
        else:
            self.val_servo.setText(f"Servo beklemede: {msg.angle}°")

        if not self._alarm_latched:
            self._set_live_region_summary(msg.angle)
        else:
            aa = self._alarm_angle if self._alarm_angle is not None else msg.angle
            self._set_alarm_region_summary(aa)

        # Hafif arşiv — her 2 sn bir anlık görüntü
        now = time.time()
        if now - self._last_snap_ts >= 2.0:
            self._last_snap_ts = now
            self._log_db(
                EventType.STATE_SNAPSHOT,
                f"açı={msg.angle}° tarama={'on' if msg.scanning else 'off'} "
                f"alev={'evet' if msg.fire else 'hayır'}",
                angle=msg.angle,
                alarm_active=msg.fire,
            )

    def _on_alarm(self, msg: object) -> None:
        if not isinstance(msg, AlarmMessage):
            return
        ang = msg.angle if msg.angle is not None else self._last_angle
        self._raise_alarm(ang, source="ALARM")

    def _on_clear(self) -> None:
        self._clear_alarm(source="CLEAR")

    def _raise_alarm(self, angle: int, source: str) -> None:
        if self._alarm_latched:
            return
        self._alarm_latched = True
        self._alarm_angle = int(angle)
        self._last_angle = self._alarm_angle
        self._last_hw_monotonic = time.monotonic()
        self.val_alarm.setText(region_status_text(self._alarm_angle, alarm=True))
        self.val_alarm.setStyleSheet(f"color: {COL_DANGER};")
        self.val_sys.setText("ALARM")
        self.val_servo.setText(
            f"Servo alarm noktasında sabit: {self._alarm_angle}°"
        )
        self._set_alarm_region_summary(self._alarm_angle)
        self._alarm_blink_on = False
        self._alarm_blink.start()
        self._apply_alarm_topbar(True)

        self._log_db(
            EventType.ALARM,
            f"Alev algılandı ({source})",
            angle=self._alarm_angle,
            alarm_active=True,
        )
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(
            f"[{ts}] >>> ALEV — Servo acisi: {self._alarm_angle}° | kaynak: {source}"
        )

        payload = AlarmPayload(
            detected_at=datetime.now(),
            angle_deg=self._alarm_angle,
            level="CRITICAL",
            status_line="Alev / yangın sensörü tetiklendi",
            system_status=self.val_link.text() or "—",
        )
        if self._notify.has_channels:
            ok, info = self._notify.send_alarm(payload)
            self._last_notify_str = datetime.now().strftime("%H:%M:%S")
            self.val_notify.setText(self._last_notify_str)
            self._log_db(
                EventType.SERIAL,
                f"Uzak bildirim: {info}",
                angle=self._alarm_angle,
                alarm_active=True,
            )
            if not ok:
                self._log_db(EventType.ERROR, info, angle=self._alarm_angle)

    def _clear_alarm(self, source: str) -> None:
        if not self._alarm_latched:
            self._last_fire = False
            return
        self._alarm_latched = False
        self._alarm_angle = None
        self._last_fire = False
        self._alarm_blink.stop()
        self._apply_alarm_topbar(False)
        self.val_alarm.setText("Alarm yok")
        self.val_alarm.setStyleSheet("")
        self.val_sys.setText("Hazır")
        self.val_servo.setText(
            "Tarama açık" if self._scanning else "Tarama durdu"
        )
        self._set_live_region_summary(self._last_angle)
        self._log_db(EventType.CLEAR, f"Alarm sona erdi ({source})", alarm_active=False)

    def _apply_alarm_topbar(self, active: bool) -> None:
        base = APP_STYLESHEET
        self.setStyleSheet(base + (alarm_stylesheet() if active else ""))

    def _toggle_alarm_topbar(self) -> None:
        self._alarm_blink_on = not self._alarm_blink_on
        c = COL_DANGER if self._alarm_blink_on else "#ff9aa8"
        self.status_pill.setStyleSheet(
            f"background-color: #2a1518; border: 1px solid {c}; "
            f"border-radius: 12px; padding: 4px 12px; color: {c};"
        )

    def _apply_control_states(self) -> None:
        c = self.controls
        busy = self._connected
        c.btn_connect.setEnabled(not busy)
        c.btn_disconnect.setEnabled(busy)
        c.btn_telegram_test.setEnabled(True)

    def _tick_clock(self) -> None:
        self.clock_lbl.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _on_clear_log(self) -> None:
        self._logs.clear()
        self.log_text.clear()
        self._log_db(EventType.SYSTEM, "Günlük temizlendi.")

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "CSV kaydet",
            "yangin_olaylari.csv",
            "CSV (*.csv)",
        )
        if not path:
            return
        n = self._logs.export_csv(Path(path), self._filter_kind())
        QMessageBox.information(self, "Dışa aktarma", f"{n} satır yazıldı.")

    def closeEvent(self, event) -> None:
        if isinstance(self._io, SerialBridge):
            self._io.disconnect_port(emit=False)
        elif isinstance(self._io, MockDataBridge):
            self._io.stop()
        super().closeEvent(event)
