from borsapy import kap  # Modülü doğrudan içe aktardık
import pandas as pd
from google import genai
import gspread
import datetime
import os
import json

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def kap_fon_ozeti_al():
    print("borsapy ile KAP verileri çekiliyor...")
    
    try:
        # Doğrudan kap modülünü kullanıyoruz
        df_kap = kap.get_daily_disclosures() 
    except Exception as e:
        print(f"KAP verisi çekilirken hata oluştu: {e}")
        # Hata durumunda metod isimlerini görmek için:
        try:
            print("Mevcut metodlar:", dir(kap))
        except:
            pass
        return
    
    if df_kap is None or df_kap.empty:
        print("Bugün KAP'a düşen yeni bir bildirim bulunamadı.")
        return

    fon_haberleri = []
    
    for index, row in df_kap.iterrows():
        sirket = str(row.get('companyName', '')).upper()
        baslik = str(row.get('title', row.get('subject', ''))).upper()
        
        if "FON" in sirket or "PORTFÖY" in sirket or "FON" in baslik:
            link = f"https://www.kap.org.tr/tr/Bildirim/{row.get('disclosureIndex', '')}"
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
