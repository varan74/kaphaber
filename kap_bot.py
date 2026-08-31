import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import json
import time
from google import genai
import gspread
import datetime
import os

# API anahtarını GitHub Secrets'tan alıyor
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def kap_fon_ozeti_al():
    url = "https://www.kap.org.tr/tr/api/disclosures"
    print("Bağlanılıyor...")
    
  try:
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        driver = uc.Chrome(
            options=options, 
            version_main=151,
            headless=True, 
            use_subprocess=True
        )
        
        driver.get(url)
        time.sleep(5) 
        
        icerik = driver.find_element(By.TAG_NAME, "body").text
        veri = json.loads(icerik)
        driver.quit()
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        try:
            driver.quit()
        except:
            pass
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
        # JSON dosyasını GitHub Secrets üzerinden sanal olarak okuyor
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
