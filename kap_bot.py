import pandas as pd
from borsapy.market import get_kap_provider
from google import genai
import gspread
import datetime
import os
import json

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def kap_fon_ozeti_al():
    print("borsapy üzerinden KAP'a bağlanılıyor...")
    
    try:
        # Doğru modülü çağırdık
        kap = get_kap_provider()
        
        # İçindeki kullanılabilir metodları loga yazdırıyoruz (hata ayıklamak için)
        metodlar = [m for m in dir(kap) if not m.startswith('_')]
        print("Mevcut KAP Metodları:", metodlar)
        
        # Olası metod isimlerini akıllıca deniyoruz
        df_kap = None
        if hasattr(kap, 'get_daily_disclosures'):
            df_kap = kap.get_daily_disclosures()
        elif hasattr(kap, 'get_disclosures'):
            df_kap = kap.get_disclosures()
        else:
            print("KAP bildirimlerini çeken metod bulunamadı. Lütfen logdaki 'Mevcut KAP Metodları' çıktısını paylaşın.")
            return
            
    except Exception as e:
        print(f"KAP verisi çekilirken hata oluştu: {e}")
        return
    
    if df_kap is None or (isinstance(df_kap, pd.DataFrame) and df_kap.empty) or len(df_kap) == 0:
        print("Bugün KAP'a düşen yeni bir bildirim bulunamadı.")
        return

    fon_haberleri = []
    
    # Gelen veri Pandas DataFrame ise
    if isinstance(df_kap, pd.DataFrame):
        for index, row in df_kap.iterrows():
            sirket = str(row.get('companyName', row.get('company', ''))).upper()
            baslik = str(row.get('title', row.get('subject', ''))).upper()
            
            if "FON" in sirket or "PORTFÖY" in sirket or "FON" in baslik:
                idx = row.get('disclosureIndex', row.get('index', ''))
                link = f"https://www.kap.org.tr/tr/Bildirim/{idx}"
                fon_haberleri.append(f"Şirket: {sirket}\nBaşlık: {baslik}\nLink: {link}")
    # Gelen veri JSON (Sözlük) listesi ise
    else:
        for row in df_kap:
            sirket = str(row.get('companyName', row.get('company', ''))).upper()
            baslik = str(row.get('title', row.get('subject', ''))).upper()
            
            if "FON" in sirket or "PORTFÖY" in sirket or "FON" in baslik:
                idx = row.get('disclosureIndex', row.get('index', ''))
                link = f"https://www.kap.org.tr/tr/Bildirim/{idx}"
                fon_haberleri.append(f"Şirket: {sirket}\nBaşlık: {baslik}\nLink: {link}")

    if not fon_haberleri:
        print("Bugün KAP'a düşen yeni bir 'fon' bildirimi bulunamadı.")
        return

    print(f"{len(fon_haberleri)} adet fon bildirimi bulundu. Gemini ile özetleniyor...")
    metin = "\n\n".join(fon_haberleri)
    prompt = f"Aşağıdaki KAP fon bildirimlerini incele. Yatırımcılar için günlük bülten şeklinde, kısa maddeler halinde özetle:\n\n{metin}"
    
    try:
        cevap = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return
    
    try:
        gcp_creds = json.loads(os.environ.get("GCP_CREDENTIALS"))
        gc = gspread.service_account_from_dict(gcp_creds)
        tablo_id = "1BeRZvdTRZC9Kb8R2TprmYiTgzyDMaqr10p0xxhBJ0AM"
        sayfa = gc.open_by_key(tablo_id).sheet1
        
        tarih = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sayfa.append_row([tarih, cevap.text])
        print("İşlem tamamlandı! Özet E-Tablo'ya başarıyla yazıldı.")
    except Exception as e:
        print(f"E-Tablo hatası: {e}")

if __name__ == "__main__":
    kap_fon_ozeti_al()
