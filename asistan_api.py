"""
Doktor Asistanı API (Gemini 2.x + LangChain + FastAPI)

Bu dosya, terminaldeki sohbeti HTTP tabanlı bir servise çevirir.
İstemciler (web/mobil/CLI) → /chat’e POST atar → LLM (Gemini) yanıtını JSON döndürür.

Neden bu katman?
- Terminal tek kullanıcı içindir; gerçek hayatta çoklu istemci/API gerekir.
- API, istemcilerle “stabil sözleşme (schema)” sunar; entegrasyon ve test kolaylaşır.

Veri akışı (yüksek seviye):
1) İstemci, JSON ile POST /chat çağırır: {"name","age","gender","message","session_id"}
2) Sunucu, bu kullanıcı + session_id için hafıza (ConversationBufferMemory) bulur/yoksa oluşturur.
3) İlk mesajsa, “sistem talimatı” (rol/üslup/sınırlar) gerçek system rolüyle hafızaya eklenir.
4) Kullanıcı mesajı + hafıza → LLM’e verilir; yanıt üretilir.
5) {"response": "..."} şeklinde döneriz.

Güvenlik sınırı:
- Bu sistem tıbbi teşhis/tedavi/ilaç önermez; sadece genel bilgi verir.
- Acil durumda 112 / profesyonel yardım vurgulanır.

Hızlı kullanım:
- Sunucu:  uvicorn asistan_api:app --reload
- Docs:    http://127.0.0.1:8000/docs
- Health:  http://127.0.0.1:8000/health
- .env:    GOOGLE_API_KEY=YOUR_KEY
           LLM_MODEL=gemini-2.5-flash   (opsiyonel; yoksa varsayılan kullanılır)
"""

# ==================== 0) Bağımlılıklar ve temel kurulum ====================
# logging: print yerine üretime uygun, seviyeli loglama
# dotenv : gizli anahtarları .env’den okumak için (anahtarları koda gömmeyiz)
# FastAPI : HTTP framework
# Pydantic: istek/yanıt şemaları (makine ve insan için anlaşılır sözleşme)
# LangChain + Gemini: LLM erişimi ve sohbet hafızası

import os
import logging
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.messages import SystemMessage  # System rolü için

# ==================== 1) Loglama ====================
# Format kısa ve okunaklı; gereksiz gürültü yok, üretimde yönlendirmesi kolay.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("doctor-assistant-api")


# ==================== 2) Ortam değişkenleri (.env) ====================
# .env → GOOGLE_API_KEY okuruz. Anahtar yoksa erken ve net bir hata ile dururuz.
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY bulunamadı. .env dosyanızı kontrol edin.")

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")  # opsiyonel model seçimi


# ==================== 3) FastAPI uygulaması ====================
# Basit bir tanımla başlıyoruz; Swagger dokümanları otomatik üretilecektir.
app = FastAPI(
    title="Doktor Asistanı API",
    version="1.1.0",
    description="Gemini 2.x tabanlı, kişiselleştirilmiş ve hafızalı sohbet API’si",
)


# ==================== 4) LLM (Gemini) konfigürasyonu ====================
# model      : "gemini-2.5-flash" iyi bir başlangıç; zor muhakeme için "gemini-2.5-pro"
# temperature: 0.3–0.7 güvenli aralık; yükseldikçe yaratıcılık artar ama sapma riski de artar
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    temperature=0.7,
    api_key=GOOGLE_API_KEY,
    # api_version="v1",  # model/sürüm uyumsuzluğu görürsen açmayı dene
)


# ==================== 5) Kullanıcı bazlı konuşma hafızası ====================
# Basit ve etkili bir sözlük: { user_session_key -> ConversationBufferMemory }
# Not: Üretimde “name” yerine benzersiz “user_id” kullanmayı tercih edin.
user_to_memory: Dict[str, ConversationBufferMemory] = {}


# ==================== 6) İstek/Yanıt şemaları ====================
# İstemci ile net bir sözleşmemiz olsun. Hata mesajları da daha anlaşılır olur.

