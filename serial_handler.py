"""
Arduino → PC seri okuma (salt okunur). Satır sonu \\n.

Protokol:
  STATE|a=<0-180>,f=<0|1>,s=<0|1>
    a = kalibre edilmis mantiksal aci (sol=0, orta=90, sag=180)
    f = onaylanmis alarm aktif mi
    s = tarama hareket halinde (alarmda servo durduğu için 0)
  ALARM|a=<açı>
    a = sensorun gordugu aci araliginin orta noktasi
  CLEAR, YOK, YANGIN (eski uyumluluk)
"""
from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass

import serial
from PyQt6.QtCore import QObject, pyqtSignal

_STATE_RE = re.compile(
    r"^STATE\|a=(?P<a>\d+),f=(?P<f>[01]),s=(?P<s>[01])$",
    re.IGNORECASE,
)
_ALARM_RE = re.compile(r"^ALARM\|a=(?P<a>\d+)$", re.IGNORECASE)


@dataclass
class StateMessage:
    angle: int
    fire: bool
    scanning: bool


@dataclass
class AlarmMessage:
    angle: int | None


@dataclass
class ClearMessage:
    pass


class SerialBridge(QObject):
    """Arka planda seri port okur; Arduino'ya yazı gönderilmez."""

    state_update = pyqtSignal(object)
    alarm_event = pyqtSignal(object)
    clear_event = pyqtSignal()
    link_changed = pyqtSignal(bool, str)
    io_error = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._ser: serial.Serial | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._rx_buffer = ""

    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def connect_port(self, port: str, baud: int) -> None:
        self.disconnect_port(emit=False)
        try:
            self._ser = serial.Serial(port, baud, timeout=0.1)
            try:
                self._ser.reset_input_buffer()
                self._ser.reset_output_buffer()
            except Exception:
                pass
            self._running = True
            self.link_changed.emit(True, f"Bağlı: {port} @ {baud}")
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            self._ser = None
            self._running = False
            self.link_changed.emit(False, self._human_serial_error(e))

    def disconnect_port(self, emit: bool = True) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        self._rx_buffer = ""
        if emit:
            self.link_changed.emit(False, "Bağlantı kapalı")

    def _read_loop(self) -> None:
        assert self._ser is not None
        time.sleep(2.2)
        while self._running and self._ser.is_open:
            try:
                chunk = self._ser.read(256)
                if not chunk:
                    continue
                self._rx_buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in self._rx_buffer:
                    line, self._rx_buffer = self._rx_buffer.split("\n", 1)
                    self._dispatch_line(line.strip())
            except serial.SerialException as e:
                self.io_error.emit(str(e))
                self.link_changed.emit(False, "Seri bağlantı koptu veya hata oluştu")
                break
            except Exception as e:
                self.io_error.emit(str(e))

    def _dispatch_line(self, line: str) -> None:
        if not line:
            return
        for msg in parse_serial_line(line):
            if isinstance(msg, StateMessage):
                self.state_update.emit(msg)
            elif isinstance(msg, AlarmMessage):
                self.alarm_event.emit(msg)
            elif isinstance(msg, ClearMessage):
                self.clear_event.emit()

    @staticmethod
    def _human_serial_error(e: BaseException) -> str:
        s = str(e)
        if "ClearCommError" in s or "Erişim engellendi" in s or isinstance(
            e, PermissionError
        ):
            return "Port kullanımda, kesilmiş veya erişim engellendi."
        if "could not open port" in s.lower() or "FileNotFoundError" in s:
            return "Port bulunamadı veya yanlış COM seçildi."
        return s


def parse_serial_line(line: str) -> list[object]:
    raw = line.strip()
    if not raw:
        return []

    if raw.upper().startswith("ACK|") or raw.upper().startswith("NAK|"):
        return []

    m = _STATE_RE.match(raw)
    if m:
        return [
            StateMessage(
                angle=int(m.group("a")),
                fire=m.group("f") == "1",
                scanning=m.group("s") == "1",
            )
        ]

    m = _ALARM_RE.match(raw)
    if m:
        return [AlarmMessage(angle=int(m.group("a")))]

    u = raw.upper()
    if u == "CLEAR" or u == "YOK":
        return [ClearMessage()]
    if u == "YANGIN":
        return [AlarmMessage(angle=None)]

    return []
