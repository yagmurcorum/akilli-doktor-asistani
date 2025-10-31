# Akıllı Doktor Asistanı (Gemini) - Terminal Uygulaması
# Amaç:
# - Kullanıcının adı/yaşı/cinsiyeti ile kişiselleştirilmiş, hafızalı bir sohbet deneyimi sunmak
# - LLM (Gemini) ile tek dosyalık, bağımlılığı düşük bir terminal arayüzü sağlamak
#
# Temel Fikir:
# - İlk turda, asistanın “rol/üslup/sınırları” ve kullanıcının profilini (ad/yaş/cinsiyet) içeren
#   bir başlangıç talimatı (system benzeri içerik) hafızaya eklenir.
# - Ardından her kullanıcı mesajı, hafızadaki geçmişle birlikte LLM’e gönderilir ve yanıt üretilir.
#
# Bağımlılıklar:
# - python-dotenv: .env’den API anahtarını okumak için
# - langchain, langchain-google-genai: LLM erişimi + sohbet hafızası
#
# .env İçeriği (örnek):
#   GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
#   LLM_MODEL=gemini-2.5-flash   # opsiyonel; yoksa varsayılan kullanılır

# ------------------------- 0) Kütüphaneler ve ortam ayarları -------------------------
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
# from langchain_core.messages import SystemMessage  # İstersen system rolüyle eklemek için aç

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

# ------------------------- 1) Ortam değişkenlerini yükle (.env) ----------------------
# - GOOGLE_API_KEY zorunlu (Google AI Studio anahtarı)
# - LLM_MODEL opsiyonel (varsayılan: gemini-2.5-flash)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin.")
llm_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# ------------------------- 2) LLM yapılandırması (Gemini) ----------------------------
# - model: Başlangıç için 'gemini-2.5-flash' (hız/ücret dengesi iyi)
# - temperature: 0.3–0.7 güvenli; yükseldikçe yaratıcılık artar ama sapma riski artar
llm = ChatGoogleGenerativeAI(
    model=llm_model,
    temperature=0.7,
    api_key=api_key
)

# ------------------------- 3) Yardımcı: giriş doğrulama/normalize --------------------
def ask_int_in_range(prompt: str, min_value: int, max_value: int) -> int:
    """
    Kullanıcıdan sayısal bir değer iste ve [min_value, max_value] aralığına düşene kadar sor.
    Not: 1–120 sağlık uygulamalarında yaygın makul aralıktır; istersen kolayca değiştirebilirsin.
    """
    while True:
        raw = input(prompt).strip()
        if raw.isdigit():
            value = int(raw)
            if min_value <= value <= max_value:
                return value
        print(f"⚠ Lütfen {min_value}–{max_value} aralığında bir sayı girin.")

def normalize_gender(raw: str) -> str:
    """
    Girilen cinsiyet metnini nötr ve kısa etiketlere normalize eder.
    Kabul edilen örnek girişler:
      - female:  female, f, kadın, kadin
      - male  :  male, m, erkek
      - other :  diğer tüm girişler (boş dahil)
    """
    if not raw:
        return "other"
    v = raw.strip().lower()
    if v in {"female", "f", "kadın", "kadin"}:
        return "female"
    if v in {"male", "m", "erkek"}:
        return "male"
    return "other"

# ------------------------- 4) Konuşma hafızası ve sohbet zinciri ---------------------
# - ConversationBufferMemory: tüm geçmiş mesajları saklar
# - ConversationChain: LLM + hafıza ile uçtan uca sohbet akışı
memory = ConversationBufferMemory(return_messages=True)
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)  # verbose=False: konsol gürültüsünü azalt

# ------------------------- 5) Kişiselleştirme bilgilerini al -------------------------
print("\n=== Akıllı Doktor Asistanı ===")
name = input("Adınız: ").strip()
if not name:
    name = "Misafir"  # boşsa nazik bir varsayılan
age = ask_int_in_range("Yaşınız (1–120): ", 1, 120)
gender_raw = input("Cinsiyetiniz (female/male/other - boş geçersen other): ").strip()
gender = normalize_gender(gender_raw)

# ------------------------- 6) Başlangıç talimatı (system benzeri içerik) ------------
# - Asistanın rolü/üslubu/sınırları ve kullanıcının profili (ad/yaş/cinsiyet) netleştirilir
# - Not: İstersen SystemMessage ile “gerçek” system rolü şeklinde de eklenebilir (aşağıdaki alternatif).
intro = (
    f"Rolün: Deneyimli bir sağlık asistanısın. Danışan {name}, {age} yaşında. "
    f"Hitap tonunu {'kapsayıcı' if gender == 'other' else 'nazik ve empatik'} tut. "
    "Amaç: Sağlıkla ilgili sorulara nazik, sade ve yaşa uygun yanıtlar vermek; "
    "genel, güvenli ve uygulanabilir öneriler sunmak. "
    "Sınırlar: Kesin tanı/ilaç/tedavi yazma; riskli veya acil belirtilerde profesyonel yardıma yönlendir. "
    "Sunum: Kısa paragraflar; gerektiğinde madde işaretleri; gereksiz tıbbi jargondan kaçın. "
    f"Hitap: {name} ismini gerektiğinde kullan; sakin ve empatik bir ton benimse; paniğe sevk etme."
)

# ------------------------- 7) Başlangıç bağlamını hafızaya ekle ----------------------
# Yöntem-A (basit, çalışır): talimatı kullanıcı mesajı gibi eklemek
memory.chat_memory.add_user_message(intro)

# Yöntem-B (daha doğru rol ataması): SystemMessage olarak eklemek
# from langchain_core.messages import SystemMessage
# memory.chat_memory.add_message(SystemMessage(content=intro))

print(f"\nMerhaba {name}! Ben sağlık asistanınım.")
print("Sorularını paylaşmaya başlayabilirsin. Çıkmak için 'quit' yaz.\n")

# ------------------------- 8) Sohbet döngüsü ----------------------------------------
while True:
    user_msg = input(f"{name}: ").strip()

    # Kullanıcı çıkmak isterse
    if user_msg.lower() == "quit":
        print("\n▶ Oturum sonlandırıldı. Sağlıklı günler dilerim!")
        break

    # Boş mesajı nazikçe uyar
    if not user_msg:
        print("⚠ Boş mesaj algılandı. Lütfen bir soru veya açıklama yazın.\n")
        continue

    # LLM yanıtı üret
    reply = conversation.predict(input=user_msg)

    # Yanıtı profesyonel formatta göster
    print("\n— Doktor Asistanı —")
    print(reply if reply else "(boş yanıt)")
    print("— — — — — — — — — —\n")

    # Hafızayı sade ve numaralı olarak göster (öğrenme/demonstrasyon amaçlı)
    # Not: Üretimde gizlilik/gürültü sebepleriyle genelde gösterilmez
    print("Hafıza Özeti:")
    for idx, m in enumerate(memory.chat_memory.messages, start=1):
        role = m.type.upper()
        preview = m.content if len(m.content) <= 120 else m.content[:117] + "..."
        print(f"  {idx:02d}. {role}: {preview}")
    print("----------------------------\n")