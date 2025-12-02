import streamlit as st
import requests
import json
import os
import time
import random
from datetime import datetime, timedelta
import pandas as pd

# --- 1. AYARLAR VE SABİTLER ---
st.set_page_config(page_title="GeziStory", page_icon="🧿", layout="wide")

# GÜVENLİK PROTOKOLÜ: API Anahtarları Secrets'tan çekiliyor
try:
    FIREBASE_API_KEY = st.secrets["general"]["FIREBASE_API_KEY"]
    PROJECT_ID = st.secrets["general"]["PROJECT_ID"]
    IMGBB_API_KEY = st.secrets["general"]["IMGBB_API_KEY"]
except Exception as e:
    st.error("🚨 KRİTİK HATA: API Anahtarları bulunamadı! Lütfen .streamlit/secrets.toml dosyasını oluşturduğunuzdan emin olun.")
    st.stop()

MAP_BANNER_URL = "https://i.ibb.co/KpKykTMf/Gemini-Generated-mage-4zpeqj4zp.png"
SHOPIER_LINK_REKLAM = "https://www.shopier.com/ShowProductNew/products.php?id=TEMSILI_REKLAM_LINK"
SHOPIER_LINK_BAGIS = "https://www.shopier.com/ShowProductNew/products.php?id=TEMSILI_BAGIS_LINK"
SHOPIER_LINK_KURUMSAL = "https://www.shopier.com/ShowProductNew/products.php?id=KURUMSAL_SPONSOR_LINK"
PLACEHOLDER_AD_IMG = "https://i.ibb.co/wNdhcmw/reklam-ver.png"

# STANDART 81 İL LİSTESİ
ALL_PROVINCES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
    "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli",
    "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane",
    "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli",
    "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat",
    "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman",
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"
]

# --- LEZZET İSTİHBARAT DOSYASI (GASTRO-INTEL) ---
CITY_GASTRO_GUIDE = {
    "Adana": {"yemek": "Adana Kebap, Şalgam, Bıcı Bıcı, Muzlu Süt", "butce": "Uygun-Orta", "tuyo": "Kebabın yanında gelen salatalara para verme, onlar ikramdır! Şalgamı acılı iç."},
    "Gaziantep": {"yemek": "Beyran, Katmer, Ali Nazik, Yuvalama, Baklava", "butce": "Orta-Yüksek", "tuyo": "Beyran sabah kahvaltısında içilir. Katmeri Zekeriya Usta'da ye."},
    "Hatay": {"yemek": "Tepsi Kebabı, Künefe, Humus, Belen Tava", "butce": "Uygun", "tuyo": "Künefeyi yemekten hemen sonra sıcak sıcak göm. Peyniri sünmüyorsa iade et."},
    "İstanbul": {"yemek": "Sultanahmet Köftesi, Balık Ekmek (Eminönü), Islak Hamburger", "butce": "Değişken", "tuyo": "Turistik yerlerde (Sultanahmet vb.) fiyatları menüden kontrol etmeden oturma."},
    "İzmir": {"yemek": "Boyoz, Kumru, Söğüş, İzmir Bombası", "butce": "Orta", "tuyo": "Boyozu haşlanmış yumurta ile ye. Çiğdem'e çekirdek deme, garipserler."},
    "Trabzon": {"yemek": "Kuymak (Muhlama), Akçaabat Köfte, Hamsiköy Sütlacı", "butce": "Orta", "tuyo": "Kuymak çatalla değil, ekmek banarak yenir. Sütlaç yerinde (Hamsiköy) güzeldir."},
    "Kayseri": {"yemek": "Mantı, Pastırma, Sucuk Ekmek, Yağlama", "butce": "Orta", "tuyo": "Bir kaşığa 40 tane mantı sığmıyorsa o Kayseri mantısı değildir (şaka şaka, lezzetine bak)."},
    "Bursa": {"yemek": "İskender Kebap, Pideli Köfte, Kestane Şekeri", "butce": "Yüksek", "tuyo": "Gerçek İskender için mavi dükkanı bul. Pideli köfte öğrenci dostudur."},
    "Mardin": {"yemek": "Kaburga Dolması, Sembusek, Mırra", "butce": "Orta-Yüksek", "tuyo": "Mırra (acı kahve) içtikten sonra fincanı yere koyma, koyarsan fincanı dolduranla evlenmek zorunda kalırsın (efsaneye göre)."},
    "Şanlıurfa": {"yemek": "Ciğer Kebabı, Lahmacun, Şıllık Tatlısı", "butce": "Uygun", "tuyo": "Ciğeri sabah kahvaltısında ye. Urfa'da acıdan kaçış yok, zevk almaya bak."},
    "Erzurum": {"yemek": "Cağ Kebabı, Kadayıf Dolması", "butce": "Orta", "tuyo": "Cağ kebabı şişle gelir, 'tamam' diyene kadar getirmeye devam ederler. Dikkat et."},
    "Van": {"yemek": "Van Kahvaltısı, Otlu Peynir", "butce": "Orta", "tuyo": "Kahvaltı salonlarında çeşit çoktur, bitiremeyeceğin kadar şey isteme, israf olmasın."},
    "Mersin": {"yemek": "Tantuni, Cezerye, Kerebiç", "butce": "Uygun", "tuyo": "Tantuniye limon sıkılır. Yoğurtlu tantuni de denemelisin."},
    "Konya": {"yemek": "Etli Ekmek, Fırın Kebabı, Mevlana Şekeri", "butce": "Uygun-Orta", "tuyo": "Etli ekmek elle yenir. 'Pide' dersen kızabilirler."},
    "Antalya": {"yemek": "Piyaz (Tahinli), Şiş Köfte, Yanık Dondurma", "butce": "Orta-Yüksek", "tuyo": "Piyazı köftenin yanında mutlaka iste. Tahinli olması seni şaşırtmasın, efsanedir."}
}

# RÜTBE VE LİMİT AYARLARI
RANK_SYSTEM = {
    "caylak": {"min": 0, "limit_post": 0, "limit_comment": 5, "can_route": False, "see_gurme": True, "can_apply_sponsor": False, "label": "🐣 Çaylak", "color": "#95a5a6"},
    "gezgin": {"min": 251, "limit_post": 5, "limit_comment": 20, "can_route": False, "see_gurme": True, "can_apply_sponsor": True, "label": "🎒 Gezgin", "color": "#3498db"},
    "kultur_elcisi": {"min": 1001, "limit_post": 999, "limit_comment": 999, "can_route": True, "see_gurme": True, "can_apply_sponsor": True, "label": "🏆 Kültür Elçisi", "color": "#e67e22"},
    "evliya_celebi": {"min": 5000, "limit_post": 999, "limit_comment": 999, "can_route": True, "see_gurme": True, "can_apply_sponsor": True, "label": "👑 Evliya Çelebi", "color": "#e74c3c"},
    "admin": {"min": 0, "limit_post": 999, "limit_comment": 999, "can_route": True, "see_gurme": True, "can_apply_sponsor": True, "label": "🛡️ Yönetici", "color": "#000000"},
    "mod": {"min": 0, "limit_post": 999, "limit_comment": 999, "can_route": True, "see_gurme": True, "can_apply_sponsor": True, "label": "🎩 Moderatör", "color": "#8e44ad"},
    "gurme": {"min": 0, "limit_post": 999, "limit_comment": 999, "can_route": True, "see_gurme": True, "can_apply_sponsor": True, "label": "🍷 Gurme", "color": "#c0392b"}
}
RANK_HIERARCHY = ["caylak", "gezgin", "kultur_elcisi", "evliya_celebi", "gurme", "mod", "admin"]

# --- 2. HTML VE CSS ---
def get_app_css():
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&family=Pacifico&display=swap');

:root {
    --primary-color: #1E81B0;
    --secondary-color: #FFD700;
    --bg-color: #f8f9fa;
    --card-bg: #ffffff;
    --text-dark: #2c3e50;
}

html, body, [class*="css"] { font-family: 'Poppins', sans-serif; background-color: var(--bg-color); color: var(--text-dark); }

/* Logo Stili */
.main-logo { 
    font-family: 'Pacifico', cursive; 
    font-size: 48px; 
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color)); 
    -webkit-background-clip: text; 
    -webkit-text-fill-color: transparent; 
    white-space: nowrap; 
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1); 
}
.logo-emoji { font-size: 38px; -webkit-text-fill-color: initial; }

