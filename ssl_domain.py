import ssl
import socket
import time
import pandas as pd
import requests
from datetime import datetime, timezone
from prometheus_client import start_http_server, Gauge

# Prometheus metriği (Tek Tip)
DOMAIN_SSL_EXPIRY_DAYS = Gauge("domain_ssl_expiry_days", "The number of days left until SSL or Domain expiration.", ["site", "description", "type"])

# WHOIS API Bilgileri (Kendi API Key’ini buraya ekle!)
API_KEY = "at_8jaZQ0rsE6DCV2EVSVwqaEPNz7gbB"
WHOIS_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

def siteleri_oku(dosya_adi="input.xlsx"):
    """Excel dosyasından site adreslerini ve açıklamalarını okur."""
    try:
        df = pd.read_excel(dosya_adi, dtype=str)
        if df.columns[0] != "site" or df.columns[1] != "description":
            df.columns = ["site", "description"]
        df = df.dropna(subset=["site"])
        return df[["site", "description"]].values.tolist()
    except Exception as e:
        print(f"❌ Hata: Site listesi okunamadı! Hata mesajı: {e}")
        return []

def ssl_kontrol(site, description):
    """Verilen sitenin SSL sertifikasını kontrol eder."""
    site = site.replace("https://", "").replace("http://", "").strip()
    try:
        context = ssl.create_default_context()
        with socket.create_connection((site, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=site) as ssock:
                sertifika = ssock.getpeercert()
        bitis_tarihi = datetime.strptime(sertifika['notAfter'], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        kalan_sure = (bitis_tarihi - datetime.now(timezone.utc)).days
        DOMAIN_SSL_EXPIRY_DAYS.labels(site=site, description=description, type="ssl").set(kalan_sure)
    except Exception as e:
        print(f"❌ Hata ({site} - SSL): {e}")

def domain_kontrol(site, description):
    """Verilen domainin süresini WHOIS API ile kontrol eder."""
    domain = site.strip().replace("www.", "")
    try:
        params = {"apiKey": API_KEY, "domainName": domain, "outputFormat": "json"}
        response = requests.get(WHOIS_URL, params=params)
        data = response.json()
        expiration_date = data.get("WhoisRecord", {}).get("expiresDate", "Unknown")
        if expiration_date != "Unknown":
            expiration_date = pd.to_datetime(expiration_date).replace(tzinfo=None)
            days_left = (expiration_date - pd.to_datetime("today").replace(tzinfo=None)).days
            DOMAIN_SSL_EXPIRY_DAYS.labels(site=site, description=description, type="domain").set(days_left)
    except Exception as e:
        print(f"❌ Hata ({site} - Domain): {e}")

def main():
    start_http_server(9000)
    print("🚀 Prometheus Exporter başlatıldı! http://127.0.0.1:9000/metrics")
    while True:
        siteler = siteleri_oku()
        for site, description in siteler:
            ssl_kontrol(site, description)
            domain_kontrol(site, description)
        time.sleep(3600)

if __name__ == "__main__":
    main()
