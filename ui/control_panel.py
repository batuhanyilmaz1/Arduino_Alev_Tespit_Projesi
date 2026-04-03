"""
Sol panel: yalnızca seri bağlantı ve Telegram testi (Arduino’ya komut gönderilmez).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ControlPanel(QWidget):
    connect_clicked = pyqtSignal()
    disconnect_clicked = pyqtSignal()
    telegram_test_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(268)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("COM3 veya /dev/ttyUSB0")
        self.baud_spin = QSpinBox()
        self.baud_spin.setRange(300, 921600)
        self.baud_spin.setValue(9600)
        self.baud_spin.setSingleStep(300)

        self.btn_connect = QPushButton("Bağlan")
        self.btn_disconnect = QPushButton("Bağlantıyı kes")
        self.btn_telegram_test = QPushButton("Telegram test bildirimi")
        for b in (self.btn_connect, self.btn_disconnect, self.btn_telegram_test):
            b.setMinimumHeight(36)
            b.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )

        self.btn_connect.clicked.connect(self.connect_clicked.emit)
        self.btn_disconnect.clicked.connect(self.disconnect_clicked.emit)
        self.btn_telegram_test.clicked.connect(self.telegram_test_clicked.emit)

        inner = QWidget()
        inner.setObjectName("ControlInner")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(12)
        inner_layout.setContentsMargins(8, 8, 8, 8)

        conn_box = QGroupBox("Bağlantı")
        cg = QGridLayout(conn_box)
        cg.setHorizontalSpacing(8)
        cg.setVerticalSpacing(8)
        cg.addWidget(QLabel("Port"), 0, 0)
        cg.addWidget(self.port_edit, 0, 1)
        cg.addWidget(QLabel("Baud"), 1, 0)
        cg.addWidget(self.baud_spin, 1, 1)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.btn_connect, 1)
        row.addWidget(self.btn_disconnect, 1)
        cg.addLayout(row, 2, 0, 1, 2)

        ext = QGroupBox("Bildirim")
        ev = QVBoxLayout(ext)
        ev.setSpacing(8)
        ev.addWidget(self.btn_telegram_test)

        note = QLabel(
            "Arduino yalnızca okunur: STATE / ALARM / CLEAR.\n"
            "Gosterilen aci kalibre edilir: sol=0, orta=90, sag=180."
        )
        note.setWordWrap(True)
        note.setObjectName("Hint")
        note.setStyleSheet("color: #8b93a7; font-size: 11px;")

        inner_layout.addWidget(conn_box)
        inner_layout.addWidget(ext)
        inner_layout.addWidget(note)
        inner_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_mock_mode(self, mock: bool) -> None:
        self.port_edit.setEnabled(not mock)
        self.baud_spin.setEnabled(not mock)
