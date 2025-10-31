"""
streamlit_ui.py — Modern Akıllı Doktor Asistanı Web Arayüzü

════════════════════════════════════════════════════════════════════════════════
GENEL BAKIŞ
════════════════════════════════════════════════════════════════════════════════
Bu uygulama, kullanıcının sağlık sorularını hızlıca yapay zekaya sorabilmesi
amacıyla tasarlanmıştır. Hem modern hem profesyonel bir kullanıcı deneyimi sunar.
Streamlit ile geliştirilmiştir.

TEMEL ÖZELLİKLER
────────────────────────────────────────────
• Çoklu sohbet desteği (her sohbet bağımsız hafıza)
• Yaşa ve isme göre kişiselleştirilmiş yanıtlar
• Modern/Mobil uyumlu kullanıcı arayüzü (responsive design)
• Gerçek zamanlı mesajlaşma ve renkli balonlar
• Zengin yardım paneli ve sorun giderici öneriler
• FastAPI backend entegrasyonu ve CORS desteği

KURULUM · ÇALIŞTIRMA · YAYINLAMA
────────────────────────────────────────────
pip install streamlit requests
streamlit run streamlit_ui.py
—
Streamlit Cloud, Deta, Heroku vb. platformlarda kolayca çalışır.
API_URL ortam değişkeniyle backend adresi dışardan ayarlanabilir.
════════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import uuid
import time
import html
import requests
import streamlit as st

# ════════════════════════════════════════════════════════════════════════════
# 📡 BACKEND BAĞLANTISI / API URL
# ════════════════════════════════════════════════════════════════════════════
API_URL = os.getenv("API_URL", "https://akilli-doktor-api.onrender.com/chat")

# ════════════════════════════════════════════════════════════════════════════
# 🎨 TASARIM SİSTEMİ VE STİLLER
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Akıllı Doktor Asistanı",
    page_icon="🩺",
    layout="wide"
)
st.markdown(
    """
    <style>
      /* Google Fonts - Daha modern font */
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      
      html, body, [data-testid="stApp"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f1f8 100%) !important;
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #1a1a1a;
      }

      /* Üst header - Premium görünüm */
      .topbar {
        position: sticky; top: 0; z-index: 999;
        background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
        border-bottom: 1px solid rgba(0, 157, 220, 0.15);
        box-shadow: 0 4px 24px rgba(0, 102, 255, 0.08);
        backdrop-filter: blur(10px);
      }
      .topbar-inner { 
        max-width:1320px; 
        margin:0 auto; 
        padding:20px 28px; 
        display:flex; 
        flex-direction:column; 
        align-items:flex-start; 
        gap:6px;
      }
      .brand { 
        font-size: 30px; 
        font-weight: 800; 
        background: linear-gradient(120deg, #0066FF 0%, #00ADEF 50%, #00D4FF 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        background-clip:text;
        letter-spacing: -0.5px;
      }
      .brand-tagline { 
        color:#5a6c7d; 
        font-size:15.5px; 
        font-weight:500;
        letter-spacing: 0.2px;
      }

      /* Ana düzen - Premium kartlar */
      .layout { max-width: 1320px; margin:30px auto 24px; padding:0 16px;}
      .card { 
        background: linear-gradient(135deg, #ffffff 0%, #fefeff 100%);
        border-radius:24px; 
        box-shadow: 0 8px 32px rgba(0, 102, 255, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
        border:1px solid rgba(0, 157, 220, 0.12);
        transition: all 0.3s ease;
      }
      .card:hover {
        box-shadow: 0 12px 48px rgba(0, 102, 255, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06);
      }
      .sidebar-card { padding:24px 18px; }
      .chat-card { padding:28px 32px; display:flex; flex-direction:column; }

      /* Sohbet balonu yapısı - Daha şık */
      .chat-scroll { 
        flex: 1; 
        overflow-y:auto; 
        padding-right:12px; 
        margin:0; 
        scrollbar-width: thin;
        scrollbar-color: #009DDC #f0f0f0;
      }
      .chat-scroll::-webkit-scrollbar { width: 6px; }
      .chat-scroll::-webkit-scrollbar-track { background: #f0f0f0; border-radius: 10px; }
      .chat-scroll::-webkit-scrollbar-thumb { background: #009DDC; border-radius: 10px; }
      
      .row    { display:flex; margin:16px 0; animation: fadeIn 0.4s ease; }
      @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      
      .left   { justify-content:flex-start; }
      .right  { justify-content:flex-end; }
      .bubble { 
        max-width:75%; 
        padding:16px 20px; 
        border-radius:20px; 
        line-height:1.6; 
        font-size:15.5px; 
        box-shadow:0 4px 16px rgba(0, 102, 255, 0.12);
        transition: transform 0.2s ease;
        word-wrap: break-word; white-space: normal;
      }
      .bubble:hover { transform: translateY(-2px); }
      
      .user   { 
        background: linear-gradient(135deg, #0066FF 0%, #00ADEF 100%); 
        color: #fff; 
        font-weight:600;
        border-bottom-right-radius: 4px;
      }
      .bot    { 
        background: linear-gradient(135deg, #FFD93D 0%, #FFC107 100%); 
        color:#1a1a1a; 
        font-weight:600;
        border-bottom-left-radius: 4px;
      }
      .stamp  { opacity:.65; font-size:11.5px; margin-left:10px; font-style:normal; font-weight:500; }

      /* Sohbet listesi - Modern kartlar */
      .session-btn{ 
        width:100%; 
        text-align:left; 
        border:2px solid rgba(0, 157, 220, 0.15); 
        background:#ffffff;
        padding:14px 18px; 
        border-radius:16px; 
        margin-bottom:12px; 
        cursor:pointer; 
        font-size:15px; 
        font-weight:600;
        transition: all .25s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
      }
      .session-btn:hover { 
        border-color:#009DDC; 
        background:linear-gradient(135deg, #e6f7ff 0%, #f0fbff 100%);
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 157, 220, 0.15);
      }
      .session-btn.active { 
        border-color:#009DDC; 
        background:linear-gradient(135deg, #e6f7ff 0%, #f0fbff 100%);
        box-shadow: 0 4px 16px rgba(0, 157, 220, 0.2);
      }
      
      /* Streamlit butonları - Premium stil */
      .stButton > button {
        border-radius:12px !important;
        font-weight:600 !important;
        transition: all .25s ease !important;
        font-size: 15px !important;
        padding: 12px 20px !important;
        border: 2px solid transparent !important;
        background: linear-gradient(135deg, #0066FF 0%, #00ADEF 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.25) !important;
      }
      .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 102, 255, 0.35) !important;
      }
      
      /* Text input - Premium stil */
      .stTextInput > div > div > input {
        border-radius:12px !important; 
        border:2px solid rgba(0, 157, 220, 0.2) !important; 
        transition: all .25s ease !important;
      }
      .stTextInput > div > div > input:focus {
        border-color:#009DDC !important; 
        box-shadow: 0 0 0 4px rgba(0, 157, 220, 0.15) !important;
        background: #fafbff !important;
      }

      /* Chat input - Premium görünüm */
      .stChatInput {
        border-top: 2px solid rgba(0, 157, 220, 0.1);
        padding-top: 20px;
        margin-top: 20px;
      }
      .stChatInput > div {
        border-radius: 16px !important;
        border: 2px solid rgba(0, 157, 220, 0.2) !important;
        box-shadow: 0 4px 16px rgba(0, 102, 255, 0.08) !important;
        background: #ffffff !important;
      }
      .stChatInput > div:focus-within {
        border-color: #009DDC !important;
        box-shadow: 0 4px 24px rgba(0, 157, 220, 0.2) !important;
      }

      /* Hızlı çipler paneli - Premium butonlar (Görsel iyileştirme) */
      .chips {
        display:grid;
        grid-template-columns:repeat(4,1fr);
        gap:14px;
        margin-top:24px;
        margin-bottom:16px;
      }
      @media (max-width:950px){ .chips{grid-template-columns:repeat(3,1fr);} }
      @media (max-width:700px){ .chips{grid-template-columns:repeat(2,1fr);} }

      .chipbtn {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        gap:8px;
        padding:14px 16px;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        color:#025a96;
        border-radius:16px;
        font-size:15px;
        font-weight:800;
        cursor:pointer;
        transition: all .25s ease;
        border:2px solid rgba(2, 90, 150, 0.18);
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.12);
        letter-spacing: .2px;
      }
      .chipbtn:hover {
        background: linear-gradient(135deg, #0066FF 0%, #00ADEF 100%);
        color:white;
        border-color:#0066FF;
        transform: translateY(-2px);
        box-shadow: 0 10px 26px rgba(0, 102, 255, 0.28);
      }
      
      /* Başlıklar, caption, divider */
      h3 { font-weight: 700 !important; color: #1e293b !important; letter-spacing: -0.3px !important; }
      .stCaption { color: #64748b !important; font-weight: 500 !important; letter-spacing: 0.3px !important; }
      hr { border-color: rgba(0, 157, 220, 0.15) !important; margin: 24px 0 !important; }
    </style>
    <div class="topbar">
      <div class="topbar-inner">
        <div class="brand">🩺 Akıllı Doktor Asistanı</div>
        <div class="brand-tagline">Danışman yapay zeka ile sağlık sorularınıza akıllı yanıt</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ════════════════════════════════════════════════════════════════════════════
# 🧩 METİN GÜVENLİ/GENİŞLETİLMİŞ GÖSTERİM YARDIMCISI
# ════════════════════════════════════════════════════════════════════════════
def render_bubble_text(text: str) -> str:
    """
    Balonlarda metni güvenli ve düzgün satır sonlarıyla göstermek için:
      1) HTML'yi kaçır (XSS/bozulma önler)
      2) \n kaçışlarını <br> ile görünür yeni satıra çevir
    """
    safe = html.escape(text or "")
    return safe.replace("\n", "<br>")

# ════════════════════════════════════════════════════════════════════════════
# 🗂️ SOHBET DURUMU — Çoklu Oturum Hafızası
# ════════════════════════════════════════════════════════════════════════════
if "chats" not in st.session_state:   # Tüm kayıtlı sohbetler: { chat_id: [ (rol,mesaj,zaman), ... ] }
    st.session_state.chats = {}
if "titles" not in st.session_state:  # Sohbet başlıkları: { chat_id: başlık }
    st.session_state.titles = {}
if "current_chat_id" not in st.session_state:
    cid = uuid.uuid4().hex[:8]
    st.session_state.current_chat_id = cid
    st.session_state.chats[cid] = []
    st.session_state.titles[cid] = "Yeni sohbet"

def active_history():
    """Aktif sohbetin geçmişi"""
    return st.session_state.chats[st.session_state.current_chat_id]

def append_message(role, text):
    """İlgili tipte mesajı aktifte sona ekle"""
    active_history().append((role, text, time.time()))

def send_and_append(message_text: str):
    """
    Kullanıcı mesajını ekrana ve API'ye gönderir, asistan yanıtını balon olarak getirir.
    Adımlar:
      1) Giriş kontrolleri
      2) Kullanıcı mesajını hemen ekranda göster
      3) API'ye POST et
      4) Yanıta göre ekle/hata
    """
    user_name = st.session_state.get("name_input", "").strip()
    age_txt   = st.session_state.get("age_input", "").strip()
    gender    = st.session_state.get("gender_input", "Seçiniz")

    # Giriş doğrulama (tek mesajda görünür olsun diye birleştirildi)
    missing = []
    if not user_name:
        missing.append("Ad")
    if not age_txt or not age_txt.isdigit():
        missing.append("Yaş (sayı)")
    if gender == "Seçiniz":
        missing.append("Cinsiyet")
    if missing:
        st.error("Lütfen şu alanları doldurun: " + ", ".join(missing))
        return

    append_message("Kullanıcı", message_text.strip())

    try:
        payload = {
            "name": user_name,
            "age": int(age_txt),
            "gender": gender,               # (Backend kullanmasa da ileriye dönük)
            "message": message_text.strip(),
            "session_id": st.session_state.current_chat_id,
        }
        with st.spinner("Yanıt hazırlanıyor..."):
            resp = requests.post(API_URL, json=payload, timeout=60)
        if resp.status_code == 200:
            reply = resp.json().get("response", "")
            append_message("Asistan", reply)
        else:
            st.error(f"Sunucu hatası [{resp.status_code}]: {resp.text}")
    except requests.RequestException as exc:
        st.error(f"Bağlantı hatası: {exc}")

# ════════════════════════════════════════════════════════════════════════════
# 📐 SAYFA DÜZENİ — Sol: Sohbetler/Profil · Orta: Chat (chat üstte, butonlar altta)
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="layout">', unsafe_allow_html=True)
col_side, col_chat = st.columns([0.92, 3.08])

# ════════════════════════════════════════════════════════════════════════════
# SOL PANEL — Sohbetler ve Kullanıcı Bilgileri
# ════════════════════════════════════════════════════════════════════════════
with col_side:
    st.markdown('<div class="card sidebar-card">', unsafe_allow_html=True)
    st.subheader("💬 Sohbetler")
    for cid in list(st.session_state.chats.keys()):
        title = st.session_state.titles.get(cid, f"Sohbet {cid}")
        is_active = (cid == st.session_state.current_chat_id)
        if st.button(title, key=f"sbtn_{cid}", use_container_width=True):
            st.session_state.current_chat_id = cid
            st.rerun()
        st.markdown(f"<div class='session-btn{' active' if is_active else ''}'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Yeni", use_container_width=True):
            nid = uuid.uuid4().hex[:8]
            st.session_state.chats[nid] = []
            st.session_state.titles[nid] = "Yeni sohbet"
            st.session_state.current_chat_id = nid
            st.rerun()
    with c2:
        if st.button("🗑️ Sil", use_container_width=True):
            if len(st.session_state.chats) > 1:
                del st.session_state.titles[st.session_state.current_chat_id]
                del st.session_state.chats[st.session_state.current_chat_id]
                st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                st.rerun()
    st.divider()
    st.subheader("👤 Kullanıcı Bilgileri")
    st.text_input("Ad",  key="name_input", placeholder="Adınızı yazın...", autocomplete="off")
    st.text_input("Yaş", key="age_input",  placeholder="Örn: 24",        autocomplete="off")
    st.selectbox(
        "Cinsiyet",
        options=["Seçiniz", "Kadın", "Erkek", "Diğer"],
        index=0,
        key="gender_input",
        help="Kişiselleştirme için gereklidir."
    )
    st.caption("Ad, yaş ve cinsiyet bilgisi, asistan cevaplarını kişiselleştirmek için kullanılır.")
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# ORTA PANEL — Chat Arayüzü
# ════════════════════════════════════════════════════════════════════════════
with col_chat:
    st.markdown('<div class="card chat-card">', unsafe_allow_html=True)

    # (1) Sohbet geçmişi
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    for role, text, ts in active_history():
        ts_str = time.strftime("%H:%M", time.localtime(ts))
        side  = "right" if role == "Kullanıcı" else "left"
        klass = "user" if role == "Kullanıcı" else "bot"
        safe_text = render_bubble_text(text)
        st.markdown(
            f"""
            <div class="row {side}">
              <div class="bubble {klass}">
                <b>{role}</b><span class="stamp">· {ts_str}</span><br>
                {safe_text}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # (2) Mesaj girişi (Enter = Gönder) — Zorunlu alan kontrolleri send_and_append içinde
    user_msg = st.chat_input("Sağlık sorunuz / belirtinizi yazın ve Enter'a basın…")
    if user_msg:
        send_and_append(user_msg)
        st.rerun()

    # (3) Hızlı başlat çipleri — Görsel olarak iyileştirildi
    st.caption("⚡ Hızlı başlat (örnek rahatsızlıklar)")
    st.markdown('<div class="chips">', unsafe_allow_html=True)
    chip_data = [
        ("🤕 Baş ağrısı",       "Başım ağrıyor; ne yapmalıyım?"),
        ("🌡️ Ateş",             "Ateşim var; evde neler yapabilirim?"),
        ("🤢 Mide bulantısı",   "Mide bulantım var; önerin nedir?"),
        ("😖 Boğaz ağrısı",     "Boğazım ağrıyor; nasıl rahatlarım?"),
        ("😷 Öksürük",          "Öksürüyorum; ne önerirsin?"),
        ("💪 Kas ağrısı",       "Kas ağrılarım var; nasıl hafifletebilirim?"),
        ("🥱 Yorgunluk",        "Sürekli yorgun hissediyorum; önerin?"),
        ("😴 Uyku problemi",    "Uyuyamıyorum; tavsiyen ne?"),
        ("🤒 Karın ağrısı",     "Karın ağrım var; doktora gitmeli miyim?"),
        ("🦴 Bel ağrısı",       "Belim ağrıyor; neler iyi gelir?"),
        ("🤧 Alerji",           "Alerji belirtilerim var; evde ne yapabilirim?"),
        ("🤧 Soğuk algınlığı",  "Soğuk algınlığı yaşıyorum; nasıl toparlanırım?"),
    ]
    chipcols = st.columns(4)
    for i, (label, msg) in enumerate(chip_data):
        if chipcols[i % 4].button(label, key=f"chip_{i}", help=f'"{label}" için hızlı soru'):
            send_and_append(msg)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # layout END

# ════════════════════════════════════════════════════════════════════════════
# ALT BİLGİ
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div style="text-align: center; margin:28px 0 8px 0; opacity:.65; font-size:13.5px; font-weight:500; color:#64748b;">
      🩺 Akıllı Doktor Asistanı · v1.0 | Bilgi amaçlıdır, tanı ve tedavi için hekiminize başvurunuz.
    </div>
    """,
    unsafe_allow_html=True
)