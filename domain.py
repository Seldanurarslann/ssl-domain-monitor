from prometheus_client import start_http_server, Gauge
import requests
import pandas as pd
import os
import time
import pytz

# Prometheus metrikleri
domain_expiry_days_left = Gauge('domain_expiry_days_left', 'The number of days left until the domain expiration.', ['domain'])

# WHOIS API Bilgileri (Kendi API Key’ini buraya ekle!)
API_KEY = "at_8jaZQ0rsE6DCV2EVSVwqaEPNz7gbB"  # Buraya aldığın API Key’i ekle
WHOIS_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

# Excel dosyasının yolu
excel_file = "input.xlsx"

# Dosyanın var olup olmadığını kontrol et
if not os.path.isfile(excel_file):
    print(f"Hata: {excel_file} dosyası bulunamadı!")
    exit(1)

# Excel dosyasını oku
df = pd.read_excel(excel_file)

# Prometheus başlıkları
def update_metrics():
    # Domainleri işle
    for index, row in df.iterrows():
        domain = str(row["site"]).strip().replace("www.", "")

        if not domain:
            continue

        try:
            # WHOIS API isteği yap
            params = {
                "apiKey": API_KEY,
                "domainName": domain,
                "outputFormat": "json",
            }
            response = requests.get(WHOIS_URL, params=params)

            # JSON yanıtı işle
            data = response.json()
            expiration_date = data.get("WhoisRecord", {}).get("expiresDate", "Unknown")
            
            # Veriyi epoch formatına çevir ve metrikleri güncelle
            if expiration_date != "Unknown":
                # Tarihi timezone'suz hale getir
                expiration_date = pd.to_datetime(expiration_date).replace(tzinfo=None)
                today = pd.to_datetime("today").replace(tzinfo=None)
                
                # Kalan gün sayısını hesapla
                days_left = (expiration_date - today).days
                domain_expiry_days_left.labels(domain=domain).set(days_left)

        except Exception as e:
            print(f"❌ Hata ({domain}): {e}")

def main():
    # Prometheus HTTP server'ı başlat (8001 portu)
    start_http_server(8001)
    print("🚀 Prometheus Exporter başlatıldı! http://127.0.0.1:8001/metrics")
    
    while True:
        update_metrics()  # Metrikleri güncelle
        time.sleep(3600)  # 1 saatte bir güncelle

if __name__ == "__main__":
    main()
