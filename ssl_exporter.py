import ssl
import socket
import time
import pandas as pd
from datetime import datetime, timezone
from prometheus_client import start_http_server, Gauge

# Prometheus metriği oluştur
SSL_KALAN_GUN = Gauge("ssl_kalan_gun", "SSL sertifikasının bitmesine kalan gün", ["site", "description"])

def siteleri_oku(dosya_adi="input.xlsx"):
    """Excel dosyasından site adreslerini ve açıklamalarını okur."""
    try:
        # Excel dosyasını oku
        df = pd.read_excel(dosya_adi, dtype=str)
        
        # Okunan sütunları kontrol et
        print(f"📊 Okunan sütunlar: {df.columns.tolist()}")

        # Eğer sütun isimleri yanlışsa, manuel olarak düzelterek ata
        if df.columns[0] != "site" or df.columns[1] != "description":
            df.columns = ["site", "description"]
        
        # Boş satırları temizle
        df = df.dropna(subset=["site"])

        return df[["site", "description"]].values.tolist()
    except Exception as e:
        print(f"❌ Hata: Site listesi okunamadı! Hata mesajı: {e}")
        return []

def ssl_kontrol(site, description):
    """Verilen sitenin SSL sertifikasını kontrol eder ve kalan gün sayısını hesaplar."""
    site = site.replace("https://", "").replace("http://", "").strip()  # Protokolü temizle
    try:
        context = ssl.create_default_context()
        with socket.create_connection((site, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=site) as ssock:
                sertifika = ssock.getpeercert()

        # Sertifika bitiş tarihini al
        bitis_tarihi = datetime.strptime(sertifika['notAfter'], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        bugun = datetime.now(timezone.utc) 

        kalan_sure = (bitis_tarihi - bugun).days

        print(f"✅ {site}: SSL Sertifikası {kalan_sure} gün sonra sona erecek. (Açıklama: {description})")
        SSL_KALAN_GUN.labels(site=site, description=description).set(kalan_sure)

    except ssl.SSLError:
        print(f"⚠️ {site}: SSL sertifikası alınamıyor, HTTP olabilir.")
    except Exception as e:
        print(f"❌ Hata ({site}): {e}")

def main():
    # Prometheus HTTP server'ı başlat (8000 portu)
    start_http_server(8000)
    print("🚀 Prometheus Exporter başlatıldı! http://127.0.0.1:8000/metrics")

    while True:
        print("🔄 SSL Kontrolleri Yenileniyor...")
        siteler = siteleri_oku()  # Excel'den site listesini oku
        if not siteler:
            print("❌ Site listesi boş veya okunamadı.")
        else:
            for site, description in siteler:
                ssl_kontrol(site, description)
        time.sleep(3600)  # 1 saatte bir güncelle

if __name__ == "__main__":
    main()
