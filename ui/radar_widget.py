"""
Yarım daire tarama: yeşil/mavi tarama ışını, ibre, alarmda kırmızı nokta.
"""
from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from ui.styles import COL_ACCENT, COL_BORDER, COL_DANGER, COL_MUTED


def region_label(angle_deg: int) -> str:
    if angle_deg < 60:
        return "Sol bölge"
    if angle_deg < 120:
        return "Orta bölge"
    return "Sağ bölge"


def region_status_text(angle_deg: int, *, alarm: bool) -> str:
    if angle_deg < 60:
        return "Sol bölgede alev tespit edildi." if alarm else "Tarama şu anda sol bölgede."
    if angle_deg < 120:
        return "Orta bölgede alev tespit edildi." if alarm else "Tarama şu anda orta bölgede."
    return "Sağ bölgede alev tespit edildi." if alarm else "Tarama şu anda sağ bölgede."


class RadarWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(420, 260)
        self._angle: int = 0
        self._alarm_angle: Optional[int] = None
        self._alarm_active: bool = False

    def set_state(self, angle_deg: int, alarm_angle: Optional[int], alarm: bool) -> None:
        self._angle = max(0, min(180, int(angle_deg)))
        self._alarm_angle = (
            max(0, min(180, int(alarm_angle))) if alarm_angle is not None else None
        )
        self._alarm_active = alarm
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 24
        cx = w / 2
        cy = h - margin
        r = min(w / 2 - margin, h - margin * 2)

        dash = QPen(QColor(COL_BORDER))
        dash.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(dash)
        for deg in (60, 120):
            edge = self._point(cx, cy, r, deg)
            painter.drawLine(QPointF(cx, cy), edge)

        pen = QPen(QColor(COL_BORDER))
        pen.setWidth(2)
        painter.setPen(pen)
        rect_f = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        painter.drawArc(rect_f, 0, 180 * 16)

        painter.setPen(QColor(COL_MUTED))
        for text, deg in [("Sol", 28), ("Orta", 90), ("Sağ", 152)]:
            p = self._point(cx, cy, r + 14, deg)
            painter.drawText(int(p.x() - 16), int(p.y()), text)

        # Tarama ışını (servo ile birlikte hareket eden yelpaze)
        self._draw_sweep_beam(painter, cx, cy, r * 0.95, self._angle, self._alarm_active)

        # İbre
        needle = QColor(COL_ACCENT)
        if self._alarm_active:
            needle = QColor("#ff6b6b")
        self._draw_needle(painter, cx, cy, r * 0.92, self._angle, needle, 4)

        # Uçta parlak nokta
        tip = self._point(cx, cy, r * 0.92, self._angle)
        painter.setBrush(needle.lighter(120))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(tip, 5, 5)

        if self._alarm_active and self._alarm_angle is not None:
            self._draw_marker(
                painter, cx, cy, r * 0.78, self._alarm_angle, QColor(COL_DANGER)
            )

    def _theta(self, servo_deg: float) -> float:
        return math.pi * (1.0 - servo_deg / 180.0)

    def _point(self, cx: float, cy: float, radius: float, servo_deg: float) -> QPointF:
        t = self._theta(servo_deg)
        return QPointF(cx + radius * math.cos(t), cy - radius * math.sin(t))

    def _draw_sweep_beam(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        radius: float,
        servo_deg: float,
        alarm: bool,
    ) -> None:
        half = 20.0
        path = QPainterPath()
        path.moveTo(QPointF(cx, cy))
        steps = 16
        for i in range(steps + 1):
            d = servo_deg - half + (2 * half) * (i / steps)
            d = max(0.0, min(180.0, d))
            path.lineTo(self._point(cx, cy, radius, d))
        path.closeSubpath()
        if alarm:
            c = QColor(255, 60, 60, 85)
        else:
            c = QColor(62, 200, 120, 70)
        painter.fillPath(path, c)
        rim = QPen(QColor(255, 255, 255, 40) if not alarm else QColor(255, 100, 100, 90))
        rim.setWidth(1)
        painter.setPen(rim)
        painter.drawPath(path)

    def _draw_needle(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        length: float,
        servo_deg: float,
        color: QColor,
        width: int,
    ) -> None:
        tip = self._point(cx, cy, length, servo_deg)
        pen = QPen(color)
        pen.setWidth(width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(cx, cy), tip)

    def _draw_marker(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        radius: float,
        servo_deg: float,
        color: QColor,
    ) -> None:
        p = self._point(cx, cy, radius, servo_deg)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(p, 11, 11)
        painter.setPen(QPen(color.lighter(130)))
        painter.drawText(int(p.x() + 14), int(p.y() + 5), f"{int(servo_deg)}°")