class ChatRequest(BaseModel):
    """
    İstemci istek gövdesi.
    - name       : Kullanıcı adı (hafıza anahtarı; üretimde user_id önerilir)
    - age        : Yaş (üslup ve tavsiyelerde yaş-duyarlılık için)
    - gender     : Cinsiyet (hitap/ton kişiselleştirmesi için; 'female'/'male'/'other' gibi)
    - message    : Kullanıcı mesajı/sorusu (LLM’e iletilecek asıl içerik)
    - session_id : Aynı kullanıcı için paralel ya da bağımsız oturumları ayırmak için
    """
    name: str
    age: int
    gender: str
    message: str
    session_id: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name boş olamaz")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v <= 0 or v > 120:
            raise ValueError("age 1-120 aralığında olmalıdır")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        # Serbest metin kabul ediyoruz ama normalize ediyoruz (female/male/other gibi)
        normalized = v.strip().lower()
        if normalized in {"kadın", "kadin", "female", "f"}:
            return "female"
        if normalized in {"erkek", "male", "m"}:
            return "male"
        # diğer her şey 'other'
        return "other"


class ChatResponse(BaseModel):
    """
    Model yanıtı. Sade ve genişletilebilir (ileride meta/usage eklenebilir).
    - response : Metinsel cevap
    """
    response: str


# ==================== 7) Sistem talimatı (asistanın davranış sözleşmesi) ====================
# İlk turda hafızaya eklenir. Üslup/rol/sınırları belirler; tutarlılık sağlar.
def build_system_instruction(name: str, age: int, gender: str) -> str:
    # Hitap tonunu cinsiyete göre hafif kişiselleştir (nötr tutmaya özen göster)
    gender_note = {
        "female": "Hitap tonunu nazik ve empatik tut.",
        "male": "Hitap tonunu nazik ve empatik tut.",
        "other": "Hitap tonunu kapsayıcı ve empatik tut.",
    }[gender]

    return (
        f"Rolün: Deneyimli bir sağlık asistanısın. Danışan {name}, {age} yaşında. "
        f"{gender_note} "
        "Amaç: Sağlıkla ilgili sorulara nazik, sade ve yaşa uygun yanıtlar vermek; "
        "genel, güvenli ve uygulanabilir öneriler sunmak. "
        "Sınırlar: Kesin tanı/ilaç/tedavi yazma; riskli veya acil belirtilerde profesyonel yardıma yönlendir. "
        "Sunum: Kısa paragraflar; gerektiğinde madde işaretleri; gereksiz tıbbi jargondan kaçın. "
        f"Hitap: {name} ismini gerektiğinde kullan; sakin ve empatik bir ton benimse; paniğe sevk etme. "
        "Gerektiğinde kullanıcıya sorularla netleştirme yap; belirsizliği dürüstçe belirt. "
        "Acil uyarılar: Hayati risk içeren belirtilerde 112’yi veya en yakın sağlık kuruluşunu öner."
    )


# ==================== 8) Yardımcı uç noktalar (root/health) ====================
# Root: Tarayıcıyla açıldığında 404 yerine hoş bir mesaj verelim.
@app.get("/")
def root():
    return {"status": "ok", "message": "Doktor Asistanı API - Belgeler için /docs, sohbet için /chat"}

# Health: Basit sağlık sondajı; otomasyon/izleme için idealdir.
@app.get("/health")
def health():
    return {"ok": True}


# ==================== 9) Ana iş: POST /chat ====================
# Akış:
#   1) Kullanıcı+session hafızasını getir/yoksa oluştur (bağlam korunur)
#   2) İlk mesajda sistem talimatını system rolüyle hafızaya ekle
#   3) Mesaj + hafıza → LLM; yanıtı üret
#   4) Kısa, profesyonel bir log yaz; yalnızca gereken özet bilgiyi tut

@app.post("/chat", response_model=ChatResponse)
async def chat_with_doctor(req: ChatRequest) -> ChatResponse:
    try:
        # 1) Hafıza anahtarı: name + session_id (varsa). Üretimde user_id önerilir.
        base_key = req.name.strip().lower()
        session_suffix = f":{req.session_id.strip()}" if req.session_id else ""
        user_session_key = f"{base_key}{session_suffix}"

        if user_session_key not in user_to_memory:
            user_to_memory[user_session_key] = ConversationBufferMemory(return_messages=True)

        memory = user_to_memory[user_session_key]

        # 2) İlk turda sistem talimatını system rolüyle hafızaya ekle
        if len(memory.chat_memory.messages) == 0:
            sys_msg = build_system_instruction(req.name, req.age, req.gender)
            memory.chat_memory.add_message(SystemMessage(content=sys_msg))

        # 3) LLM + hafıza ile sohbet
        conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
        reply = conversation.predict(input=req.message)

        # 4) Kısa, profesyonel log (gizli veri yok; temel ölçümler var)
        logger.info(
            "chat | user=%r age=%s gender=%s session=%r msg_len=%d resp_len=%d model=%s",
            req.name, req.age, req.gender, req.session_id, len(req.message), len(reply), LLM_MODEL
        )

        return ChatResponse(response=reply)

    except Exception as exc:
        # Üretimde kullanıcıya çok detay verme; ayrıntı log’da kalsın.
        logger.exception("chat failed: %s", exc)
        raise HTTPException(status_code=500, detail="Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.")


