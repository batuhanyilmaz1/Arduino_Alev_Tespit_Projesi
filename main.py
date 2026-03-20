import serial
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
import pyttsx3
from datetime import datetime
import time

# --- AYARLAR ---
SERI_PORT = 'COM3'
BAUD_RATE = 9600

class YanginPaneli:
    def __init__(self, root):
        self.root = root
        self.root.title("GÜVENLİ HAT - YANGIN TAKİP MERKEZİ")
        self.root.geometry("700x500")
        self.root.config(bg="#1a1a1a")
        
        # Üst Durum Paneli
        self.durum_frame = tk.Frame(self.root, bg="#222", height=150)
        self.durum_frame.pack(fill="x", padx=10, pady=10)
        
        self.durum_label = tk.Label(
            self.durum_frame, text="SİSTEM ÇEVRİMİÇİ", 
            font=("Courier", 30, "bold"), fg="#00ff00", bg="#222"
        )
        self.durum_label.pack(expand=True, pady=30)

        # Olay Günlüğü (Log) Başlığı
        tk.Label(self.root, text="SİSTEM OLAY GÜNLÜĞÜ", font=("Arial", 10, "bold"), 
                 fg="white", bg="#1a1a1a").pack(anchor="w", padx=20)

        # Log Ekranı
        self.log_ekrani = scrolledtext.ScrolledText(
            self.root, width=80, height=15, font=("Consolas", 10),
            bg="black", fg="#00ff00", insertbackground="white"
        )
        self.log_ekrani.pack(padx=20, pady=10)

        self.yangin_var_mi = False
        self.log_ekle("Sistem başlatıldı. Arduino bağlantısı bekleniyor...")

        # Arduino Dinleme Thread'i
        Thread(target=self.seri_dinle, daemon=True).start()

    def log_ekle(self, mesaj):
        zaman = datetime.now().strftime("%H:%M:%S")
        self.log_ekrani.insert(tk.END, f"[{zaman}] > {mesaj}\n")
        self.log_ekrani.see(tk.END)

    def flasor_efekti(self):
        """Yangın anında ekranı yakıp söndürür"""
        if self.yangin_var_mi == True:
            mevcut_renk = self.durum_label.cget("bg")
            yeni_renk = "red" if mevcut_renk == "#222" else "#222"
            yeni_yazi = "white" if mevcut_renk == "#222" else "red"
            
            self.durum_label.config(bg=yeni_renk, fg=yeni_yazi)
            self.durum_frame.config(bg=yeni_renk)
            self.root.after(500, self.flasor_efekti)
        else:
            self.durum_label.config(bg="#222", fg="#00ff00", text="SİSTEM GÜVENDE")
            self.durum_frame.config(bg="#222")

    def seri_dinle(self):
        try:
            ser = serial.Serial(SERI_PORT, BAUD_RATE, timeout=1)
            self.log_ekle(f"Bağlantı başarılı: {SERI_PORT}")
            
            while True:
                if ser.in_waiting > 0:
                    satir = ser.readline().decode('utf-8').strip()
                    
                    if satir == "YANGIN" and not self.yangin_var_mi:
                        self.yangin_var_mi = True
                        self.durum_label.config(text="⚠️ YANGIN ALGILANDI ⚠️")
                        self.log_ekle("KRİTİK UYARI: ALEV TESPİT EDİLDİ!")
                        self.flasor_efekti()
                        
                    elif satir == "YOK" and self.yangin_var_mi:
                        self.yangin_var_mi = False
                        self.log_ekle("BİLGİ: Yangın kontrol altına alındı.")
                        self.durum_label.config(text="SİSTEM GÜVENDE")

        except Exception as e:
            hata_mesaji = str(e)
            if "ClearCommError failed" in hata_mesaji or "Erişim engellendi" in hata_mesaji or isinstance(e, PermissionError):
                self.log_ekle("HATA: Bağlantı başarısız. Port kullanımda, kesilmiş veya erişim engellendi.")
            if "could not open port" in hata_mesaji or "FileNotFoundError" in hata_mesaji:
                self.log_ekle("HATA: Bağlantı Başarısız. Lütfen Arduino'nun bağlı olduğu portu kontrol ediniz.")
            else:
                self.log_ekle(f"HATA: {e}")

# Uygulamayı başlat
if __name__ == "__main__":
    root = tk.Tk()
    app = YanginPaneli(root)
    root.mainloop()