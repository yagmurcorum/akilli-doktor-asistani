# 🩺 Akıllı Doktor Asistanı (Gemini)
Bu proje, sağlıkla ilgili genel sorulara kibar ve yaşa duyarlı yanıtlar veren bir sohbet asistanıdır. İki çalışma biçimi: Terminalden sohbet ve FastAPI ile REST API.

## 1) Problem Tanımı
- Kullanıcı sağlık soruları sorar; asistan yaşa duyarlı, nazik ve güvenli cevaplar üretir.
- Konuşma hafızası sayesinde önceki mesajlar unutulmaz.
- Önce terminalde hızlı dene; sonra API ile dış dünyaya aç.

## 2) Öğrenme Hedefleri
- Gemini 2.x ile LLM kullanımı ve parametre seçimi
- LangChain ile hafıza (ConversationBufferMemory) ve zincir
- FastAPI + Uvicorn ile REST API
- .env ile gizli anahtar yönetimi, requests ile istemci

## 3) Teknolojiler
- FastAPI + Uvicorn
- LangChain
- Gemini (langchain-google-genai, google-generativeai): 2.5-flash (hız/fiyat), 2.5-pro (muhakeme)
- python-dotenv
- requests  
Neden Gemini 2.x? Uzun bağlam penceresi, güncel hız/kalite profilleri.

## 4) Dosya Yapısı
akilli-doktor-asistani/
- asistan_terminal.py  (Terminal sohbet)
- asistan_api.py       (FastAPI sunucusu)
- asistan_istemci.py   (Terminalden API’ye sohbet)
- requirements.txt     
- .env                 (API anahtarı – paylaşmayın)
- README.md            (bu dosya)

## 5) Kurulum (VS Code + PowerShell)
1) cd "<proje_klasörü_yolu>"  
2) python -m venv venv  →  .\venv\Scripts\Activate.ps1  
3) Paketler:
- pip install fastapi==0.120.1 uvicorn==0.38.0 python-dotenv==1.2.1 requests==2.32.5
- pip install "langchain==0.3.27" "langchain-core==0.3.79" "langchain-community==0.3.30"
- pip install "langchain-google-genai==2.0.10" "google-generativeai==0.8.5"  
4) .env
- GOOGLE_API_KEY=BURAYA_GEMINI_API_KEY  
- LLM_MODEL=gemini-2.5-flash  (istersen gemini-2.5-pro)

## 6) Nasıl Çalıştırılır?
A) Terminal sohbeti: python asistan_terminal.py  
B) API: uvicorn asistan_api:app --reload  
- Test ekranı: http://127.0.0.1:8000/docs  
- Sağlık: http://127.0.0.1:8000/health  
C) İstemci (opsiyonel): python asistan_istemci.py  
- API_URL: http://127.0.0.1:8000/chat