# ==================== 10) Kullanım notu  ====================
# Bu servisi iki farklı şekilde test edebilirsin:
# 1) En kolay yol: Sadece tarayıcıdaki test ekranını (docs) kullan
# 2) Alternatif yol: VS Code içinde iki terminal ile (biri sunucu, diğeri mesaj gönderen)
#
# 1) Sadece “docs” ile test (önerilen, tek terminal yeter)
#   a) VS Code → Terminal → New Terminal
#   b) Sanal ortamı aç: .\venv\Scripts\Activate.ps1
#   c) Sunucuyu çalıştır: uvicorn asistan_api:app --reload
#      - Ekranda şunları görürsen hazır:
#        “Uvicorn running on http://127.0.0.1:8000”
#        “Application startup complete.”
#   d) Tarayıcı aç → http://127.0.0.1:8000/docs
#      - Bu sayfa, “hazır form” gibidir.
#   e) /chat bölümünü bul → “Try it out” butonuna bas → şu alanları doldur:
#      - name: Yagmur
#      - age: 24
#      - gender: female
#      - message: Başım ağrıyor…
#      - session_id: test-oturum-1  (opsiyonel)
#      Sonra “Execute” de.
#   f) Hemen altta “Responses” bölümünde modelin cevabını görürsün (response alanında).
#
# 2) İki terminal ile test (sadece alternatif; yapmak zorunda değilsin)
#   Terminal-1 (Sunucu):
#     - .\venv\Scripts\Activate.ps1
#     - uvicorn asistan_api:app --reload
#   Terminal-2 (Mesaj gönderen):
#     - .\venv\Scripts\Activate.ps1
#     - Aşağıdaki komutu yapıştır (bu komut, /chat’e doğru formatta mesaj yollar):
#       Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -Body (@{
#         name="Yagmur"; age=24; gender="female"; message="Başım ağrıyor."; session_id="test-oturum-1"
#       } | ConvertTo-Json) -ContentType "application/json"
#     - Terminal, modelin cevabını yazdırır.
#
# Neden tarayıcı adres çubuğu yerine “docs” ya da komut?
# - Adres çubuğu “GET” gönderir; /chat ise “POST” ister. Bu yüzden tarayıcıda /chat yazınca olmaz.
# - “docs” sayfasındaki “Try it out” butonu, POST isteğini senin yerine doğru şekilde gönderir.
#
# Hızlı kontrol adresleri:
#   - Sağlık:  http://127.0.0.1:8000/health  →  {"ok": True} görmelisin
#   - Doküman: http://127.0.0.1:8000/docs    →  hazır test ekranı
#
# Sık karşılaşılan durumlar (kısa çözümler):
#   - 405 (Method Not Allowed): /chat’i tarayıcıda açtın (GET). Çözüm: /docs’tan “Execute” ile gönder veya yukarıdaki komutu kullan (POST).
#   - 404 (Not Found): Yanlış yer. Sohbet için /chat, test ekranı için /docs, sağlık için /health.
#   - 422: name (yazı), age (sayı), gender (yazı), message (yazı) alanlarını eksiksiz doldur.
#   - 500 veya model hatası: .env’de GOOGLE_API_KEY yok/yanlış olabilir. .env’yi düzelt → terminali kapat-aç → sunucuyu yeniden başlat.
#   - “Port 8000 meşgul”: Sunucuyu kapat (Ctrl+C). Gerekirse:
#       netstat -ano | findstr :8000
#       Stop-Process -Id <PID> -Force
#
# ÖZETLERSEK:
#   - asistan_api:app  → “sunucu”
#   - /chat            → “soru gönderdiğin kapı” (POST ister)
#   - /docs            → “soru göndermeyi kolaylaştıran ekran (Try it out)”