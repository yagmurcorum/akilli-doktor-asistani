# 🩺 Akıllı Doktor Asistanı (Gemini 2.5 + LangChain + FastAPI + Streamlit)

**Akıllı Doktor Asistanı**, yaş ve cinsiyete göre kişiselleştirilmiş, hafızalı ve empatik bir sağlık danışmanıdır.  
Üç farklı şekilde kullanılabilir:

- 🖥️ **Terminal** (doğrudan LLM ile sohbet)  
- 🌐 **FastAPI REST API**  
- 💻 **Streamlit Web Arayüzü** (modern, çoklu sohbet destekli)

> ⚠️ Sistem yalnızca bilgilendirme amaçlıdır. Tıbbi tanı veya tedavi sunmaz; acil durumlarda 112 aranmalıdır.


## 🎯 Amaç

Kullanıcı, sağlıkla ilgili sorularını doğal dilde sorar.  
Asistan, kullanıcının adı, yaşı ve cinsiyetine göre yanıtları kişiselleştirir.  
Konuşma hafızası sayesinde önceki mesajlar korunur, yanıtlar bağlamdan kopmaz.  
Cinsiyet ve yaş gruplarına özel öneriler içerir.


## ⚙️ Temel Özellikler

- **Kişiselleştirme:** Cinsiyet ve yaş grubuna özel SystemMessage ile farklı sağlık odakları.  
- **Hafıza Yönetimi:** LangChain `ConversationBufferMemory`; sistem mesajı korunarak budama (`MEMORY_MAX_MESSAGES`).  
- **Çoklu Oturum:** Her sohbetin bağımsız `session_id`’si vardır.  
- **Modern Web UI:** Streamlit ile çoklu sohbet, hızlı başlat çipleri, mobil uyumlu tasarım.  
- **Güvenlik:** `.env` yönetimi, CORS beyaz listesi (`ALLOWED_ORIGINS`), XSS koruması, hata maskeleme.


## 🧩 Teknik Mimari

```text
Kullanıcı / UI
    │
    ▼
FastAPI (/chat)  ──► LangChain ConversationChain ──► Gemini 2.5
    │                        ▲
    │                        │
    └───► ConversationBufferMemory (user + session_id)
```

**Akış:**

1. İstemci, FastAPI `/chat` endpoint’ine `name`, `age`, `gender`, `message`, `session_id` gönderir.
2. Backend, hafıza oluşturur veya yükler, SystemMessage ekler.
3. LangChain ConversationChain modeli (Gemini 2.5 Flash) çağrılır.
4. Yanıt hafızaya kaydedilir, gerekirse budanır.


## 📁 Dosya Yapısı

```text
akilli-doktor-asistani/
├── asistan_api.py          # FastAPI backend (ana API)
├── asistan_terminal.py     # Doğrudan LLM ile terminal sohbeti
├── asistan_istemci.py      # API istemcisi (terminal)
├── streamlit_ui.py         # Streamlit web arayüzü
├── requirements.txt        # Bağımlılıklar
├── .env.example            # Örnek ortam değişkenleri
└── README.md
```


## ⚙️ Ortam Değişkenleri (.env)

```env
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
LLM_MODEL=gemini-2.5-flash
MEMORY_MAX_MESSAGES=20
DEBUG=false
ALLOWED_ORIGINS=http://localhost:8501,https://akilli-doktor-asistani.streamlit.app
API_URL=http://127.0.0.1:8000/chat
```

> `.env` dosyasını repoya yükleme.
> `.gitignore` içinde `.env`, `venv/`, `__pycache__/`, `.streamlit/` yer almalı.



## 🚀 Kurulum ve Çalıştırma

```bash
# 1. Ortam oluştur
python -m venv venv
.\venv\Scripts\activate  # veya source venv/bin/activate

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. FastAPI başlat
uvicorn asistan_api:app --reload

# 4. Web UI başlat
streamlit run streamlit_ui.py
```

**Test:**

* FastAPI: http://127.0.0.1:8000/docs
* Streamlit: http://localhost:8501



## 🔗 API Özeti

### POST `/chat`

**İstek:**

```json
{
  "name": "Yagmur",
  "age": 24,
  "gender": "female",
  "message": "Başım ağrıyor; ne yapmalıyım?",
  "session_id": "chat123"
}
```

**Yanıt:**

```json
{ "response": "Sayın Yagmur, baş ağrısı için..." }
```


## ☁️ Deploy

### 🔹 Backend (FastAPI) – Render

* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn asistan_api:app --host 0.0.0.0 --port $PORT`
* **Environment Variables:**
  `GOOGLE_API_KEY`, `LLM_MODEL`, `ALLOWED_ORIGINS`, `MEMORY_MAX_MESSAGES`

### 🔹 Web UI (Streamlit Cloud)

* **Main file:** `streamlit_ui.py`
* **API_URL:** `https://akilli-doktor-asistani.onrender.com/chat`


## 🛡️ Güvenlik ve Sınırlamalar

* `.env` dosyasını paylaşma.
* CORS ayarlarını yalnızca güvenilir domainlerle sınırla.
* Yanıtlar yalnızca bilgilendirme amaçlıdır, tıbbi teşhis değildir.


## 🧠 Gelecek Planı

* [ ] SQLite/SQLAlchemy ile kalıcı hafıza
* [ ] Çoklu dil desteği (TR/EN)
* [ ] Sesli asistan ve geri bildirim modülü
* [ ] Gelişmiş istatistik/log analizi


## 👩‍💻 Geliştiren

**Yağmur Çorum**

> Gemini 2.5 + LangChain ile kişiselleştirilmiş yapay zekâ asistanı geliştirme projesi

**Teknolojiler:** FastAPI · LangChain · Streamlit · Google Gemini
**Amaç:** Kişiye özel, güvenli ve anlamlı sağlık danışma deneyimi oluşturmak