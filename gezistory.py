import streamlit as st
import requests
import json

# --- AYARLAR (FIREBASE VE IMGBB ANAHTARLARI) ---
FIREBASE_API_KEY = "AIzaSyC3EMl5PW6g5dg9nw6OmJlBMe9gCHPqt24"
PROJECT_ID = "gezistory-app"
IMGBB_API_KEY = "ee85b5ea6763bbfa7faf74fa792874ab" # Senin verdiğin ImgBB anahtarı

# --- FOTOĞRAF YÜKLEME MOTORU (IMGBB) ---
def upload_to_imgbb(image_file):
    """
    Kullanıcının seçtiği fotoğrafı ImgBB sunucularına yükler
    ve oradan gelen internet linkini (URL) geri döndürür.
    """
    try:
        # ImgBB'ye gönderilecek paketi hazırlıyoruz
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
        }
        files = {
            "image": image_file.getvalue()
        }
        
        # Postacıyı yola çıkarıyoruz
        response = requests.post(url, data=payload, files=files)
        
        # Cevabı kontrol ediyoruz
        if response.status_code == 200:
            # Başarılı! Linki içinden alalım
            return response.json()["data"]["url"]
        else:
            st.error("Resim yüklenirken bir hata oluştu. ImgBB cevap vermedi.")
            return None
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
        return None

# --- FIREBASE BAĞLANTI MOTORU ---
class FirebaseService:
    def __init__(self):
        self.auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts"
        self.db_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

    def sign_up(self, email, password):
        payload = {"email": email, "password": password, "returnSecureToken": True}
        r = requests.post(f"{self.auth_url}:signUp?key={FIREBASE_API_KEY}", json=payload)
        return r.json()

    def sign_in(self, email, password):
        payload = {"email": email, "password": password, "returnSecureToken": True}
        r = requests.post(f"{self.auth_url}:signInWithPassword?key={FIREBASE_API_KEY}", json=payload)
        return r.json()

    def add_story(self, token, story_data):
        firestore_data = {
            "fields": {
                "baslik": {"stringValue": story_data['baslik']},
                "sehir": {"stringValue": story_data['sehir']},
                "mod": {"stringValue": story_data['mod']},
                "yazar": {"stringValue": story_data['yazar']},
                "resim": {"stringValue": story_data['resim']},
                "ozet": {"stringValue": story_data['ozet']}
            }
        }
        url = f"{self.db_url}/stories?key={FIREBASE_API_KEY}"
        r = requests.post(url, json=firestore_data)
        return r.status_code == 200

    def get_stories(self):
        r = requests.get(f"{self.db_url}/stories?key={FIREBASE_API_KEY}")
        if r.status_code != 200 or 'documents' not in r.json():
            return []
        
        clean_stories = []
        for doc in r.json()['documents']:
            fields = doc.get('fields', {})
            clean_stories.append({
                "baslik": fields.get('baslik', {}).get('stringValue', ''),
                "sehir": fields.get('sehir', {}).get('stringValue', ''),
                "mod": fields.get('mod', {}).get('stringValue', ''),
                "yazar": fields.get('yazar', {}).get('stringValue', ''),
                "resim": fields.get('resim', {}).get('stringValue', ''),
                "ozet": fields.get('ozet', {}).get('stringValue', '')
            })
        return clean_stories

fb = FirebaseService()

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="GeziStory", page_icon="🌍", layout="wide")

# Oturum Durumu
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# --- YAN MENÜ ---
with st.sidebar:
    st.title("🌍 GeziStory")
    st.caption("Hikayeni Paylaş, Dünyayı Keşfet")
    
    if st.session_state.user_token is None:
        st.info("Hikaye yazmak için giriş yapmalısın.")
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        
        with tab1:
            email_giris = st.text_input("E-posta", key="L1")
            pass_giris = st.text_input("Şifre", type="password", key="L2")
            if st.button("Giriş Yap", type="primary"):
                user = fb.sign_in(email_giris, pass_giris)
                if 'idToken' in user:
                    st.session_state.user_token = user['idToken']
                    st.session_state.user_email = user['email']
                    st.success("Hoş geldin!")
                    st.rerun()
                else:
                    st.error("Hatalı e-posta veya şifre.")

        with tab2:
            email_kayit = st.text_input("E-posta", key="S1")
            pass_kayit = st.text_input("Şifre (Min 6 karakter)", type="password", key="S2")
            if st.button("Kayıt Ol"):
                user = fb.sign_up(email_kayit, pass_kayit)
                if 'idToken' in user:
                    st.success("Kayıt Başarılı! Şimdi giriş yapabilirsin.")
                else:
                    hata_mesaji = user.get('error', {}).get('message', 'Bilinmiyor')
                    st.error(f"Hata: {hata_mesaji}")
    else:
        st.success(f"👤 {st.session_state.user_email}")
        if st.button("Çıkış Yap"):
            st.session_state.user_token = None
            st.rerun()

    st.divider()
    st.subheader("🔍 Keşfet")
    filter_city = st.selectbox("Hangi Şehir?", ["Tümü", "İstanbul", "İzmir", "Kapadokya", "Antalya", "Roma", "Paris"])
    filter_mode = st.selectbox("Modun Ne?", ["Tümü", "Tarih", "Gurme", "Doğa", "Macera"])

