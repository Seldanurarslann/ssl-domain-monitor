import pandas as pd
import subprocess
import re
import os
import time
from datetime import datetime
from prometheus_client import start_http_server, Gauge

# Prometheus metrikleri
domain_expiry_gauge = Gauge('domain_check', 'Days left until the domain expires', ['domain'])

# Excel dosyasının yolu
excel_file = "input.xlsx"

# Dosyanın var olup olmadığını kontrol et
if not os.path.isfile(excel_file):
    print(f"Hata: {excel_file} dosyası bulunamadı!")
    exit(1)

# WHOIS sorgusu için regex desenleri
expiry_patterns = [
    r"Expires on: (\d{4}-\d{2}-\d{2})",
    r"Expiry Date: (\d{4}-\d{2}-\d{2})",
    r"Registry Expiry Date: (\d{4}-\d{2}-\d{2})",
    r"Expiration Date: (\d{4}-\d{2}-\d{2})",
    r"Expiry Date: (\d{2}-[A-Za-z]{3}-\d{4})",  # 01-Jan-2025 formatı
    r"Expiry Date: (\d{2}\.\d{2}\.\d{4})",      # 01.01.2025 formatı
    r"Expiry: (\d{2}/\d{2}/\d{4})",             # 01/01/2025 formatı
    r"Expiration Date: (\d{2} [A-Za-z]{3} \d{4})", # 01 Jan 2025 formatı
]

# Prometheus HTTP sunucusunu başlat
start_http_server(8001)  # 8001 portunda çalıştır

def get_domains():
    """Excel'deki domainleri oku"""
    df = pd.read_excel(excel_file)
    return [str(row["site"]).strip().replace("www.", "") for index, row in df.iterrows() if row["site"]]

def get_whois_expiry(domain):
    """WHOIS sorgusu yaparak domainin bitiş tarihini al"""
    try:
        whois_output = subprocess.run(["wsl", "whois", domain], capture_output=True, text=True).stdout
        for pattern in expiry_patterns:
            match = re.search(pattern, whois_output)
            if match:
                return match.group(1)  # Tarihi döndür
    except Exception as e:
        print(f'Hata: {domain} için WHOIS sorgusu başarısız! - {e}')
    return None

def parse_expiry_date(date_str):
    """Tarih formatlarını kontrol edip datetime nesnesine dönüştür"""
    if not date_str:
        return None
    date_formats = [
        "%Y-%m-%d", "%d-%b-%Y", "%d.%m.%Y", "%d/%m/%Y", "%d %b %Y"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def update_metrics():
    """Tüm domainler için WHOIS sorgusu yap ve metrikleri güncelle"""
    domains = get_domains()
    for domain in domains:
        expiry_date_str = get_whois_expiry(domain)
        expiry_date = parse_expiry_date(expiry_date_str)

        if expiry_date:
            days_left = (expiry_date - datetime.today()).days
            domain_expiry_gauge.labels(domain=domain).set(days_left)
            print(f"{domain}: {days_left} gün kaldı")
        else:
            domain_expiry_gauge.labels(domain=domain).set(-1)  # Hata kodu olarak -1 ata
            print(f"{domain}: Geçerli bitiş tarihi bulunamadı!")

# Sonsuz döngüde metrikleri güncelle
while True:
    update_metrics()
    time.sleep(3600)  # 1 saatte bir çalıştır (Grafana'da düzenli veri almak için)
