"""
Doktor Asistanı API (Gemini 2.x + LangChain + FastAPI)

FastAPI ile HTTP tabanlı sohbet servisi.
İstemciler POST /chat ile mesaj gönderir, LLM yanıtı JSON olarak döner.
Detaylı kullanım için README.md dosyasına bakın.
"""

import os
import uuid
import logging
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_core.messages import SystemMessage

# Loglama: Üretimde ne olduğunu takip edebilmek için sade format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("doctor-assistant-api")


# Ortam değişkenleri: API anahtarları, model ve CORS ayarları

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY bulunamadı. .env dosyanızı kontrol edin.")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# CORS whitelist: Production'da yalnızca güvenilir istemcilere izin ver
# Örn: ALLOWED_ORIGINS="https://*.streamlit.app,https://*.streamlit.io,http://localhost:8501"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://*.streamlit.app,https://*.streamlit.io,http://localhost:8501",
    ).split(",")
    if o.strip()
]

# Hafıza limiti: RAM şişmesin, sadece son N mesajı tut (system mesajı korunur)
MAX_MEMORY_MESSAGES = int(os.getenv("MEMORY_MAX_MESSAGES", "20"))


# FastAPI uygulaması
app = FastAPI(
    title="Doktor Asistanı API",
    version="1.1.0",
    description="Gemini 2.x tabanlı, kişiselleştirilmiş ve hafızalı sohbet API'si",
)

# CORS: Sadece belirlenen origin'lerden gelen web isteklerine izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# LLM (Gemini) istemcisi
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    temperature=0.7,
    api_key=GOOGLE_API_KEY,
)


# Kullanıcı bazlı konuşma hafızası: her kullanıcı/oturum için ayrı
user_to_memory: Dict[str, ConversationBufferMemory] = {}

# İstek/Yanıt modelleri
class ChatRequest(BaseModel):
    """İstemci istek gövdesi"""
    name: str           # Kullanıcı adı (hafıza anahtarı için)
    age: int            # Yaş (1-120 aralığında)
    gender: str         # Cinsiyet (female/male/other)
    message: str        # Kullanıcı mesajı
    session_id: Optional[str] = None  # Çoklu oturum için opsiyonel (istemci üretirse benzersiz olmalı)

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
        """Cinsiyet metnini normalize eder (female/male/other)"""
        normalized = v.strip().lower()
        if normalized in {"kadın", "kadin", "female", "f"}:
            return "female"
        if normalized in {"erkek", "male", "m"}:
            return "male"
        return "other"

class ChatResponse(BaseModel):
    """Model yanıtı"""
    response: str


# Sistem talimatı: modelin rolünü/tonunu/sınırlarını belirler
def build_system_instruction(name: str, age: int, gender: str) -> str:
    """
    Cinsiyet ve yaşa göre kişiselleştirilmiş sistem talimatı oluşturur.
    - Hitap tonu cinsiyete göre değişir
    - Yaş ve cinsiyete özel sağlık önerileri eklenir
    - Cinsiyete özel risk faktörleri vurgulanır
    """
    # Cinsiyete göre hitap ve ton
    if gender == "female":
        hitap_tonu = "Sayın" if age >= 18 else "Sevgili"
        hitap_ozel = "Kadın sağlığı konularında (adet döngüsü, hamilelik, menopoz, meme sağlığı vb.) özel dikkat göster. "
        risk_faktoru = "Kadınlarda özellikle dikkat edilmesi gereken konular: meme kanseri taraması, rahim ağzı kanseri, kemik sağlığı (osteoporoz), tiroid sorunları. "
        hitap_stili = "nazik, empatik ve anlayışlı"
    elif gender == "male":
        hitap_tonu = "Sayın" if age >= 18 else "Sevgili"
        hitap_ozel = "Erkek sağlığı konularında (prostat sağlığı, testosteron seviyeleri, kalp sağlığı vb.) özel dikkat göster. "
        risk_faktoru = "Erkeklerde özellikle dikkat edilmesi gereken konular: prostat sağlığı, kalp-damar hastalıkları, testis kanseri, karaciğer sağlığı. "
        hitap_stili = "nazik, empatik ve doğrudan"
    else:  # other
        hitap_tonu = "Sayın" if age >= 18 else "Sevgili"
        hitap_ozel = "Sağlık konularında kapsayıcı ve hassas bir yaklaşım benimse. "
        risk_faktoru = "Genel sağlık taramaları ve önleyici bakım konularında bilgilendir. "
        hitap_stili = "kapsayıcı, empatik ve saygılı"

    # Yaş grubuna göre ek yönlendirme
    if age < 18:
        yas_notu = "Genç/çocuk sağlığı konularında yaş grubuna uygun, anlaşılır dil kullan. "
        yas_ozel = "Büyüme-gelişme, aşı takvimi, ergenlik dönemi sağlığı gibi konularda bilgilendir. "
    elif age >= 50:
        yas_notu = "Orta-ileri yaş grubuna özel sağlık konularını (kronik hastalıklar, taramalar, yaşam tarzı) vurgula. "
        yas_ozel = "Düzenli sağlık kontrolleri, kanser taramaları, kalp sağlığı, diyabet riski gibi konularda öneriler sun. "
    else:
        yas_notu = "Genç erişkin sağlığı konularında (yaşam tarzı, önleyici bakım, mental sağlık) odaklan. "
        yas_ozel = "Sağlıklı yaşam alışkanlıkları, düzenli egzersiz, beslenme, stres yönetimi konularında rehberlik et. "

    return (
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
        f"Sınırlar: "
        f"- Kesin tanı/ilaç/tedavi yazma; riskli veya acil belirtilerde profesyonel yardıma yönlendir. "
        f"- Tıbbi jargondan kaçın, anlaşılır dil kullan. "
        f"- {name}'in yaşı ({age}) ve cinsiyet ({gender}) bilgisini cevaplarında dikkate al. "
        f"\n\n"
        f"Sunum: "
        f"- Kısa paragraflar; gerektiğinde madde işaretleri. "
        f"- {name} ismini gerektiğinde kullan; sakin ve empatik bir ton benimse; paniğe sevk etme. "
        f"- Gerektiğinde kullanıcıya sorularla netleştirme yap; belirsizliği dürüstçe belirt. "
        f"\n\n"
        f"Acil uyarılar: Hayati risk içeren belirtilerde (göğüs ağrısı, nefes darlığı, bilinç kaybı, şiddetli kanama vb.) "
        f"hemen 112'yi veya en yakın acil servise gitmesini öner. "
        f"\n\n"
        f"Cinsiyet ve yaş özel bilgiler: "
        f"{name} için cinsiyet ({gender}) ve yaş ({age}) bilgisini kullanarak "
        f"uygun sağlık önerileri, risk faktörleri ve dikkat edilmesi gereken konuları belirt."
    )