/* Hero Banner */
.hero-banner-container { width: 100%; overflow: hidden; border-radius: 15px; box-shadow: 0 8px 20px rgba(0,0,0,0.15); border: 2px solid #222; margin-top: 10px; }
.hero-banner-img { width: 100%; height: 140px; object-fit: cover; object-position: center; display: block; }

/* KART TASARIMLARI */
.discover-card { 
    border-radius: 15px; 
    overflow: hidden; 
    box-shadow: 0 6px 15px rgba(0,0,0,0.08); 
    margin-bottom: 15px; 
    background: var(--card-bg); 
    border: 1px solid #eee; 
}
.card-image-wrapper { position: relative; width: 100%; height: 220px; }
.card-img-main { width: 100%; height: 100%; object-fit: cover; }
.card-caption { padding: 15px; font-size: 13px; color: #444; line-height: 1.5; border-top: 1px solid #f5f5f5; }

/* Etiketler */
.glass-tag { position: absolute; bottom: 10px; left: 10px; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(6px); padding: 6px 12px; border-radius: 30px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); max-width: 90%; }
.mini-avatar { width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--primary-color); object-fit: cover; }
.user-info-text { font-size: 11px; font-weight: bold; color: #333 !important; line-height: 1.2; }
.location-text { font-size: 9px; color: #444 !important; font-weight: normal; }
.category-badge { position: absolute; top: 10px; right: 10px; background: rgba(30, 129, 176, 0.9); color: white; padding: 5px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; backdrop-filter: blur(4px); box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
.info-strip { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.9), rgba(0,0,0,0)); padding: 40px 10px 10px 10px; color: #f1f1f1; font-size: 11px; text-align: right; pointer-events: none; }

/* Butonlar */
.stButton button { border-radius: 8px !important; font-weight: 600 !important; }
.stButton button[kind="primary"] { background-color: var(--secondary-color) !important; color: #222 !important; border: none !important; }

/* Diğer Bileşenler */
.profile-header { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 25px; margin-bottom: 20px; border-left: 6px solid var(--primary-color); }
.profile-avatar { width: 90px; height: 90px; border-radius: 50%; border: 3px solid #eee; object-fit: cover; }
.profile-info { flex-grow: 1; }
.profile-name { font-size: 26px; font-weight: 800; color: #2c3e50 !important; margin: 0; }
.stat-box { background: #f0f4f8; padding: 8px 15px; border-radius: 8px; font-weight: bold; border: 1px solid #dde1e6; color: var(--primary-color); }
.challenge-board { background: linear-gradient(135deg, #111, #333); color: #0f0; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
.challenge-title { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
.challenge-entry-card { background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; margin-bottom: 15px; }
.challenge-img { width: 100%; height: 200px; object-fit: cover; }
.challenge-text { padding: 12px; font-size: 13px; font-style: italic; color: #555; background: #fffdf0; margin: 10px; border-radius: 0 8px 8px 0; border-left: 4px solid var(--secondary-color); }
.challenge-user { padding: 0 10px 10px 10px; font-weight: bold; font-size: 12px; color: #333; display: flex; justify-content: space-between; }
.gastro-card { background-color: #fff8e1; border-left: 5px solid #ffc107; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: #333; }
.gastro-title { font-weight: 800; font-size: 18px; color: #d35400; margin-bottom: 8px; }
.sidebar-box { background: white; border: 1px solid #eee; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.sidebar-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; border-bottom: 2px solid #FFD700; display: inline-block; padding-bottom: 2px; color: #000 !important; }
.route-card-summary { display: flex; flex-direction: column; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #eee; }
.route-cover-small { width: 100%; height: 160px; object-fit: cover; }
.route-info-box { padding: 12px; }
.route-title-small { font-size: 16px; font-weight: bold; color: #222; margin-bottom: 5px; }
.route-meta-small { font-size: 11px; color: #666; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #eee; padding-top: 8px; }
.route-badge { background: #e3f2fd; color: #1565c0; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
.timeline-container { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 10px; }
.timeline-box { background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 8px; min-width: 120px; text-align: center; }
.poll-box { background: white; padding: 20px; border-radius: 12px; margin-top: 20px; border-top: 5px solid var(--primary-color); }
.sponsor-pool-box { background: linear-gradient(135deg, #2c3e50, #4ca1af); color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
.empty-state-box { text-align: center; padding: 40px; color: #888; background: #fff; border-radius: 15px; border: 2px dashed #ddd; margin: 20px 0; }
.empty-state-icon { font-size: 60px; display: block; margin-bottom: 10px; opacity: 0.7; }
.product-link-btn { display: inline-block; background: linear-gradient(45deg, #FF8F00, #FF6F00); color: white; padding: 6px 12px; border-radius: 20px; font-size: 11px; text-decoration: none; margin-top: 8px; font-weight: bold; }
.winner-card { border: 1px solid #eee; border-radius: 10px; padding: 10px; margin-bottom: 10px; background: #fff; display: flex; align-items: center; gap: 10px; }

/* MOBİL İÇİN ÖZEL KURALLAR (RESPONSIVE) */
@media only screen and (max-width: 768px) {
    .main-logo { font-size: 32px; }
    .logo-emoji { font-size: 28px; }
    .hero-banner-img { height: 100px; }
    .card-image-wrapper { height: 180px; } /* Mobilde resimler biraz daha kısa olsun */
    .profile-header { flex-direction: column; text-align: center; padding: 15px; }
    .profile-avatar { width: 80px; height: 80px; margin-bottom: 10px; }
    .profile-info { width: 100%; }
    .stat-box { display: inline-block; margin: 3px; font-size: 11px; padding: 5px 10px; }
    .glass-tag { padding: 4px 8px; bottom: 5px; left: 5px; }
    .mini-avatar { width: 30px; height: 30px; }
    .user-info-text { font-size: 10px; }
    .location-text { font-size: 8px; }
    .challenge-text { font-size: 11px; }
}
</style>"""

def get_badge_html(role):
    data = RANK_SYSTEM.get(role, RANK_SYSTEM['caylak'])
    # RÜTBE RENGİ VE GÖRÜNÜRLÜK AYARI YAPILDI
    return f'<span style="background:{data["color"]}; color:white; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:bold; box-shadow:0 2px 4px rgba(0,0,0,0.2); text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">{data["label"]}</span>'

def render_empty_state(message, icon="🌵"):
    st.markdown(f"""
    <div class="empty-state-box">
        <span class="empty-state-icon">{icon}</span>
        <h4>{message}</h4>
    </div>
    """, unsafe_allow_html=True)

def get_announcement_html(text): 
    if not text or not text.strip(): return "" 
    return f"""<div class="system-announcement"><span>📢 <b>SİSTEM DUYURUSU:</b> {text}</span></div>"""

def calculate_time_ago(date_str):
    try:
        dt = datetime.fromisoformat(date_str[:19])
        diff = datetime.now() - dt
        if diff.days > 365: return f"{diff.days // 365} yıl önce"
        elif diff.days > 30: return f"{diff.days // 30} ay önce"
        elif diff.days > 0: return f"{diff.days} gün önce"
        elif diff.seconds > 3600: return f"{diff.seconds // 3600} saat önce"
        elif diff.seconds > 60: return f"{diff.seconds // 60} dk önce"
        else: return "Az önce"
    except: return "Eskiden"

def get_discover_card_html(story):
    avatar_url = story.get('author_avatar') or f"https://ui-avatars.com/api/?name={story['author']}&background=random&color=fff&size=64"
    cat_icons = {"Gurme": "🍽️", "Tarih": "🏛️", "Doğa": "🌲", "Mekan": "☕", "Manzara": "📸", "Genel": "🌍"}
    budget = story.get('budget', 0)
    price_label = "Bedava" if budget == 0 else f"{budget} TL"
    time_label = calculate_time_ago(story.get('date_str', str(datetime.now())))
    
    tags_html = ""
    if 'tags' in story and story['tags']:
        tags_str = " ".join([f"#{t}" for t in story['tags'][:3]])
        tags_html = f"<div style='font-size:10px; color:#1E81B0; margin-top:2px;'>{tags_str}</div>"

    product_html = ""
    if story.get('product_link'):
        product_html = f"""<a href="{story['product_link']}" target="_blank" class="product-link-btn">🎒 Ekipmanı İncele</a>"""

    info_strip_html = f"""<div class="info-strip">💸 Tahmini: {price_label} | 🕒 {time_label}</div>"""
    return f"""<div class="discover-card"><div class="card-image-wrapper"><img src="{story['img']}" class="card-img-main"><div class="category-badge">{cat_icons.get(story.get('category','Genel'),"🌍")} {story.get('category','Genel')}</div>{info_strip_html}<div class="glass-tag"><img src="{avatar_url}" class="mini-avatar"><div><div class="user-info-text">{story['author']}</div><div class="location-text">📍 {story['city']}</div></div></div></div><div class="card-caption"><b>{story['title']}:</b> {story['summary']}{tags_html}{product_html}</div></div>"""

def get_comment_html(comment): return f"""<div class="comment-box"><div class="comment-user">{comment['user']}</div><div class="comment-text">{comment['text']}</div></div>"""
def get_route_card_html(story):
    # 1. Resim Verilerini Al ve Garantile
    images = story.get('images_list', [])
    if not images: 
        if story.get('img'): images = [story.get('img')]
        else: images = ["https://via.placeholder.com/400x200"]

    # 2. Profil ve Zaman Verileri
    avatar_url = story.get('author_avatar') or f"https://ui-avatars.com/api/?name={story['author']}&background=random&color=fff&size=64"
    time_label = calculate_time_ago(story.get('date_str', str(datetime.now())))

    # 3. Resim Düzeni (Mozaik Mantığı)
    img_count = len(images)
    image_layout_html = ""

    if img_count == 1:
        # Tek Resim
        image_layout_html = f'<img src="{images[0]}" style="width:100%; height:100%; object-fit:cover; display:block;">'
    elif img_count == 2:
        # İki Resim (%50 - %50)
        image_layout_html = f"""<div style="display:flex; width:100%; height:100%;"><div style="width:50%; height:100%; border-right:1px solid white; overflow:hidden;"><img src="{images[0]}" style="width:100%; height:100%; object-fit:cover; display:block;"></div><div style="width:50%; height:100%; overflow:hidden;"><img src="{images[1]}" style="width:100%; height:100%; object-fit:cover; display:block;"></div></div>"""
    else: 
        # Mozaik (Sol Büyük, Sağ 2 Küçük)
        extra = img_count - 3
        overlay = f'<div style="position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); color:white; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:16px;">+{extra}</div>' if extra > 0 else ''
        image_layout_html = f"""<div style="display:flex; width:100%; height:100%;"><div style="width:60%; height:100%; border-right:1px solid white; overflow:hidden;"><img src="{images[0]}" style="width:100%; height:100%; object-fit:cover; display:block;"></div><div style="width:40%; height:100%; display:flex; flex-direction:column;"><div style="height:50%; width:100%; border-bottom:1px solid white; overflow:hidden;"><img src="{images[1]}" style="width:100%; height:100%; object-fit:cover; display:block;"></div><div style="height:50%; width:100%; position:relative; overflow:hidden;"><img src="{images[2]}" style="width:100%; height:100%; object-fit:cover; display:block;">{overlay}</div></div></div>"""

    # 4. HTML ÇIKTISI (Askeri Düzen - Tek Blok)
    # Kritik Nokta: {image_layout_html} yerleştirildikten hemen sonra absolute pozisyonlu glass-tag ekleniyor.
    
    return f"""<div class="discover-card" style="margin-bottom:15px;"><div class="card-image-wrapper" style="height:220px; position:relative; overflow:hidden;">{image_layout_html}<div style="position:absolute; top:10px; left:10px; background:rgba(0,0,0,0.6); color:white; padding:2px 8px; border-radius:10px; font-size:10px; z-index:10;">📸 {img_count}</div><div class="category-badge" style="z-index:10;">{story.get('category','Genel')}</div><div class="glass-tag" style="z-index:20; position:absolute; bottom:10px; left:10px;"><img src="{avatar_url}" class="mini-avatar"><div><div class="user-info-text">{story['author']}</div><div class="location-text">📍 {story['city']}</div></div></div></div><div class="card-caption"><div style="font-weight:bold; font-size:15px; margin-bottom:5px; color:#2c3e50;">{story['title']}</div><div style="font-size:12px; color:#555; line-height:1.4; max-height:40px; overflow:hidden; margin-bottom:10px;">{story['summary']}</div><div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #eee; padding-top:8px; margin-bottom:5px;"><div style="color: #d9534f; font-weight: 800; font-size: 11px;">💸 Bu rotada {story['budget']} TL harcarsın</div><div style="font-size: 10px; color: #999;">🕒 {time_label}</div></div><div style="font-size:11px; color:#1E81B0;"><b>🎒 {len(story.get('stops', []))} Duraklı Rota</b></div></div></div>"""

def get_route_summary_card_html(story):
    img_src = (story.get('images_list') or [story.get('img')] or ["https://via.placeholder.com/400x200"])[0]
    return f"""<div class="route-card-summary"><img src="{img_src}" class="route-cover-small"><div class="route-info-box"><div><div class="route-title-small">{story['title']}</div><div class="route-meta"><span>📍 {story['city']}</span><span class="route-badge">{len(story.get('stops', []))} Durak</span></div></div><div class="route-meta-small" style="margin-bottom:0; border-top:1px solid #eee; padding-top:8px;"><span>👤 {story['author']}</span><span style="font-weight:bold; color:#d9534f; font-size:10px;">💸 Tahmini Hasar: {story['budget']} TL</span></div></div></div>"""
def get_route_detail_timeline_html(stops):
    timeline_html = '<div class="timeline-container">'
    for idx, stop in enumerate(stops):
        s_icon = {"Tarih": "🏛️", "Yemek": "🍽️", "Manzara": "📸", "Kafe": "☕", "Doğa": "🌲", "Müze": "🖼️"}.get(stop.get('type', 'Gezilecek Yer'), "📍")
        timeline_html += f"""<div class="timeline-step"><div class="timeline-box"><div class="t-icon">{s_icon}</div><div class="t-name">{stop.get('place','Durak')}</div><div class="t-price">{stop.get('price',0)} TL</div></div></div>""" + ("""<div class="timeline-arrow">➝</div>""" if idx < len(stops) - 1 else "")
    return timeline_html + '</div>'
def get_profile_header_html(user_data):
    points = user_data['points']
    role = user_data['role']
    next_level_points = RANK_SYSTEM['evliya_celebi']['min'] if role == 'evliya_celebi' else (RANK_SYSTEM['kultur_elcisi']['min'] if points < 1000 else (RANK_SYSTEM['evliya_celebi']['min'] if points < 5000 else 100000))
    progress = 100 if role == 'evliya_celebi' else min(100, int((points / next_level_points) * 100))
    avatar_src = user_data.get('avatar') or f"https://ui-avatars.com/api/?name={user_data['nick']}&background=random&color=fff&size=128"
    
    followers_count = len(user_data.get('followers', []))
    following_count = len(user_data.get('following', []))
    
    return f"""<div class="profile-header"><img src="{avatar_src}" class="profile-avatar"><div class="profile-info"><div class="profile-name">{user_data['nick']} {get_badge_html(user_data['role'])}</div><div class="profile-stats"><div class="stat-box">💰 {user_data.get('balance', 0)} TL</div><div class="stat-box">⭐ {points} Puan</div><div class="stat-box">👥 {followers_count} Takipçi</div><div class="stat-box">👣 {following_count} Takip</div></div><div style="margin-top:10px;"><div style="font-size:10px; color:#666; margin-bottom:2px;">Seviye İlerlemesi: %{progress}</div><div style="width:100%; background:#eee; height:8px; border-radius:4px;"><div style="width:{progress}%; background:linear-gradient(90deg, #1E81B0, #3498db); height:100%; border-radius:4px;"></div></div></div></div></div>"""

# --- 3. BACKEND SERVİSİ ---
class FirebaseService:
    def __init__(self):
        self.auth_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        self.db_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
        self.commit_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:commit?key={FIREBASE_API_KEY}"

    def _log_error(self, operation, error):
        print(f"⚠️ [HATA RAPORU - {operation}]: {error}")
        return None

    def sign_in_anonymously(self):
        try: 
            return requests.post(f"{self.auth_url}:signUp?key={FIREBASE_API_KEY}", json={"returnSecureToken": True}).json()
        except Exception as e: return self._log_error("Anonim Giriş", e)

    def sign_up(self, email, password, nick):
        try:
            r = requests.post(f"{self.auth_url}:signUp?key={FIREBASE_API_KEY}", json={"email": email, "password": password, "returnSecureToken": True})
            if r.status_code != 200:
                err_msg = r.json().get('error', {}).get('message', 'Bilinmeyen Hata')
                return False, f"Kayıt Hatası: {err_msg}"
            
            if 'idToken' in r.json():
                requests.patch(f"{self.db_url}/users/{r.json()['localId']}?key={FIREBASE_API_KEY}", json={"fields": {"nickname": {"stringValue": nick}, "email": {"stringValue": email}, "role": {"stringValue": "caylak"}, "wallet_balance": {"integerValue": 0}, "earnings": {"integerValue": 0}, "points": {"integerValue": 0}, "visited_cities": {"arrayValue": {"values": []}}, "saved_routes": {"arrayValue": {"values": []}}, "followers": {"arrayValue": {"values": []}}, "following": {"arrayValue": {"values": []}}}})
                return True, "Kayıt Başarılı!"
            return False, "Token alınamadı."
        except Exception as e: 
            self._log_error("Kayıt Olma", e)
            return False, "Sunucu bağlantı hatası."

    def sign_in(self, email, password):
        try: 
            r = requests.post(f"{self.auth_url}:signInWithPassword?key={FIREBASE_API_KEY}", json={"email": email, "password": password, "returnSecureToken": True})
            if r.status_code != 200: return None
            return r.json()
        except Exception as e: return self._log_error("Giriş Yapma", e)
    
    def get_profile(self, uid):
        try:
            r = requests.get(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}")
            if r.status_code != 200:
                return {"nick": "Misafir", "balance": 0, "earnings": 0, "role": "misafir", "points": 0, "visited_cities": [], "saved_routes": [], "followers": [], "following": []}
            
            f = r.json().get('fields', {})
            return {
                "nick": f.get('nickname',{}).get('stringValue','Adsız'), 
                "balance": int(f.get('wallet_balance',{}).get('integerValue',0)), 
                "earnings": int(f.get('earnings',{}).get('integerValue',0)), 
                "points": int(f.get('points',{}).get('integerValue',0)), 
                "role": f.get('role',{}).get('stringValue','caylak'), 
                "avatar": f.get('avatar',{}).get('stringValue',''),
                "visited_cities": [x.get('stringValue') for x in f.get('visited_cities',{}).get('arrayValue',{}).get('values',[])], 
                "saved_routes": [x.get('stringValue') for x in f.get('saved_routes',{}).get('arrayValue',{}).get('values',[])],
                "followers": [x.get('stringValue') for x in f.get('followers',{}).get('arrayValue',{}).get('values',[])],
                "following": [x.get('stringValue') for x in f.get('following',{}).get('arrayValue',{}).get('values',[])]
            }
        except Exception as e: 
            self._log_error("Profil Çekme", e)
            return {"nick": "Hata", "balance": 0, "role": "caylak", "points": 0}
    
    def update_visited_cities(self, uid, cities):
        try: return requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=visited_cities", json={"fields": {"visited_cities": {"arrayValue": {"values": [{"stringValue": c} for c in cities]}}}}).status_code == 200
        except: return False
    def update_nickname(self, uid, new_nick):
        try: return requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=nickname", json={"fields": {"nickname": {"stringValue": new_nick}}}).status_code == 200
        except: return False
    def update_profile_image(self, uid, url):
        try: return requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=avatar", json={"fields": {"avatar": {"stringValue": url}}}).status_code == 200
        except: return False
    def manage_saved_route(self, uid, route_id, is_saving):
        try:
            op = "appendMissingElements" if is_saving else "removeAllFromArray"
            writes = [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}", "fieldTransforms": [{"fieldPath": "saved_routes", op: {"values": [{"stringValue": route_id}]}}]}}]
            return requests.post(self.commit_url, json={"writes": writes}).status_code == 200
        except: return False
    
    def follow_user(self, current_uid, target_uid):
        try:
            writes = [
                {"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{target_uid}", "fieldTransforms": [{"fieldPath": "followers", "appendMissingElements": {"values": [{"stringValue": current_uid}]}}]}},
                {"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{current_uid}", "fieldTransforms": [{"fieldPath": "following", "appendMissingElements": {"values": [{"stringValue": target_uid}]}}]}}
            ]
            requests.post(self.commit_url, json={"writes": writes})
            self.send_message("Sistem", target_uid, "🎉 Yeni bir takipçin var!", "GeziStory")
        except Exception as e: self._log_error("Takip Etme", e)

    def unfollow_user(self, current_uid, target_uid):
        try:
            writes = [
                {"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{target_uid}", "fieldTransforms": [{"fieldPath": "followers", "removeAllFromArray": {"values": [{"stringValue": current_uid}]}}]}},
                {"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{current_uid}", "fieldTransforms": [{"fieldPath": "following", "removeAllFromArray": {"values": [{"stringValue": target_uid}]}}]}}
            ]
            requests.post(self.commit_url, json={"writes": writes})
        except Exception as e: self._log_error("Takipten Çıkma", e)

    @st.cache_data(ttl=600)
    def get_all_users_cached(_self, limit):
        try:
            mask_query = "&mask.fieldPaths=nickname&mask.fieldPaths=email&mask.fieldPaths=role&mask.fieldPaths=wallet_balance&mask.fieldPaths=earnings&mask.fieldPaths=points&mask.fieldPaths=avatar"
            r = requests.get(f"{_self.db_url}/users?key={FIREBASE_API_KEY}&pageSize={limit}{mask_query}")
            if r.status_code != 200: return []
            
            users_list = []
            for d in r.json().get('documents',[]):
                f = d.get('fields', {})
                users_list.append({
                    "uid": d['name'].split('/')[-1], 
                    "nick": f.get('nickname',{}).get('stringValue','-'), 
                    "email": f.get('email',{}).get('stringValue','-'), 
                    "role": f.get('role',{}).get('stringValue','caylak'), 
                    "balance": int(f.get('wallet_balance',{}).get('integerValue',0)), 
                    "earnings": int(f.get('earnings',{}).get('integerValue',0)), 
                    "points": int(f.get('points',{}).get('integerValue',0)),
                    "avatar": f.get('avatar',{}).get('stringValue','')
                })
            return users_list
        except Exception as e: 
            _self._log_error("Kullanıcı Listesi", e)
            return []
    def get_all_users(self, limit=20): return self.get_all_users_cached(limit)

    def update_user_role(self, uid, new_role):
        try: 
            self.get_all_users_cached.clear()
            return requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=role", json={"fields": {"role": {"stringValue": new_role}}}).status_code == 200
        except: return False

    def delete_story(self, story_id):
        try: 
            self.get_stories_cached.clear()
            return requests.delete(f"{self.db_url}/stories/{story_id}?key={FIREBASE_API_KEY}").status_code == 200
        except: return False
    def delete_forum_post(self, post_id):
        try: 
            st.cache_data.clear() 
            return requests.delete(f"{self.db_url}/forum_posts/{post_id}?key={FIREBASE_API_KEY}").status_code == 200
        except: return False
    def update_system_announcement(self, text):
        try: return requests.patch(f"{self.db_url}/system/general?key={FIREBASE_API_KEY}", json={"fields": {"announcement": {"stringValue": text}}}).status_code == 200
        except: return False
    
    def update_sidebar_content(self, data):
        fields = {}
        if 'ann_text' in data: fields['ann_text'] = {"stringValue": data['ann_text']}
        if 'ann_img' in data: fields['ann_img'] = {"stringValue": data['ann_img']}
        if 'ad_img' in data: fields['ad_img'] = {"stringValue": data['ad_img']}
        if 'ad_link' in data: fields['ad_link'] = {"stringValue": data['ad_link']}
        if 'ad_youtube' in data: fields['ad_youtube'] = {"stringValue": data['ad_youtube']}
        mask_str = "&".join([f"updateMask.fieldPaths={k}" for k in fields.keys()])
        requests.patch(f"{self.db_url}/system/general?key={FIREBASE_API_KEY}&{mask_str}", json={"fields": fields})

    def get_sidebar_content(self):
        try:
            f = requests.get(f"{self.db_url}/system/general?key={FIREBASE_API_KEY}").json().get('fields', {})
            return {
                "ann_text": f.get('ann_text', {}).get('stringValue', ''),
                "ann_img": f.get('ann_img', {}).get('stringValue', ''),
                "ad_img": f.get('ad_img', {}).get('stringValue', ''),
                "ad_link": f.get('ad_link', {}).get('stringValue', '#'),
                "ad_youtube": f.get('ad_youtube', {}).get('stringValue', ''),
                "announcement": f.get('announcement', {}).get('stringValue', '')
            }
        except: return {}

    def get_system_announcement(self): 
        val = self.get_sidebar_content().get('announcement', '')
        return val.strip() if val else ""

    def add_story(self, data):
        try:
            self.get_stories_cached.clear()
            p = self.get_profile(data['uid'])
            avatar = p.get('avatar', '')
            
            # Etiketleri Formatla
            tags_list = [{"stringValue": t.strip()} for t in data.get('tags', []) if t.strip()]
            
            # HATA DÜZELTİLDİ: Resim Listesini Firebase Formatına Çevir
            # Python listesini (['url1', 'url2']) Firestore Array formatına dönüştürüyoruz
            images_formatted = [{"stringValue": url} for url in data.get('images_list', [])]

            product_link = data.get('product_link', '')
            
            requests.post(f"{self.db_url}/stories?key={FIREBASE_API_KEY}", json={"fields": {
                "baslik": {"stringValue": data['title']}, 
                "sehir": {"stringValue": data['city']}, 
                "yazar": {"stringValue": data['author']}, 
                "author_avatar": {"stringValue": avatar}, 
                "resim": {"stringValue": data['img']}, 
                "images_list": {"arrayValue": {"values": images_formatted}}, # DÜZELTİLEN SATIR
                "ozet": {"stringValue": data['summary']}, 
                "kategori": {"stringValue": data['category']}, 
                "butce": {"integerValue": data['budget']}, 
                "stops": {"stringValue": json.dumps(data['stops'])}, 
                "uid": {"stringValue": data['uid']}, 
                "tags": {"arrayValue": {"values": tags_list}}, 
                "product_link": {"stringValue": product_link},
                "likes": {"arrayValue": {"values": []}}, 
                "comments": {"arrayValue": {"values": []}}, 
                "view_count": {"integerValue": 0}, 
                "date": {"timestampValue": datetime.utcnow().isoformat() + "Z"}
            }})
        except Exception as e: st.error(f"Hikaye eklenirken hata oluştu: {e}")
    
    @st.cache_data(ttl=600)
    def get_stories_cached(_self):
        try:
            r = requests.get(f"{_self.db_url}/stories?key={FIREBASE_API_KEY}")
            stories = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    try:
                        f = doc.get('fields', {})
                        likes = [x.get('stringValue') for x in f.get('likes',{}).get('arrayValue',{}).get('values',[])]
                        tags = [x.get('stringValue') for x in f.get('tags',{}).get('arrayValue',{}).get('values',[])]
                        # EKSİK OLAN KISIM EKLENDİ: Resim Listesini Çekme
                        images_list = [x.get('stringValue') for x in f.get('images_list',{}).get('arrayValue',{}).get('values',[])]
                        
                        stories.append({
                            "id": doc['name'].split('/')[-1], 
                            "title": f.get('baslik',{}).get('stringValue','-'), 
                            "city": f.get('sehir',{}).get('stringValue','-'), 
                            "author": f.get('yazar',{}).get('stringValue','-'), 
                            "author_avatar": f.get('author_avatar',{}).get('stringValue',''), 
                            "img": f.get('resim',{}).get('stringValue',''), 
                            "images_list": images_list, # ARTIK LİSTE BURADA
                            "summary": f.get('ozet',{}).get('stringValue',''), 
                            "category": f.get('kategori',{}).get('stringValue','Genel'), 
                            "budget": int(f.get('butce',{}).get('integerValue',0)), 
                            "stops": json.loads(f.get('stops',{}).get('stringValue','[]')), 
                            "uid": f.get('uid',{}).get('stringValue',''), 
                            "tags": tags,
                            "product_link": f.get('product_link', {}).get('stringValue', ''),
                            "like_count": len(likes), 
                            "liked_uids": likes, 
                            "comments": [{"user": c.get('mapValue',{}).get('fields',{}).get('user',{}).get('stringValue'), "text": c.get('mapValue',{}).get('fields',{}).get('text',{}).get('stringValue')} for c in f.get('comments',{}).get('arrayValue',{}).get('values',[])], 
                            "view_count": int(f.get('view_count',{}).get('integerValue',0)), 
                            "date_str": f.get('date',{}).get('timestampValue','')
                        })
                    except: continue
            
            return sorted(stories, key=lambda x: x['date_str'], reverse=True)
            
        except Exception as e:
            _self._log_error("Hikayeleri Getir", e)
            return []
    
    def get_stories(self): return self.get_stories_cached()

    def send_message(self, from_uid, to_uid, text, sender_name):
        try:
            payload = {"fields": { "from_uid": {"stringValue": from_uid}, "to_uid": {"stringValue": to_uid}, "text": {"stringValue": text}, "sender_name": {"stringValue": sender_name}, "date": {"stringValue": str(datetime.now())[:19]} }}
            requests.post(f"{self.db_url}/messages?key={FIREBASE_API_KEY}", json=payload)
        except Exception as e: self._log_error("Mesaj Gönder", e)
    
    def get_messages(self, user_uid):
        try:
            r = requests.get(f"{self.db_url}/messages?key={FIREBASE_API_KEY}")
            msgs = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('to_uid',{}).get('stringValue') == user_uid:
                        msgs.append({ "id": doc['name'].split('/')[-1], "text": f.get('text',{}).get('stringValue',''), "sender": f.get('sender_name',{}).get('stringValue','Sistem'), "date": f.get('date',{}).get('stringValue','') })
            return sorted(msgs, key=lambda x: x['date'], reverse=True)
        except: return []

    def get_user_content(self, target_uid):
        all_stories = self.get_stories()
        user_stories = [s for s in all_stories if s['uid'] == target_uid]
        all_posts = self.get_forum_posts()
        user_posts = [p for p in all_posts if p['uid'] == target_uid]
        return user_stories, user_posts

    def get_sponsorship_pool(self):
        try:
            return int(requests.get(f"{self.db_url}/system/pool?key={FIREBASE_API_KEY}").json().get('fields',{}).get('balance',{}).get('integerValue',0))
        except: return 0
    def add_to_sponsorship_pool(self, amount):
        requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/system/pool", "fieldTransforms": [{"fieldPath": "balance", "increment": {"integerValue": str(amount)}}]}}]})
    def add_sponsor_application(self, data):
        payload = {"fields": { "nick": {"stringValue": data['nick']}, "uid": {"stringValue": data['uid']}, "reason": {"stringValue": data['reason']}, "route_plan": {"stringValue": data['route_plan']}, "status": {"stringValue": "pending"}, "date": {"stringValue": str(datetime.now())[:19]} }}
        requests.post(f"{self.db_url}/sponsor_apps?key={FIREBASE_API_KEY}", json=payload)
    def get_sponsor_applications(self):
        try:
            r = requests.get(f"{self.db_url}/sponsor_apps?key={FIREBASE_API_KEY}")
            apps = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('status',{}).get('stringValue') == 'pending':
                        apps.append({ "id": doc['name'].split('/')[-1], "nick": f.get('nick',{}).get('stringValue','-'), "uid": f.get('uid',{}).get('stringValue',''), "reason": f.get('reason',{}).get('stringValue',''), "route_plan": f.get('route_plan',{}).get('stringValue','') })
            return apps
        except: return []
    def get_past_winners(self):
        try:
            r = requests.get(f"{self.db_url}/sponsor_winners?key={FIREBASE_API_KEY}")
            winners = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    winners.append({ "nick": f.get('nick',{}).get('stringValue','-'), "route": f.get('route',{}).get('stringValue','-'), "cost": f.get('cost',{}).get('integerValue',0), "date": f.get('date',{}).get('stringValue','') })
            return winners
        except: return []
    def select_winner(self, app_id, nick, route, cost):
        requests.delete(f"{self.db_url}/sponsor_apps/{app_id}?key={FIREBASE_API_KEY}")
        requests.post(f"{self.db_url}/sponsor_winners?key={FIREBASE_API_KEY}", json={"fields": {"nick": {"stringValue": nick}, "route": {"stringValue": route}, "cost": {"integerValue": cost}, "date": {"stringValue": str(datetime.now())[:10]}}})
        requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/system/pool", "fieldTransforms": [{"fieldPath": "balance", "increment": {"integerValue": str(-cost)}}]}}]})

    def add_main_ad(self, data):
        expiry_date = (datetime.now() + timedelta(days=1)).isoformat()
        payload = {"fields": { "business_name": {"stringValue": data['business_name']}, "link": {"stringValue": data['link']}, "image": {"stringValue": data['image']}, "status": {"stringValue": "pending"}, "owner_uid": {"stringValue": data['uid']}, "date": {"stringValue": str(datetime.now())[:19]}, "expiry_date": {"stringValue": expiry_date} }}
        requests.post(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}", json=payload)

    def get_active_main_ad(self):
        try:
            r = requests.get(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}")
            now_str = datetime.now().isoformat()
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('status',{}).get('stringValue') == 'active':
                         exp = f.get('expiry_date', {}).get('stringValue', '2099-01-01')
                         if exp > now_str:
                             return {"image": f.get('image',{}).get('stringValue',''), "link": f.get('link',{}).get('stringValue','#'), "type": "user_ad"}
            return None
        except: return None

    def get_pending_main_ads(self):
        try:
            r = requests.get(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}")
            ads = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('status',{}).get('stringValue') == 'pending':
                        ads.append({ "id": doc['name'].split('/')[-1], "business_name": f.get('business_name',{}).get('stringValue','-'), "link": f.get('link',{}).get('stringValue',''), "image": f.get('image',{}).get('stringValue','') })
            return ads
        except: return []

    def approve_main_ad(self, ad_id):
        requests.patch(f"{self.db_url}/sidebar_ads/{ad_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status", json={"fields": {"status": {"stringValue": "active"}}})

    def add_gurme_offer(self, data):
        expiry_date = (datetime.now() + timedelta(days=5)).isoformat()
        payload = {"fields": { "business_name": {"stringValue": data['business_name']}, "city": {"stringValue": data['city']}, "address": {"stringValue": data['address']}, "offer_title": {"stringValue": data['offer_title']}, "discount_code": {"stringValue": data['discount_code']}, "referrer_uid": {"stringValue": data['referrer_uid']}, "referrer_nick": {"stringValue": data['referrer_nick']}, "status": {"stringValue": "pending"}, "owner_uid": {"stringValue": data['uid']}, "date": {"stringValue": str(datetime.now())[:19]}, "expiry_date": {"stringValue": expiry_date} }}
        requests.post(f"{self.db_url}/gurme_offers?key={FIREBASE_API_KEY}", json=payload)
    def get_gurme_offers(self, status="active"):
        try:
            r = requests.get(f"{self.db_url}/gurme_offers?key={FIREBASE_API_KEY}")
            offers = []
            now_str = datetime.now().isoformat()
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    s = f.get('status',{}).get('stringValue','pending')
                    exp = f.get('expiry_date', {}).get('stringValue', '2099-01-01')
                    if s == "active" and exp < now_str: continue 
                    if s == status:
                        offers.append({ "id": doc['name'].split('/')[-1], "business_name": f.get('business_name',{}).get('stringValue','-'), "city": f.get('city',{}).get('stringValue','-'), "address": f.get('address',{}).get('stringValue','-'), "offer_title": f.get('offer_title',{}).get('stringValue','-'), "discount_code": f.get('discount_code',{}).get('stringValue','****'), "referrer_uid": f.get('referrer_uid',{}).get('stringValue',''), "referrer_nick": f.get('referrer_nick',{}).get('stringValue','Yok'), "expiry_date": exp[:10] })
            return offers
        except: return []
    def approve_gurme_offer(self, offer_id, referrer_uid):
        requests.patch(f"{self.db_url}/gurme_offers/{offer_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status", json={"fields": {"status": {"stringValue": "active"}}})
        if referrer_uid: 
            # PARA EKLEME İŞLEMİ İPTAL EDİLDİ (NULL)
            # requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{referrer_uid}", "fieldTransforms": [{"fieldPath": "earnings", "increment": {"integerValue": "20"}}]}}]})
            self.send_message("Sistem", referrer_uid, "🎉 Tebrikler! Referans olduğun bir ilan onaylandı. (Ödül sistemi yapılandırılıyor...)", "GeziStory Yönetim")
        return True
    
    def add_forum_post(self, data):
        st.cache_data.clear() 
        allowed, msg = self.check_daily_limit_and_update(data['uid'], 'post')
        if not allowed: st.error(msg); return
        payload = { "fields": { 
            "kategori": {"stringValue": data['cat']}, "baslik": {"stringValue": data['title']}, "icerik": {"stringValue": data['body']}, 
            "yazar": {"stringValue": data['author']}, "uid": {"stringValue": data['uid']}, "tarih": {"stringValue": str(datetime.now())[:19]},
            "city": {"stringValue": data.get('city', '')}, "from_where": {"stringValue": data.get('from_where', '')}, "to_where": {"stringValue": data.get('to_where', '')}
        }}
        r = requests.post(f"{self.db_url}/forum_posts?key={FIREBASE_API_KEY}", json=payload)
        if r.status_code != 200: st.error(f"Hata oluştu: {r.text}")
        else: self.add_points(data['uid'], 10) # GÜNCELLENDİ: 10 Puan

    def get_forum_posts(self):
        try:
            r = requests.get(f"{self.db_url}/forum_posts?key={FIREBASE_API_KEY}")
            posts = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    likes_list = [x.get('stringValue') for x in f.get('likes',{}).get('arrayValue',{}).get('values',[])]
                    comments_list = []
                    if 'comments' in f:
                        comm_arr = f['comments'].get('arrayValue', {}).get('values', [])
                        for c in comm_arr:
                            comments_list.append({ "user": c.get('mapValue',{}).get('fields',{}).get('user',{}).get('stringValue'), "text": c.get('mapValue',{}).get('fields',{}).get('text',{}).get('stringValue') })
                    posts.append({ 
                        "id": doc['name'].split('/')[-1], "cat": f.get('kategori',{}).get('stringValue','Genel'), "title": f.get('baslik',{}).get('stringValue','-'), 
                        "body": f.get('icerik',{}).get('stringValue',''), "author": f.get('yazar',{}).get('stringValue','Anonim'), "uid": f.get('uid',{}).get('stringValue',''), 
                        "date": f.get('tarih',{}).get('stringValue','Tarih Yok'), "likes": likes_list, "comments": comments_list,
                        "city": f.get('city',{}).get('stringValue',''), "from_where": f.get('from_where',{}).get('stringValue',''), "to_where": f.get('to_where',{}).get('stringValue','')
                    })
            return posts
        except Exception as e: return []

    def update_forum_interaction(self, post_id, action, data=None):
        try:
            st.cache_data.clear() 
            if action == "like" and st.session_state.user_uid:
                op = "removeAllFromArray" if st.session_state.user_uid in data['current_likes'] else "appendMissingElements"
                requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/forum_posts/{post_id}", "fieldTransforms": [{"fieldPath": "likes", op: {"values": [{"stringValue": st.session_state.user_uid}]}}]}}]})
            elif action == "comment" and data:
                allowed, msg = self.check_daily_limit_and_update(st.session_state.user_uid, 'comment')
                if not allowed: st.error(msg); return
                new_c = {"mapValue": {"fields": {"user": {"stringValue": st.session_state.user_nick}, "text": {"stringValue": data['text']}, "date": {"stringValue": str(datetime.now())}}}}
                current = data.get('current_comments', [])
                all_c = [{"mapValue": {"fields": {"user": {"stringValue": c['user']}, "text": {"stringValue": c['text']}, "date": {"stringValue": "old"}}}} for c in current] + [new_c]
                requests.patch(f"{self.db_url}/forum_posts/{post_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=comments", json={"fields": {"comments": {"arrayValue": {"values": all_c}}}})
                self.add_points(st.session_state.user_uid, 3)
        except Exception as e: st.error(f"İşlem hatası: {e}")

    def check_daily_limit_and_update(self, uid, action_type):
        today_str = datetime.now().date().isoformat()
        try:
            user_doc = requests.get(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}").json().get('fields', {})
            last_date = user_doc.get('last_action_date', {}).get('stringValue', '')
            daily_post = int(user_doc.get('daily_post_count', {}).get('integerValue', 0))
            daily_comment = int(user_doc.get('daily_comment_count', {}).get('integerValue', 0))
            role = user_doc.get('role', {}).get('stringValue', 'caylak')
            if last_date != today_str: daily_post = 0; daily_comment = 0
            limit_post = RANK_SYSTEM.get(role, RANK_SYSTEM['caylak'])['limit_post']
            limit_comment = RANK_SYSTEM.get(role, RANK_SYSTEM['caylak'])['limit_comment']
            if action_type == 'post':
                if daily_post >= limit_post: return False, f"Günlük konu açma limitin doldu! ({daily_post}/{limit_post})"
                daily_post += 1
            elif action_type == 'comment':
                if daily_comment >= limit_comment: return False, f"Günlük yorum yapma limitin doldu! ({daily_comment}/{limit_comment})"
                daily_comment += 1
            fields = { "last_action_date": {"stringValue": today_str}, "daily_post_count": {"integerValue": daily_post}, "daily_comment_count": {"integerValue": daily_comment} }
            requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=last_action_date&updateMask.fieldPaths=daily_post_count&updateMask.fieldPaths=daily_comment_count", json={"fields": fields})
            return True, "OK"
        except: return True, "Limit Check Skipped"
    def check_and_update_rank(self, uid, current_points, current_role):
        new_role = "caylak"
        if current_points >= 5000: new_role = "evliya_celebi"
        elif current_points >= 1000: new_role = "kultur_elcisi"
        elif current_points >= 251: new_role = "gezgin"
        try:
            if RANK_HIERARCHY.index(current_role) > RANK_HIERARCHY.index(new_role): return 
        except: pass
        if new_role != current_role:
            self.update_user_role(uid, new_role)
            return new_role
        return None
    def update_interaction(self, story_id, action, current_likes=[], comment_data=None, current_comments=[]):
        try:
            self.get_stories_cached.clear() 
            if action == "view":
                requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/stories/{story_id}", "fieldTransforms": [{"fieldPath": "view_count", "increment": {"integerValue": 1}}]}}]})
            elif action == "like" and st.session_state.user_uid:
                op = "removeAllFromArray" if st.session_state.user_uid in current_likes else "appendMissingElements"
                requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/stories/{story_id}", "fieldTransforms": [{"fieldPath": "likes", op: {"values": [{"stringValue": st.session_state.user_uid}]}}]}}]})
                if op == "appendMissingElements": self.add_points(st.session_state.user_uid, 2)
            elif action == "comment" and comment_data:
                allowed, msg = self.check_daily_limit_and_update(st.session_state.user_uid, 'comment')
                if not allowed: st.error(msg); return
                new_comment = {"mapValue": {"fields": {"user": {"stringValue": comment_data['user']}, "text": {"stringValue": comment_data['text']}, "date": {"stringValue": str(datetime.now())}}}}
                all_comments = [{"mapValue": {"fields": {"user": {"stringValue": c['user']}, "text": {"stringValue": c['text']}, "date": {"stringValue": "old"}}}} for c in current_comments] + [new_comment]
                requests.patch(f"{self.db_url}/stories/{story_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=comments", json={"fields": {"comments": {"arrayValue": {"values": all_comments}}}})
                self.add_points(st.session_state.user_uid, 5) # GÜNCELLENDİ: 5 Puan
        except Exception as e: st.error(f"İşlem hatası: {e}")

    def add_points(self, uid, points):
        try:
            self.get_all_users_cached.clear()
            requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}", "fieldTransforms": [{"fieldPath": "points", "increment": {"integerValue": str(points)}}]}}]})
            if uid == st.session_state.user_uid:
                current_p = st.session_state.get('user_points', 0) + points
                st.session_state.user_points = current_p 
                new_role = self.check_and_update_rank(uid, current_p, st.session_state.user_role)
                if new_role: 
                    st.session_state.user_role = new_role
                    st.balloons()
                    st.toast(f"Tebrikler! Seviye Atladın: {RANK_SYSTEM[new_role]['label']} 🚀")
        except Exception as e: st.error(f"Puan ekleme hatası: {e}")

    # --- CHALLENGE METHODS ---
    def update_active_challenge(self, ch_id, title, desc, reward):
        try:
            payload = {"fields": { "id": {"stringValue": str(ch_id)}, "title": {"stringValue": title}, "desc": {"stringValue": desc}, "reward": {"stringValue": reward}, "active": {"booleanValue": True} }}
            requests.patch(f"{self.db_url}/challenges/active_one?key={FIREBASE_API_KEY}", json=payload)
        except Exception as e: st.error(f"Yarışma güncellenemedi: {e}")

    def get_active_challenge(self):
        try:
            r = requests.get(f"{self.db_url}/challenges/active_one?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                f = r.json().get('fields', {})
                return {
                    "id": f.get('id', {}).get('stringValue', '1'),
                    "title": f.get('title', {}).get('stringValue', 'Henüz Yarışma Yok'),
                    "desc": f.get('desc', {}).get('stringValue', 'Beklemede kalın...'),
                    "reward": f.get('reward', {}).get('stringValue', '-')
                }
            return None
        except: return None

    def add_challenge_entry(self, ch_id, data):
        try:
            self.get_challenge_entries_cached.clear()
            requests.post(f"{self.db_url}/challenge_entries?key={FIREBASE_API_KEY}", json={"fields": {
                "challenge_id": {"stringValue": str(ch_id)},
                "user": {"stringValue": data['user']},
                "text": {"stringValue": data['text']},
                "city": {"stringValue": data['city']},
                "img": {"stringValue": data['img']},
                "likes": {"arrayValue": {"values": []}}, 
                "date": {"stringValue": str(datetime.now())[:19]}
            }})
            self.add_points(st.session_state.user_uid, 20) # GÜNCELLENDİ: 20 Puan
        except Exception as e: st.error(f"Katılım hatası: {e}")

    def update_challenge_like(self, entry_id, user_uid, current_likes):
        try:
            self.get_challenge_entries_cached.clear()
            op = "removeAllFromArray" if user_uid in current_likes else "appendMissingElements"
            requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/challenge_entries/{entry_id}", "fieldTransforms": [{"fieldPath": "likes", op: {"values": [{"stringValue": user_uid}]}}]}}]})
        except: pass

    @st.cache_data(ttl=30)
    def get_challenge_entries_cached(_self, filter_id):
        try:
            r = requests.get(f"{_self.db_url}/challenge_entries?key={FIREBASE_API_KEY}")
            entries = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    entry_ch_id = f.get('challenge_id', {}).get('stringValue', '1')
                    likes = [x.get('stringValue') for x in f.get('likes',{}).get('arrayValue',{}).get('values',[])]
                    if entry_ch_id == str(filter_id):
                        entries.append({
                            "id": doc['name'].split('/')[-1],
                            "user": f.get('user',{}).get('stringValue','-'),
                            "text": f.get('text',{}).get('stringValue',''),
                            "city": f.get('city',{}).get('stringValue',''),
                            "img": f.get('img',{}).get('stringValue',''),
                            "likes": likes,
                            "like_count": len(likes),
                            "date": f.get('date',{}).get('stringValue','')
                        })
            # SIRALAMA: En çok beğeni alan en üstte
            return sorted(entries, key=lambda x: x['like_count'], reverse=True)
        except: return []
    
    def get_challenge_entries(self, filter_id): return self.get_challenge_entries_cached(filter_id)

    # --- POLL (ANKET) METHODS ---
    def create_simple_poll(self, question, options):
        fields = {"question": {"stringValue": question}, "total_votes": {"integerValue": 0}}
        for i, opt in enumerate(options):
             fields[f"opt_{i}_name"] = {"stringValue": opt}
             fields[f"opt_{i}_count"] = {"integerValue": 0}
        
        requests.patch(f"{self.db_url}/polls/simple_poll?key={FIREBASE_API_KEY}", json={"fields": fields})

    def get_simple_poll(self):
        try:
            r = requests.get(f"{self.db_url}/polls/simple_poll?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                f = r.json().get('fields', {})
                options = []
                for i in range(4): # Max 4 seçenek
                    if f.get(f"opt_{i}_name"):
                        options.append({
                            "name": f.get(f"opt_{i}_name", {}).get('stringValue'),
                            "count": int(f.get(f"opt_{i}_count", {}).get('integerValue', 0)),
                            "id": i
                        })
                return {"question": f.get('question', {}).get('stringValue'), "options": options}
            return None
        except: return None

    def vote_simple_poll(self, opt_index):
        try:
            requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/polls/simple_poll", "fieldTransforms": [{"fieldPath": f"opt_{opt_index}_count", "increment": {"integerValue": 1}}]}}]})
        except: pass


def upload_to_imgbb(file):
    try: return requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY}, files={"image": file.getvalue()}).json()["data"]["url"]
    except: return None

# --- 4. SAYFA GÖRÜNÜMLERİ ---
# GİRİŞ PENCERESİ TANIMLAMASI
if hasattr(st, "dialog"):
    @st.dialog("✨ GeziStory Giriş Kapısı")
    def entry_dialog(fb):
        t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        with t1:
            with st.form("modal_login"):
                m = st.text_input("E-posta")
                p = st.text_input("Şifre", type="password")
                if st.form_submit_button("Giriş Yap", type="secondary"): 
                    u = fb.sign_in(m, p)
                    if u and 'localId' in u:
                        profile_data = fb.get_profile(u['localId'])
                        st.session_state.update(user_token=u['idToken'], user_uid=u['localId'], user_nick=profile_data['nick'], user_balance=profile_data['balance'], user_role=profile_data['role'], user_points=profile_data['points'], user_saved_routes=profile_data['saved_routes'])
                        st.rerun() 
                    elif u is None:
                        st.error("Giriş başarısız! E-posta veya şifre hatalı olabilir.")
        with t2:
            with st.form("modal_register"):
                n = st.text_input("Kullanıcı Adı (Zorunlu)")
                mm = st.text_input("E-posta")
                pp = st.text_input("Şifre", type="password")
                if st.form_submit_button("Kayıt Ol", type="secondary"):
                    if not n: st.error("Lütfen kendinize bir kullanıcı adı belirleyin!")
                    elif not mm or not pp: st.error("E-posta ve şifre boş olamaz.")
                    else:
                        ok, msg = fb.sign_up(mm, pp, n)
                        if ok: st.success("Kayıt Başarılı! Giriş sekmesinden girebilirsin."); time.sleep(2)
                        else: st.error(msg)
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("✨ GeziStory Giriş Kapısı")
    def entry_dialog(fb):
        t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        with t1:
            with st.form("modal_login"):
                m = st.text_input("E-posta")
                p = st.text_input("Şifre", type="password")
                if st.form_submit_button("Giriş Yap", type="secondary"): 
                    u = fb.sign_in(m, p)
                    if u and 'localId' in u:
                        profile_data = fb.get_profile(u['localId'])
                        st.session_state.update(user_token=u['idToken'], user_uid=u['localId'], user_nick=profile_data['nick'], user_balance=profile_data['balance'], user_role=profile_data['role'], user_points=profile_data['points'], user_saved_routes=profile_data['saved_routes'])
                        st.rerun() 
                    elif u is None:
                        st.error("Giriş başarısız! E-posta veya şifre hatalı olabilir.")
        with t2:
            with st.form("modal_register"):
                n = st.text_input("Kullanıcı Adı (Zorunlu)")
                mm = st.text_input("E-posta")
                pp = st.text_input("Şifre", type="password")
                if st.form_submit_button("Kayıt Ol", type="secondary"):
                    if not n: st.error("Lütfen kendinize bir kullanıcı adı belirleyin!")
                    elif not mm or not pp: st.error("E-posta ve şifre boş olamaz.")
                    else:
                        ok, msg = fb.sign_up(mm, pp, n)
                        if ok: st.success("Kayıt Başarılı! Giriş sekmesinden girebilirsin."); time.sleep(2)
                        else: st.error(msg)
else:
    def entry_dialog(fb):
        st.error("Giriş penceresi açılamadı. Lütfen 'pip install streamlit --upgrade' komutunu çalıştırın.")

def check_login_and_warn():
    if not st.session_state.user_token:
        st.error("🛑 Bu işlemi yapmak için giriş yapmalısın!")
        st.toast("Yukarıdaki 'Giriş Yap / Kayıt Ol' butonunu kullanabilirsin.")
        return False
    return True

if hasattr(st, "dialog"):
    @st.dialog("📨 Mesaj Oku")
    def view_message_dialog(msg, fb):
        st.markdown(f"**Gönderen:** {msg['sender']}")
        st.caption(f"Tarih: {msg['date']}")
        st.divider()
        st.write(msg['text'])
        
        with st.expander("↩️ Yanıtla"):
            reply_text = st.text_area("Cevabınız", key=f"reply_{msg['id']}")
            if st.button("Yanıtı Gönder", key=f"send_reply_{msg['id']}"):
                if reply_text:
                    if msg.get('from_uid'):
                        fb.send_message(st.session_state.user_uid, msg['from_uid'], reply_text, st.session_state.user_nick)
                        st.success("Yanıt gönderildi!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Sistem mesajlarına yanıt verilemez.")
                else:
                    st.warning("Boş mesaj gönderilemez.")

        if st.button("Kapat"): st.rerun()
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("📨 Mesaj Oku")
    def view_message_dialog(msg, fb):
        st.markdown(f"**Gönderen:** {msg['sender']}")
        st.caption(f"Tarih: {msg['date']}")
        st.divider()
        st.write(msg['text'])
        
        with st.expander("↩️ Yanıtla"):
            reply_text = st.text_area("Cevabınız", key=f"reply_{msg['id']}")
            if st.button("Yanıtı Gönder", key=f"send_reply_{msg['id']}"):
                if reply_text:
                    if msg.get('from_uid'):
                        fb.send_message(st.session_state.user_uid, msg['from_uid'], reply_text, st.session_state.user_nick)
                        st.success("Yanıt gönderildi!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Sistem mesajlarına yanıt verilemez.")
                else:
                    st.warning("Boş mesaj gönderilemez.")
        if st.button("Kapat"): st.rerun()
else:
    def view_message_dialog(msg, fb): pass

def render_comments_content(story, fb_service):
    st.markdown(f"**{story['title']}**"); st.caption(f"✍️ {story['author']} | 📍 {story['city']}"); st.write(story['summary']); st.divider(); st.markdown("###### Yorumlar")
    if not story['comments']: st.info("Henüz yorum yok.")
    else: 
        for c in story['comments']: st.markdown(get_comment_html(c), unsafe_allow_html=True)
    st.divider()
    if st.session_state.user_token:
        with st.form(f"cf_{story['id']}", clear_on_submit=True):
            nc = st.text_input("Yorum")
            if st.form_submit_button("Gönder") and nc: fb_service.update_interaction(story['id'], "comment", comment_data={"user": st.session_state.user_nick, "text": nc}, current_comments=story['comments']); st.success("Gönderildi!"); st.rerun()

def render_route_detail_content(story, fb_service): 
    # RESİM GALERİSİ
    images = story.get('images_list', []) or ([story['img']] if story.get('img') else [])
    if images:
        st.markdown(f"**📸 Rota Fotoğrafları ({len(images)})**")
        cols = st.columns(min(len(images), 3)) # En fazla 3 sütun
        for i, img in enumerate(images):
            cols[i % 3].image(img, use_container_width=True)
    
    st.divider()
    st.markdown(f"### {story['title']}", unsafe_allow_html=True)
    st.caption(f"📍 {story['city']} | 👤 {story['author']} | 🗓️ {str(story.get('date_str', ''))[:10]}")
    
    st.info(story['summary'])
    
    st.markdown("##### 🗺️ Rota Planı ve Duraklar")
    # Duraklar burada detaylı sergileniyor
    st.markdown(get_route_detail_timeline_html(story['stops']), unsafe_allow_html=True)
    
    st.divider()
    
    # ETKİLEŞİM ALANI
    c1, c2, c3 = st.columns(3)
    # Beğeni
    if c1.button(f"{'❤️' if story.get('liked_by_me') else '🤍'} {story['like_count']} Beğeni", key=f"d_lk_{story['id']}", use_container_width=True): 
        if st.session_state.user_token: 
            fb_service.update_interaction(story['id'], "like", current_likes=story['liked_uids'])
            st.rerun()
    
    # Yorumlar (Sadece görüntüleme sayısı)
    c2.button(f"💬 {len(story['comments'])} Yorum", disabled=True, use_container_width=True)
    
    # Kaydet
    is_saved = story['id'] in st.session_state.get('user_saved_routes', [])
    if c3.button("❌ Çıkar" if is_saved else "💾 Kaydet", key=f"sv_{story['id']}", use_container_width=True):
        if st.session_state.user_token:
            fb_service.manage_saved_route(st.session_state.user_uid, story['id'], not is_saved)
            if is_saved: st.session_state.user_saved_routes.remove(story['id'])
            else: st.session_state.user_saved_routes.append(story['id'])
            st.rerun()

    # YORUMLARI LİSTELE
    st.markdown("###### 💬 Yorumlar")
    if story['comments']:
        for c in story['comments']: st.markdown(get_comment_html(c), unsafe_allow_html=True)
    else:
        st.caption("Henüz yorum yapılmamış.")
        
    # YENİ YORUM EKLEME
    if st.session_state.user_token:
        with st.form(f"comm_form_{story['id']}", clear_on_submit=True):
            txt = st.text_input("Yorum Yaz")
            if st.form_submit_button("Gönder") and txt:
                fb_service.update_interaction(story['id'], "comment", comment_data={"user": st.session_state.user_nick, "text": txt}, current_comments=story['comments'])
                st.rerun()

    # KAHVE ISMARLA BUTONU (EN ALT - GENİŞ)
    st.markdown("---")
    st.markdown('<div class="coffee-btn-container">', unsafe_allow_html=True)
    if st.session_state.user_uid != story['uid']:
        # Butonu genişletmek için use_container_width=True ve büyük stil
        if st.button(f"☕ {story['author']} kişisine Kahve Ismarla (100 TL)", type="primary", use_container_width=True, key=f"tip_big_{story['id']}"):
            if st.session_state.user_token:
                # Bakiye kontrolü ve transferi (Simüle ediyoruz, backend fonksiyonu eklenmeli)
                if st.session_state.user_balance >= 100:
                    # Burada send_tip metodu olmadığı için doğrudan puan/bakiye işlemi yapılmalı veya metod eklenmeli.
                    # Şimdilik bakiye varsa düşüyoruz, gerçek transfer için backend metoduna ihtiyaç var.
                    # Geçici olarak sadece mesaj veriyoruz:
                    st.balloons()
                    st.success(f"Harika! {story['author']} sana minnettar kalacak. (Demo: 100 TL işlem)")
                else:
                    st.error("Bakiye yetersiz! Cüzdanını kontrol et.")
            else:
                st.warning("Giriş yapmalısın.")
    else:
        st.info("Bu senin kendi rotan.")
    st.markdown('</div>', unsafe_allow_html=True)

if hasattr(st, "dialog"):
    @st.dialog("💬 Yorumlar")
    def view_comments_dialog(story, fb): render_comments_content(story, fb)
    @st.dialog("🗺️ Rota Detayları")
    def view_route_detail_dialog(story, fb): render_route_detail_content(story, fb)
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("💬 Yorumlar")
    def view_comments_dialog(story, fb): render_comments_content(story, fb)
    @st.experimental_dialog("🗺️ Rota Detayları")
    def view_route_detail_dialog(story, fb): render_route_detail_content(story, fb)
else:
    def view_comments_dialog(s,f): pass
    def view_route_detail_dialog(s,f): pass

def render_create_route_section(fb):
    user_role = st.session_state.get('user_role', 'caylak')
    min_rank_idx = RANK_HIERARCHY.index('kultur_elcisi')
    user_rank_idx = RANK_HIERARCHY.index(user_role) if user_role in RANK_HIERARCHY else 0
    
    if user_rank_idx < min_rank_idx:
        st.warning(f"🔒 Rota oluşturmak için en az **'Kültür Elçisi'** seviyesinde olmalısın. (Senin seviyen: {RANK_SYSTEM.get(user_role, {}).get('label')})")
        st.info("Puan toplayarak seviye atlayabilirsin!")
        return

    if 'new_stops' not in st.session_state: st.session_state.new_stops = []
    
    st.markdown("##### 📝 Yeni Rota Planlayıcı")
    t = st.text_input("Rota Başlığı")
    c_city, c_cat = st.columns(2)
    c = c_city.selectbox("Şehir", ["İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"])
    cat = c_cat.selectbox("Kategori", ["Tarih","Doğa","Yemek","Manzara","Müze","Kafe"])
    
    imgs = st.file_uploader("Rota Görselleri (En az 1, En fazla 5)", type=['jpg','png'], accept_multiple_files=True)
    sm = st.text_area("Rota Özeti (50 - 250 Karakter)", max_chars=250, placeholder="Rotanızı kısaca anlatın...")
    
    st.markdown("###### 📍 Duraklar (En Az 3 Durak)")
    c1, c2, c3, c4 = st.columns([2,1,1,1])
    sn = c1.text_input("Durak Adı"); stp = c2.selectbox("Tür", ["Tarih","Yemek","Manzara","Kafe","Doğa"]); sp = c3.number_input("Harcama (TL)", min_value=0, step=10)
    
    if c4.button("Ekle +", use_container_width=True):
        if sn: st.session_state.new_stops.append({"place":sn,"type":stp,"price":sp}); st.rerun()
        else: st.warning("Durak adı boş olamaz.")

    if st.session_state.new_stops:
        st.markdown(get_route_detail_timeline_html(st.session_state.new_stops), unsafe_allow_html=True)
        total_budget = sum(s['price'] for s in st.session_state.new_stops)
        st.caption(f"Toplam Durak: {len(st.session_state.new_stops)} | Toplam Bütçe: {total_budget} TL")
        if st.button("🗑️ Son Durağı Sil"): st.session_state.new_stops.pop(); st.rerun()

    st.divider()
    errors = []
    if not t: errors.append("• Başlık girilmedi.")
    if not imgs or len(imgs) < 1: errors.append("• En az 1 resim yüklemelisin.")
    if len(imgs) > 5: errors.append("• En fazla 5 resim yükleyebilirsin.")
    if len(sm) < 50: errors.append(f"• Özet çok kısa ({len(sm)}/50).")
    if len(st.session_state.new_stops) < 3: errors.append(f"• En az 3 durak eklemelisin.")

    if errors:
        for err in errors: st.error(err)
        st.button("Yayınla (Eksikleri Tamamla)", disabled=True)
    else:
        if st.button("🚀 Rotayı Yayınla", type="primary", use_container_width=True):
            img_urls = []
            with st.spinner("Resimler yükleniyor..."):
                for img_file in imgs:
                    url = upload_to_imgbb(img_file)
                    if url: img_urls.append(url)
            
            if img_urls:
                total_budget = sum(s['price'] for s in st.session_state.new_stops)
                fb.add_story({"title":t, "city":c, "img":img_urls[0], "images_list": img_urls, "summary":sm, "category":cat, "budget":total_budget, "stops":st.session_state.new_stops, "author":st.session_state.user_nick, "uid":st.session_state.user_uid, "tags": []})
                
                fb.add_points(st.session_state.user_uid, 100) # GÜNCELLENDİ: 100 Puan
                
                st.session_state.new_stops = []; st.session_state.show_create = False
                st.balloons(); st.success("Rota başarıyla yayınlandı! (+100 Puan)"); time.sleep(2); st.rerun()

def render_forum(fb):
    st.markdown("### 🗣️ Gezgin Forumu")
    
    if st.session_state.user_token:
        with st.expander("➕ Yeni Konu Başlat (+15 Puan)", expanded=False):
            cat = st.selectbox("Kategori", ["Genel", "Yol Arkadaşı", "Vize Sorunları", "Ekipman", "Şehir Dedikoduları"])
            with st.form("forum_post_form"):
                c_title = st.text_input("Başlık", placeholder="Kısa ve öz...")
                f_city = ""
                f_from = ""
                f_to = ""
                if cat == "Şehir Dedikoduları": f_city = st.selectbox("Hangi Şehir Hakkında?", ["İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"])
                elif cat == "Yol Arkadaşı": c1, c2 = st.columns(2); f_from = c1.text_input("Nereden"); f_to = c2.text_input("Nereye")
                body = st.text_area("Detaylar", placeholder="Aklına takılanları sor veya tecrübeni paylaş...", height=100)
                if st.form_submit_button("Yayınla", type="primary"):
                    if c_title and body:
                        if cat == "Yol Arkadaşı" and (not f_from or not f_to): st.warning("Lütfen nereden ve nereye gideceğinizi yazın.")
                        else:
                            with st.spinner("Yayınlanıyor..."):
                                fb.add_forum_post({ "cat": cat, "title": c_title, "body": body, "author": st.session_state.user_nick, "uid": st.session_state.user_uid, "city": f_city, "from_where": f_from, "to_where": f_to })
                                st.toast("Konu açıldı! Puan hanene +15 eklendi. 🚀"); time.sleep(1.5); st.rerun()
                    else: st.warning("Lütfen başlık ve içerik giriniz.")
    
    st.divider()
    posts = fb.get_forum_posts(); cats = ["Genel", "Yol Arkadaşı", "Vize Sorunları", "Ekipman", "Şehir Dedikoduları"]; tabs = st.tabs(cats)
    for i, cat in enumerate(cats):
        with tabs[i]:
            cat_posts = [p for p in posts if p['cat'] == cat]
            if not cat_posts: 
                render_empty_state("Bu kategoride henüz ses yok...", "📭")
            else:
                for p in cat_posts:
                    extra_info = ""
                    if p.get('city'): extra_info = f" ({p['city']})"
                    if p.get('from_where'): extra_info = f" ({p['from_where']} ➝ {p['to_where']})"
                    with st.expander(f"📌 {p['title']}{extra_info}  |  👤 {p['author']}  |  🕒 {p['date'][:10]}"):
                        c_del, c_profile = st.columns([1, 6])
                        if st.session_state.user_uid == p['uid']:
                            if c_del.button("🗑️ Sil", key=f"del_fp_{p['id']}"): fb.delete_forum_post(p['id']); st.rerun()
                        if c_profile.button(f"👤 {p['author']}'ın Profiline Bak", key=f"vp_fp_{p['id']}"):
                            st.session_state.view_target_uid = p['uid']
                            st.session_state.active_tab = "public_profile"
                            st.rerun()

                        st.markdown(f"**{p['body']}**"); st.divider()
                        c_like, c_comm_count = st.columns([1, 5])
                        is_liked = st.session_state.user_uid in p['likes'] if st.session_state.user_uid else False
                        if c_like.button(f"{'❤️' if is_liked else '🤍'} {len(p['likes'])}", key=f"f_like_{p['id']}"):
                            if st.session_state.user_token: fb.update_forum_interaction(p['id'], "like", data={'current_likes': p['likes']}); st.rerun()
                            else: st.toast("Giriş yapmalısın!")
                        c_comm_count.caption(f"💬 {len(p['comments'])} Yorum")
                        for c in p['comments']: st.markdown(f"<div style='background:#f9f9f9; padding:8px; border-radius:5px; margin-bottom:5px; font-size:13px;'><b>{c['user']}:</b> {c['text']}</div>", unsafe_allow_html=True)
                        if st.session_state.user_token:
                            with st.form(key=f"f_comm_form_{p['id']}", clear_on_submit=True):
                                new_c = st.text_input("Cevap Yaz (+3 Puan)", placeholder="Fikrini belirt...")
                                if st.form_submit_button("Gönder", type="secondary") and new_c:
                                    fb.update_forum_interaction(p['id'], "comment", data={'text': new_c, 'current_comments': p['comments']}); st.toast("Cevaplandı! +3 Puan"); time.sleep(1); st.rerun()

def render_gurme(fb):
    st.markdown("### 🎟️ Gurme Fırsatlar")
    
    # REKLAM ALANI (Yüksek Gelir)
    st.markdown('<div style="width:100%; height:90px; background:#f0f2f6; border:1px solid #ddd; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:20px;"><span style="color:#888; font-weight:bold;">📢 REKLAM ALANI (Google AdSense - 970x90)</span></div>', unsafe_allow_html=True)
    
    # KURAL: HERKES GÖREBİLİR (Kilitsiz)
    offers = fb.get_gurme_offers(status="active")
    
    if not offers: 
        render_empty_state("Henüz aktif bir fırsat yok.", "🍽️")
    
    cols = st.columns(3)
    for i, offer in enumerate(offers):
        with cols[i%3]:
            # Herkese açık olduğu için kilit yok, blur yok.
            code_display = offer['discount_code']
            
            st.markdown(f"""<div class="gurme-card"><div class="gurme-header">{offer['business_name']} | {offer['city']}</div><div class="gurme-body" style="position:relative;"><div style="font-weight:bold; font-size:16px; margin-bottom:5px;">{offer['offer_title']}</div><div style="font-size:12px; color:#555; margin-bottom:5px;">📍 {offer['address']}</div><div style="background:#eee; padding:5px; text-align:center; letter-spacing:2px; font-family:monospace;">{code_display}</div><div style="font-size:10px; color:#888; margin-top:5px; text-align:right;">Son Kullanma: {offer['expiry_date']}</div></div></div>""", unsafe_allow_html=True)
    st.divider()
    
    with st.expander("📢 İşletmenizi Ekleyin (Reklam Verin)"):
        st.info("İlanınız 5 gün boyunca yayında kalır. Fiyat: 1000 TL")
        with st.form("gurme_add_form"):
            bn = st.text_input("İşletme Adı"); ct = st.selectbox("Şehir", ["İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"]); adr = st.text_area("Adres"); ot = st.text_input("Fırsat Başlığı"); dc = st.text_input("İndirim Kodu")
            
            users = fb.get_all_users(limit=50)
            current_uid = st.session_state.user_uid
            elciler = [u for u in users if u['role'] in ['kultur_elcisi', 'evliya_celebi'] and u['uid'] != current_uid]
            elci_options = {f"{u['nick']} ({u['role']})": u for u in elciler}
            selected_elci_label = st.selectbox("Referans (Varsa)", ["Yok"] + list(elci_options.keys()))
            
            st.markdown(f'<a href="{SHOPIER_LINK_REKLAM}" target="_blank" class="shopier-btn">💳 1000 TL ile İlan Oluştur</a>', unsafe_allow_html=True)
            if st.form_submit_button("Onaya Gönder"):
                if bn and ot and dc and adr:
                    ref_uid = ""; ref_nick = "Yok"
                    if selected_elci_label != "Yok": sel_user = elci_options[selected_elci_label]; ref_uid = sel_user['uid']; ref_nick = sel_user['nick']
                    fb.add_gurme_offer({ "business_name": bn, "city": ct, "offer_title": ot, "discount_code": dc, "referrer_uid": ref_uid, "referrer_nick": ref_nick, "address": adr, "uid": st.session_state.user_uid if st.session_state.user_uid else "guest" })
                    st.success("İlan alındı!")
                else: st.warning("Eksik bilgi.")

def render_sponsor(fb):
    pool_balance = fb.get_sponsorship_pool()
    st.markdown(f"""<div class="sponsor-pool-box"><h1>🤝 ÖĞRENCİYE IŞIK OL FONU</h1><div style="font-size:36px; font-weight:bold;">{pool_balance} TL</div><div>Toplanan Destek</div></div>""", unsafe_allow_html=True)
    
    tab_kurumsal, tab_bireysel = st.tabs(["🏢 Kurumsal İşbirliği", "🎒 Bireysel Destek"])
    
    with tab_kurumsal:
        c_k1, c_k2 = st.columns([1, 1])
        with c_k1:
            st.image(PLACEHOLDER_AD_IMG, caption="Markanız Burada Yer Alsın")
        with c_k2:
            st.markdown("### 🌟 Vizyoner Sponsor Olun")
            st.write("GeziStory, Türkiye'nin en hızlı büyüyen yeni nesil gezgin platformudur. Markanızı binlerce gezginle buluşturmak için bizimle iletişime geçin.")
            st.info("Aylık Sponsorluk Paketi: **5.000 TL** (Lansmana Özel)")
            st.write("Sponsor olduğunuz öğrenci, sadece sitemizde değil; **Instagram, TikTok ve tüm sosyal mecralarda** sizin etiketinizle (#MarkaAdı) 'Gerçek Reklam' yapacaktır.")
            st.markdown(f'<a href="{SHOPIER_LINK_KURUMSAL}" target="_blank" class="shopier-btn">🚀 Sponsor Olmak İstiyorum</a>', unsafe_allow_html=True)

    with tab_bireysel:
        st.markdown("### 🎒 Bir Öğrencinin Hayaline Dokun")
        st.write("Ders kitapları dünyayı anlatır, seyahat ise öğretir. Bir üniversite öğrencisinin ilk Kapadokya deneyimine veya ilk tren yolculuğuna sponsor olun.")
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.info("☕ **Yol Kahvesi Ismarla**")
            st.markdown(f'<a href="{SHOPIER_LINK_BAGIS}" target="_blank" class="shopier-btn">50 TL Destek</a>', unsafe_allow_html=True)
        with col_b2:
            st.warning("🚌 **Otobüs Bileti Al**")
            st.markdown(f'<a href="{SHOPIER_LINK_BAGIS}" target="_blank" class="shopier-btn">500 TL Destek</a>', unsafe_allow_html=True)
        with col_b3:
            st.success("🎒 **Çantasını Hazırla**")
            st.markdown(f'<a href="{SHOPIER_LINK_BAGIS}" target="_blank" class="shopier-btn">1000 TL Destek</a>', unsafe_allow_html=True)

        st.caption("Ödeme yaptıktan sonra aşağıdaki butona basarak bildir.")
        if st.button("Destek Oldum, Bildir!"): st.toast("Teşekkürler! Desteğin incelenip havuza eklenecektir.")
    
    st.divider()
    st.markdown("### 🏆 Geçmişte Gezenler (Şeffaflık Duvarı)")
    winners = fb.get_past_winners()
    if not winners: 
        render_empty_state("Henüz kimseyi uçurmadık. İlk talihli sen olabilirsin!", "✈️")
    else:
        for w in winners: st.markdown(f"""<div class="winner-card"><div style="font-size:24px;">🎉</div><div><div style="font-weight:bold;">{w['nick']}</div><div style="font-size:12px; color:#555;">Rota: {w['route']} | Tutar: {w['cost']} TL | Tarih: {w['date']}</div></div></div>""", unsafe_allow_html=True)

# --- KEŞFET FONKSİYONU ---
def render_kesfet(stories, fb, search_term=""):
    stories = [s for s in stories if not s.get('stops') or len(s['stops']) == 0]
    user_name = st.session_state.user_nick if st.session_state.user_nick else "Gezgin"
    c_head, c_sel = st.columns([2,1])
    c_head.markdown(f"### 👋 Hoş geldin, {user_name}")
    
    cities = sorted(list(set(s['city'] for s in stories)))
    if 'active_city' not in st.session_state: st.session_state.active_city = "Tümü"
    sel_city = c_sel.selectbox("Şehir Seç:", ["Tümü"] + cities, key="city_selector")
    st.session_state.active_city = sel_city 
    
    if sel_city in CITY_GASTRO_GUIDE:
        info = CITY_GASTRO_GUIDE[sel_city]
        st.markdown(f"""<div class="gastro-card"><div class="gastro-title">🍽️ {sel_city} Lezzet Dosyası</div><div class="gastro-item"><b>🍖 Ne Yenir:</b> {info['yemek']}</div><div class="gastro-item"><b>💰 Bütçe:</b> {info['butce']}</div><div class="gastro-item"><b>💡 Tüyo:</b> {info['tuyo']}</div></div>""", unsafe_allow_html=True)

    if 'active_mood' not in st.session_state: st.session_state.active_mood = "Hepsi"
    col_count = 6 if st.session_state.user_token else 5
    m_cols = st.columns(col_count)
    
# --- MOBİL UYUMLU MOOD SEÇİCİ ---
    # Butonlar mobilde alt alta dizildiği için kötü görünüyor.
    # Bunun yerine yatay radyo butonları veya pills (yeni sürüm) kullanmak daha iyidir.
    # Burada özel CSS ile buton görünümü verilmiş Radio kullanacağız.
    
    mood_options = ["🌍 Hepsi", "💸 Parasızım", "⚡ Acelem Var", "📸 Fotoğraf", "🍽️ Açım"]
    if st.session_state.user_token:
        mood_options.insert(1, "👥 Takip")
    
    # Seçili olanın indeksini bul
    current_mood_label = next((m for m in mood_options if st.session_state.active_mood in m), "🌍 Hepsi")
    try:
        current_idx = mood_options.index(current_mood_label)
    except: current_idx = 0

    # Yatay Radyo Butonu (Mobilde de yatay kaydırılabilir olur, alt alta dizilmez)
    selected_mood = st.radio("Modunu Seç:", mood_options, index=current_idx, horizontal=True, label_visibility="collapsed")
    
    # Seçimi İşle
    # Emojiyi kaldırıp ham key'i buluyoruz (Örn: "🌍 Hepsi" -> "Hepsi")
    mapping = {"🌍 Hepsi": "Hepsi", "👥 Takip": "Takip", "💸 Parasızım": "Parasiz", "⚡ Acelem Var": "Hizli", "📸 Fotoğraf": "Foto", "🍽️ Açım": "Acim"}
    new_mood_key = mapping.get(selected_mood, "Hepsi")
    
    if st.session_state.active_mood != new_mood_key:
        st.session_state.active_mood = new_mood_key
        st.rerun()
    
    mood = st.session_state.active_mood
    
    main_col, side_col = st.columns([0.7, 0.3])
    with main_col:
        if search_term:
            st.info(f"🔍 '{search_term}' için sonuçlar:")
            all_users = fb.get_all_users(limit=50) 
            found_users = [u for u in all_users if search_term.lower() in u['nick'].lower()]
            if found_users:
                st.markdown("###### 👤 Kullanıcılar")
                u_cols = st.columns(min(len(found_users), 4))
                for idx, u in enumerate(found_users[:4]): 
                    with u_cols[idx]:
                         if st.button(f"{u['nick']}", key=f"s_user_{u['uid']}"):
                             st.session_state.view_target_uid = u['uid']; st.session_state.active_tab = "public_profile"; st.rerun()
                st.divider()

            filtered = []
            for s in stories:
                in_title = search_term.lower() in s['title'].lower()
                in_city = search_term.lower() in s['city'].lower()
                in_tags = any(search_term.lower() in t.lower() for t in s.get('tags', []))
                if in_title or in_city or in_tags: filtered.append(s)
        else:
            filtered = stories
            if sel_city != "Tümü": filtered = [s for s in filtered if s['city'] == sel_city]
            if mood == "Parasiz": filtered = [s for s in filtered if s.get('budget', 0) <= 200]
            elif mood == "Foto": filtered = [s for s in filtered if s['category'] in ['Manzara', 'Doğa']]
            elif mood == "Acim": filtered = [s for s in filtered if s['category'] in ['Gurme', 'Mekan']]
            if mood == "Takip" and st.session_state.user_token:
                 my_profile = fb.get_profile(st.session_state.user_uid)
                 my_following = my_profile.get('following', [])
                 filtered = [s for s in filtered if s['uid'] in my_following]

        if not filtered: render_empty_state("Aradığın kriterlerde hiç hikaye yok.", "🏜️")
        
        if st.session_state.user_token:
            with st.expander("➕ Tekli Hikaye Paylaş"):
                user_role = st.session_state.get('user_role', 'caylak')
                if user_role == 'caylak':
                    st.warning("🛑 **Erişim Engellendi: Çaylak Seviyesi**")
                    st.error("Öncelikle 250 puan toplayarak 'Gezgin' rütbesine gelmelisin.")
                    st.info("💡 İpucu: **YARIŞMA (Challenge)** sekmesindeki görevlere katılarak hızlı puan kazanabilirsin.")
                else:
                    if check_login_and_warn():
                        allowed, msg = fb.check_daily_limit_and_update(st.session_state.user_uid, 'post')
                        if allowed:
                            with st.form("p_f"):
                                c=st.selectbox("Şehir",["İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"]); i=st.file_uploader("Foto"); t=st.text_input("Başlık"); 
                                s=st.text_area("Not"); tags_input = st.text_input("Etiketler (Virgülle ayırın: #doğa, #kamp)")
                                product_link_input = ""
                                if user_role in ['evliya_celebi', 'admin', 'mod']: st.info("👑 Evliya Çelebi Ayrıcalığı: Ürün Linki Ekle"); product_link_input = st.text_input("🔗 Önerdiğin Ürün Linki (Opsiyonel)")
                                k=st.radio("Kategori",["Gurme","Tarih","Doğa","Mekan","Manzara"],horizontal=True)
                                cost = st.number_input("Tahmini Harcama (TL)", min_value=0, step=10)
                                if st.form_submit_button("Paylaş", type="secondary") and i and t and s:
                                    u=upload_to_imgbb(i)
                                    tags_processed = [tag.strip().replace("#", "") for tag in tags_input.split(",") if tag.strip()]
                                    if u: 
                                        fb.add_story({"title":t, "city":c, "img":u, "summary":s, "category":k, "budget":cost, "stops":[], "author":st.session_state.user_nick, "uid":st.session_state.user_uid, "tags": tags_processed, "product_link": product_link_input})
                                        fb.add_points(st.session_state.user_uid, 30) # GÜNCELLENDİ: 30 Puan
                                        st.success("Yayınlandı! (+30 Puan)"); time.sleep(1); st.rerun()
                        else: st.warning(msg)

        st.markdown(f"##### 🔥 İçerikler ({len(filtered)})")
        for i in range(0, len(filtered), 2):
            for col, story in zip(st.columns(2), filtered[i:i+2]):
                with col:
                    st.markdown(get_discover_card_html(story), unsafe_allow_html=True)
                    b1, b2, b3 = st.columns(3)
                    if b1.button(f"{'❤️' if story.get('liked_by_me') else '🤍'} {story['like_count']}", key=f"k_lk_{story['id']}"):
                         if st.session_state.user_token: fb.update_interaction(story['id'], "like", current_likes=story['liked_uids']); st.rerun()
                    if b2.button(f"💬 {len(story['comments'])}", key=f"k_cm_{story['id']}"): fb.update_interaction(story['id'], "view"); view_comments_dialog(story, fb)
                    if b3.button(f"👤 {story['author']}", key=f"vp_st_{story['id']}"): st.session_state.view_target_uid = story['uid']; st.session_state.active_tab = "public_profile"; st.rerun()
                    if st.session_state.user_uid == story['uid']:
                        if st.button("🗑️ Sil", key=f"del_st_{story['id']}"): fb.delete_story(story['id']); st.rerun()

    with side_col:
        sys_data = fb.get_sidebar_content()
        st.markdown('<div class="sidebar-box"><div class="sidebar-title">📢 Duyurular</div>', unsafe_allow_html=True)
        if sys_data.get('ann_text') or sys_data.get('ann_img'):
            if sys_data.get('ann_img'): st.image(sys_data['ann_img'])
            if sys_data.get('ann_text'): st.info(sys_data['ann_text'])
        else:
            st.caption("Son Tartışmalar:")
            for p in fb.get_forum_posts()[:3]: st.markdown(f"- {p['title']}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-box"><div class="sidebar-title">✨ Sponsor</div>', unsafe_allow_html=True)
        active_user_ad = fb.get_active_main_ad()
        if active_user_ad: st.image(active_user_ad['image']); st.markdown(f"[👉 {active_user_ad.get('business_name', 'Fırsat')} İçin Tıkla]({active_user_ad['link']})")
        elif sys_data.get('ad_youtube'): st.video(sys_data['ad_youtube'])
        elif sys_data.get('ad_img'): st.image(sys_data['ad_img']); st.markdown(f"[Detaylı Bilgi]({sys_data.get('ad_link', '#')})")
        else: st.image(PLACEHOLDER_AD_IMG, caption="Buraya Reklam Verin")
        
        with st.expander("📢 Buraya Reklam Ver"):
            st.info("Ana sayfa vitrininde 24 saat boyunca yer alın. Ücret: 1000 TL")
            with st.form("sidebar_user_ad_form"):
                bn = st.text_input("İşletme / Kampanya Adı"); lnk = st.text_input("Yönlendirilecek Link"); img_file = st.file_uploader("Görsel", type=['jpg','png'])
                st.markdown(f'<a href="{SHOPIER_LINK_REKLAM}" target="_blank" class="shopier-btn">💳 Ödeme Yap</a>', unsafe_allow_html=True)
                if st.form_submit_button("Gönder"):
                    if bn and lnk and img_file:
                        u = upload_to_imgbb(img_file)
                        if u: fb.add_main_ad({"business_name": bn, "link": lnk, "image": u, "uid": st.session_state.user_uid}); st.success("Gönderildi!")
                    else: st.warning("Eksik bilgi.")
        st.markdown('</div>', unsafe_allow_html=True)
# --- MOBİL İÇİN EKSTRA REKLAM ALANI (Sidebar Kapalıyken Görünsün) ---
    st.divider()
    st.caption("Sponsorlu İçerik")
    active_user_ad_mobile = fb.get_active_main_ad()
    if active_user_ad_mobile:
        st.image(active_user_ad_mobile['image'], use_container_width=True)
        st.markdown(f"**👉 [{active_user_ad_mobile.get('business_name', 'Fırsat')} İçin Tıkla]({active_user_ad_mobile['link']})**")
    else:
        st.image("https://via.placeholder.com/600x150?text=Mobil+Reklam+Alani", use_container_width=True)

# --- render_kesfet fonksiyonunun bittiği yerin altı ---

def render_rotalar(stories, fb, search_term):
    # 1. TEMEL VERİ HAZIRLIĞI (Sadece Rotaları Ayıkla)
    routes = [s for s in stories if s.get('stops') and len(s['stops']) > 0]
    
    # Şehir Listesini Rotalardan Çıkar
    cities = sorted(list(set(r['city'] for r in routes)))

    # 2. ÜST BAR: BAŞLIK VE FİLTRE (Keşfet Mantığı)
    c_head, c_sel = st.columns([3, 1])
    
    with c_head:
        st.markdown("### 🗺️ Rotalar ve Gezi Planları")
    
    with c_sel:
        # Şehir Seçici (Varsayılan: Tümü)
        selected_city = st.selectbox("Şehir Filtrele", ["Tümü"] + cities, key="route_city_filter")

    # 3. ROTA OLUŞTURMA PANELİ
    if st.session_state.user_token:
        with st.expander("➕ Yeni Bir Rota Planla", expanded=False):
            render_create_route_section(fb)
    else:
        st.info("Rota oluşturmak için giriş yapmalısın.")

    st.divider()

    # 4. FİLTRELEME MOTORU
    # A) Şehir Filtresi
    if selected_city != "Tümü":
        routes = [r for r in routes if r['city'] == selected_city]

    # B) Arama Terimi Filtresi (Main'den gelen)
    if search_term:
        term = search_term.lower()
        routes = [r for r in routes if term in r['title'].lower() or term in r['city'].lower()]

    # 5. LİSTELEME (GRID SİSTEMİ)
    if not routes:
        msg = f"{selected_city} için henüz planlanmış bir rota yok." if selected_city != "Tümü" else "Henüz planlanmış bir rota yok."
        render_empty_state(msg, "🎒")
    else:
        # Sayfa Düzeni: Sol (3 birim) - Sağ (1 birim)
        col_main, col_sidebar = st.columns([3, 1])
        
        with col_main:
            st.markdown(f"##### 🎒 {selected_city if selected_city != 'Tümü' else 'Güncel'} Rotalar ({len(routes)})")
            
            # Her satırda 2 rota olacak şekilde döngü
            for i in range(0, len(routes), 2):
                row_cols = st.columns(2)
                
                # 1. Rota (Sol)
                with row_cols[0]:
                    route = routes[i]
                    st.markdown(get_route_card_html(route), unsafe_allow_html=True)
                    if st.button("🔍 İNCELE", key=f"r_vw_{route['id']}", use_container_width=True):
                        fb.update_interaction(route['id'], "view")
                        view_route_detail_dialog(route, fb)
                
                # 2. Rota (Sağ - Eğer varsa)
                if i + 1 < len(routes):
                    with row_cols[1]:
                        route2 = routes[i+1]
                        st.markdown(get_route_card_html(route2), unsafe_allow_html=True)
                        if st.button("🔍 İNCELE", key=f"r_vw_{route2['id']}", use_container_width=True):
                            fb.update_interaction(route2['id'], "view")
                            view_route_detail_dialog(route2, fb)
                
                st.markdown("<br>", unsafe_allow_html=True) # Satır arası boşluk

        # SAĞ REKLAM ALANI
        with col_sidebar:
            st.markdown('<div class="sidebar-box" style="margin-top:40px;">', unsafe_allow_html=True)
            st.image("https://via.placeholder.com/300x600?text=REKLAM+ALANI", caption="Sponsorlu İçerik")
            st.markdown('</div>', unsafe_allow_html=True)

# --- render_challenge fonksiyonunun başladığı yerin üstü ---

# --- CHALLENGE SEKME İÇERİĞİ (SEKMELİ YAPI) ---
def render_challenge(fb):
    st.markdown("### 🏆 MEYDAN OKUMA (Challenge)")
    
    # REKLAM ALANI (Yüksek Gelir)
    st.markdown('<div style="width:100%; height:90px; background:#f0f2f6; border:1px solid #ddd; border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:20px;"><span style="color:#888; font-weight:bold;">📢 REKLAM ALANI (Google AdSense - 970x90)</span></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🚀 OPERASYON ODASI (Görev & Katıl)", "📸 SAHA RAPORLARI (Arşiv)"])
    active_ch = fb.get_active_challenge()
    
    with tab1:
        c_left, c_right = st.columns([1, 1])
        with c_left:
            if st.session_state.user_role in ['admin', 'mod']:
                with st.expander("⚙️ Yönetim Paneli"):
                    with st.form("new_ch_form"):
                        ch_id_input = st.number_input("Hafta", min_value=1, value=1); ch_title = st.text_input("Başlık"); ch_desc = st.text_area("Açıklama"); ch_reward = st.text_input("Ödül")
                        if st.form_submit_button("Yayınla"): fb.update_active_challenge(ch_id_input, ch_title, ch_desc, ch_reward); st.success("Yayınlandı!"); time.sleep(1); st.rerun()
                    with st.form("new_poll_form"):
                        p_q = st.text_input("Anket Sorusu"); p_opts = st.text_input("Seçenekler (Virgülle)")
                        if st.form_submit_button("Başlat"):
                             if p_opts: fb.create_simple_poll(p_q, [o.strip() for o in p_opts.split(",") if o.strip()]); st.success("Başladı!"); time.sleep(1); st.rerun()

            if active_ch:
                st.markdown(f"""<div class="challenge-board"><div class="challenge-title">🔥 CHALLENGE #{active_ch['id']} 🔥</div><h2 style="color:white;">{active_ch['title']}</h2><p style="color:#ddd;">{active_ch['desc']}</p><div style="background:#FFD700; color:black; padding:5px; border-radius:5px; font-weight:bold; display:inline-block; margin-top:10px;">🎁 ÖDÜL: {active_ch['reward']}</div></div>""", unsafe_allow_html=True)
                active_poll = fb.get_simple_poll()
                if active_poll:
                    st.markdown(f'<div class="poll-box"><div class="poll-title">📊 {active_poll["question"]}</div>', unsafe_allow_html=True)
                    total_votes = sum(o['count'] for o in active_poll['options'])
                    for opt in active_poll['options']:
                        col_p1, col_p2 = st.columns([3, 1])
                        pct = (opt['count'] / total_votes) if total_votes > 0 else 0
                        col_p1.progress(pct, text=f"{opt['name']} ({opt['count']} oy)")
                        if col_p2.button("Oy Ver", key=f"vote_{opt['id']}"): fb.vote_simple_poll(opt['id']); st.toast("Kaydedildi!"); time.sleep(1); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else: render_empty_state("Aktif bir görev yok.", "💤")

        with c_right:
            if st.session_state.get(f"ch_submitted_{active_ch['id']}", False):
                st.success("✅ Raporun iletildi! Diğer katılımları yan sekmeden görebilirsin.")
            else:
                st.markdown("##### 🎯 Senin Sıran! (10 Puan)")
                if check_login_and_warn():
                    with st.form("ch_entry_form"):
                        e_img = st.file_uploader("Kanıt", type=['jpg', 'png']); e_text = st.text_area("Hikayen", max_chars=140); e_city = st.selectbox("Nerede?", ["Seçiniz"] + ALL_PROVINCES)
                        if st.form_submit_button("Gönder ve Katıl 🚀", type="primary"):
                            if e_img and e_text and e_city != "Seçiniz":
                                img_url = upload_to_imgbb(e_img)
                                if img_url:
                                    fb.add_challenge_entry(active_ch['id'], {"user": st.session_state.user_nick, "text": e_text, "city": e_city, "img": img_url})
                                    st.session_state[f"ch_submitted_{active_ch['id']}"] = True; st.balloons(); st.success("Katılım alındı!"); time.sleep(1); st.rerun()
                            else: st.warning("Eksik bilgi.")

    with tab2:
        selected_ch_id = st.selectbox("Hafta Seç", [1, 2, 3, 4, 5], index=int(active_ch['id'])-1 if active_ch else 0)
        st.markdown(f"#### 📸 Challenge #{selected_ch_id} Raporları")
        entries = fb.get_challenge_entries(selected_ch_id)
        if not entries: render_empty_state("Henüz kimse katılmadı.", "📭")
        else:
            cols = st.columns(4)
            for i, entry in enumerate(entries):
                with cols[i % 4]:
                    st.markdown(f"""<div class="challenge-entry-card"><img src="{entry['img']}" class="challenge-img"><div class="challenge-text">"{entry['text']}"</div><div class="challenge-user"><span>👤 {entry['user']}</span><span>📍 {entry['city']}</span></div></div>""", unsafe_allow_html=True)
                    if st.button(f"🔥 {entry['like_count']}", key=f"ch_like_{entry['id']}", use_container_width=True): fb.update_challenge_like(entry['id'], st.session_state.user_uid, entry['likes']); st.rerun()
                    if st.session_state.user_role in ['admin', 'mod']:
                        if st.button("👑 KAZANAN", key=f"win_ch_{entry['id']}"): st.balloons(); fb.update_active_challenge(selected_ch_id, f"KAZANAN: {entry['user']}", "Tebrikler!", "ÖDÜL VERİLDİ"); st.rerun()

def render_admin(fb):
    st.header("👑 Yönetici"); 
    
    # PAGINATION İLE KULLANICI YÜKLEME
    if 'user_limit' not in st.session_state: st.session_state.user_limit = 20
    u = fb.get_all_users(limit=st.session_state.user_limit)
    
    s = fb.get_stories(); 
    if st.session_state.user_role not in ['admin', 'mod']: st.error("Yetkisiz Giriş!"); return

    pending_offers = fb.get_gurme_offers(status="pending")
    pending_apps = fb.get_sponsor_applications() 
    pending_ads = fb.get_pending_main_ads()
    
    c1,c2,c3,c4=st.columns(4); c1.metric("Üye (Yüklü)",len(u)); c2.metric("İçerik",len(s)); c3.metric("Bakiye", sum(x['balance'] for x in u)); c4.metric("Bekleyen Reklam", len(pending_offers) + len(pending_ads))
    
    t1,t2,t3,t4,t5,t6,t7 = st.tabs(["Üyeler","İçerik","Duyuru","📢 Vitrin & Reklam", "Gurme Onayı", "Anasayfa Reklam Onayı", "Sponsorluk"])
    with t1:
        for x in u:
            if st.session_state.user_role == 'mod' and x['role'] in ['admin','mod']: continue
            c_a, c_b = st.columns([3,1]); c_a.write(f"**{x['nick']}** ({x['points']} P) - {x['role']}"); 
            nr=c_b.selectbox("Rütbe", ["caylak","gezgin","kultur_elcisi","evliya_celebi","mod","admin","gurme"], key=f"r_{x['uid']}", index=0)
            if c_b.button("Update", key=f"u_{x['uid']}"): fb.update_user_role(x['uid'], nr); st.success("OK")
        
        # DAHA FAZLA YÜKLE BUTONU
        if st.button("➕ Daha Fazla Kullanıcı Yükle (+20)"):
            st.session_state.user_limit += 20
            st.rerun()

    with t2:
        for x in s:
            with st.expander(f"{x['title']} ({x['author']})"):
                if st.button("Sil", key=f"del_{x['id']}"): fb.delete_story(x['id']); st.rerun()
    with t3:
        if st.session_state.user_role=='admin' and st.button("Yayınla") and (txt:=st.text_input("Metin")): fb.update_system_announcement(txt); st.success("OK")
    with t4:
        st.markdown("##### Sağ Sidebar Ayarları")
        with st.form("sidebar_form"):
            ann_text = st.text_input("Duyuru Metni (Boşsa Forum gözükür)")
            ann_img_file = st.file_uploader("Duyuru Resmi", type=['jpg','png'])
            st.divider()
            ad_youtube = st.text_input("Varsayılan YouTube Video Linki (Öncelikli)")
            ad_link = st.text_input("Varsayılan Reklam Linki (Video yoksa)")
            ad_img_file = st.file_uploader("Varsayılan Reklam Görseli", type=['jpg','png'])
            if st.form_submit_button("Kaydet / Temizle (Boş Gönder)"):
                data = {'ann_text': ann_text, 'ad_link': ad_link, 'ad_youtube': ad_youtube}
                if ann_img_file: data['ann_img'] = upload_to_imgbb(ann_img_file)
                if ad_img_file: data['ad_img'] = upload_to_imgbb(ad_img_file)
                fb.update_sidebar_content(data)
                st.success("Vitrin güncellendi!")
        
        if st.button("❌ Duyuruyu Tamamen Kaldır"):
             fb.update_sidebar_content({'ann_text': '', 'ann_img': ''})
             st.success("Duyuru kaldırıldı.")

    with t5: 
        if not pending_offers: st.info("Onay bekleyen Gurme ilanı yok.")
        for off in pending_offers:
            with st.expander(f"📌 {off['business_name']} ({off['offer_title']})"):
                st.write(f"**Şehir:** {off['city']}"); st.write(f"**Kod:** {off['discount_code']}"); st.write(f"**Referans:** {off['referrer_nick']}")
                if st.button("✅ Onayla", key=f"app_{off['id']}"): fb.approve_gurme_offer(off['id'], off['referrer_uid']); st.success("Onaylandı"); time.sleep(1); st.rerun()
    
    with t6: 
        if not pending_ads: st.info("Onay bekleyen Vitrin Reklamı yok.")
        for ad in pending_ads:
             with st.expander(f"📺 {ad['business_name']}"):
                 st.image(ad['image'])
                 st.write(f"Link: {ad['link']}")
                 if st.button("✅ Yayına Al (24 Saat)", key=f"app_ad_{ad['id']}"):
                     fb.approve_main_ad(ad['id'])
                     st.success("Reklam yayına alındı!")
                     time.sleep(1); st.rerun()

    with t7:
        st.write("##### 💰 Havuz Yönetimi")
        pool = fb.get_sponsorship_pool()
        st.metric("Havuz Bakiyesi", f"{pool} TL")
        add_amount = st.number_input("Havuza Para Ekle (Manuel)", step=50)
        if st.button("Ekle (+)", key="add_pool"):
             fb.add_to_sponsorship_pool(add_amount); st.success("Eklendi"); st.rerun()
        st.divider()
        st.write("##### 🎓 Başvurular")
        if not pending_apps: st.info("Bekleyen başvuru yok.")
        for app in pending_apps:
            with st.expander(f"📄 {app['nick']} - {app['route_plan']}"):
                st.write(f"**Sebep:** {app['reason']}")
                cost_est = st.number_input("Tahmini Maliyet (Ödenecek)", min_value=0, key=f"cost_{app['id']}")
                if st.button("🏆 Kazanan İlan Et", key=f"win_{app['id']}"):
                    if cost_est <= pool:
                        fb.select_winner(app['id'], app['nick'], app['route_plan'], cost_est)
                        st.balloons(); st.success(f"{app['nick']} geziye gönderildi!"); time.sleep(2); st.rerun()
                    else: st.error("Havuzda yeterli bakiye yok!")

# --- YENİ HAFİF HARİTA SİSTEMİ (ROZETLER) ---
def render_conquest_map(visited_cities):
    st.markdown("### 🗺️ Fetih Paneli")
    st.caption("Gezdiğin iller **YEŞİL**, henüz gitmediklerin **GRİ** görünür.")
    
    # İlerleme Durumu
    progress = len(visited_cities) / 81
    st.progress(progress)
    st.caption(f"Türkiye'nin %{int(progress*100)}'ini fethettin! ({len(visited_cities)}/81)")

    # Rozet Izgarası (Grid)
    html_content = '<div class="conquest-grid">'
    for city in ALL_PROVINCES:
        is_visited = city in visited_cities
        # Eğer gezildiyse Yeşil sınıfı, değilse Gri sınıfı
        css_class = "city-visited" if is_visited else "city-not-visited"
        # İkon seçimi
        icon = "✅" if is_visited else "⬜"
        
        # Tıklanabilir gibi görünmesin diye pointer-events kapalı olabilir ama şimdilik görsel olsun
        html_content += f'<div class="city-badge {css_class}">{icon} {city}</div>'
    
    html_content += '</div>'
    
    # HTML'i Ekrana Bas
    st.markdown(html_content, unsafe_allow_html=True)

def render_profile(fb):
    p = fb.get_profile(st.session_state.user_uid)
    st.session_state.user_saved_routes = p.get('saved_routes', [])
    if p['nick'] == "Adsız": st.warning("⚠️ Hey Gezgin! Seni 'Adsız' olarak tanıyoruz. Lütfen aşağıdan kendine bir isim seç.")
    
    # Profil Başlığı
    st.markdown(get_profile_header_html(p), unsafe_allow_html=True)
    
    # --- YENİ HARİTA BURADA ÇAĞIRILIYOR ---
    render_conquest_map(p.get('visited_cities', []))
    # --------------------------------------
    
    st.divider()
    
    # Şehir Ekleme Paneli
    with st.expander("📍 Haritanı Boya / Şehir Ekle"):
        current_cities = p.get('visited_cities', [])
        selected_cities = st.multiselect(
            "Gezdiğin İlleri İşaretle:", 
            ALL_PROVINCES, 
            default=[c for c in current_cities if c in ALL_PROVINCES]
        )
        
        if st.button("Haritayı Güncelle", type="primary"):
            fb.update_visited_cities(st.session_state.user_uid, selected_cities)
            st.success("Fetih listen güncellendi! 🎨")
            time.sleep(1)
            st.rerun()

    # Kimlik Güncelleme
    with st.expander("✏️ Kimlik Bilgilerini Güncelle", expanded=(p['nick'] == "Adsız")):
        with st.form("update_nick_form"):
            new_nick = st.text_input("Yeni Kullanıcı Adı", value=p['nick'])
            new_avatar = st.file_uploader("Profil Resmi Yükle", type=['jpg', 'png', 'jpeg'])
            if st.form_submit_button("Güncelle", type="primary"):
                if new_avatar:
                    url = upload_to_imgbb(new_avatar)
                    if url: fb.update_profile_image(st.session_state.user_uid, url)
                if new_nick and new_nick != "Adsız":
                    if fb.update_nickname(st.session_state.user_uid, new_nick):
                        st.session_state.user_nick = new_nick 
                        st.success("İsmin başarıyla değiştirildi! 🎉"); time.sleep(1); st.rerun()
                    else: st.error("Bir hata oluştu, tekrar dene.")
                else: st.success("Profil resmi güncellendi!"); time.sleep(1); st.rerun()
    
    st.divider()
    
    # Alt Sekmeler (Mesajlar, Paylaşımlar vs.)
    t1, t2, t3, t4 = st.tabs(["✉️ Mesajlar", "📝 Paylaşımlarım", "🇹🇷 Pasaport", "📦 Kayıtlar & Cüzdan"])
    
    with t1: 
        msgs = fb.get_messages(st.session_state.user_uid)
        st.session_state.seen_msgs_count = len(msgs)
        if not msgs: render_empty_state("Gelen kutun boş. Sessizliğin sesi...", "📭")
        for m in msgs:
            if st.button(f"📩 {m['sender']} - {m['date']}", key=f"read_msg_{m['id']}", use_container_width=True):
                view_message_dialog(m, fb)

    with t2: 
        my_stories, my_posts = fb.get_user_content(st.session_state.user_uid)
        if not my_stories and not my_posts: render_empty_state("Henüz bir izin yok. Keşfetmeye başla!", "👣")
        
        st.write(f"**Toplam Hikaye:** {len(my_stories)} | **Toplam Forum Konusu:** {len(my_posts)}")
        for s in my_stories: st.caption(f"📸 {s['title']} ({s['city']}) - {s['date_str'][:10]}")
        for p in my_posts: st.caption(f"🗣️ {p['title']} ({p['cat']}) - {p['date'][:10]}")

    with t3: 
        st.info("Bu sekme artık yukarıdaki Fetih Paneli ile birleştirildi.")
    
    with t4: 
        st.write(f"Bakiye: {p.get('balance', 0)} TL | Kazanç: {p.get('earnings', 0)} TL"); st.caption("Kayıtlı rotalarım ve içeriklerim burada listelenecek.")

def render_public_profile(fb, target_uid):
    if st.button("⬅️ Geri Dön"): 
        st.session_state.active_tab = "kesfet"
        st.rerun()
        
    p = fb.get_profile(target_uid)
    
    st.markdown(get_profile_header_html(p), unsafe_allow_html=True)
    
    # --- YENİ HARİTA SİSTEMİ (HATA VERMEZ) ---
    st.markdown(f"### 🗺️ {p['nick']}'in Fetih Paneli")
    # Buraya da aynı hafif harita fonksiyonunu veriyoruz
    render_conquest_map(p.get('visited_cities', []))

    if st.session_state.user_token:
        col_follow, col_msg = st.columns(2)
        # ... (Kodun geri kalanı aynı kalacak)
        my_following = fb.get_profile(st.session_state.user_uid).get('following', [])
        
        with col_follow:
            if target_uid in my_following:
                if st.button("❌ Takipten Çık", use_container_width=True):
                    fb.unfollow_user(st.session_state.user_uid, target_uid)
                    st.success("Takipten çıkıldı."); time.sleep(0.5); st.rerun()
            else:
                target_role = p.get('role', 'caylak')
                target_rank_idx = RANK_HIERARCHY.index(target_role)
                gezgin_idx = RANK_HIERARCHY.index('gezgin')
                
                if target_rank_idx >= gezgin_idx:
                     if st.button("➕ Takip Et", type="primary", use_container_width=True):
                         fb.follow_user(st.session_state.user_uid, target_uid)
                         st.balloons(); st.success("Takip edildi!"); time.sleep(1); st.rerun()
                else:
                    st.warning(f"🔒 {p['nick']} henüz 'Çaylak'. Takip edilebilmesi için 'Gezgin' olmalı.")

        with col_msg:
            with st.expander(f"✉️ Mesaj Gönder"):
                with st.form("send_msg_form"):
                    txt = st.text_area("Mesajın")
                    if st.form_submit_button("Gönder"):
                        fb.send_message(st.session_state.user_uid, target_uid, txt, st.session_state.user_nick)
                        st.success("Mesaj gönderildi!")
    
    st.divider()
    st.write(f"**{p['nick']}** Paylaşımları:")
    stories, posts = fb.get_user_content(target_uid)
    t1, t2 = st.tabs(["📸 Hikayeler", "🗣️ Forum Konuları"])
    with t1:
        if not stories: render_empty_state("Henüz hikaye paylaşmamış.", "📭")
        for s in stories: st.write(f"- {s['title']} ({s['city']})")
    with t2:
        if not posts: render_empty_state("Henüz konu açmamış.", "📭")
        for po in posts: st.write(f"- {po['title']}")

def sidebar(fb):
    with st.sidebar:
        if st.session_state.user_token:
            st.write(f"Hoş geldin, **{st.session_state.user_nick}**"); st.caption(f"Bakiye: {st.session_state.user_balance} TL | Puan: {st.session_state.user_points}")
            if st.session_state.user_nick == "Adsız": st.error("🚨 Lütfen profilinden ismini güncelle!")
            if st.button("Çıkış", type="secondary"): st.session_state.clear(); st.rerun()
        else: st.info("👋 Hoş geldin! İçerikleri gezebilirsin. Etkileşim için yukarıdaki Sarı Buton'dan giriş yap.")

def main():
    if 'user_token' not in st.session_state: st.session_state.update(user_token=None, user_uid=None, user_nick=None, user_balance=0, user_role='caylak', user_points=0, active_tab="kesfet", user_saved_routes=[], active_mood="Hepsi", seen_msgs_count=0)
    fb = FirebaseService(); st.markdown(get_app_css(), unsafe_allow_html=True)
    if not st.session_state.user_token: fb.sign_in_anonymously()
    
    if st.session_state.user_token:
        latest_profile = fb.get_profile(st.session_state.user_uid)
        st.session_state.user_role = latest_profile.get('role', 'caylak')
        st.session_state.user_nick = latest_profile.get('nick', 'Adsız')
        st.session_state.user_balance = latest_profile.get('balance', 0)
        st.session_state.user_points = latest_profile.get('points', 0)

    anno = fb.get_system_announcement()
    if anno: st.markdown(get_announcement_html(anno), unsafe_allow_html=True)
    
    if st.session_state.user_token:
        msgs = fb.get_messages(st.session_state.user_uid)
        total_msgs = len(msgs)
        unread_count = total_msgs - st.session_state.seen_msgs_count
        if unread_count > 0:
            if st.button(f"🔔 {unread_count} YENİ", type="primary"): st.session_state.active_tab = "profil"; st.rerun()
        else:
            if st.button("🔔", disabled=True): pass
    
    c_logo, c_map = st.columns([1, 3])
    with c_logo: st.markdown('<div class="main-logo">GeziStory <span class="logo-emoji">🧿</span></div>', unsafe_allow_html=True)
    with c_map: st.markdown(f'<div class="hero-banner-container"><img src="{MAP_BANNER_URL}" class="hero-banner-img"></div>', unsafe_allow_html=True)
    
    search_term = st.text_input("🔍 GeziStory'de Ara...", placeholder="Şehir, rota, yazar adı veya etiket (#doğa)...").strip()
    
    c_void, c_login = st.columns([3, 2]) 
    with c_login:
        if not st.session_state.user_token:
            if st.button("🔐 Giriş Yap / Kayıt Ol", type="primary", use_container_width=True): entry_dialog(fb)
        else:
             cols = st.columns(2) if st.session_state.user_role in ['admin','mod'] else st.columns([1, 0.1])
             if cols[0].button("👤 Profil", type="primary", use_container_width=True): st.session_state.active_tab="profil"; st.rerun()
             if st.session_state.user_role in ['admin','mod']:
                 if cols[1].button("👑 Yönetim", type="primary", use_container_width=True): st.session_state.active_tab="admin"; st.rerun()

    st.divider()
    c1,c2,c3,c4,c5,c6 = st.columns(6) 
    
    bt1 = "primary" if st.session_state.active_tab=="kesfet" else "secondary"
    if c1.button("🎲 KEŞFET", type=bt1, use_container_width=True): st.session_state.active_tab="kesfet"; st.rerun()
    
    bt2 = "primary" if st.session_state.active_tab=="rotalar" else "secondary"
    if c2.button("🗺️ ROTALAR", type=bt2, use_container_width=True): st.session_state.active_tab="rotalar"; st.rerun()
    
    bt_ch = "primary" if st.session_state.active_tab=="challenge" else "secondary"
    if c3.button("🏆 YARIŞMA", type=bt_ch, use_container_width=True): st.session_state.active_tab="challenge"; st.rerun()

    bt3 = "primary" if st.session_state.active_tab=="forum" else "secondary"
    if c4.button("🗣️ FORUM", type=bt3, use_container_width=True): st.session_state.active_tab="forum"; st.rerun()
    
    bt4 = "primary" if st.session_state.active_tab=="gurme" else "secondary"
    if c5.button("🎟️ GURME", type=bt4, use_container_width=True): st.session_state.active_tab="gurme"; st.rerun()
    
    bt5 = "primary" if st.session_state.active_tab=="sponsor" else "secondary"
    if c6.button("🎓 SPONSOR", type=bt5, use_container_width=True): st.session_state.active_tab="sponsor"; st.rerun()
    
    stories = fb.get_stories()
    
    if st.session_state.active_tab=="kesfet": render_kesfet(stories, fb, search_term)
    elif st.session_state.active_tab=="rotalar": render_rotalar(stories, fb, search_term)
    elif st.session_state.active_tab=="challenge": render_challenge(fb)
    elif st.session_state.active_tab=="forum": render_forum(fb)
    elif st.session_state.active_tab=="gurme": render_gurme(fb)
    elif st.session_state.active_tab=="sponsor": render_sponsor(fb)
    elif st.session_state.active_tab=="admin": render_admin(fb)
    elif st.session_state.active_tab=="profil": render_profile(fb)
    elif st.session_state.active_tab=="public_profile": render_public_profile(fb, st.session_state.view_target_uid)
    
    sidebar(fb)

if __name__ == "__main__": main()