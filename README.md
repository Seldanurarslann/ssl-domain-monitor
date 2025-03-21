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

Linux/WSL ortamında whois komutunun yüklü olduğundan emin olun:
