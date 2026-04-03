from __future__ import annotations

<<<<<<< HEAD
import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_root_s = str(_PROJECT_ROOT)
if _root_s not in sys.path:
    sys.path.insert(0, _root_s)
=======
SERI_PORT = 'COM3'
BAUD_RATE = 9600

class YanginPaneli:
    def __init__(self, root):
        self.root = root
        self.root.title("GÜVENLİ HAT - YANGIN TAKİP MERKEZİ")
        self.root.geometry("700x500")
        self.root.config(bg="#1a1a1a")
        
        self.durum_frame = tk.Frame(self.root, bg="#222", height=150)
        self.durum_frame.pack(fill="x", padx=10, pady=10)
        
        self.durum_label = tk.Label(
            self.durum_frame, text="SİSTEM ÇEVRİMİÇİ", 
            font=("Courier", 30, "bold"), fg="#00ff00", bg="#222"
        )
        self.durum_label.pack(expand=True, pady=30)
>>>>>>> 1c88e3ba6cd5c30c9c85ed30aaed8b95336d7d10

from PyQt6.QtWidgets import QApplication

from config import DEFAULT_ENV_PATH, load_config
from ui.main_window import MainWindow
from ui.styles import APP_STYLESHEET


<<<<<<< HEAD
def main() -> int:
    parser = argparse.ArgumentParser(description="Yangın takip merkezi")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Arduino olmadan sahte veri ile arayüzü çalıştır",
    )
    args = parser.parse_args()
=======
        Thread(target=self.seri_dinle, daemon=True).start()
>>>>>>> 1c88e3ba6cd5c30c9c85ed30aaed8b95336d7d10

    cfg = load_config(DEFAULT_ENV_PATH)
    app = QApplication(sys.argv)
    app.setApplicationName("Güvenli Hat")
    app.setStyleSheet(APP_STYLESHEET)

    win = MainWindow(cfg, mock_mode=args.mock)
    win.show()
    return app.exec()


<<<<<<< HEAD
if __name__ == "__main__":
    raise SystemExit(main())
=======
        except Exception as e:
            hata_mesaji = str(e)
            if "ClearCommError failed" in hata_mesaji or "Erişim engellendi" in hata_mesaji or isinstance(e, PermissionError):
                self.log_ekle("HATA: Bağlantı başarısız. Port kullanımda, kesilmiş veya erişim engellendi.")
            if "could not open port" in hata_mesaji or "FileNotFoundError" in hata_mesaji:
                self.log_ekle("HATA: Bağlantı Başarısız. Lütfen Arduino'nun bağlı olduğu portu kontrol ediniz.")
            else:
                self.log_ekle(f"HATA: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = YanginPaneli(root)
    root.mainloop()
>>>>>>> 1c88e3ba6cd5c30c9c85ed30aaed8b95336d7d10
