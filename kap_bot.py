import requests
import json
from google import genai
import gspread
import datetime
import os
import urllib.parse

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def kap_fon_ozeti_al():
    print("GitHub IP engelini aşmak için Proxy kanalları deneniyor...")
    
    hedef_url = "https://www.kap.org.tr/tr/api/disclosures"
    kodlanmis_url = urllib.parse.quote(hedef_url, safe='')
    
    # Cloudflare engellerini aşmak için sırayla denenecek 3 farklı ücretsiz proxy kanalı
    proxy_kanallari = [
        f"https://api.allorigins.win/raw?url={kodlanmis_url}",
        f"https://api.codetabs.com/v1/proxy?quest={hedef_url}",
        f"https://corsproxy.io/?{kodlanmis_url}"
    ]
    
    veri = None
    for kanal in proxy_kanallari:
        try:
            isim = kanal.split('/')[2]
            print(f"Denenen kanal: {isim}")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(kanal, headers=headers, timeout=20)
            
            if response.status_code == 200:
                try:
                    veri = response.json()
                    print(f"Bağlantı BAŞARILI! Veri {isim} üzerinden çekildi.")
                    break # Başarılı olursa diğer proxy'leri denemeden döngüden çık
                except json.JSONDecodeError:
                    print("Bu kanal Cloudflare engeline takıldı, diğerine geçiliyor.")
        except Exception as e:
            print(f"Kanal başarısız: {e}")
            
    if not veri:
        print("Tüm proxy kanalları başarısız oldu. KAP API'si geçici olarak yanıt vermiyor olabilir.")
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
