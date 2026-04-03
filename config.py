from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_PATH = ROOT_DIR / ".env"


def _env_str(key: str, default: str = "") -> str:
    raw = os.getenv(key)
    if raw is None:
        return default
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s


def _env_int(key: str, default: int) -> int:
    v = _env_str(key, "")
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def normalize_serial_port(name: str) -> str:
    s = name.strip()
    m = re.match(r"(?i)^com\D*(\d+)", s)
    if m:
        return f"COM{m.group(1)}"
    return s


@dataclass
class AppConfig:
    serial_port: str
    baud_rate: int
    telegram_bot_token: str
    telegram_chat_id: str

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def load_config(env_path: Path | None = None) -> AppConfig:
    """
    Tek yapılandırma dosyası: proje kökündeki `.env`.
    Dosya yoksa ortam değişkenleri ve varsayılanlar kullanılır.
    """
    path = env_path or DEFAULT_ENV_PATH
    if path.is_file():
        load_dotenv(path, encoding="utf-8")

    raw_port = _env_str("SERIAL_PORT", "").strip()
    port = normalize_serial_port(raw_port or "COM3")
    baud = _env_int("BAUD_RATE", 9600)
    token = _env_str("TELEGRAM_BOT_TOKEN", "").strip()
    chat = _env_str("TELEGRAM_CHAT_ID", "").strip()

    return AppConfig(
        serial_port=port,
        baud_rate=baud,
        telegram_bot_token=token,
        telegram_chat_id=chat,
    )
