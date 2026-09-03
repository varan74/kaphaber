import borsapy
import pandas as pd
from google import genai
import gspread
import datetime
import os
import json

def kap_fon_ozeti_al():
    print("--- BORSAPY İÇERİĞİ ---")
    print("Ana Modüller:", dir(borsapy))
    
    for attr_name in dir(borsapy):
        if not attr_name.startswith("__"):
            try:
                attr = getattr(borsapy, attr_name)
                print(f"{attr_name} Modülü İçeriği:", dir(attr))
            except:
                pass
    print("-----------------------")
    print("Lütfen Github Actions loglarındaki bu çıktıyı kopyalayıp buraya yapıştırın. Doğru fonksiyonu hemen bulalım.")

if __name__ == "__main__":
    kap_fon_ozeti_al()
