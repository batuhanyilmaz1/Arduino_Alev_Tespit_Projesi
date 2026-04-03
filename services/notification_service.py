"""
Uzak bildirimler: Telegram ve genişletilebilir taban sınıfı.
Token / chat id yapılandırmadan okunur; kodda sabitlenmez.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import requests

from config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class AlarmPayload:
    """Alarm anında dış kanala gönderilecek özet."""

    detected_at: datetime
    angle_deg: int | None
    level: str  # örn. CRITICAL
    status_line: str
    system_status: str


class NotificationChannel(ABC):
    """Yeni kanallar (e-posta, Pushbullet, …) bu arayüzle eklenebilir."""

    name: str = "base"

    @abstractmethod
    def send_text(self, text: str) -> tuple[bool, str]:
        """(başarılı_mı, açıklama) döner."""


class TelegramChannel(NotificationChannel):
    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._token = bot_token
        self._chat_id = chat_id
        self._api = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_text(self, text: str) -> tuple[bool, str]:
        try:
            # HTML parse_mode özel karakterlerde hata verebilir; düz metin güvenli
            r = requests.post(
                self._api,
                json={"chat_id": self._chat_id, "text": text},
                timeout=15,
            )
            if r.ok:
                return True, "Telegram: gönderildi"
            return False, f"Telegram HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            logger.exception("Telegram gönderim hatası")
            return False, f"Telegram ağ hatası: {e}"


class NotificationService:
    """
    Kayıtlı kanallara mesaj gönderir. Yapılandırma yoksa no-op olur.
    """

    def __init__(self, cfg: AppConfig) -> None:
        self._channels: list[NotificationChannel] = []
        if cfg.telegram_enabled:
            self._channels.append(
                TelegramChannel(cfg.telegram_bot_token, cfg.telegram_chat_id)
            )

    def register_channel(self, channel: NotificationChannel) -> None:
        self._channels.append(channel)

    @property
    def has_channels(self) -> bool:
        return bool(self._channels)

    def send_alarm(self, payload: AlarmPayload) -> tuple[bool, str]:
        angle_txt = (
            f"{payload.angle_deg}°" if payload.angle_deg is not None else "bilinmiyor"
        )
        body = (
            "YANGIN / ALEV ALARMI\n"
            f"Zaman: {payload.detected_at:%Y-%m-%d %H:%M:%S}\n"
            f"Servo durduğu açı (Arduino pos, sg90s): {angle_txt}\n"
            f"Alarm seviyesi: {payload.level}\n"
            f"Durum: {payload.status_line}\n"
            f"Sistem: {payload.system_status}"
        )
        return self._broadcast(body)

    def send_test(self, label: str = "Test") -> tuple[bool, str]:
        now = datetime.now()
        msg = (
            f"{label}\n"
            f"Zaman: {now:%Y-%m-%d %H:%M:%S}\n"
            "Bu mesaj kontrol panelinden gönderilmiştir."
        )
        return self._broadcast(msg)

    def _broadcast(self, text: str) -> tuple[bool, str]:
        if not self._channels:
            return False, "Bildirim kanalı yapılandırılmamış (.env)"
        results: list[str] = []
        ok_any = False
        for ch in self._channels:
            ok, info = ch.send_text(text)
            ok_any = ok_any or ok
            results.append(f"{ch.name}: {info}")
        return ok_any, " | ".join(results)
