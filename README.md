# 🛡 SSL ve Domain Süre Takip Sistemi

Bu proje, belirlenen sitelerin **SSL sertifika** ve **domain sürelerini** takip ederek **Prometheus** metriklerini sunar.

## 🚀 Özellikler

- Sitelerin **SSL sertifika** geçerlilik süresini kontrol eder.
- **WHOIS** sorgusu yaparak **domain süresini** öğrenir.
- **Prometheus Exporter** olarak çalışarak **metrikleri** dışa aktarır.
- **Saatte bir otomatik çalışarak** güncel verileri sağlar.

---

## 📌 Kurulum ve Kullanım

### 1️⃣ Gerekli Bağımlılıkları Yükleyin

Python bağımlılıklarını yükleyin:

```bash
pip install prometheus_client
```

Linux/WSL ortamında whois komutunun yüklü olduğundan emin olun:

```bash
sudo apt update && sudo apt install whois
```
### 2️⃣ input.json Dosyasını Oluşturun

Takip etmek istediğiniz siteleri aşağıdaki formatta bir input.json dosyasına ekleyin:

```bash
[
  {"site": "example.com", "description": "Örnek Site"},
  {"site": "github.com", "description": "GitHub"}
]
```

### 3️⃣ Uygulamayı Çalıştırın

```bash
python main.py
```

Başarılı çalıştırıldığında şu mesajı görmelisiniz:

```bash
🚀 Prometheus Exporter başlatıldı: http://127.0.0.1:9000/metrics
🔄 SSL ve Domain Kontrolleri Yenileniyor...
```

### 📊 Prometheus Metrikleri

Örnek Prometheus çıktısı:

```bash
# HELP ssl_domain_kalan_gun SSL ve Domain bitiş süresi
# TYPE ssl_domain_kalan_gun gauge
ssl_domain_kalan_gun{site="github.com",description="GitHub",type="SSL"} 88.0
ssl_domain_kalan_gun{site="github.com",description="GitHub",type="Domain"} 365.0

```

### 📡 Grafana ile Görselleştirme
```bash
ssl_domain_kalan_gun
```
###  🛠 Hata Giderme

- SSL sertifikası alınamıyor: socket.timeout veya SSLError hatası alıyorsanız, hedef siteye 443 portundan erişiminizi kontrol edin.
- WHOIS bilgisi bulunamıyor: WHOIS sunucuları bazen cevap vermeyebilir. whois komutunu terminalde manuel çalıştırarak çıktıyı kontrol edin.
- Prometheus çalışmıyor: http://127.0.0.1:9000/metrics adresine tarayıcıdan erişerek metriklerin görüntülendiğinden emin olun.

---