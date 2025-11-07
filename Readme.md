# 🩺 Akıllı Doktor Asistanı (Gemini 2.5 + LangChain + FastAPI + Streamlit)

**Akıllı Doktor Asistanı**, yaş ve cinsiyete göre kişiselleştirilmiş, hafızalı ve empatik bir sağlık danışmanıdır.  
Üç farklı şekilde kullanılabilir:

- 🖥️ **Terminal** (doğrudan LLM ile sohbet)  
- 🌐 **FastAPI REST API**  
- 💻 **Streamlit Web Arayüzü** (modern, çoklu sohbet destekli)

> ⚠️ Sistem yalnızca bilgilendirme amaçlıdır. Tıbbi tanı veya tedavi sunmaz; acil durumlarda 112 aranmalıdır.

---

## 🎯 Amaç

Kullanıcı, sağlıkla ilgili sorularını doğal dilde sorar.  
Asistan, kullanıcının **adı**, **yaşı** ve **cinsiyetine** göre yanıtları kişiselleştirir.  
Konuşma hafızası sayesinde önceki mesajlar korunur, yanıtlar bağlamdan kopmaz.  
Cinsiyet ve yaş gruplarına özel öneriler içerir.

---

## ⚙️ Temel Özellikler

- **Kişiselleştirme:** Cinsiyet ve yaş grubuna özel SystemMessage kullanımı  
- **Hafıza Yönetimi:** `ConversationBufferMemory` ile sistem mesajı korunarak budama (`MEMORY_MAX_MESSAGES`)  
- **Çoklu Oturum:** Her sohbetin bağımsız `session_id`’si vardır  
- **Modern Web UI:** Streamlit ile çoklu sohbet, hızlı başlat çipleri, mobil uyumlu tasarım  
- **Güvenlik:** `.env` yönetimi, CORS beyaz listesi (`ALLOWED_ORIGINS`), XSS koruması, hata maskeleme  
- **Sürekli Çalışırlık:** `keep_alive.yml` GitHub Action dosyası API’nin uykuda kalmasını önler  
- **Otomatik Dağıtım:** Render ve Streamlit Cloud arasında CI/CD bağlantısı

---

## 🧩 Teknik Mimari

```text
Kullanıcı / UI (Streamlit)
        │
        ▼
FastAPI (/chat) ─► LangChain ConversationChain ─► Gemini 2.5 (Flash)
        │                     ▲
        │                     │
        └──► ConversationBufferMemory (user + session_id)
```

**Akış:**
1. Kullanıcı, `/chat` endpoint’ine `name`, `age`, `gender`, `message`, `session_id` gönderir  
2. Backend hafızayı oluşturur, SystemMessage ekler  
3. LangChain modeli (Gemini 2.5) çağrılır  
4. Yanıt hafızaya kaydedilir ve istemciye döner  

---

## 📁 Dosya Yapısı

```text
akilli-doktor-asistani/
├── asistan_api.py                # FastAPI backend (ana API)
├── asistan_terminal.py           # Doğrudan LLM ile terminal sohbeti
├── asistan_istemci.py            # API istemcisi (terminal)
├── streamlit_ui.py               # Streamlit web arayüzü
├── requirements.txt              # Bağımlılıklar
├── runtime.txt                   # Render için Python sürümü (3.11.9)
├── .env.example                  # Ortam değişkeni şablonu
├── .github/
│   └── workflows/
│       └── keep_alive.yml        # API’nin uykuda kalmaması için otomatik ping işlemi
└── README.md
```

---

## ⚙️ Ortam Değişkenleri (.env)

```env
# Akıllı Doktor Asistanı - Örnek Ortam Değişkenleri

GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE

LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
# Alternatif: gemini-2.5-pro (daha güçlü muhakeme)

MEMORY_MAX_MESSAGES=20
DEBUG=false

# Geliştirme ortamı ve yayın adresleri
ALLOWED_ORIGINS=http://localhost:8501,https://akilli-doktor-asistani.streamlit.app

# Backend API adresi
# Lokal geliştirme:
API_URL=http://127.0.0.1:8000/chat
# Yayın sonrası:
# API_URL=https://akilli-doktor-asistani-buef.onrender.com/chat
```

> `.env` dosyasını repoya yükleme.  
> `.gitignore` içinde `.env`, `venv/`, `__pycache__/`, `.streamlit/` mutlaka yer almalıdır.

---

## 🚀 Kurulum ve Çalıştırma (Lokal)

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

