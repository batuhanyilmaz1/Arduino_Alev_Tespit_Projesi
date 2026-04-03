"""
Donanım yokken dashboard'u demo etmek için sahte seri akışı üretir.
Ana (GUI) iş parçacığında QTimer ile çalışır.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from serial_handler import AlarmMessage, ClearMessage, StateMessage


@dataclass
class MockConfig:
    """Demo hızı ve alarm sıklığı."""

    tick_ms: int = 80
    alarm_probability_per_tick: float = 0.004


class MockDataBridge(QObject):
    """
    SerialBridge ile aynı sinyal şekli: state_update, alarm_event, clear_event.
    Bağlantı sinyalleri mock için anlık True döner.
    """

    state_update = pyqtSignal(object)
    alarm_event = pyqtSignal(object)
    clear_event = pyqtSignal()
    link_changed = pyqtSignal(bool, str)
    io_error = pyqtSignal(str)

    def __init__(self, cfg: MockConfig | None = None) -> None:
        super().__init__()
        self._cfg = cfg or MockConfig()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._angle = 0
        self._dir = 1
        self._alarm = False
        self._scanning = True
        self._alarm_angle: int | None = None
        self._ticks_in_alarm = 0

    def start(self) -> None:
        self._angle = 0
        self._alarm = False
        self._scanning = True
        self.link_changed.emit(True, "Mock veri: bağlantı simülasyonu")
        self._timer.start(self._cfg.tick_ms)

    def stop(self) -> None:
        self._timer.stop()
        self.link_changed.emit(False, "Mock veri durduruldu")

    def is_running(self) -> bool:
        return self._timer.isActive()

    def _tick(self) -> None:
        if self._alarm:
            self._ticks_in_alarm += 1
            self.state_update.emit(
                StateMessage(
                    angle=self._alarm_angle or self._angle,
                    fire=True,
                    scanning=False,
                )
            )
            if self._ticks_in_alarm > 35 or random.random() < 0.02:
                self._alarm = False
                self._ticks_in_alarm = 0
                self.clear_event.emit()
            return

        if self._scanning:
            self._angle += self._dir * 3
            if self._angle >= 180:
                self._angle = 180
                self._dir = -1
            elif self._angle <= 0:
                self._angle = 0
                self._dir = 1

        self.state_update.emit(
            StateMessage(angle=self._angle, fire=False, scanning=self._scanning)
        )

        if random.random() < self._cfg.alarm_probability_per_tick:
            self._alarm = True
            self._alarm_angle = self._angle
            self._ticks_in_alarm = 0
            self.alarm_event.emit(AlarmMessage(angle=self._angle))
