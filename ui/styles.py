"""
Dashboard QSS — renkler ve tipografi tek yerde; arayüz kodundan ayrık.
"""
from __future__ import annotations

# Sakin tema + alarm vurgusu
COL_BG = "#12141a"
COL_PANEL = "#1a1d26"
COL_BORDER = "#2a3142"
COL_TEXT = "#e8eaef"
COL_MUTED = "#8b93a7"
COL_ACCENT = "#3d9cfd"
COL_OK = "#3ecf8e"
COL_WARN = "#ffb020"
COL_DANGER = "#ff4d4d"

APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {COL_BG};
}}
QWidget {{
    color: {COL_TEXT};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}
QLabel {{
    background-color: transparent;
    color: {COL_TEXT};
}}
QFrame#TopBar {{
    background-color: {COL_PANEL};
    border-bottom: 1px solid {COL_BORDER};
}}
QLabel#Brand {{
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QLabel#Clock {{
    color: {COL_MUTED};
    font-family: Consolas, monospace;
}}
QLabel#StatusPill {{
    border-radius: 12px;
    padding: 4px 12px;
    background-color: {COL_BORDER};
    color: {COL_TEXT};
}}
QGroupBox {{
    font-weight: 600;
    border: 1px solid {COL_BORDER};
    border-radius: 8px;
    margin-top: 10px;
    padding: 12px 8px 8px 8px;
    background-color: {COL_PANEL};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {COL_MUTED};
    background-color: transparent;
}}
QPushButton {{
    background-color: {COL_BORDER};
    color: {COL_TEXT};
    border: 1px solid {COL_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 22px;
}}
QPushButton:hover:enabled {{
    border-color: {COL_ACCENT};
    color: {COL_ACCENT};
}}
QPushButton:pressed {{
    background-color: #252a36;
}}
QPushButton:disabled {{
    color: #555a66;
    border-color: #2a2f38;
}}
QPushButton#Danger {{
    background-color: #3a2024;
    border-color: {COL_DANGER};
    color: {COL_DANGER};
}}
QLineEdit, QSpinBox, QComboBox {{
    background-color: #0e1016;
    border: 1px solid {COL_BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    color: {COL_TEXT};
}}
QTextEdit, QPlainTextEdit {{
    background-color: #0a0c10;
    border: 1px solid {COL_BORDER};
    border-radius: 6px;
    color: #c8f5c4;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
}}
QScrollBar:vertical {{
    background: {COL_PANEL};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COL_BORDER};
    min-height: 24px;
    border-radius: 4px;
}}
QFrame#Card {{
    background-color: {COL_PANEL};
    border: 1px solid {COL_BORDER};
    border-radius: 10px;
}}
QFrame#SummaryCard {{
    background-color: {COL_PANEL};
    border: 1px solid {COL_BORDER};
    border-radius: 14px;
}}
QFrame#LogDock {{
    background-color: {COL_PANEL};
    border-top: 1px solid {COL_BORDER};
}}
QLabel#CardTitle {{
    color: {COL_MUTED};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}
QLabel#CardValue {{
    color: {COL_TEXT};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#SummaryTitle {{
    color: {COL_TEXT};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#SummaryText {{
    color: {COL_MUTED};
    font-size: 14px;
}}
"""


def alarm_stylesheet() -> str:
    """Alarm modunda üst çubuğa ek vurgu."""
    return f"""
    QFrame#TopBar {{
        background-color: #2a1518;
        border-bottom: 1px solid {COL_DANGER};
    }}
    """
