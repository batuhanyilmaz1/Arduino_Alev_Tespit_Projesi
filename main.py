from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Proje root ekleme
_PROJECT_ROOT = Path(__file__).resolve().parent
_root_s = str(_PROJECT_ROOT)
if _root_s not in sys.path:
    sys.path.insert(0, _root_s)

# Serial config (ileride kullanılabilir)
SERI_PORT = "COM3"
BAUD_RATE = 9600

# PyQt6
from PyQt6.QtWidgets import QApplication

# Proje modülleri
from config import DEFAULT_ENV_PATH, load_config
from ui.main_window import MainWindow
from ui.styles import APP_STYLESHEET


def main() -> int:
    parser = argparse.ArgumentParser(description="Yangın takip merkezi")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Arduino olmadan sahte veri ile arayüzü çalıştır",
    )
    args = parser.parse_args()

    # Config yükle
    cfg = load_config(DEFAULT_ENV_PATH)

    # Uygulama başlat
    app = QApplication(sys.argv)
    app.setApplicationName("Güvenli Hat")
    app.setStyleSheet(APP_STYLESHEET)

    # Ana pencere
    win = MainWindow(cfg, mock_mode=args.mock)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())