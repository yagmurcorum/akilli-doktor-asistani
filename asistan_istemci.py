"""
asistan_istemci.py  (Terminal İstemcisi)

Amaç:
- Komut satırından (terminal) FastAPI sunucusundaki /chat adresine mesaj göndermek
- Sunucudan gelen modeli (Gemini) yanıtını ekranda göstermek
- API sözleşmesine uygun olarak: name, age, gender, message (+ opsiyonel session_id) göndermek

Ön koşullar:
- API sunucusu çalışıyor olmalı:
   1) .\venv\Scripts\Activate.ps1
    2) uvicorn asistan_api:app --reload
- Test ekranı (istersen): http://127.0.0.1:8000/docs
- Sohbet adresi:          http://127.0.0.1:8000/chat  (yalnızca POST kabul eder)

Önemli notlar (API sözleşmesi):
- name       : metin (boş olamaz; istemci boşsa “Misafir” varsayılanını kullanır)
- age        : tam sayı (1–120 aralığında olmalı; aksi halde tekrar istenir)
- gender     : metin; 'female' / 'male' / 'other' (esnek girdi alınıp normalize edilir)
- message    : metin (kullanıcının sorusu)
- session_id : metin (opsiyonel) → Aynı kullanıcı için farklı sohbet defterleri açmana yarar
               - Boş bırakırsan aynı “name” için tek bir hafıza kullanılır
               - Doldurursan name + ":" + session_id anahtarı ile ayrık bir hafıza tutulur
"""

import requests  # Sunucuya HTTP isteği atmak için gerekli kütüphane

# 1) API sunucusunun adresi
#    - Aynı bilgisayarda  127.0.0.1 (localhost) doğrudur
#    - Port 8000 ise: http://127.0.0.1:8000
#    - Biz doğrudan /chat uç noktasına mesaj atacağız
API_URL = "http://127.0.0.1:8000/chat"