# --- ANA EKRAN ---

st.title("GeziStory Akışı")

# Yazar Paneli (FOTOĞRAF YÜKLEME EKLENDİ 📸)
if st.session_state.user_token:
    with st.expander("✍️ Yeni Bir Hikaye Yaz (Yazar Paneli)", expanded=True):
        st.write("GeziStory topluluğuna yeni bir keşif hediye et.")
        
        # Form işlemleri
        with st.form("hikaye_formu", clear_on_submit=True): 
            c1, c2 = st.columns(2)
            with c1:
                y_baslik = st.text_input("Başlık", placeholder="Örn: Balat'ta Gizli Teras")
                y_sehir = st.selectbox("Şehir", ["İstanbul", "İzmir", "Kapadokya", "Antalya", "Roma", "Paris"])
            with c2:
                y_mod = st.selectbox("Kategori", ["Tarih", "Gurme", "Doğa", "Macera"])
                # YENİ: Dosya Yükleyici
                y_dosya = st.file_uploader("Fotoğraf Yükle 📸", type=["jpg", "png", "jpeg"])
            
            y_ozet = st.text_area("Hikayen", placeholder="Buraya gitmelisiniz çünkü...")
            
            # Gönder butonu formun içinde olmalı
            submitted = st.form_submit_button("Hikayeyi Yayınla 🚀")
            
            if submitted:
                if not y_baslik or not y_ozet:
                    st.warning("Lütfen başlık ve hikaye kısımlarını doldur.")
                else:
                    # 1. Önce resmi yükleyelim (Eğer varsa)
                    final_resim_url = "https://via.placeholder.com/800x400?text=GeziStory" # Varsayılan
                    
                    if y_dosya is not None:
                        with st.spinner("Fotoğraf yükleniyor..."): # Dönme efekti
                            uploaded_url = upload_to_imgbb(y_dosya)
                            if uploaded_url:
                                final_resim_url = uploaded_url
                    
                    # 2. Sonra veriyi kaydedelim
                    new_story = {
                        "baslik": y_baslik, "sehir": y_sehir, "mod": y_mod,
                        "resim": final_resim_url,
                        "ozet": y_ozet, "yazar": st.session_state.user_email.split('@')[0]
                    }
                    
                    if fb.add_story(st.session_state.user_token, new_story):
                        st.success("Yayınlandı! Fotoğraf ve yazı buluta gönderildi.")
                        st.rerun()
                    else:
                        st.error("Bir sorun oluştu.")

# Hikayeleri Listeleme
st.divider()
st.subheader(f"🎒 {filter_city if filter_city != 'Tümü' else 'Dünya'} Günlükleri")

all_stories = fb.get_stories()

filtered_stories = []
for s in all_stories:
    city_match = (filter_city == "Tümü") or (s['sehir'] == filter_city)
    mode_match = (filter_mode == "Tümü") or (s['mod'] == filter_mode)
    if city_match and mode_match:
        filtered_stories.append(s)

if not filtered_stories:
    st.info("Henüz bu kategoride bir hikaye yok. İlk yazan sen ol! 👆")
else:
    cols = st.columns(3)
    for index, story in enumerate(filtered_stories):
        with cols[index % 3]:
            with st.container(border=True):
                # Resim varsa göster
                if story['resim']:
                    st.image(story['resim'], use_container_width=True)
                
                st.subheader(story['baslik'])
                st.caption(f"📍 {story['sehir']} | 🏷️ {story['mod']}")
                st.write(story['ozet'])
                st.caption(f"✍️ Yazar: {story['yazar']}")
                
                if st.button("Beğen ❤️", key=f"btn_{index}"):
                    st.toast("Beğenin gönderildi!")