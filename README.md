# Güvenli Hat — Arduino Alev Tespit Sistemi

Servo motorla 180° tarama yapan bir alev sensörünün yangın tespitini gerçek zamanlı olarak bilgisayara aktardığı bir güvenlik sistemi.

---

## Nasıl Çalışır?

1. **Arduino** tarafı servo motoru sürekli 0°–180° arasında döndürür ve her adımda alev sensörünü kontrol eder.
2. Alev tespit edildiğinde kırmızı LED yanar, buzzer çalar ve servo o açıda kilitlenir; seri porta `YANGIN` mesajı gönderilir.
3. **Python** tarafı (`main.py`) seri portu arka planda dinler; mesaj gelince arayüzde kırmızı flaşör efekti başlar ve olay günlüğüne kaydedilir.
4. Tehdit geçince Arduino `YOK` mesajı gönderir, sistem yeşile döner.

---

## Donanım

| Bileşen | Pin |
|---|---|
| Alev sensörü | D4 |
| Kırmızı LED | D13 |
| Yeşil LED | D3 |
| Buzzer | D8 |
| SG90 Servo | D5 |

---

## Kurulum

### Arduino
`.ino` dosyasını Arduino IDE ile açıp kartınıza yükleyin.

### Python
```bash
pip install pyserial pyttsx3
```

`main.py` içinde `SERI_PORT` değerini kendi portunuzla değiştirin (örn. `COM3`, `COM5`), ardından çalıştırın:

```bash
python main.py
```

---

## Gereksinimler

- Python 3.x
- Arduino Uno (veya uyumlu kart)
- `pyserial`, `pyttsx3`, `tkinter` (tkinter Python ile birlikte gelir)