def normalize_gender(raw: str) -> str:
    """
    Girilen cinsiyet metnini API'nin beklediği değerlere normalize eder.
    Kabul edilen örnek girişler:
      - female:  female, f, kadın, kadin
      - male  :  male, m, erkek
      - other :  diğer tüm girişler
    """
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
    Bu fonksiyon EŞİTTİR “Sunucuya bir mesaj gönder ve cevabı geri döndür”.
    Neden fonksiyon yazdık?
    - Kod tekrarını önler
    - Hata yakalama ve formatlama tek yerde olur

    name       : Kullanıcı adı (sunucuda konuşma hafızasını bu isimle eşliyoruz)
    age        : Yaş (asistanın üslubunu yaşa uygun hale getirmek için)
    gender     : 'female' / 'male' / 'other' (normalize edilmiş olmalı)
    message    : Kullanıcının sorduğu soru/mesaj
    session_id : Aynı kullanıcı için farklı, birbirinden izole sohbet oturumları açmak için opsiyonel kimlik

    Dönen değer: Sunucunun JSON yanıtındaki 'response' metni
    """
    # Sunucuya göndereceğimiz veri paketi (JSON gövdesi)
    payload = {
        "name": name,         # hafıza anahtarı gibi kullanılıyor
        "age": age,           # yaş: üslup/tavsiye için (API 1–120 aralığı bekler)
        "gender": gender,     # cinsiyet: ton/hitap kişiselleştirmesi (female/male/other)
        "message": message    # asıl soru/mesaj
    }
    # session_id boş değilse ekle (boş ise hiç göndermemek daha temizdir)
    if session_id:
        payload["session_id"] = session_id

    try:
        # Sunucuya POST isteği atıyoruz
        # - json=payload dersen requests senin için Content-Type: application/json ayarlar
        # - timeout=30: Ağ sorunu olursa en fazla 30 saniye bekle, sonra hata ver
        response = requests.post(API_URL, json=payload, timeout=30)

        # HTTP 200 ise başarılı demektir
        if response.status_code == 200:
            data = response.json()               # Örn: {"response": "modelin cevabı"}
            return data.get("response", "")      # 'response' anahtarını güvenle al
        else:
            # 200 değilse, sunucudan dönen hata bilgisini döndürelim
            # Örn: 422 (tip/alan hatası), 500 (sunucu hatası) vb.
            return f"⚠ Sunucu hatası [{response.status_code}]: {response.text}"

    except requests.exceptions.RequestException as e:
        # İnternet yok, sunucu kapalı, adres yanlış, zaman aşımı vs. gibi tüm ağ hataları burada yakalanır
        return f"⚠ Bağlantı hatası: {e}"


def ask_int_in_range(prompt: str, min_value: int, max_value: int) -> int:
    """
    Kullanıcıdan sayısal bir değer iste ve [min_value, max_value] aralığına düşene kadar sor.
    API, yaş için 1–120 aralığını beklediğinden, burada doğrulamayı yapıyoruz.
    """
    while True:
        raw = input(prompt).strip()
        if raw.isdigit():
            value = int(raw)
            if min_value <= value <= max_value:
                return value
        print(f"⚠ Lütfen {min_value}–{max_value} aralığında bir sayı girin.")


def main() -> None:
    """
    Uygulamanın başladığı yer.
    Akış:
      1) Kullanıcıdan ad, yaş ve cinsiyet al (gerekli doğrulamalarla)
      2) Opsiyonel session_id al (boş geçilebilir)
      3) Sonsuz döngüde kullanıcıdan mesaj al
      4) 'quit' yazarsa çık
      5) Her mesajı sunucuya gönder, yanıtı göster
    """
    print("\n=== Doktor Asistanı İstemcisi ===")
    print("Bu program, yazdıklarını AI doktora iletip cevabı getirir.")
    print("Çıkmak için istediğin zaman 'quit' yazıp Enter'a basabilirsin.\n")

    # Ad: boş girilirse nazik varsayılan kullan
    name = input("Adınız: ").strip()
    if not name:
        name = "Misafir"

    # Yaş: 1–120 aralığında zorunlu
    age = ask_int_in_range("Yaşınız (1–120): ", 1, 120)

    # Cinsiyet: esnek girdi al, normalize et (female/male/other)
    gender_raw = input("Cinsiyetiniz (female/male/other - boş geçersen other): ").strip()
    gender = normalize_gender(gender_raw)

    # Opsiyonel session_id: boş bırakabilirsin (aynı 'name' için tek defter)
    # Doldurursan 'name:session_id' hafıza anahtarıyla ayrık bir sohbet defteri oluşur
    session_id = input("Oturum kimliği (opsiyonel, yeni sohbet için farklı bir değer gir): ").strip()
    if not session_id:
        session_id = None

    print("\nSohbet başladı. Mesajını yaz ve Enter'a bas. (Çıkmak için 'quit')\n")

    # Sonsuz sohbet döngüsü
    while True:
        # Kullanıcıdan bir mesaj isteyelim
        user_msg = input(f"{name}: ").strip()
        # 'quit' yazarsa döngüden çık, programı sonlandır
        if user_msg.lower() == "quit":
            print("▶ Oturum sonlandırıldı. Görüşmek üzere!")
            break

        # Boş mesaj yazdıysa uyar ve döngünün başına dön
        if not user_msg:
            print("⚠ Boş mesaj yazdın. Lütfen bir şeyler yazıp Enter'a bas.\n")
            continue

        # Mesajı sunucuya gönderip cevabı al
        reply = send_message(name, age, gender, user_msg, session_id=session_id)

        # Cevabı şık bir şekilde yazdıralım
        print("\n— Doktor Asistanı —")
        print(reply if reply else "(boş yanıt)")
        print("— — — — — — — — — —\n")


# “Bu dosyayı doğrudan çalıştırdığında main() çalışsın”
# (Başka bir dosyada import edilirse main otomatik çalışmaz — iyi bir davranış)
if __name__ == "__main__":
    main()