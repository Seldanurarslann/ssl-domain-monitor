import ssl
import socket
import time
import subprocess
import re
import os
import json
from datetime import datetime, timezone
from prometheus_client import start_http_server, Gauge

# **Prometheus Metrikleri**
SSL_DOMAIN_METRIC = Gauge("ssl_domain_kalan_gun", "SSL ve Domain bitiş süresi", ["site", "description", "type"])

# **WHOIS sorgusu için regex desenleri**
EXPIRY_PATTERNS = [
    r"Expires on: (\d{4}-\d{2}-\d{2})",
    r"Expiry Date: (\d{4}-\d{2}-\d{2})",
    r"Registry Expiry Date: (\d{4}-\d{2}-\d{2})",
    r"Expiration Date: (\d{4}-\d{2}-\d{2})",
    r"Expiry Date: (\d{2}-[A-Za-z]{3}-\d{4})",
    r"Expiry Date: (\d{2}\.\d{2}\.\d{4})",
    r"Expiry: (\d{2}/\d{2}/\d{4})",
    r"Expiration Date: (\d{2} [A-Za-z]{3} \d{4})",
]

def siteleri_oku(dosya_adi="input.json"):
    """JSON dosyasından site adreslerini ve açıklamalarını okur."""
    try:
        with open(dosya_adi, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Her bir öğenin "site" ve "description" anahtarlarını içerdiğinden emin olun.
        sites = []
        for item in data:
            if "site" in item and "description" in item:
                sites.append([item["site"], item["description"]])
            else:
                print(f"⚠️ Hatalı veri: {item}")
        print(f"📊 Okunan {len(sites)} site bilgisi.")
        return sites
    except Exception as e:
        print(f"❌ Site listesi okunamadı! Hata: {e}")
        return []

def ssl_kontrol(site, description):
    """SSL sertifikasının bitiş tarihini kontrol eder."""
    site = site.replace("https://", "").replace("http://", "").strip()
    try:
        context = ssl.create_default_context()
        with socket.create_connection((site, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=site) as ssock:
                sertifika = ssock.getpeercert()

        bitis_tarihi = datetime.strptime(sertifika['notAfter'], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        kalan_sure = (bitis_tarihi - datetime.now(timezone.utc)).days

        print(f"✅ {site}: SSL Sertifikası {kalan_sure} gün sonra sona erecek.")
        SSL_DOMAIN_METRIC.labels(site=site, description=description, type="SSL").set(kalan_sure)

    except Exception as e:
        print(f"⚠️ {site}: SSL hatası - {e}")
        SSL_DOMAIN_METRIC.labels(site=site, description=description, type="SSL").set(-1)

def get_whois_expiry(domain):
    """WHOIS sorgusu yaparak domainin bitiş tarihini alır."""
    try:
        whois_output = subprocess.run(["wsl", "whois", domain], capture_output=True, text=True).stdout
        for pattern in EXPIRY_PATTERNS:
            match = re.search(pattern, whois_output)
            if match:
                return match.group(1)
    except Exception as e:
        print(f'⚠️ WHOIS hatası: {domain} - {e}')
    return None

def parse_expiry_date(date_str):
    """Farklı tarih formatlarını datetime nesnesine çevirir."""
    if not date_str:
        return None
    date_formats = ["%Y-%m-%d", "%d-%b-%Y", "%d.%m.%Y", "%d/%m/%Y", "%d %b %Y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def domain_kontrol(site, description):
    """Domainin WHOIS süresini kontrol eder."""
    domain = site.replace("www.", "").strip()
    expiry_date_str = get_whois_expiry(domain)
    expiry_date = parse_expiry_date(expiry_date_str)

    if expiry_date:
        days_left = (expiry_date - datetime.today()).days
        print(f"✅ {domain}: Domain süresi {days_left} gün kaldı.")
        SSL_DOMAIN_METRIC.labels(site=site, description=description, type="Domain").set(days_left)
    else:
        print(f"❌ {domain}: Domain süresi bulunamadı!")
        SSL_DOMAIN_METRIC.labels(site=site, description=description, type="Domain").set(-1)

def main():
    """Ana döngü: Verileri al, kontrol et, Prometheus'a gönder."""
    start_http_server(9000)
    print("🚀 Prometheus Exporter başlatıldı: http://127.0.0.1:9000/metrics")

    while True:
        print("🔄 SSL ve Domain Kontrolleri Yenileniyor...")
        siteler = siteleri_oku()
        if not siteler:
            print("❌ Site listesi boş!")
        else:
            for site, description in siteler:
                ssl_kontrol(site, description)
                domain_kontrol(site, description)
        time.sleep(3600)  # 1 saat bekle ve tekrar çalıştır

if __name__ == "__main__":
    main()
