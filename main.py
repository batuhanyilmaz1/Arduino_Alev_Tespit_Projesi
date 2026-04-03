from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_root_s = str(_PROJECT_ROOT)
if _root_s not in sys.path:
    sys.path.insert(0, _root_s)

from PyQt6.QtWidgets import QApplication

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

    cfg = load_config(DEFAULT_ENV_PATH)
    app = QApplication(sys.argv)
    app.setApplicationName("Güvenli Hat")
    app.setStyleSheet(APP_STYLESHEET)

    win = MainWindow(cfg, mock_mode=args.mock)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