**Test adresleri:**
- FastAPI: http://127.0.0.1:8000/docs  
- Streamlit: http://localhost:8501  

---

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

---

## ☁️ Deploy Mimarisi

| Katman                | Platform        | Açıklama                                                  |
|------------------------|-----------------|-----------------------------------------------------------|
| **Backend (FastAPI)**  | **Render**       | Model isteklerini işler, `/chat` endpoint’ini barındırır. |
| **Frontend (Streamlit)** | **Streamlit Cloud** | Kullanıcı arayüzü, API’ye istek atar.                |

---

### 🔹 Backend (Render)

- **Build Command:**  
  `pip install -r requirements.txt`

- **Start Command:**  
  `uvicorn asistan_api:app --host 0.0.0.0 --port $PORT`

- **Ek dosya:** `runtime.txt`  
  (Render’da Python 3.11.9 kullanılmasını sağlar)

- **Environment Variables:**
  ```
  GOOGLE_API_KEY=<senin_api_keyin>
  ALLOWED_ORIGINS=http://localhost:8501,https://akilli-doktor-asistani.streamlit.app
  LLM_MODEL=gemini-2.5-flash
  MEMORY_MAX_MESSAGES=20
  ```

---

### 🔹 Frontend (Streamlit Cloud)

- **Main file:** `streamlit_ui.py`  
- **Linked repo:** `yagmurcorum/akilli-doktor-asistani`  
- **API_URL:** `https://akilli-doktor-asistani-buef.onrender.com/chat`  
- **Deploy URL:** [https://akilli-doktor-asistani.streamlit.app](https://akilli-doktor-asistani.streamlit.app)

---

## 🔁 CI/CD Süreci

- GitHub repo → Render bağlantılıdır  
- `main` branch’e yapılan her `git push`, Render üzerinde otomatik yeni deploy tetikler  
- `.github/workflows/keep_alive.yml`, Render API’sini düzenli aralıklarla ping atarak aktif tutar  

---

## 🛡️ Güvenlik ve Sınırlamalar

- `.env` dosyası **asla repoya yüklenmemelidir.** Gizli API anahtarları yalnızca yerelde veya güvenli ortam değişkenleri üzerinden tanımlanmalıdır.

- `ALLOWED_ORIGINS` değişkeni ile **CORS politikası** uygulanmaktadır.  
  Bu ayar sayesinde yalnızca `localhost` ve `https://akilli-doktor-asistani.streamlit.app` gibi güvenilir domainlerden gelen istekler kabul edilir.  
  Böylece dış kaynaklı (örneğin kötü niyetli sitelerin) API’ye erişimi engellenir.

- FastAPI bu kontrolü aşağıdaki **CORS middleware** üzerinden gerçekleştirir:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=allowed_origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
Bu yapı her gelen istekte `Origin` başlığını kontrol eder ve yalnızca izinli domainlerden gelen talepleri kabul eder.  
İzinli olmayan domainlerden gelen çağrılar tarayıcı tarafından otomatik olarak engellenir.

`DEBUG=false` olmalıdır.  
Production ortamında `DEBUG=true` bırakmak, loglarda hassas veri sızıntısına yol açabilir.

Yanıtlar yalnızca **bilgilendirme amaçlıdır**.  
Sistem herhangi bir şekilde **tıbbi tanı veya tedavi önerisi** sunmaz; acil durumlarda **112** aranmalıdır.

---

## 🔬 Geliştirme Süreci ve Öğrenilenler

Bu proje, bir yapay zekâ modelinin yalnızca çalışmasını değil, aynı zamanda **üretim ortamına taşınmasını** hedefleyen kapsamlı bir öğrenme sürecinin ürünü oldu.

### 🧱 1. Mimari Tasarım
Proje ilk olarak basit bir terminal sohbeti olarak başladı, ardından **FastAPI** ile API katmanı eklendi ve son olarak **Streamlit** ile kullanıcı arayüzü oluşturularak üç katmanlı bir mimariye dönüştü.  
Bu yapı, yapay zekâ modellerinin yalnızca geliştirilmesi değil, aynı zamanda uçtan uca **erişilebilir servis** hâline getirilmesini sağladı.

### ⚙️ 2. Model Seçimi ve Optimizasyon
Gemini 2.5 ailesinden **`gemini-2.5-flash`**, maliyet-verimlilik dengesi ve yanıt hızı nedeniyle tercih edildi.  
`gemini-2.5-pro` modeli ise derin muhakeme ve tıbbi bilgi yoğunluğu gerektiren senaryolar için alternatif olarak test edildi.  
Model çağrıları **LangChain ConversationChain** üzerinden yönetilerek bağlamsal tutarlılık sağlandı.

### 🧠 3. Hafıza Yönetimi
LangChain’in `ConversationBufferMemory` bileşeni, önceki kullanıcı mesajlarını saklayarak çok adımlı diyalogları mümkün kıldı.  
Ancak modelin bellek tüketimini dengelemek için `MEMORY_MAX_MESSAGES` parametresi eklendi.  
Bu sayede sistem uzun konuşmalarda bile **bağlamı koruyarak optimize edilmiş** yanıtlar üretti.

### 🌐 4. API ve CORS Güvenliği
FastAPI ile oluşturulan `/chat` endpoint’i, Streamlit arayüzünden güvenli çağrılar alabilmesi için **CORS (Cross-Origin Resource Sharing)** yapılandırmasıyla korundu.  
`.env` dosyasında `ALLOWED_ORIGINS` değeri tanımlanarak yalnızca `localhost` ve Streamlit Cloud domainlerinden gelen istekler kabul edildi.  
Bu, temel ama kritik bir güvenlik katmanı oluşturdu.

### 💻 5. Modern Web Arayüzü (Streamlit)
Arayüzde kullanıcı deneyimi ön planda tutuldu:
- **Çoklu sohbet** desteği  
- **Yaş ve cinsiyete göre kişiselleştirme**  
- **Hızlı başlat çipleri**  
- **Responsive, gradient tabanlı tasarım**  
- **Gerçek zamanlı renkli balonlar**  

Ayrıca, `render_bubble_text()` fonksiyonu sayesinde modelin ürettiği Markdown veya HTML biçimli çıktılar güvenli şekilde render edildi.  
XSS (cross-site scripting) riskini önlemek için tüm metinler `html.escape()` ile temizlendi.

### 🚀 6. Dağıtım (Deploy) Süreci
- **Backend:** Render platformunda barındırıldı (`https://akilli-doktor-asistani-buef.onrender.com`)  
- **Frontend:** Streamlit Cloud üzerinde yayınlandı (`https://akilli-doktor-asistani.streamlit.app`)  
- **runtime.txt:** Render’da doğru Python sürümünü (3.11.9) garanti altına aldı  
- **keep_alive.yml:** GitHub Actions workflow’u, Render API’sini periyodik olarak ping’leyerek uyku moduna geçmesini engelledi  

Bu yapı sayesinde proje **tam otomatik CI/CD hattına** kavuştu:  
`main` branch’e her push sonrası Render kendini otomatik yeniden deploy ediyor.

### 🧩 7. Karşılaşılan Sorunlar ve Çözümler
- Render’ın “sleep” moduna geçmesi → keep-alive workflow ile çözüldü  
- CORS hataları → `.env` beyaz listesiyle giderildi  
- Streamlit’te `\n` format bozulması → `replace("\\n", "<br>")` ile düzeltildi  
- Timeout ve yavaş yanıt problemleri → `requests.post(..., timeout=90)` eklendi  

### 📈 8. Öğrenilenler
Bu proje sürecinde yalnızca “bir model çalıştırmak” değil, aynı zamanda:
- **Yapay zekâ servis mimarisi**  
- **CI/CD otomasyonu**  
- **CORS güvenliği**  
- **LangChain hafıza yönetimi**  
- **Kullanıcı deneyimi odaklı UI geliştirme**  
konularında uçtan uca bir deneyim kazanıldı.

---

## 🧩 Sonuç

“Akıllı Doktor Asistanı”, büyük dil modellerinin yalnızca metin üreten sistemler değil, **erişilebilir ve sürdürülebilir yapay zekâ servislerine dönüşebileceğini** gösteren bir örnektir.  
Matematik, yazılım mühendisliği ve yapay zekâ prensiplerinin birleştiği bu proje, gelecekteki tıbbi danışmanlık sistemleri için sağlam bir temel sunmaktadır.

> 💡 *Bu proje, araştırma amaçlıdır. Gerçek tıbbi teşhis ve tedavi için profesyonel hekim desteği gereklidir.*

---

## 👩‍💻 Geliştiren

**Yağmur Çorum**  
> Gemini 2.5 + LangChain ile kişiselleştirilmiş yapay zekâ asistanı geliştirme projesi

**Teknolojiler:** FastAPI · LangChain · Streamlit · Google Gemini  
**Amaç:** Kişiye özel, güvenli ve anlamlı sağlık danışma deneyimi oluşturmak
