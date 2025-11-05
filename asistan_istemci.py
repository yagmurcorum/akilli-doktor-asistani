"""
asistan_istemci.py (Terminal İstemcisi)

Terminal üzerinden FastAPI sunucusundaki /chat endpoint'ine mesaj gönderir.
API sunucusu çalışıyor olmalıdır (uvicorn asistan_api:app --reload).
Detaylı kullanım için README.md dosyasına bakın.
"""

import requests
import os
from dotenv import load_dotenv
# API sunucu adresi
API_URL = "http://127.0.0.1:8000/chat"

def normalize_gender(raw: str) -> str:
    """Cinsiyet metnini API'nin beklediği değerlere normalize eder (female/male/other)"""
    if not raw:
        return "other"
    v = raw.strip().lower()
    if v in {"female", "f", "kadın", "kadin"}:
        return "female"
    if v in {"male", "m", "erkek"}:
        return "male"
    return "other"

def send_message(name: str, age: int, gender: str, message: str, session_id: str | None = None) -> str:
    """
    Sunucuya mesaj gönderir ve cevabı döndürür.
    
    Parametreler:
    - name: Kullanıcı adı (hafıza anahtarı için)
    - age: Yaş (1-120)
    - gender: Cinsiyet (female/male/other)
    - message: Kullanıcı mesajı
    - session_id: Opsiyonel oturum kimliği (çoklu sohbet için)
    
    Döner: Sunucunun yanıt metni veya hata mesajı
    """
    payload = {
        "name": name,
        "age": age,
        "gender": gender,
        "message": message
    }
    if session_id:
        payload["session_id"] = session_id
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "")
        else:
            return f"⚠ Sunucu hatası [{response.status_code}]: {response.text}"
    except requests.exceptions.RequestException as e:
        return f"⚠ Bağlantı hatası: {e}"

def ask_int_in_range(prompt: str, min_value: int, max_value: int) -> int:
    """Kullanıcıdan sayısal değer ister ve belirtilen aralıkta olana kadar sorar"""
    while True:
        raw = input(prompt).strip()
        if raw.isdigit():
            value = int(raw)
            if min_value <= value <= max_value:
                return value
        print(f"⚠ Lütfen {min_value}–{max_value} aralığında bir sayı girin.")

def main() -> None:
    """Ana program: Kullanıcıdan bilgileri alır ve sohbet döngüsü başlatır"""
    print("\n=== Doktor Asistanı İstemcisi ===")
    print("Bu program, yazdıklarını AI doktora iletip cevabı getirir.")
    print("Çıkmak için istediğin zaman 'quit' yazıp Enter'a basabilirsin.\n")
    
    # Kullanıcı bilgilerini al
    name = input("Adınız: ").strip()
    if not name:
        name = "Misafir"
    
    age = ask_int_in_range("Yaşınız (1–120): ", 1, 120)
    
    gender_raw = input("Cinsiyetiniz (female/male/other - boş geçersen other): ").strip()
    gender = normalize_gender(gender_raw)
    
    session_id = input("Oturum kimliği (opsiyonel, yeni sohbet için farklı bir değer gir): ").strip()
    if not session_id:
        session_id = None
    
    print("\nSohbet başladı. Mesajını yaz ve Enter'a bas. (Çıkmak için 'quit')\n")
    
    # Sohbet döngüsü
    while True:
        user_msg = input(f"{name}: ").strip()
        
        if user_msg.lower() == "quit":
            print("▶ Oturum sonlandırıldı. Görüşmek üzere!")
            break
        
        if not user_msg:
            print("⚠ Boş mesaj yazdın. Lütfen bir şeyler yazıp Enter'a bas.\n")
            continue
        
        # Mesajı sunucuya gönder ve yanıtı al
        reply = send_message(name, age, gender, user_msg, session_id=session_id)
        
        # Yanıtı göster
        print("\n— Doktor Asistanı —")
        print(reply if reply else "(boş yanıt)")
        print("— — — — — — — — — —\n")

if __name__ == "__main__":
    main()
