from curl_cffi import requests
import json
from google import genai
import gspread
import datetime
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def kap_fon_ozeti_al():
    url = "https://www.kap.org.tr/tr/api/disclosures"
    print("Bağlanılıyor...")
    
    try:
        # impersonate="chrome" parametresi ile Cloudflare engelini aşıyoruz
        response = requests.get(url, impersonate="chrome", timeout=30)
        veri = response.json()
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return
    
    fon_haberleri = []
    for bildirim in veri:
        basic = bildirim.get("basic", {})
        sirket = basic.get("companyName", "") or ""
        baslik = basic.get("title", basic.get("subject", "")) or ""
        
        if "FON" in sirket.upper() or "PORTFÖY" in sirket.upper() or "FON" in baslik.upper():
            link = f"https://www.kap.org.tr/tr/Bildirim/{basic.get('disclosureIndex')}"
            fon_haberleri.append(f"Şirket: {sirket}\nBaşlık: {baslik}\nLink: {link}")
    
    if not fon_haberleri:
        print("Yeni bildirim yok.")
        return

    print("Gemini ile özetleniyor...")
    metin = "\n\n".join(fon_haberleri)
    prompt = f"KAP fon bildirimlerini incele. Yatırımcılar için günlük bülten şeklinde, kısa maddeler halinde özetle:\n\n{metin}"
    
    try:
        cevap = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
    except Exception as e:
        print(f"Gemini hatası: {e}")
        return
    
    try:
        gcp_creds = json.loads(os.environ.get("GCP_CREDENTIALS"))
        gc = gspread.service_account_from_dict(gcp_creds)
        
        tablo_id = "1BeRZvdTRZC9Kb8R2TprmYiTgzyDMaqr10p0xxhBJ0AM"
        sayfa = gc.open_by_key(tablo_id).sheet1
        
        tarih = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sayfa.append_row([tarih, cevap.text])
        print("Google E-Tablo'ya başarıyla yazıldı!")
    except Exception as e:
        print(f"E-Tablo hatası: {e}")

if __name__ == "__main__":
    kap_fon_ozeti_al()
