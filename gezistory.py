import streamlit as st
import requests
import json
import time
import random
from datetime import datetime

# --- 1. AYARLAR ---
FIREBASE_API_KEY = "AIzaSyC3EMl5PW6g5dg9nw6OmJlBMe9gCHPqt24"
PROJECT_ID = "gezistory-app"
IMGBB_API_KEY = "ee85b5ea6763bbfa7faf74fa792874ab"
WEATHER_API_KEY = "4a3503250b73c46d3d44101e63777507" 

st.set_page_config(page_title="GeziStory", page_icon="🧿", layout="wide") # Layout wide yapıldı (Panel için)

# --- 2. HTML VE TASARIM YARDIMCILARI (ASKERİ DÜZEN) ---

def get_app_css():
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Lato', sans-serif; }
.nav-btn { width: 100%; padding: 15px; border-radius: 12px; text-align: center; cursor: pointer; transition: 0.3s; border: 1px solid #ddd; font-weight: bold; }
.discover-card { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 5px; background: white; border: 1px solid #f0f0f0; transition: transform 0.2s; cursor: pointer; }
.discover-card:hover { transform: translateY(-2px); }
.card-image-wrapper { position: relative; width: 100%; height: 220px; }
.card-img-main { width: 100%; height: 100%; object-fit: cover; }
.glass-tag { position: absolute; bottom: 10px; left: 10px; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(4px); padding: 5px 10px; border-radius: 20px; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); max-width: 90%; }
.mini-avatar { width: 24px; height: 24px; border-radius: 50%; border: 1px solid #ddd; }
.user-info-text { font-size: 11px; font-weight: bold; color: #333; line-height: 1.2; }
.location-text { font-size: 9px; color: #666; font-weight: normal; }
.category-badge { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.6); color: white; padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; backdrop-filter: blur(2px); }
.card-caption { padding: 10px 12px; font-size: 12px; color: #444; line-height: 1.4; border-top: 1px solid #f5f5f5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.comment-box { background: #f9f9f9; padding: 10px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #eee; }
.comment-user { font-weight: bold; font-size: 12px; color: #333; }
.comment-text { font-size: 13px; color: #555; }
.route-card-horizontal { display: flex; flex-direction: column; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #eee; margin-bottom: 30px; }
.route-header-collage { display: flex; height: 220px; width: 100%; position: relative; }
.collage-left { width: 60%; height: 100%; position: relative; }
.collage-right { width: 40%; height: 100%; display: flex; flex-direction: column; }
.collage-img-main { width: 100%; height: 100%; object-fit: cover; }
.collage-img-small { width: 100%; height: 50%; object-fit: cover; border-left: 2px solid white; }
.collage-img-small:first-child { border-bottom: 2px solid white; }
.route-header-single { position: relative; height: 200px; width: 100%; }
.route-overlay-info { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.5) 70%, transparent 100%); padding: 20px 15px 12px 15px; color: white; }
.route-title { font-size: 20px; font-weight: 800; margin-bottom: 6px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.route-meta { font-size: 12px; display: flex; gap: 15px; opacity: 0.95; align-items: center; }
.route-body { padding: 20px; }
.route-summary { font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 20px; }
.timeline-container { display: flex; align-items: flex-start; overflow-x: auto; padding-bottom: 10px; gap: 0px; }
.timeline-step { display: flex; align-items: center; flex-shrink: 0; }
.timeline-box { background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 8px 12px; min-width: 140px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 4px; transition: transform 0.2s; }
.timeline-box:hover { transform: scale(1.02); border-color: #1E81B0; background: #f0f7ff; }
.t-icon { font-size: 20px; }
.t-name { font-size: 12px; font-weight: bold; color: #333; }
.t-price { font-size: 10px; color: #666; background: #eee; padding: 2px 6px; border-radius: 4px; }
.timeline-arrow { color: #bbb; font-size: 18px; margin: 0 5px; display: flex; align-items: center; height: 100%; }
.route-card-summary { display: flex; flex-direction: column; height: 100%; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #eee; transition: transform 0.2s; }
.route-card-summary:hover { transform: translateY(-3px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }
.route-cover-small { width: 100%; height: 160px; object-fit: cover; }
.route-info-box { padding: 12px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
.route-title-small { font-size: 16px; font-weight: bold; color: #222; margin-bottom: 5px; line-height: 1.3; }
.route-meta-small { font-size: 11px; color: #666; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.route-badge { background: #e3f2fd; color: #1565c0; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
.coffee-btn-container { margin-top: 20px; padding-top: 15px; border-top: 1px dashed #ddd; text-align: center; }
.stButton button[kind="primary"] { background-color: #FFD700 !important; color: #333 !important; border: none !important; font-weight: bold !important; box-shadow: 0 4px 10px rgba(255, 215, 0, 0.4) !important; }
.stButton button[kind="primary"]:hover { background-color: #E6C200 !important; transform: scale(1.02); }
/* Rozet Stilleri */
.badge-admin { background: #000; color: #FFD700; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; border: 1px solid #FFD700; }
.badge-mod { background: #4a148c; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
.badge-gurme { background: #880e4f; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
.badge-elci { background: #f57f17; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
.badge-gezgin { background: #1565c0; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
.badge-caylak { background: #78909c; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
::placeholder { color: #ccc !important; opacity: 1; }
</style>"""

def get_badge_html(role):
    if role == 'admin': return '<span class="badge-admin">👑 Yönetici</span>'
    elif role == 'mod': return '<span class="badge-mod">🎩 Moderatör</span>'
    elif role == 'gurme': return '<span class="badge-gurme">🍷 Kültür Gurmesi</span>'
    elif role == 'elci': return '<span class="badge-elci">🏆 Kültür Elçisi</span>'
    elif role == 'gezgin': return '<span class="badge-gezgin">🎒 Gezgin</span>'
    else: return '<span class="badge-caylak">🐣 Çaylak</span>'

def get_discover_card_html(story):
    avatar_url = f"https://ui-avatars.com/api/?name={story['author']}&background=random&color=fff&size=64"
    category = story.get('category', 'Genel')
    cat_icons = {"Gurme": "🍽️", "Tarih": "🏛️", "Doğa": "🌲", "Mekan": "☕", "Manzara": "📸", "Genel": "🌍"}
    cat_icon = cat_icons.get(category, "🌍")
    return f"""<div class="discover-card">
<div class="card-image-wrapper">
<img src="{story['img']}" class="card-img-main">
<div class="category-badge">{cat_icon} {category}</div>
<div class="glass-tag">
<img src="{avatar_url}" class="mini-avatar">
<div>
<div class="user-info-text">{story['author']}</div>
<div class="location-text">📍 {story['city']}</div>
</div>
</div>
</div>
<div class="card-caption">
<b>{story['title']}:</b> {story['summary']}
</div>
</div>"""

def get_culture_badge_html():
    return "Scan <span style='background:#FFD700; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;'>🏆 Kültür Elçisi</span>"

def get_comment_html(comment):
    return f"""<div class="comment-box">
<div class="comment-user">{comment['user']}</div>
<div class="comment-text">{comment['text']}</div>
</div>"""

def get_route_card_html(story):
    images = story.get('images_list', [])
    if not images and story.get('img'): images = [story['img']] 
    header_html = ""
    if len(images) >= 3:
        header_html = f"""<div class="route-header-collage">
<div class="collage-left">
<img src="{images[0]}" class="collage-img-main">
<div class="route-overlay-info">
<div class="route-title">{story['title']}</div>
<div class="route-meta">
<span>📍 {story['city']}</span>
<span>👤 {story['author']}</span>
<span>💰 {story['budget']} TL</span>
</div>
</div>
</div>
<div class="collage-right">
<img src="{images[1]}" class="collage-img-small">
<img src="{images[2]}" class="collage-img-small">
</div>
</div>"""
    else:
        img_src = images[0] if images else "https://via.placeholder.com/400x200"
        header_html = f"""<div class="route-header-single">
<img src="{img_src}" class="collage-img-main">
<div class="route-overlay-info">
<div class="route-title">{story['title']}</div>
<div class="route-meta">
<span>📍 {story['city']}</span>
<span>👤 {story['author']}</span>
<span>💰 {story['budget']} TL</span>
</div>
</div>
</div>"""
    timeline_html = ""
    for idx, stop in enumerate(story['stops']):
        s_name = stop.get('place', 'Durak')
        s_price = stop.get('price', 0)
        s_type = stop.get('type', 'Gezilecek Yer') 
        icon_map = {"Tarih": "🏛️", "Yemek": "🍽️", "Manzara": "📸", "Kafe": "☕", "Doğa": "🌲", "Müze": "🖼️"}
        s_icon = icon_map.get(s_type, "📍")
        timeline_html += f"""<div class="timeline-step">
<div class="timeline-box">
<div class="t-icon">{s_icon}</div>
<div class="t-name">{s_name}</div>
<div class="t-price">{s_price} TL</div>
</div>
</div>"""
        if idx < len(story['stops']) - 1: timeline_html += """<div class="timeline-arrow">➝</div>"""
    return f"""<div class="route-card-horizontal">
{header_html}
<div class="route-body">
<div class="route-summary">{story['summary']}</div>
<div style="font-size:11px; font-weight:bold; color:#888; margin-bottom:10px; letter-spacing:1px;">ROTA DETAYLARI</div>
<div class="timeline-container">
{timeline_html}
</div>
</div>
</div>"""

def get_route_summary_card_html(story):
    images = story.get('images_list', [])
    img_src = images[0] if images else (story.get('img') or "https://via.placeholder.com/400x200")
    stop_count = len(story.get('stops', []))
    return f"""<div class="route-card-summary">
<img src="{img_src}" class="route-cover-small">
<div class="route-info-box">
<div>
<div class="route-title-small">{story['title']}</div>
<div class="route-meta-small">
<span>📍 {story['city']}</span>
<span class="route-badge">{stop_count} Durak</span>
</div>
</div>
<div class="route-meta-small" style="margin-bottom:0; border-top:1px solid #eee; padding-top:8px;">
<span>👤 {story['author']}</span>
<span style="font-weight:bold; color:#d9534f; font-size:10px;">💸 Tahmini Hasar: {story['budget']} TL</span>
</div>
</div>
</div>"""

def get_route_detail_timeline_html(stops):
    timeline_html = '<div class="timeline-container">'
    for idx, stop in enumerate(stops):
        s_name = stop.get('place', 'Durak')
        s_price = stop.get('price', 0)
        s_type = stop.get('type', 'Gezilecek Yer')
        icon_map = {"Tarih": "🏛️", "Yemek": "🍽️", "Manzara": "📸", "Kafe": "☕", "Doğa": "🌲", "Müze": "🖼️"}
        s_icon = icon_map.get(s_type, "📍")
        timeline_html += f"""<div class="timeline-step">
<div class="timeline-box">
<div class="t-icon">{s_icon}</div>
<div class="t-name">{s_name}</div>
<div class="t-price">{s_price} TL</div>
</div>
</div>"""
        if idx < len(stops) - 1: timeline_html += """<div class="timeline-arrow">➝</div>"""
    timeline_html += '</div>'
    return timeline_html

# --- 3. BACKEND SERVİSİ (LOGIC) ---
class FirebaseService:
    def __init__(self):
        self.auth_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        self.db_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

    def sign_in_anonymously(self):
        try:
            payload = {"returnSecureToken": True}
            r = requests.post(f"{self.auth_url}:signUp?key={FIREBASE_API_KEY}", json=payload)
            if 'idToken' in r.json(): return r.json()
            return None
        except: return None

    def sign_in(self, email, password):
        try:
            payload = {"email": email, "password": password, "returnSecureToken": True}
            r = requests.post(f"{self.auth_url}:signInWithPassword?key={FIREBASE_API_KEY}", json=payload)
            return r.json() if 'idToken' in r.json() else None
        except: return None

    def get_profile(self, uid):
        try:
            r = requests.get(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                f = r.json().get('fields', {})
                balance = int(f.get('wallet_balance', {}).get('integerValue', 0))
                earnings = int(f.get('earnings', {}).get('integerValue', 0))
                role = f.get('role', {}).get('stringValue', 'caylak') # Varsayılan: çaylak
                return {
                    "nick": f.get('nickname', {}).get('stringValue', 'Adsız'), 
                    "balance": balance,
                    "earnings": earnings,
                    "role": role
                }
        except: pass
        return {"nick": "Misafir", "balance": 0, "earnings": 0, "role": "misafir"}

    def get_all_users(self):
        try:
            # Not: Gerçek projede pagination lazım, şimdilik ilk 100
            r = requests.get(f"{self.db_url}/users?key={FIREBASE_API_KEY}&pageSize=100")
            if r.status_code != 200: return []
            users = []
            for doc in r.json().get('documents', []):
                f = doc.get('fields', {})
                uid = doc['name'].split('/')[-1]
                users.append({
                    "uid": uid,
                    "nick": f.get('nickname', {}).get('stringValue', 'Bilinmiyor'),
                    "email": f.get('email', {}).get('stringValue', '-'),
                    "role": f.get('role', {}).get('stringValue', 'caylak'),
                    "balance": int(f.get('wallet_balance', {}).get('integerValue', 0)),
                    "earnings": int(f.get('earnings', {}).get('integerValue', 0))
                })
            return users
        except: return []

    def update_user_role(self, uid, new_role):
        try:
            url = f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=role"
            payload = {"fields": {"role": {"stringValue": new_role}}}
            r = requests.patch(url, json=payload)
            return r.status_code == 200
        except: return False

    def delete_story(self, story_id):
        try:
            r = requests.delete(f"{self.db_url}/stories/{story_id}?key={FIREBASE_API_KEY}")
            return r.status_code == 200
        except: return False

    def add_story(self, data):
        stops_json = json.dumps(data['stops'])
        payload = {
            "fields": {
                "baslik": {"stringValue": data['title']},
                "sehir": {"stringValue": data['city']},
                "yazar": {"stringValue": data['author']},
                "resim": {"stringValue": data['img']},
                "ozet": {"stringValue": data['summary']},
                "kategori": {"stringValue": data['category']},
                "butce": {"integerValue": data['budget']},
                "stops": {"stringValue": stops_json},
                "uid": {"stringValue": data['uid']},
                "likes": {"arrayValue": {"values": []}},
                "comments": {"arrayValue": {"values": []}},
                "view_count": {"integerValue": 0},
                "date": {"timestampValue": datetime.utcnow().isoformat() + "Z"}
            }
        }
        requests.post(f"{self.db_url}/stories?key={FIREBASE_API_KEY}", json=payload)

    def get_stories(self):
        token_to_use = st.session_state.user_token if st.session_state.user_token else st.session_state.guest_token
        headers = {"Authorization": f"Bearer {token_to_use}"} if token_to_use else {}
        try:
            r = requests.get(f"{self.db_url}/stories?key={FIREBASE_API_KEY}", headers=headers)
            if r.status_code != 200 or 'documents' not in r.json(): return []
            stories = []
            for doc in r.json()['documents']:
                try:
                    f = doc.get('fields', {})
                    title = f.get('baslik', {}).get('stringValue', 'Başlıksız')
                    city = f.get('sehir', {}).get('stringValue', 'Bilinmiyor')
                    author = f.get('yazar', {}).get('stringValue', 'Anonim')
                    img = f.get('resim', {}).get('stringValue', 'https://via.placeholder.com/150')
                    summary = f.get('ozet', {}).get('stringValue', '')
                    category = f.get('kategori', {}).get('stringValue', 'Genel')
                    try: budget = int(f.get('butce', {}).get('integerValue', 0))
                    except: budget = 0
                    try: view_count = int(f.get('view_count', {}).get('integerValue', 0))
                    except: view_count = 0
                    stops_str = f.get('stops', {}).get('stringValue', '[]')
                    try: stops = json.loads(stops_str)
                    except: stops = []
                    likes_array = f.get('likes', {}).get('arrayValue', {}).get('values', [])
                    liked_uids = [x.get('stringValue') for x in likes_array]
                    comments_array = f.get('comments', {}).get('arrayValue', {}).get('values', [])
                    comments = []
                    for c in comments_array:
                        vals = c.get('mapValue', {}).get('fields', {})
                        comments.append({
                            "user": vals.get('user', {}).get('stringValue', 'Anonim'),
                            "text": vals.get('text', {}).get('stringValue', ''),
                            "date": vals.get('date', {}).get('stringValue', '')
                        })
                    liked_by_me = False
                    if st.session_state.user_uid and st.session_state.user_uid in liked_uids: liked_by_me = True
                    stories.append({
                        "id": doc['name'].split('/')[-1],
                        "title": title, "city": city, "author": author, "img": img,
                        "summary": summary, "category": category, "budget": budget,
                        "stops": stops, "uid": f.get('uid', {}).get('stringValue', ''),
                        "like_count": len(liked_uids), "liked_uids": liked_uids,
                        "liked_by_me": liked_by_me, "comments": comments,
                        "comment_count": len(comments), "view_count": view_count
                    })
                except: continue 
            return stories
        except: return []

    def update_interaction(self, story_id, action, current_likes=[], current_views=0, comment_data=None, current_comments=[]):
        doc_url = f"{self.db_url}/stories/{story_id}?key={FIREBASE_API_KEY}"
        update_data = {}
        update_mask = []
        if action == "like" and st.session_state.user_uid:
            user_id = st.session_state.user_uid
            new_likes = list(current_likes)
            if user_id in new_likes: new_likes.remove(user_id)
            else: new_likes.append(user_id)
            values_json = [{"stringValue": uid} for uid in new_likes]
            update_data["likes"] = {"arrayValue": {"values": values_json}}
            update_mask.append("likes")
        elif action == "view":
            new_views = current_views + 1
            update_data["view_count"] = {"integerValue": new_views}
            update_mask.append("view_count")
        elif action == "comment" and comment_data:
            new_comment_obj = { "mapValue": { "fields": { "user": {"stringValue": comment_data['user']}, "text": {"stringValue": comment_data['text']}, "date": {"stringValue": str(datetime.now())} } } }
            existing_comments_json = []
            for c in current_comments:
                existing_comments_json.append({ "mapValue": { "fields": { "user": {"stringValue": c['user']}, "text": {"stringValue": c['text']}, "date": {"stringValue": c['date']} } } })
            existing_comments_json.append(new_comment_obj)
            update_data["comments"] = {"arrayValue": {"values": existing_comments_json}}
            update_mask.append("comments")
        if update_data:
            params = [f"updateMask.fieldPaths={field}" for field in update_mask]
            query_string = "&".join(params)
            final_url = f"{doc_url}&{query_string}"
            payload = {"fields": update_data}
            requests.patch(final_url, json=payload)

    def send_tip(self, from_uid, to_uid, amount):
        try:
            user_doc = f"{self.db_url}/users/{from_uid}?key={FIREBASE_API_KEY}"
            r = requests.get(user_doc)
            current_balance = int(r.json().get('fields', {}).get('wallet_balance', {}).get('integerValue', 0))
            if current_balance < amount: return False, "Yetersiz Bakiye"
            new_balance = current_balance - amount
            requests.patch(user_doc, json={"fields": {"wallet_balance": {"integerValue": new_balance}}})
            commission = 7 
            net_earnings = amount - commission
            author_doc = f"{self.db_url}/users/{to_uid}?key={FIREBASE_API_KEY}"
            r_auth = requests.get(author_doc)
            current_earnings = int(r_auth.json().get('fields', {}).get('earnings', {}).get('integerValue', 0))
            new_earnings = current_earnings + net_earnings
            requests.patch(f"{author_doc}?updateMask.fieldPaths=earnings", json={"fields": {"earnings": {"integerValue": new_earnings}}})
            return True, "Başarılı"
        except Exception as e: return False, str(e)

    def get_weather(self, city):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=tr"
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                temp = int(data['main']['temp'])
                desc = data['weather'][0]['description'].capitalize()
                icon = data['weather'][0]['icon'] 
                return {"temp": temp, "desc": desc, "icon": icon}
        except: pass
        return None

def upload_to_imgbb(file):
    try:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY}
        files = {"image": file.getvalue()}
        response = requests.post(url, data=payload, files=files)
        if response.status_code == 200: return response.json()["data"]["url"]
    except: return None
    return None

# --- 4. SAYFA GÖRÜNÜMLERİ (VIEWS) ---

if hasattr(st, "dialog"): dialog_decorator = st.dialog
elif hasattr(st, "experimental_dialog"): dialog_decorator = st.experimental_dialog
else: dialog_decorator = None 

def render_comments_content(story, fb_service):
    st.markdown(f"**{story['title']}**")
    st.caption(f"✍️ {story['author']} | 📍 {story['city']}")
    st.write(story['summary'])
    st.divider()
    st.markdown("###### Yorumlar")
    if not story['comments']: st.info("Henüz yorum yapılmamış. İlk yorumu sen yap!")
    else:
        for c in story['comments']: st.markdown(get_comment_html(c), unsafe_allow_html=True)
    st.divider()
    if st.session_state.user_token:
        with st.form(f"comment_form_{story['id']}", clear_on_submit=True):
            new_comment = st.text_input("Yorumun:", placeholder="Düşüncelerini yaz...")
            if st.form_submit_button("Gönder"):
                if new_comment:
                    fb_service.update_interaction(story['id'], "comment", comment_data={"user": st.session_state.user_nick, "text": new_comment}, current_comments=story['comments'])
                    st.success("Yorum gönderildi!")
                    st.rerun()
    else: st.warning("Yorum yazmak için üye olmalısın.")

def render_route_detail_content(story, fb_service): 
    weather = fb_service.get_weather(story['city'])
    weather_html = ""
    if weather:
        icon_url = f"http://openweathermap.org/img/wn/{weather['icon']}.png"
        weather_html = f"""<span style="background:#e0f7fa; color:#006064; padding:4px 8px; border-radius:15px; font-size:12px; display:inline-flex; align-items:center; gap:5px; border:1px solid #b2ebf2;">
        <img src="{icon_url}" style="width:20px; height:20px;"> {weather['desc']} {weather['temp']}°C
        </span>"""
    images = story.get('images_list', [])
    if not images and story.get('img'): images = [story['img']]
    cols = st.columns(len(images)) if images else []
    for i, img_url in enumerate(images):
        if i < 3: cols[i].image(img_url, use_container_width=True)
    st.markdown(f"### {story['title']} {weather_html}", unsafe_allow_html=True)
    st.caption(f"📍 {story['city']} | 👤 {story['author']}")
    st.write(story['summary'])
    st.info(f"Hey gezgin, sıkı dur! Bu rotayı krallar gibi gezmek sana tahmini **{story['budget']} TL**'ye patlar. Ama anılara değer, değil mi? 😉")
    st.divider()
    st.markdown("##### 🗺️ Rota Planı")
    st.markdown(get_route_detail_timeline_html(story['stops']), unsafe_allow_html=True)
    st.divider()
    c_like, c_com, c_view = st.columns([1, 1, 1])
    like_icon = "❤️" if story.get('liked_by_me', False) else "🤍"
    if c_like.button(f"{like_icon} {story['like_count']}", key=f"d_lk_{story['id']}"):
        if st.session_state.user_token: fb_service.update_interaction(story['id'], "like", current_likes=story.get('liked_uids', [])); st.rerun()
        else: st.toast("Beğenmek için üye olmalısın!")
    c_com.button(f"💬 {story.get('comment_count', 0)}", key=f"d_cm_{story['id']}", disabled=True) 
    c_view.button(f"👁️ {story.get('view_count', 0)}", key=f"d_vw_{story['id']}", disabled=True)
    st.markdown('<div class="coffee-btn-container">', unsafe_allow_html=True)
    is_owner = st.session_state.user_uid == story['uid']
    if not is_owner:
        if st.button("☕ Yazara Bir Kahve Ismarla (20 TL)", type="primary", use_container_width=True, key=f"tip_{story['id']}"):
            if st.session_state.user_token:
                current_user_balance = st.session_state.get('user_balance', 0) 
                if current_user_balance >= 20:
                    success, msg = fb_service.send_tip(st.session_state.user_uid, story['uid'], 20)
                    if success: st.balloons(); st.success("Harikasın! Kahve ısmarlandı. ☕"); st.session_state.user_balance -= 20
                    else: st.error(f"İşlem başarısız: {msg}")
                else: st.warning("⚠️ Bakiyeniz yetersiz."); st.info("📱 Cüzdanına para yüklemek için lütfen mobil uygulamamızı kullan.")
            else: st.warning("Kahve ısmarlamak için giriş yapmalısın.")
    else: st.info("😏 Bu senin kendi rotan. Kendine kahve ısmarlayamazsın (ama fikir güzel).")
    st.markdown('</div>', unsafe_allow_html=True)

if dialog_decorator:
    @dialog_decorator("💬 Yorumlar")
    def view_comments_dialog(story, fb_service): render_comments_content(story, fb_service)
    @dialog_decorator("🗺️ Rota Detayları")
    def view_route_detail_dialog(story, fb_service): render_route_detail_content(story, fb_service)
else:
    def view_comments_dialog(story, fb_service): pass
    def view_route_detail_dialog(story, fb_service): pass

def render_create_route_section(fb_service):
    if 'new_route_stops' not in st.session_state: st.session_state.new_route_stops = []
    st.markdown("##### 📝 Rota Bilgileri")
    title = st.text_input("Rota Başlığı", placeholder="Örn: Kapadokya'da Balon Keyfi")
    c_city, c_cat = st.columns(2)
    city = c_city.selectbox("Şehir", ["İstanbul", "Ankara", "İzmir", "Nevşehir", "Antalya", "Mardin", "Rize", "Diğer"])
    category = c_cat.selectbox("Kategori", ["Tarih", "Doğa", "Yemek", "Manzara", "Müze", "Kafe"])
    img_file = st.file_uploader("Kapak Fotoğrafı (Zorunlu)", type=['jpg', 'jpeg', 'png'])
    summary = st.text_area("Özet / Hikaye", placeholder="Bu rota kimler için uygun? Neden gidilmeli?", max_chars=300)
    st.divider(); st.markdown("##### 📍 Duraklar (Timeline)")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    s_name = c1.text_input("Durak Adı", placeholder="Örn: Galata Kulesi")
    s_type = c2.selectbox("Tür", ["Tarih", "Yemek", "Manzara", "Kafe", "Doğa", "Müze"])
    s_price = c3.number_input("Harcama (TL)", min_value=0, step=10)
    if c4.button("Ekle", type="secondary", use_container_width=True):
        if s_name: st.session_state.new_route_stops.append({"place": s_name, "type": s_type, "price": s_price, "time": "00:00"}); st.rerun()
        else: st.toast("Lütfen durak adı girin.")
    if st.session_state.new_route_stops:
        st.markdown(get_route_detail_timeline_html(st.session_state.new_route_stops), unsafe_allow_html=True)
        total_budget = sum([s['price'] for s in st.session_state.new_route_stops])
        st.caption(f"💰 Toplam Tahmini Bütçe: **{total_budget} TL**")
        if st.button("Son Durağı Sil"): st.session_state.new_route_stops.pop(); st.rerun()
    st.divider()
    if st.button("Rotayı Yayınla", type="primary", use_container_width=True):
        if not img_file: st.error("Lütfen bir kapak fotoğrafı yükleyin.")
        elif not title or not summary: st.error("Lütfen başlık ve özet alanlarını doldurun.")
        elif len(st.session_state.new_route_stops) < 2: st.error("Bir rota en az 2 duraktan oluşmalıdır.")
        else:
            with st.spinner("Rota oluşturuluyor..."):
                img_url = upload_to_imgbb(img_file)
                if img_url:
                    total_budget = sum([s['price'] for s in st.session_state.new_route_stops])
                    fb_service.add_story({"title": title, "city": city, "img": img_url, "summary": summary, "category": category, "budget": total_budget, "stops": st.session_state.new_route_stops, "author": st.session_state.user_nick, "uid": st.session_state.user_uid})
                    st.session_state.new_route_stops = []
                    st.session_state.show_create_form = False 
                    st.success("Harika! Rota başarıyla yayınlandı. 🎉"); time.sleep(1.5); st.rerun()
                else: st.error("Resim yüklenirken hata oluştu.")

def render_add_post_section(fb_service):
    if st.session_state.user_token:
        with st.expander("➕ Yeni Hikaye Paylaş", expanded=False):
            with st.form("share_post_form", clear_on_submit=True):
                st.caption("Hikayeni Gezginlerle Paylaş")
                city = st.selectbox("Neredeydin?", ["İstanbul", "Ankara", "İzmir", "Nevşehir", "Antalya", "Mardin", "Rize", "Diğer"])
                img_file = st.file_uploader("Kapak Fotoğrafı (Zorunlu)", type=['jpg', 'jpeg', 'png'])
                title = st.text_input("Başlık", placeholder="Örn: Galata Kulesi veya Salaş Balıkçı...")
                summary = st.text_area("Notun", placeholder="Burada neler yaşadın? Fiyatlar nasıldı? İpuçları ver...", max_chars=150)
                category = st.radio("Kategori", ["Gurme", "Tarih", "Doğa", "Mekan", "Manzara"], horizontal=True)
                if st.form_submit_button("Paylaş"):
                    if not img_file or not title or not summary: st.error("Lütfen fotoğraf, başlık ve not alanlarını doldurun.")
                    else:
                        with st.spinner("Fotoğraf yükleniyor..."):
                            img_url = upload_to_imgbb(img_file)
                            if img_url:
                                fb_service.add_story({"title": title, "city": city, "img": img_url, "summary": summary, "category": category, "budget": 0, "stops": [], "author": st.session_state.user_nick, "uid": st.session_state.user_uid})
                                st.success("Hikayen paylaşıldı! 🎉"); time.sleep(1); st.rerun()
                            else: st.error("Resim yükleme hatası.")
    else:
        if st.button("➕ Yeni Hikaye Paylaş", use_container_width=True): st.toast("Post atmak için gezgin grubuna katılmalısın! 🎒")

def render_kesfet_page(stories, fb_service):
    render_add_post_section(fb_service)
    st.write(""); st.markdown("##### 🔥 Keşfet")
    if not stories: st.info("📭 Henüz hiç hikaye yok veya yüklenemedi. Yeni bir tane eklemeyi dene!")
    else:
        random_stories = list(stories)
        for i in range(0, len(random_stories), 3):
            cols = st.columns(3)
            batch = random_stories[i:i+3]
            for idx, col in enumerate(cols):
                if idx < len(batch):
                    story = batch[idx]
                    with col:
                        st.markdown(get_discover_card_html(story), unsafe_allow_html=True)
                        c1, c2, c3 = st.columns([1, 1, 1])
                        like_icon = "❤️" if story.get('liked_by_me', False) else "🤍"
                        if c1.button(f"{like_icon} {story['like_count']}", key=f"lk_{story['id']}"):
                            if st.session_state.user_token: fb_service.update_interaction(story['id'], "like", current_likes=story.get('liked_uids', [])); st.rerun()
                            else: st.toast("Beğenmek için üye olmalısın!")
                        if c2.button(f"💬 {story.get('comment_count', 0)}", key=f"cm_{story['id']}"):
                            fb_service.update_interaction(story['id'], "view", current_views=story.get('view_count', 0))
                            if dialog_decorator: view_comments_dialog(story, fb_service)
                            else: st.session_state[f"show_comments_{story['id']}"] = not st.session_state.get(f"show_comments_{story['id']}", False)
                        c3.button(f"👁️ {story.get('view_count', 0)}", key=f"vw_{story['id']}", disabled=True)
                        if not dialog_decorator and st.session_state.get(f"show_comments_{story['id']}", False):
                            with st.container(border=True): render_comments_content(story, fb_service)

def render_rotalar_page(stories, fb_service): 
    st.markdown("### 🏛️ Şehir Rehberleri")
    if st.session_state.user_token:
        if 'show_create_form' not in st.session_state: st.session_state.show_create_form = False
        if not st.session_state.show_create_form:
            if st.button("➕ Yeni Rota Ekle", use_container_width=True): st.session_state.show_create_form = True; st.rerun()
        else:
            if st.button("❌ Vazgeç", type="secondary"): st.session_state.show_create_form = False; st.rerun()
            with st.container(border=True): render_create_route_section(fb_service)
    st.divider()
    cities = ["Tümü"] + sorted(list(set([s['city'] for s in stories])))
    selected = st.selectbox("Şehir Seç", cities)
    real_routes = [s for s in stories if len(s['stops']) > 0]
    demo_route = {
        "id": "demo_rota_1", "title": "Tarihi Yarımada'da Bir Gün", "city": "İstanbul", "author": "Gezgin_Admin (Demo)", "budget": 450,
        "summary": "İstanbul'un kalbinde, tarihin ve lezzetin iç içe geçtiği muazzam bir yürüyüş rotası.",
        "images_list": ["https://i.ibb.co/Drq4qL5/ayasofya.jpg", "https://i.ibb.co/hXZx9Xg/sultanahmet-kofte.jpg", "https://i.ibb.co/ZL5J20z/gulhane.jpg"],
        "img": "https://i.ibb.co/Drq4qL5/ayasofya.jpg",
        "stops": [{"place": "Ayasofya Camii", "time": "09:00", "price": 0, "type": "Tarih"}, {"place": "Sultanahmet", "time": "11:00", "price": 0, "type": "Manzara"}, {"place": "Köfteci", "time": "13:00", "price": 350, "type": "Yemek"}, {"place": "Gülhane", "time": "15:00", "price": 0, "type": "Doğa"}, {"place": "Eminönü", "time": "17:00", "price": 100, "type": "Manzara"}],
        "uid": "demo_user_uid", "like_count": 128, "liked_by_me": False, "comment_count": 12, "view_count": 1024, "comments": [], "liked_uids": []
    }
    if selected == "Tümü" or selected == "İstanbul": real_routes.insert(0, demo_route)
    filtered = real_routes if selected == "Tümü" else [s for s in real_routes if s['city'] == selected]
    if not filtered: st.info("📍 Bu kriterlere uygun bir rota bulunamadı.")
    else:
        for i in range(0, len(filtered), 2):
            cols = st.columns(2)
            batch = filtered[i:i+2]
            for idx, col in enumerate(cols):
                if idx < len(batch):
                    route = batch[idx]
                    with col:
                        st.markdown(get_route_summary_card_html(route), unsafe_allow_html=True)
                        if st.button("🗺️ Rotayı İncele", key=f"rd_{route['id']}", use_container_width=True):
                            if dialog_decorator: view_route_detail_dialog(route, fb_service) 
                            else: st.write("Detaylar (Eski Sürüm):", route['stops'])

# --- 5. YÖNETİCİ PANELİ ---
def render_admin_panel(fb_service):
    st.header("👑 Yönetici Kontrol Merkezi")
    
    # 1. Kuş Bakışı
    users = fb_service.get_all_users()
    stories = fb_service.get_stories()
    
    # Kasadaki Para (Toplam Cüzdan Bakiyeleri - Simülasyon)
    total_money = sum([u['balance'] for u in users])
    total_earnings = sum([u['earnings'] for u in users])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Toplam Üye", len(users))
    col2.metric("📝 Toplam İçerik", len(stories))
    col3.metric("💰 Kullanıcı Bakiyeleri", f"{total_money} TL")
    col4.metric("📈 Dağıtılan Kazanç", f"{total_earnings} TL")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["👤 Kullanıcı Yönetimi", "🗑️ İçerik Yönetimi"])
    
    with tab1:
        st.subheader("Üye Listesi ve Rütbe Atama")
        for u in users:
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: st.write(f"**{u['nick']}** ({u['email']}) - {get_badge_html(u['role'])}", unsafe_allow_html=True)
            with c2:
                new_role = st.selectbox("Rütbe", ["caylak", "gezgin", "elci", "gurme", "mod", "admin"], index=["caylak", "gezgin", "elci", "gurme", "mod", "admin"].index(u['role']), key=f"role_{u['uid']}")
            with c3:
                if st.button("Güncelle", key=f"upd_{u['uid']}"):
                    if fb_service.update_user_role(u['uid'], new_role): st.success("Rütbe güncellendi!")
                    else: st.error("Hata")
    
    with tab2:
        st.subheader("Rota ve Post Silme")
        for s in stories:
            with st.expander(f"{s['title']} - {s['author']}"):
                st.write(s['summary'])
                if st.button("🚨 Bu İçeriği Sil", key=f"del_admin_{s['id']}"):
                    fb_service.delete_story(s['id'])
                    st.rerun()

def render_sidebar(fb_service):
    with st.sidebar:
        if not st.session_state.user_token:
            st.header("Giriş Yap"); l_mail = st.text_input("E-posta"); l_pass = st.text_input("Şifre", type="password")
            if st.button("Giriş", type="primary"):
                user = fb_service.sign_in(l_mail, l_pass)
                if user: 
                    st.session_state.user_token = user['idToken']
                    st.session_state.user_uid = user['localId']
                    prof = fb_service.get_profile(user['localId'])
                    st.session_state.user_nick = prof['nick']
                    st.session_state.user_balance = prof['balance']
                    st.session_state.user_role = prof.get('role', 'caylak')
                    st.rerun()
                else: st.error("Giriş başarısız.")
        else: 
            # Rozetli Karşılama
            user_role = st.session_state.get('user_role', 'caylak')
            st.markdown(f"Hoş geldin, **{st.session_state.user_nick}** {get_badge_html(user_role)}", unsafe_allow_html=True)
            
            balance = st.session_state.get('user_balance', 0)
            st.caption(f"💰 Cüzdan: {balance} TL")
            
            # ADMIN BUTONU (Sadece Admin Görür)
            if user_role == 'admin':
                if st.button("👑 Yönetici Paneli", use_container_width=True, type="primary"):
                    st.session_state.active_tab = "admin"
                    st.rerun()
            
            if st.button("Çıkış", type="secondary"): 
                st.session_state.user_token = None
                st.session_state.user_role = None
                st.rerun()

# --- 6. ANA UYGULAMA (MAIN) ---
def main():
    if 'user_token' not in st.session_state: st.session_state.user_token = None
    if 'active_tab' not in st.session_state: st.session_state.active_tab = "kesfet"
    if 'guest_token' not in st.session_state: st.session_state.guest_token = None
    if 'user_uid' not in st.session_state: st.session_state.user_uid = None
    if 'user_nick' not in st.session_state: st.session_state.user_nick = None
    if 'user_balance' not in st.session_state: st.session_state.user_balance = 0
    if 'user_role' not in st.session_state: st.session_state.user_role = 'caylak'

    st.markdown(get_app_css(), unsafe_allow_html=True)
    fb = FirebaseService()
    
    if not st.session_state.user_token and not st.session_state.guest_token:
        guest_user = fb.sign_in_anonymously()
        if guest_user: st.session_state.guest_token = guest_user['idToken']; st.rerun()
    
    c1, c2 = st.columns([3, 1]); c1.markdown("### 🧿 GeziStory")
    col1, col2 = st.columns(2)
    
    # Navigasyon Butonları (Admin panelindeyken de çalışsın)
    btn_type_kesfet = "primary" if st.session_state.active_tab == "kesfet" else "secondary"
    btn_type_rotalar = "primary" if st.session_state.active_tab == "rotalar" else "secondary"
    
    if col1.button("🎲 KEŞFET", type=btn_type_kesfet, use_container_width=True): st.session_state.active_tab = "kesfet"; st.rerun()
    if col2.button("🗺️ ROTALAR", type=btn_type_rotalar, use_container_width=True): st.session_state.active_tab = "rotalar"; st.rerun()
        
    stories = fb.get_stories()
    
    # Sayfa Yönlendirme
    if st.session_state.active_tab == "kesfet": render_kesfet_page(stories, fb)
    elif st.session_state.active_tab == "rotalar": render_rotalar_page(stories, fb)
    elif st.session_state.active_tab == "admin": render_admin_panel(fb) # Admin Sayfası
    
    render_sidebar(fb)

if __name__ == "__main__":
    main()