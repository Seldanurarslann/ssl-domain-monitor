import ssl
import socket
import pandas as pd
import time
from datetime import datetime, timezone
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

# Excel dosya adları
INPUT_FILE = "input.xlsx"

# Flask uygulaması
app = Flask(__name__)

# Prometheus metrikleri
SSL_GUN_KALAN = Gauge("ssl_gun_kalan", "SSL Sertifikasının bitmesine kaç gün kaldı", ["site"])
SSL_HATA = Gauge("ssl_hata", "SSL Kontrol hatası (1: hata, 0: başarılı)", ["site"])

def ssl_kontrol(site):
    """Verilen sitenin SSL sertifikasını kontrol eder ve Prometheus metriklerini günceller."""
    site = site.replace("https://", "").replace("http://", "")  # Protokolü kaldır
    try:
        context = ssl.create_default_context()
        with socket.create_connection((site, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=site) as ssock:
                sertifika = ssock.getpeercert()

        # Sertifika tarihlerini UTC olarak al
        bitis_tarihi = datetime.strptime(sertifika['notAfter'], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        bugun = datetime.now(timezone.utc)

        kalan_sure = (bitis_tarihi - bugun).days

        print(f"{site}: SSL Sertifikası {kalan_sure} gün sonra sona erecek.")

        # Prometheus metriklerini güncelle
        SSL_GUN_KALAN.labels(site=site).set(kalan_sure)
        SSL_HATA.labels(site=site).set(0)

    except Exception as e:
        print(f"Hata ({site}): {e}")
        SSL_GUN_KALAN.labels(site=site).set(-1)
        SSL_HATA.labels(site=site).set(1)

def ssl_kontrol_hepsi():
    """Excel dosyasından site listesini okur ve SSL kontrollerini yapar."""
    try:
        df = pd.read_excel(INPUT_FILE)
        siteler = df["site"].dropna().tolist()
    except Exception as e:
        print(f"❌ Excel dosyası okunamadı: {e}")
        return

    for site in siteler:
        ssl_kontrol(site)

@app.route("/metrics")
def metrics():
    """Prometheus'un okuyacağı metrikleri döndürür."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

def arka_plan_ssl_kontrol():
    """Belirli aralıklarla SSL kontrollerini yenileyen fonksiyon."""
    while True:
        print("🔄 SSL Kontrolleri Yenileniyor...")
        ssl_kontrol_hepsi()
        time.sleep(300)  # 5 dakikada bir kontrol et

if __name__ == "__main__":
    from threading import Thread
    # Arka planda SSL kontrolünü çalıştır
    t = Thread(target=arka_plan_ssl_kontrol, daemon=True)
    t.start()

    # Flask sunucusunu başlat
    app.run(host="0.0.0.0", port=8000)
