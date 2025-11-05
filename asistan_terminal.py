"""
Akıllı Doktor Asistanı (Gemini) - Terminal Uygulaması

Terminal üzerinden Gemini ile kişiselleştirilmiş sağlık sohbeti sunar.
Kullanıcının ad/yaş/cinsiyet bilgisi ile hafızalı sohbet deneyimi sağlar.
Detaylı kullanım için README.md dosyasına bakın.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.messages import SystemMessage
import warnings

# Terminali gereksiz uyarı ve loglardan arındır (okunabilirlik için)
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

# .env dosyasından ortam değişkenlerini yükle ve API anahtarlarını oku
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin.")
llm_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# İzleme ve kaynak kullanımı için ayarlar:
# - DEBUG_MODE: True olduğunda her turda sohbet hafızasının kısa özetini yazdırır
# - MEMORY_MAX_MESSAGES: Mesaj sayısı bu sınırı aşarsa eski mesajları budar (bellek/masraf kontrolü)
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
MEMORY_MAX_MESSAGES = int(os.getenv("MEMORY_MAX_MESSAGES", "20"))

# Gemini istemcisini oluştur (model adı, çeşitlilik için sıcaklık, API anahtarı)
llm = ChatGoogleGenerativeAI(
    model=llm_model,
    temperature=0.7,
    api_key=api_key,
)

def ask_int_in_range(prompt: str, min_value: int, max_value: int) -> int:
    """
    Kullanıcıdan sayısal değer alır ve verilen aralıkta olana kadar tekrar ister.
    Yanlış girişlerde kullanıcıyı bilgilendirir.
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
    Cinsiyet girdisini female/male/other değerlerinden birine indirger.
    Türkçe kısaltmaları ve yazımları da destekler.
    """
    if not raw:
        return "other"
    v = raw.strip().lower()
    if v in {"female", "f", "kadın", "kadin"}:
        return "female"
    if v in {"male", "m", "erkek"}:
        return "male"
    return "other"

# Sohbet hafızası (geçmişi saklar) ve LLM ile diyalog zinciri
memory = ConversationBufferMemory(return_messages=True)
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)

# Kullanıcıdan kişiselleştirme için temel verileri al (isim/yaş/cinsiyet)
print("\n=== Akıllı Doktor Asistanı ===")
name = input("Adınız: ").strip()
if not name:
    name = "Misafir"
age = ask_int_in_range("Yaşınız (1–120): ", 1, 120)
gender_raw = input("Cinsiyetiniz (female/male/other - boş geçersen other): ").strip()
gender = normalize_gender(gender_raw)

# Cinsiyet ve yaşa bağlı selamlama/ton/odak alanlarını belirle (yanıtların kişiselleşmesi için)
if gender == "female":
    hitap_tonu = "Sayın" if age >= 18 else "Sevgili"
    hitap_ozel = "Kadın sağlığı konularında (adet döngüsü, hamilelik, menopoz, meme sağlığı vb.) özel dikkat göster. "
    risk_faktoru = "Kadınlarda özellikle dikkat edilmesi gerekenler: meme kanseri taraması, rahim ağzı kanseri, kemik sağlığı (osteoporoz), tiroid sorunları. "
    hitap_stili = "nazik, empatik ve anlayışlı"
elif gender == "male":
    hitap_tonu = "Sayın" if age >= 18 else "Sevgili"
    hitap_ozel = "Erkek sağlığı konularında (prostat sağlığı, testosteron, kalp sağlığı vb.) özel dikkat göster. "
    risk_faktoru = "Erkeklerde özellikle dikkat edilmesi gerekenler: prostat sağlığı, kalp-damar hastalıkları, testis kanseri, karaciğer sağlığı. "
    hitap_stili = "nazik, empatik ve doğrudan"
else:  # other
    # Nötr ve kapsayıcı selamlama diğer seçenekler için daha uygundur
    hitap_tonu = "Merhaba"
    hitap_ozel = "Sağlık konularında kapsayıcı ve hassas bir yaklaşım benimse. "
    risk_faktoru = "Genel sağlık taramaları ve önleyici bakım konularında bilgilendir. "
    hitap_stili = "kapsayıcı, empatik ve saygılı"

# Yaş grubuna göre ek yönlendirme (çocuk/genç erişkin/ileri yaş odakları)
if age < 18:
    yas_notu = "Genç/çocuk sağlığı konularında yaşa uygun, anlaşılır dil kullan. "
    yas_ozel = "Büyüme-gelişme, aşı takvimi, ergenlik dönemi sağlığı gibi konularda bilgilendir. "
elif age >= 50:
    yas_notu = "Orta-ileri yaş grubuna özel sağlık konularını (kronik hastalıklar, taramalar, yaşam tarzı) vurgula. "
    yas_ozel = "Düzenli kontroller, kanser taramaları, kalp sağlığı, diyabet riski gibi konularda öneriler sun. "
else:
    yas_notu = "Genç erişkin sağlığı konularında (yaşam tarzı, önleyici bakım, mental sağlık) odaklan. "
    yas_ozel = "Sağlıklı alışkanlıklar, egzersiz, beslenme, stres yönetimi konularında rehberlik et. "

# Modelin davranışını yöneten kural seti (rol, sınırlar, sunum, acil durum yönlendirmesi)
# Bunu 'SystemMessage' olarak eklemek kritik; model bunu kullanıcı mesajı değil talimat olarak okur.
intro = (
    f"Rolün: Deneyimli ve empatik bir sağlık asistanısın. Danışanın adı {name}, {age} yaşında. "
    f"Hitap: {hitap_tonu} {name} şeklinde hitap et; hitap tonunu {hitap_stili} tut. "
    f"\n\n"
    f"Kişiselleştirme: "
    f"{hitap_ozel}"
    f"{risk_faktoru}"
    f"{yas_notu}"
    f"{yas_ozel}"
    f"\n\n"
    f"Amaç: Sağlıkla ilgili sorulara nazik, sade ve {name}'in yaşına ({age}) uygun yanıtlar vermek; "
    f"genel, güvenli ve uygulanabilir öneriler sunmak. "
    f"\n\n"
    f"Sınırlar: Kesin tanı/ilaç/tedavi yazma; riskli veya acil belirtilerde profesyonel yardıma yönlendir. "
    f"Tıbbi jargondan kaçın, anlaşılır dil kullan. "
    f"{name}'in yaşı ({age}) ve cinsiyet ({gender}) bilgisini yanıtlarında dikkate al. "
    f"\n\n"
    f"Sunum: Kısa paragraflar; gerektiğinde madde işaretleri. "
    f"{name} ismini gerektiğinde kullan; sakin ve empatik bir ton benimse; paniğe sevk etme. "
    f"Gerektiğinde kullanıcıya sorularla netleştirme yap; belirsizliği dürüstçe belirt. "
    f"\n\n"
    f"Acil uyarılar: Hayati risk içeren belirtilerde (göğüs ağrısı, nefes darlığı, bilinç kaybı, şiddetli kanama vb.) "
    f"hemen 112'yi veya en yakın acil servise gitmesini öner. "
    f"\n\n"
    f"Cinsiyet ve yaş özel bilgiler: "
    f"{name} için cinsiyet ({gender}) ve yaş ({age}) bilgisini kullanarak "
    f"uygun sağlık önerileri, risk faktörleri ve dikkat edilmesi gereken konuları belirt."
)

# Kural setini sohbet hafızasına 'system' mesajı olarak ekle (bağlamın doğru anlaşılması için)
memory.chat_memory.add_message(SystemMessage(content=intro))

# Kullanıcıya başlangıç mesajları (arayüz akışı için bilgilendirme)
print(f"\nMerhaba {name}! Ben sağlık asistanınım.")
print("Sorularını paylaşmaya başlayabilirsin. Çıkmak için 'quit' yazıp Enter'a basabilirsin.\n")
def maybe_trim_memory():
    """
    Sohbet uzadıkça hafıza şişmemesi için mesajları sınırlar.
    İlk mesaj bir SystemMessage ise (kural seti) onu korur, geri kalanını sondan keser.
    """
    msgs = memory.chat_memory.messages
    if len(msgs) > MEMORY_MAX_MESSAGES:
        is_system_first = getattr(msgs[0], "type", "") == "system"
        if is_system_first:
            system_part = msgs[0:1]
            rest = msgs[1:]
            keep = (MEMORY_MAX_MESSAGES - 1)
            memory.chat_memory.messages = system_part + rest[-keep:]
        else:
            memory.chat_memory.messages = msgs[-MEMORY_MAX_MESSAGES:]

# Ana sohbet döngüsü: kullanıcıdan mesaj al, modele gönder, yanıtı göster
while True:
    user_msg = input(f"{name}: ").strip()

    # Kolay çıkış komutlarını destekle (kullanıcı deneyimi)
    if user_msg.lower()=="quit":
        print("\n▶ Oturum sonlandırıldı. Sağlıklı günler dilerim!")
        break

    # Boş girişte uyar ve yeni giriş iste
    if not user_msg:
        print("⚠ Boş mesaj algılandı. Lütfen bir soru veya açıklama yazın.\n")
        continue

    # Model çağrısı sırasında oluşabilecek ağ/kota vs. hatalarında programın çökmesini engelle
    try:
        reply = conversation.predict(input=user_msg)
    except Exception as e:
        print(f"⚠ Modelden yanıt alınamadı: {e}")
        continue

    # Yanıtı okunaklı bir blok halinde göster (terminal düzeni)
    print("\n" + "-" * 20)
    print("Doktor Asistanı:")
    print(reply if reply else "(boş yanıt)")
    print("-" * 20 + "\n")

    # DEBUG_MODE açıksa o ana kadarki sohbet hafızasının kısa bir özetini yazdır
    if DEBUG_MODE:
        print("Hafıza Özeti:")
        for idx, m in enumerate(memory.chat_memory.messages, start=1):
            role = getattr(m, "type", "msg").upper()
            content = getattr(m, "content", "")
            preview = content if len(content) <= 120 else content[:117] + "..."
            print(f" {idx:02d}. {role}: {preview}")
        print("-" * 28 + "\n")

    # Her tur sonunda hafızayı sınırla (uzun oturumlarda kaynak tasarrufu)
    maybe_trim_memory()