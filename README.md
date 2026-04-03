# Güvenli Hat — Arduino Alev Tespit Sistemi

Servo ile 180° tarama yapan alev sensörünün verisini **PyQt6 dashboard** üzerinden izlemenizi, kayıt altına almanızı ve isteğe bağlı **Telegram** bildirimi göndermenizi sağlar.

---

## Özellikler

- Gerçek zamanlı **radar / yarım daire** görünümü, anlık açı ve sol / orta / sağ bölge etiketi
- **Manuel kontrol** (tarama aç-kapa, sustur, LED, buzzer/servo testi, reset) — seri komutlar
- **Olay günlüğü** (bellek içi SQLite), filtreleme, temizleme, CSV dışa aktarma
- **Telegram** bildirimi (`.env` ile yapılandırılır, test butonu)
- **`--mock` modu**: Arduino olmadan arayüz ve alarm akışını demo etme

---

## Seri protokol (özet)

**Arduino → PC** (satır sonu `\n`):

| Satır | Anlamı |
|--------|--------|
| `STATE` + `a,f,s` | `STATE|a=0-180,f=0|1,s=0|1` — kalibre edilmiş açı, alarm durumu, tarama |
| `ALARM` + `a` | `ALARM|a=açı` — sensörün gördüğü açısal aralığın orta noktası |
| `CLEAR` | Alev yok |
| `YANGIN` / `YOK` | Eski uyumluluk |

**PC → Arduino:** `SCAN_ON`, `SCAN_OFF`, `MUTE_ON`, `MUTE_OFF`, `LEDS_OFF`, `LEDS_AUTO`, `BUZZER_TEST`, `SERVO_TEST`, `RESET`

Ayrıntılar: `serial_handler.py` dosya başındaki açıklama.

---

## Donanım

| Bileşen | Pin |
|---------|-----|
| Alev sensörü | D4 |
| Kırmızı LED | D13 |
| Yeşil LED | D3 |
| Buzzer | D8 |
| SG90 Servo | D5 |

---

## Kurulum

### 1) Arduino

`alev_tespit_projesi.ino` dosyasını Arduino IDE ile kartınıza yükleyin.

Servo ortası fiziksel olarak 90'a denk gelmiyorsa, aynı dosyanın başındaki
`SERVO_RAW_LEFT`, `SERVO_RAW_CENTER` ve `SERVO_RAW_RIGHT` sabitlerini kendi
düzeneğinize göre güncelleyin. Böylece ekranda:

- sol konum `0°`
- tam orta `90°`
- sağ konum `180°`

olarak raporlanır.

Yeni firmware, alevi ilk gördüğü anda durmak yerine alevin görüldüğü açısal
aralığı tarar ve bu aralığın orta noktasını alarm açısı olarak gönderir.
Bu sayede tek noktadaki sahte `0°` kilitlenmeleri büyük ölçüde azalır.

### 2) Python

```bash
pip install -r requirements.txt
```

Proje kökünde `.env` dosyası oluşturun:

- `SERIAL_PORT` — örn. `COM3`
- `BAUD_RATE` — `9600`
- İsteğe bağlı: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### 3) Çalıştırma

```bash
python main.py
```

Donanımsız demo:

```bash
python main.py --mock
```

Mock modda **Bağlan** ile sahte veri akışını başlatın.

---

## Proje yapısı

| Yol | Görev |
|-----|--------|
| `main.py` | Giriş noktası, `--mock` |
| `config.py` | `.env` ve ayarlar |
| `serial_handler.py` | Seri okuma/yazma, satır ayrıştırma |
| `services/log_service.py` | Bellek içi olay veritabanı |
| `services/notification_service.py` | Telegram (+ genişletilebilir kanal) |
| `services/mock_bridge.py` | Demo veri üretimi |
| `ui/` | PyQt6 arayüz ve stiller |
| `assets/` | İsteğe bağlı statik dosyalar |

---

## Gereksinimler

- Python 3.10+ önerilir
- Arduino Uno veya uyumlu kart
- Paketler: `requirements.txt`

---

## Eski Tkinter sürümüne geçiş

Önceki tek dosyalık `main.py` (Tkinter) tamamen **PyQt6 dashboard** ile değiştirildi. Eski `YANGIN` / `YOK` satırları hâlâ desteklenir; tam özellik için güncel `.ino` firmware’ini yükleyin.