# Yardımcı endpoint'ler
@app.get("/")
def root():
    """Ana sayfa: kısa yönlendirme mesajı"""
    return {
        "status": "ok",
        "message": "Doktor Asistanı API. Belgeler için /docs, sağlık kontrolü için /health, sohbet için /chat",
    }

@app.get("/health")
def health():
    """Sağlık kontrolü: otomasyon/izleme için basit yanıt"""
    return {"ok": True}


# Hafıza budama: Sistem mesajını koruyarak toplam mesaj sayısını sınırla
def trim_memory(memory: ConversationBufferMemory) -> None:
    msgs = memory.chat_memory.messages
    if len(msgs) > MAX_MEMORY_MESSAGES:
        if getattr(msgs[0], "type", "") == "system":
            system_part = msgs[0:1]
            rest = msgs[1:]
            memory.chat_memory.messages = system_part + rest[-(MAX_MEMORY_MESSAGES - 1):]
        else:
            memory.chat_memory.messages = msgs[-MAX_MEMORY_MESSAGES:]


# Ana endpoint: POST /chat
@app.post("/chat", response_model=ChatResponse)
async def chat_with_doctor(req: ChatRequest) -> ChatResponse:
    """
    Kullanıcı mesajını alır, LLM ile yanıt üretir ve döner.

    Akış:
    1) Kullanıcı+session hafızasını getir/yoksa oluştur
    2) İlk mesajda sistem talimatını (cinsiyet/yaş özel) hafızaya ekle
    3) Mesaj + hafıza → LLM; yanıt üret
    4) Yanıtı döndür ve hafızayı sınırla
    """
    try:
        # Hafıza anahtarı: name + session_id; yoksa UUID ile çakışmayı önle
        base_key = req.name.strip().lower()
        sess = (req.session_id or "").strip()
        if not sess:
            sess = uuid.uuid4().hex[:8]  # kısa ve yeterince benzersiz
        user_session_key = f"{base_key}:{sess}"

        if user_session_key not in user_to_memory:
            user_to_memory[user_session_key] = ConversationBufferMemory(return_messages=True)
        memory = user_to_memory[user_session_key]

        # İlk mesajda sistem talimatını ekle (kişiselleştirilmiş kurallar)
        if len(memory.chat_memory.messages) == 0:
            sys_msg = build_system_instruction(req.name, req.age, req.gender)
            memory.chat_memory.add_message(SystemMessage(content=sys_msg))

        # LLM + hafıza ile sohbet
        conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
        reply = conversation.predict(input=req.message)

        # Hafızayı sınırla (RAM ve maliyet kontrolü), sistem mesajını koru
        trim_memory(memory)

        # Sade log: kişisel içerik yok, sadece meta bilgiler
        logger.info(
            "chat user=%s age=%s gender=%s session=%s model=%s",
            req.name, req.age, req.gender, sess, LLM_MODEL
        )

        return ChatResponse(response=reply)
    except Exception as exc:
        logger.exception("chat failed: %s", exc)
        raise HTTPException(status_code=500, detail="Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.")