## 6.1) API’yi test etme — Try it out (en kolay yol)
- Adım 1: Sunucuyu başlat  
  .\venv\Scripts\Activate.ps1 → uvicorn asistan_api:app --reload  
  (Ekranda: “Uvicorn running on http://127.0.0.1:8000”)
- Adım 2: Tarayıcıda test ekranını aç  
  http://127.0.0.1:8000/docs
- Adım 3: /chat kutusuna gel → “Try it out” butonuna bas
  - name: Yagmur
  - age: 24
  - message: Başım ağrıyor…
  - “Execute” de
- Adım 4: Aşağıdaki “Responses” bölümünde sonucu gör  
  Code 200 ve Response body içinde {"response": "..."} yer alır.
- Not: /chat adresi POST ister. Adres çubuğu GET gönderdiğinden /chat’i doğrudan açarsan 405 (Method Not Allowed) görmen normaldir.

## 6.2) API’yi test etme — Terminal istemcisi (alternatif)
- Neden? Tarayıcıdaki forma gerek kalmadan, komut satırından gerçek bir istemci gibi test etmek için.
- Çalıştır: python asistan_istemci.py  
  - Ad ve yaş gir, mesaj yaz, yanıt terminalde görünür (çıkış: quit).
- Tek satır PowerShell örneği (istemci yazmadan hızlı dene):
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -Body (@{ name="Yagmur"; age=24; message="Başım ağrıyor." } | ConvertTo-Json) -ContentType "application/json"

## 6.3) Sık karşılaşılan durumlar — Hızlı çözümler
- 405 Method Not Allowed: /chat’i GET ile açtın → /docs’tan “Try it out” kullan ya da yukarıdaki POST komutunu çalıştır.
- 404 Not Found: Yanlış adres → Sohbet: /chat, test ekranı: /docs, sağlık: /health.
- 422 Unprocessable Entity: name (yazı), age (sayı), message (yazı) alanlarını eksiksiz gir.
- 500 Internal Server Error: Çoğunlukla `.env`’de `GOOGLE_API_KEY` eksik/yanlış. Düzelt → terminali kapat-aç → sunucuyu yeniden başlat.
- Port 8000 meşgul: netstat -ano | findstr :8000 → Stop-Process -Id <PID> -Force.

## 7) Terminal Akışı — Ne görürsün?
- İsim/yaş alınır; “başlangıç talimatı”na eklenir.
- Yanıtlar `— Doktor Asistanı —` başlığıyla gösterilir.
- Hafıza Özeti listelenir (HUMAN/AI).
- Günlükler sade (verbose=False).

Terminal çıktısı hakkında:
- Öğretici mod: `ConversationChain(..., verbose=True)` bilerek açık; zincirin adımlarını terminalde gösterir (öğrenme amaçlı faydalıdır).
- Sade mod: Daha az çıktı istersek `verbose=False` yap. API tarafında zaten `verbose=False` önerilir; ayrıntılı kayıtlar `logging` ile tutulur.

## 8) İçeride Nasıl Çalışıyor?
1) LLM (Gemini) sohbet motorudur: yazarsın, yanıtlar.  
2) ConversationBufferMemory, önceki mesajları saklar; model tutarlı devam eder.  
3) Terminal = tek süreç/tek hafıza; API = kullanıcıya özel hafıza.  
4) Parametreler: model=gemini-2.5-flash/pro; temperature=0.3–0.7.  
Sistem talimatı: Basit kullanımda kullanıcı mesajı gibi eklenir; daha doğru yaklaşım “system” rolü (LangChain SystemMessage) olarak vermektir.

## 9) Güvenlik
- `.env`’yi paylaşma; sızarsa anahtarı iptal et, yenisini üret.
- Tıbbi teşhis/ilaç önerisi yok; acil durumda 112.

## 10) Sorun Giderme
Sürüm uyumsuzluğu:
- pip uninstall -y langchain-google-genai langchain-core langchain  
- pip install "langchain==0.3.27" "langchain-core==0.3.79" "langchain-community==0.3.30"  
- pip install "langchain-google-genai==2.0.10" "google-generativeai==0.8.5"  
Model 404:
- llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)  
- Gerekirse api_version="v1" ile dene  
Modelleri listele:
- import os, google.generativeai as genai  
- genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  
- for m in genai.list_models(): print(m.name)  
Port meşgul:
- Ctrl+C → netstat -ano | findstr :8000 → Stop-Process -Id <PID> -Force  
Yanlış venv:
- deactivate → .\venv\Scripts\Activate.ps1

## 11) Geliştirme Planı
- Hafızayı SQLite/SQLAlchemy ile kalıcı yapmak
- `user_id` ile hafıza eşlemesi
- Basit web arayüzü (React + SSE)
- Güvenli yanıt şablonları (acil durum uyarısı, teşhis vermez)

## 12) Teknik Notlar (Rapor)
- `/chat` sadece POST kabul eder; test için /docs (Try it out) ya da POST komutu kullan.
- Sunucu: `uvicorn asistan_api:app --reload`
- Sağlık: `http://127.0.0.1:8000/health`
- Doküman: `http://127.0.0.1:8000/docs`
- `.env` zorunlu: `GOOGLE_API_KEY=...`
- Model: `gemini-2.5-flash` başlangıç; `gemini-2.5-pro` muhakeme; 404’de listeyi kontrol et, gerekirse `api_version="v1"`.
- Hafıza: kullanıcı başına `ConversationBufferMemory`; ilk turda sistem talimatı.
- Loglama: `logging`; root `/` için basit karşılama, `/favicon.ico` 404 normaldir.

Hazırlayan: Yağmur Çorum — Model: Google Gemini 2.x (LangChain + FastAPI) — Amaç: Yapay zekâ destekli sağlık danışma asistanı prototipi