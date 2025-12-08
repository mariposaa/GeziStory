import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
import time
import random

from datetime import datetime, timedelta

import html

try: from streamlit_js_eval import get_geolocation
except: get_geolocation = None

# --- OTOMATİK KONUM TESPİTİ ---
# --- KOORDİNAT İLE ŞEHİR BULMA ---
# --- IP İLE KONUM TESPİTİ (YEDEK) ---
def get_city_from_coordinates(lat, lon):
    try:
        headers = {"User-Agent": "GeziStoryApp/1.0"}
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            address = data.get("address", {})
            # Şehir bilgisini farklı alanlardan arayalım (city, province, state)
            city = address.get("province") or address.get("city") or address.get("state") or ""
            
            # Türkçe Karakter Mapping
            mapping = {"Istanbul": "İstanbul", "Izmir": "İzmir", "Canakkale": "Çanakkale", "Usak": "Uşak", "Kirsehir": "Kırşehir", "Sanliurfa": "Şanlıurfa", "Diyarbakir": "Diyarbakır", "Eskisehir": "Eskişehir", "Mugla": "Muğla", "Nevsehir": "Nevşehir", "Nigde": "Niğde", "Gumushane": "Gümüşhane", "Kutahya": "Kütahya", "Balikesir": "Balıkesir", "Agri": "Ağrı", "Bingol": "Bingöl", "Cankiri": "Çankırı", "Corum": "Çorum", "Elazig": "Elazığ", "Igdir": "Iğdır", "Kahramanmaras": "Kahramanmaraş", "Kirikkale": "Kırıkkale", "Kirklareli": "Kırklareli", "Tekirdag": "Tekirdağ", "Zonguldak": "Zonguldak"}
            return mapping.get(city, city)
        return None
    except: return None



# --- 1. AYARLAR VE SABİTLER ---
st.set_page_config(page_title="GeziStory", page_icon="🧿", layout="wide")

# --- BAKIM MODU ---
MAINTENANCE_MODE = True

if MAINTENANCE_MODE:
    st.markdown("""
        <style>
        .maintenance-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 80vh;
            text-align: center;
            font-family: 'Helvetica Neue', sans-serif;
            color: #2C3E50;
        }
        .maintenance-icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
        .maintenance-text {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .maintenance-subtext {
            font-size: 18px;
            color: #7F8C8D;
        }
        </style>
        <div class="maintenance-container">
            <div class="maintenance-icon">🛠️</div>
            <div class="maintenance-text">Bakımdayız ama merak etme yakında geliyoruz</div>
            <div class="maintenance-subtext">Daha iyi bir deneyim için çalışıyoruz. Lütfen daha sonra tekrar deneyin.</div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# GÜVENLİK PROTOKOLÜ: Secrets Yönetimi
FIREBASE_API_KEY = st.secrets["general"]["FIREBASE_API_KEY"]
IMGBB_API_KEY = st.secrets["general"]["IMGBB_API_KEY"]
PROJECT_ID = st.secrets["general"]["PROJECT_ID"]

MAP_BANNER_URL = "https://i.ibb.co/KpKykTMf/Gemini-Generated-mage-4zpeqj4zp.png"
SHOPIER_LINK_REKLAM = "https://www.shopier.com/gezistory/41968453"
# SHOPIER_LINK_BAGIS (Kaldırıldı)
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
FULL_81_CITY_GUIDE = {
    "Adana": {"yemek": "Adana Kebap, Şalgam, Bıcı Bıcı, Muzlu Süt", "butce": "Uygun-Orta", "tuyo": "Kebabın yanında gelen salatalara para verme, onlar ikramdır! Şalgamı acılı iç, 'acısız' dersen turist muamelesi görürsün."},
    "Adıyaman": {"yemek": "Çiğ Köfte (Etsiz), Tavuklu Pilav", "butce": "Uygun", "tuyo": "Çiğ köfteyi tavana atınca yapışıyorsa olmuştur. Acısı sonradan çıkar, hazırlıklı ol."},
    "Afyonkarahisar": {"yemek": "Sucuk Döner, Kaymak, Lokum", "butce": "Orta", "tuyo": "Kaymağı ekmek kadayıfının üzerine koymadan yeme. Sucuğu döner olarak dene, pişman olmazsın."},
    "Ağrı": {"yemek": "Abdigör Köftesi", "butce": "Uygun", "tuyo": "Abdigör köftesi Türkiye'nin en eski diyet yemeğidir, yağsızdır. İshak Paşa Sarayı manzarasında çay içmeden dönme."},
    "Amasya": {"yemek": "Amasya Elması, Keşkek, Bakla Dolması", "butce": "Uygun", "tuyo": "Elmayı kütür kütür ye. Şehzadeler yolunda yürürken kendini padişah gibi hissetmek serbest."},
    "Ankara": {"yemek": "Ankara Döneri, Aspava (SSK), Ankara Tava", "butce": "Orta", "tuyo": "Aspava'da 'Dürüm' değil 'SSK' (Soslu Soğanlı Kaşarlı) denir. Yemek bitince gelen ikramları reddetme, hakarettir."},
    "Antalya": {"yemek": "Piyaz (Tahinli), Şiş Köfte, Yanık Dondurma", "butce": "Orta-Yüksek", "tuyo": "Piyazın tahinli olması seni şaşırtmasın, asıl olay o. Yanık dondurma bozuk değildir, tadı öyledir."},
    "Artvin": {"yemek": "Laz Böreği, Karalahana Sarması, Mısır Ekmeği", "butce": "Orta", "tuyo": "Laz böreği tatlıdır, tuzlu sanıp ayran isteme. Yollar virajlıdır, midene güvenmiyorsan tıka basa yeme."},
    "Aydın": {"yemek": "Çöp Şiş, İncir, Paşa Böreği", "butce": "Orta", "tuyo": "Çöp şiş Ortaklar'da yenir. İncirin en iyisi buradadır, eve dönerken mutlaka al."},
    "Balıkesir": {"yemek": "Höşmerim, Susurluk Tostu, Ayran", "butce": "Orta", "tuyo": "Tostun yanındaki ayranın köpüğüyle bıyık yapmak zorunludur. Höşmerim sıcak yenir."},
    "Bilecik": {"yemek": "Bozcaarmut Helvası, Bıldırcın Kebabı", "butce": "Uygun", "tuyo": "Osmanlı'nın kurulduğu yerdesin, çınarların altında bir Osmanlı Şerbeti iç."},
    "Bingöl": {"yemek": "Sorina Pel, Mastuva", "butce": "Uygun", "tuyo": "Balın hası buradadır. Kahvaltıda bal-kaymak yemeden güne başlama."},
    "Bitlis": {"yemek": "Büryan Kebabı, Avşor Çorbası", "butce": "Orta", "tuyo": "Büryan uykudan feragat ister, sabah 05:00'te gidersen en iyisini yersin. Öğlene kalmaz."},
    "Bolu": {"yemek": "Mengen Pilavı, Abant Kebabı", "butce": "Orta-Yüksek", "tuyo": "Aşçıların başkenti. Yol üstü tesislerde bile yemekler gurme seviyesindedir, çekinme dal."},
    "Burdur": {"yemek": "Burdur Şiş, Ceviz Ezmesi", "butce": "Uygun", "tuyo": "Burdur Şiş, Adana'ya benzemez; daha kısadır ama lezzeti büyüktür. Ceviz ezmesini hediyelik al."},
    "Bursa": {"yemek": "İskender, Pideli Köfte, Kestane Şekeri", "butce": "Yüksek", "tuyo": "İskender'in üzerine tereyağı dökülürken 'Yeter' deme, şovun parçası o. Pideli köfte öğrenci dostu İskender'dir."},
    "Çanakkale": {"yemek": "Peynir Helvası, Ezine Peyniri, Sardalya", "butce": "Orta", "tuyo": "Peynir helvasını fırınlanmış iste. Sardalya mevsimiyse mangal yapmadan dönmek yasak."},
    "Çankırı": {"yemek": "Yaren Güveci, Yumurta Tatlısı", "butce": "Uygun", "tuyo": "Tuz mağarasını gezdiysen bol su iç. Yaren gecesine denk gelirsen kaçırma."},
    "Çorum": {"yemek": "Çorum Leblebisi, İskilip Dolması", "butce": "Uygun", "tuyo": "İskilip Dolması bir dolma değil, dev bir pilav ritüelidir. Leblebiyi taze kavrulmuş al."},
    "Denizli": {"yemek": "Denizli Kebabı (Fırın), Zafer Gazozu", "butce": "Orta", "tuyo": "Kebap elle yenir, çatal bıçak istersen garson sana tuhaf bakar. Yanına Zafer Gazozu açtır."},
    "Diyarbakır": {"yemek": "Ciğer, Karpuz, Kaburga Dolması", "butce": "Orta", "tuyo": "Burada ciğer sabah kahvaltısında yenir. Sabah 6'da ciğerci doluysa şaşırma, otur ve dürümü göm."},
    "Edirne": {"yemek": "Tava Ciğeri, Badem Ezmesi", "butce": "Orta", "tuyo": "Ciğerin yanındaki kurutulmuş biber acıdır, gaza gelip hepsini atma. 'H' harfini çok kullanma :)"},
    "Elazığ": {"yemek": "Gakgoş Döneri, Harput Köfte, Orcik", "butce": "Uygun", "tuyo": "Orcik (cevizli sucuk) almadan dönme. Harput kalesine çıkıp şehre tepeden bak."},
    "Erzincan": {"yemek": "Erzincan Döneri, Tulum Peyniri", "butce": "Uygun", "tuyo": "Döneri yaprak gibidir, ısırmadan yutulur. Tulum peynirini sıcak lavaşa sar."},
    "Erzurum": {"yemek": "Cağ Kebabı, Kadayıf Dolması", "butce": "Orta", "tuyo": "Cağ kebabı şişle gelir, sen 'Tamam' diyene kadar garson getirmeye devam eder. Dikkat et, rekor kırma."},
    "Eskişehir": {"yemek": "Çibörek, Met Helvası, Balaban Kebap", "butce": "Uygun-Orta", "tuyo": "Çibörek (Çiğbörek değil) ilk ısırıkta içindeki suyu üstüne akıtır, dikkatli ol. Porsuk kenarında çekirdek çitle."},
    "Gaziantep": {"yemek": "Beyran, Katmer, Baklava, Ali Nazik", "butce": "Orta-Yüksek", "tuyo": "Beyran çorba değil, ana yemektir ve sabah içilir. Baklavayı ters çevirip damağına yapıştırarak ye."},
    "Giresun": {"yemek": "Giresun Pidesi, Fındık Ezmesi", "butce": "Orta", "tuyo": "Pidenin kenarını koparıp ortasındaki yumurtaya banmak bir sanattır. Fındığı avuçla ye."},
    "Gümüşhane": {"yemek": "Pestil, Köme, Siron", "butce": "Uygun", "tuyo": "Pestil ve köme enerji deposudur, fazla kaçırma yerinde duramazsın."},
    "Hakkari": {"yemek": "Doğaba, Yüksekova Kebabı", "butce": "Uygun", "tuyo": "Buranın balı ve cevizi ilaç gibidir. Ters lale görürsen koparma, cezası var!"},
    "Hatay": {"yemek": "Künefe, Tepsi Kebabı, Humus", "butce": "Uygun", "tuyo": "Künefeyi yemekten sonra sıcak sıcak ye. Peyniri sünmüyorsa o künefe değildir. Meze masasına gömül."},
    "Isparta": {"yemek": "Isparta Kebabı, Gül Reçeli", "butce": "Orta", "tuyo": "Her şeyin içinde gül olabilir (lokum, reçel, sabun). Kebabı fırın kebabıdır, tandır gibi dağılır."},
    "Mersin": {"yemek": "Tantuni, Cezerye, Kerebiç", "butce": "Uygun", "tuyo": "Tantuniye limon sıkılır. Eğer 'Biftek' tantuni yiyorsan gerçek Mersin deneyimi yaşamıyorsundur, yağlısını iste."},
    "İstanbul": {"yemek": "Sultanahmet Köftesi, Balık Ekmek, Islak Hamburger", "butce": "Değişken", "tuyo": "Eminönü'nde balık ekmek yerken martılara dikkat et, ekmeği çalabilirler. Taksim'de gece sonu ıslak hamburger racondur."},
    "İzmir": {"yemek": "Boyoz, Kumru, Söğüş, İzmir Bombası", "butce": "Orta", "tuyo": "Simite 'Gevrek', çekirdeğe 'Çiğdem' de. Boyozu haşlanmış yumurtasız yeme. Söğüş seviyorsan beynine iyi bak."},
    "Kars": {"yemek": "Kaz Eti, Kars Kaşarı, Umaç Helvası", "butce": "Orta", "tuyo": "Kaz eti kışın yenir, kar yememiş kazın tadı olmaz. Peynir alırken 'Eski Kaşar'ı sor."},
    "Kastamonu": {"yemek": "Etli Ekmek, Pastırma, Çekme Helva", "butce": "Uygun", "tuyo": "Etli ekmek Konya'nınkiyle karışmasın, bu kapalıdır. Sarımsağı efsanedir."},
    "Kayseri": {"yemek": "Mantı, Pastırma, Sucuk Ekmek, Yağlama", "butce": "Orta", "tuyo": "Bir kaşığa 40 mantı sığmıyorsa o Kayseri mantısı değildir. Yağlamayı katlayıp yoğurda banarak ye."},
    "Kırklareli": {"yemek": "Kırklareli Köftesi, Hardaliye", "butce": "Orta", "tuyo": "Hardaliye alkolsüz üzüm içeceğidir, Atatürk'ün favorisidir. Tadına bakmadan geçme."},
    "Kırşehir": {"yemek": "Ahi Pilavı, Cemele Biberi", "butce": "Uygun", "tuyo": "Neşet Ertaş dinlemeden, Ahi Evran'ı ziyaret etmeden gezmiş sayılmazsın."},
    "Kocaeli": {"yemek": "Pişmaniye, Değirmendere Fındığı", "butce": "Orta", "tuyo": "Pişmaniyeyi yerken üstüne dökmemek imkansızdır, kasma. İzmit simidi pekmezlidir, çıtirdır."},
    "Konya": {"yemek": "Etli Ekmek, Fırın Kebabı, Mevlana Şekeri", "butce": "Uygun", "tuyo": "Etli ekmeğe asla 'Pide' deme, çok bozulurlar. Elle ye, çatal bıçak kullanma."},
    "Kütahya": {"yemek": "Cimcik Mantı, Sini Mantısı", "butce": "Uygun", "tuyo": "Porselen diyarıdır, hediyelik bakabilirsin. Cimcik mantı miniciktir, sabır işidir."},
    "Malatya": {"yemek": "Kayısı (Her Hali), Kağıt Kebabı", "butce": "Orta", "tuyo": "Kayısının 100 farklı çeşidini bulabilirsin. Gün kurusu ye, sindirime dosttur."},
    "Manisa": {"yemek": "Manisa Kebabı, Mesir Macunu", "butce": "Orta", "tuyo": "Mesir macunu şifalıdır ama fazla yeme, enerjisi tavan yaptırır. Kebabı pideli ve yoğurtludur."},
    "Kahramanmaraş": {"yemek": "Dondurma, Eli Böğründe", "butce": "Uygun", "tuyo": "Dondurmayı çatal bıçakla keserek yersin. Eli Böğründe tepsisini fırından sıcak sıcak al."},
    "Mardin": {"yemek": "Kaburga Dolması, Sembusek, Mırra", "butce": "Orta-Yüksek", "tuyo": "Mırra (acı kahve) içince fincanı sakın masaya koyma! Koyarsan ya fincanı dolduranla evlenirsin ya da bahşiş verirsin."},
    "Muğla": {"yemek": "Çökertme Kebabı, Muğla Köftesi", "butce": "Yüksek (Yazın)", "tuyo": "Turistik yerlerde fiyat sorarak otur. Çökertme kebabının patatesleri çıtır olmalı."},
    "Muş": {"yemek": "Muş Köftesi, Çorti Aşı", "butce": "Uygun", "tuyo": "Kışın gidiyorsan sıkı giyin. Çorti aşı (lahana turşusu yemeği) içini ısıtır."},
    "Nevşehir": {"yemek": "Testi Kebabı, Kabak Çekirdeği", "butce": "Orta-Yüksek", "tuyo": "Testiyi kırmak için şov yapma, garsona bırak. Balona binemiyorsan sabah erken kalkıp izle."},
    "Niğde": {"yemek": "Niğde Tavası, Bor Söğüşü", "butce": "Uygun", "tuyo": "Niğde gazozu efsanedir, market gazozlarına benzemez. Tavasını mutlaka dene."},
    "Ordu": {"yemek": "Ordu Tostu, Pancar Çorbası, Pide", "butce": "Uygun", "tuyo": "Tostu büyüktür, ezilerek yapılır. Boztepe'ye teleferikle çıkıp manzaraya karşı çay iç."},
    "Rize": {"yemek": "Mıhlama, Laz Böreği, Rize Simidi", "butce": "Orta", "tuyo": "Mıhlama uzuyorsa gerçektir. Çayı ince belli bardakta iç, kupa bardak isteme."},
    "Sakarya": {"yemek": "Islama Köfte, Kabak Tatlısı", "butce": "Orta", "tuyo": "Köftenin yanındaki ekmekler kemik suyuyla ıslatılmıştır, asıl lezzet oradadır. Kabak tatlısını cevizli ye."},
    "Samsun": {"yemek": "Samsun Pidesi (Bafra/Terme), Nokul", "butce": "Orta", "tuyo": "Bafra pidesi kapalıdır, Terme açıktır. Tarafını seç. Pazar kahvaltısında pide yemek adettir."},
    "Siirt": {"yemek": "Büryan Kebabı, Perde Pilavı", "butce": "Orta", "tuyo": "Büryan kuyu kebabıdır. Perde pilavının şekli fes gibidir, misafire verilen değeri gösterir."},
    "Sinop": {"yemek": "Sinop Mantısı, Nokul", "butce": "Orta", "tuyo": "Mantısı yarısı cevizli yarısı yoğurtlu yenir, 'karışık' iste. Türkiye'nin en mutlu şehrindesin, gülümse."},
    "Sivas": {"yemek": "Sivas Köftesi, Peskutan Çorbası, Kelle", "butce": "Uygun", "tuyo": "Kahvaltıda Kelle yenir mi deme, burada yenir. Sivas köftesinde sadece et ve tuz vardır, baharat arama."},
    "Tekirdağ": {"yemek": "Tekirdağ Köftesi, Peynir Helvası", "butce": "Orta", "tuyo": "Köftenin yanındaki kırmızı sos (acı sos) efsanedir. Rakoczi müzesini gez."},
    "Tokat": {"yemek": "Tokat Kebabı, Bat", "butce": "Orta", "tuyo": "Tokat kebabında et kadar sebzeler (patlıcan, sarımsak) de lezzetlidir. Bat yemeği soğuk yenir, şaşırma."},
    "Trabzon": {"yemek": "Kuymak, Akçaabat Köfte, Hamsiköy Sütlacı", "butce": "Orta", "tuyo": "Kuymak çatalla değil, ekmek banarak yenir. Sütlacı Hamsiköy'de yersen üzerine fındık döktür."},
    "Tunceli": {"yemek": "Zerefet (Babiko), Şir", "butce": "Uygun", "tuyo": "Doğası muazzamdır. Munzur suyundan iç, efsaneye göre şifalıdır."},
    "Şanlıurfa": {"yemek": "Ciğer, Lahmacun, Şıllık Tatlısı", "butce": "Uygun", "tuyo": "Acı (İsot) burada hayat tarzıdır. 'Acısız' lahmacun istersen garipserler. Sıra gecesine katıl."},
    "Uşak": {"yemek": "Tarhana Çorbası, Demir Tatlısı", "butce": "Uygun", "tuyo": "Tarhananın anavatanındasın. Sabah kahvaltısında bile çorba içilebilir."},
    "Van": {"yemek": "Van Kahvaltısı, Otlu Peynir", "butce": "Orta", "tuyo": "Kahvaltıda 30 çeşit gelir, hepsini bitirmeye çalışma. Otlu peynirin kokusu keskindir ama tadı efsanedir."},
    "Yozgat": {"yemek": "Arabaşı, Testi Kebabı", "butce": "Uygun", "tuyo": "Arabaşı çorbası değil, hamurudur. Hamuru çiğnemeden yutman lazım, yoksa gülerler."},
    "Zonguldak": {"yemek": "Uğmaç Çorbası, Malay", "butce": "Uygun", "tuyo": "Maden şehrindesin. Gökgöl mağarasını gezmeden gitme."},
    "Aksaray": {"yemek": "Aksaray Tava", "butce": "Orta", "tuyo": "Ihlara Vadisi'nde yürüyüş yapmadan yemeği hak edemezsin."},
    "Bayburt": {"yemek": "Bayburt Döneri, Tel Helva", "butce": "Uygun", "tuyo": "Sakin bir şehirdir. Döneri yerken etin tadını alırsın, sosla boğmazlar."},
    "Karaman": {"yemek": "Arabaşı, Batırık", "butce": "Uygun", "tuyo": "Batırık, kısırın sulandırılmış hali gibidir ama tadı çok başkadır. Denemeden ön yargılı olma."},
    "Kırıkkale": {"yemek": "Keskin Tava", "butce": "Uygun", "tuyo": "Ankara'ya yakındır ama tavası kendine hastır. Silah müzesini gezebilirsin."},
    "Batman": {"yemek": "Batman Usulü Mumbar, Şam Böreği", "butce": "Uygun", "tuyo": "Petrol şehrindesin. Tandır ekmeği sıcaksa kaçırma."},
    "Şırnak": {"yemek": "Perde Pilavı, Suryaz", "butce": "Uygun", "tuyo": "Cudi dağı manzarasına karşı çay iç. Misafirperverlik üst düzeydir."},
    "Bartın": {"yemek": "Amasra Salatası, Balık", "butce": "Orta", "tuyo": "Salatanın içinde en az 20 çeşit malzeme vardır. Balıktan önce salatayla doyma."},
    "Ardahan": {"yemek": "Kaz Eti, Feselli", "butce": "Orta", "tuyo": "Kışın çok soğuktur, kaz eti yiyerek ısınırsın. Balı Kafkas arıları yapar, çok değerlidir."},
    "Iğdır": {"yemek": "Bozbaş, Taş Köfte", "butce": "Uygun", "tuyo": "Bozbaş (Piti) nohutlu ve etli özel bir yemektir. Kayısı burada da meşhurdur."},
    "Yalova": {"yemek": "Yalova Sütlüsü, Termal Çorbası", "butce": "Orta", "tuyo": "Termal otellerde gevşedikten sonra sütlü tatlısını göm."},
    "Karabük": {"yemek": "Safranbolu Bükmesi, Lokum", "butce": "Orta", "tuyo": "Safranbolu evlerini gezerken sokaklar dar, topuklu giyme. Lokumun safranlısını dene."},
    "Kilis": {"yemek": "Kilis Tava, Cennet Çamuru", "butce": "Uygun", "tuyo": "Kilis Tava'nın altına patlıcan döşenir. Cennet çamuru (kaymaklı kadayıf) adının hakkını verir."},
    "Osmaniye": {"yemek": "Osmaniye Simidi, Zorkun Tavası", "butce": "Uygun", "tuyo": "Yer fıstığı her yerdedir, tazesini al. Yayla havası almadan dönme."},
    "Düzce": {"yemek": "Akçakoca Melengüçceği, Hamsili Pilav", "butce": "Orta", "tuyo": "Hem deniz hem doğa var. Şelaleleri gezdikten sonra alabalık ye."}
}

# --- STANDART YASAL METİNLER (AVUKAT GÖZDEN GEÇİRMELİDİR) ---
LEGAL_TEXT_KVKK = """
### KULLANICI SÖZLEŞMESİ VE GİZLİLİK POLİTİKASI

**1. TARAFLAR**
Bu sözleşme, GeziStory platformu ("Platform") ile Platform'a üye olan kullanıcı ("Üye") arasında akdedilmiştir.

**2. KONU**
İşbu sözleşmenin konusu, Üye'nin Platform'dan faydalanma şartlarının ve tarafların hak ve yükümlülüklerinin belirlenmesidir.

**3. ÜYELİK VE HİZMET KULLANIMI**
*   Üye, kayıt olurken verdiği bilgilerin doğru olduğunu taahhüt eder.
*   Platform, içerik paylaşımı, yorum yapma ve topluluk özelliklerini sunar.
*   Üye, Platform üzerinde suç teşkil eden, telif hakkı ihlali içeren veya genel ahlaka aykırı paylaşım yapamaz.
*   Platform, yasal zorunluluklar veya güvenlik ihlalleri durumunda üyeliği askıya alma hakkına sahiptir.

**4. GİZLİLİK VE KVKK (KİŞİSEL VERİLERİN KORUNMASI)**
*   **Veri Sorumlusu:** GeziStory Platformu.
*   **İşlenen Veriler:** Ad, soyad, e-posta adresi, profil fotoğrafı, IP adresi ve paylaşım içerikleri.
*   **İşleme Amacı:** Hizmetin sunulması, güvenliğin sağlanması, kullanıcı deneyiminin iyileştirilmesi ve yasal yükümlülüklerin yerine getirilmesi.
*   **Veri Aktarımı:** Kişisel verileriniz, yasal zorunluluklar dışında üçüncü kişilerle paylaşılmaz.
*   **Haklarınız:** KVKK 11. madde uyarınca verilerinizin işlenip işlenmediğini öğrenme, düzeltme ve silme talep etme hakkına sahipsiniz.

**5. ONAY**
Üye, kayıt formunu doldurarak ve ilgili kutucuğu işaretleyerek bu sözleşmeyi okuduğunu, anladığını ve kabul ettiğini beyan eder.

**6. ÇEREZ (COOKIE) POLİTİKASI**
*   **Çerez Nedir?** Platform'un doğru çalışması ve kullanıcı deneyiminin iyileştirilmesi amacıyla cihazınıza yerleştirilen küçük metin dosyalarıdır.
*   **Kullanım Amacı:** Oturum açma bilgilerinizi hatırlamak, site trafiğini analiz etmek ve size uygun reklamlar (Google AdSense) sunmak.
*   **Reklam Çerezleri:** Google dahil üçüncü taraf sağlayıcılar, kullanıcının web sitemize yaptığı önceki ziyaretlere dayalı olarak reklam sunmak için çerezleri kullanır.
*   **Kontrol:** Tarayıcı ayarlarınızdan çerezleri dilediğiniz zaman silebilir veya engelleyebilirsiniz. Ancak bu durumda Platform'un bazı özellikleri çalışmayabilir.
"""

GUILDS = {
    "kasifler": {"name": "Zirveye Yürüyenler", "icon": "🧗", "desc": "Zirvelerin hakimi, en yükseği hedefleyen dağcılar."},
    "gurmeler": {"name": "Gurmeler Meclisi", "icon": "🍽️", "desc": "Damak tadına düşkün, en iyi lezzetleri bulanlar."},
    "tarihciler": {"name": "Tarihçiler Cemiyeti", "icon": "📜", "desc": "Geçmişin izlerini sürenler, hikayeleri yaşatanlar."},
    "dogaseverler": {"name": "Doğa Bekçileri", "icon": "🌲", "desc": "Yeşili ve maviyi koruyan, doğayla iç içe olanlar."}
}

RANK_SYSTEM = {
    "caylak": {"min": 0, "label": "Çaylak", "color": "#95A5A6"},
    "gezgin": {"min": 250, "label": "Gezgin", "color": "#3498DB"},
    "kultur_elcisi": {"min": 1000, "label": "Kültür Elçisi", "color": "#9B59B6"},
    "evliya_celebi": {"min": 5000, "label": "Evliya Çelebi", "color": "#F1C40F"},
    "admin": {"min": 0, "label": "Yönetici", "color": "#E74C3C"},
    "mod": {"min": 0, "label": "Moderatör", "color": "#E67E22"},
    "gurme": {"min": 0, "label": "Gurme", "color": "#27AE60"}
}

RANK_HIERARCHY = ["caylak", "gezgin", "gurme", "kultur_elcisi", "evliya_celebi", "mod", "admin"]
# --- 2. HTML VE CSS ---
def get_app_css():
    return """<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700;900&family=Lato:wght@300;400;700&family=Pacifico&display=swap');

:root {
    --primary-color: #16A085; /* Koyu Selçuklu Turkuazı */
    --secondary-color: #D35400; /* Kiremit / Altın Sarısı */
    --bg-color: #FEFDF5; /* Sıcak Krem */
    --card-bg: #FAF9F6; /* Kırık Beyaz */
    --text-dark: #2C3E50; /* Koyu Lacivert/Gri */
}

html, body, [class*="css"] { font-family: 'Lato', sans-serif; background-color: var(--bg-color); color: var(--text-dark); }

/* Selçuklu Arka Plan Deseni (Multiple Backgrounds) */
.stApp {
    background-color: var(--bg-color);
}

.stApp::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    
    /* Resmi 4 kez çağırıyoruz */
    background-image: 
        url('https://i.ibb.co/WhqJ4wT/images-2-removebg-preview.png'),
        url('https://i.ibb.co/WhqJ4wT/images-2-removebg-preview.png'),
        url('https://i.ibb.co/WhqJ4wT/images-2-removebg-preview.png'),
        url('https://i.ibb.co/WhqJ4wT/images-2-removebg-preview.png');
        
    /* Konumlarını rastgele dağıtıyoruz (Sol-Üst, Sağ-Alt, Sol-Alt, Sağ-Üst) */
    background-position: 
        5% 10%,   /* Sol Üst */
        95% 90%,  /* Sağ Alt */
        5% 90%,   /* Sol Alt */
        95% 10%;  /* Sağ Üst */
        
    /* Boyutlarını değiştiriyoruz ki doğal dursun */
    background-size: 180px, 250px, 140px, 200px;
    
    background-repeat: no-repeat;
    
    /* Çok silik yapıyoruz (Göz yormaması için) */
    opacity: 0.10; 
    
    z-index: 0; /* İçeriğin altında ama zemin renginin üstünde */
    pointer-events: none; /* Tıklamaları engellemesin */
}

/* Başlıklar */
h1, h2, h3, .route-title, .gastro-title, .sidebar-title, .profile-name { font-family: 'Merriweather', serif; }

/* Logo */
.main-logo {
    font-family: 'Pacifico', cursive;
    font-size: 48px;
    background: linear-gradient(45deg, var(--secondary-color), var(--primary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    white-space: nowrap;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}
.logo-emoji { font-size: 38px; -webkit-text-fill-color: initial; }

/* MODAL/DIALOG STYLING - Force Light Theme */
div[role="dialog"] {
    background-color: var(--bg-color) !important;
    color: var(--text-dark) !important;
    border: 1px solid var(--primary-color);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
div[role="dialog"] header, div[role="dialog"] div {
    background-color: transparent !important;
    color: var(--text-dark) !important;
}

/* Hero Banner */
.hero-banner-container { width: 100%; overflow: hidden; border-radius: 8px; box-shadow: 0 4px 12px rgba(211, 84, 0, 0.15); border: 2px solid var(--primary-color); margin-top: 10px; }
.hero-banner-img { width: 100%; height: 140px; object-fit: cover; object-position: center; display: block; }

/* KART TASARIMLARI (Selçuklu Teması) */
.discover-card {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(211, 84, 0, 0.15);
    margin-bottom: 15px;
    background: var(--card-bg);
    border: 1px solid #EAECEE;
    /* Selçuklu Bordürü (Fallback) */
    border-top: 4px solid var(--secondary-color);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.discover-card:hover { transform: translateY(-3px); box-shadow: 0 8px 15px rgba(211, 84, 0, 0.25); border-color: var(--primary-color); }

.card-image-wrapper { position: relative; width: 100%; height: 220px; }
.card-img-main { width: 100%; height: 100%; object-fit: cover; }
.card-caption { padding: 15px; font-size: 14px; color: #555; line-height: 1.6; border-top: 1px solid #f0f0f0; font-family: 'Lato', sans-serif; }

/* Etiketler */
.glass-tag { position: absolute; bottom: 10px; left: 10px; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(6px); padding: 6px 12px; border-radius: 30px; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 90%; }
.mini-avatar { width: 40px; height: 40px; border-radius: 50%; border: 2px solid var(--primary-color); object-fit: cover; }
.user-info-text { font-size: 12px; font-weight: bold; color: #2C3E50 !important; line-height: 1.2; }
.location-text { font-size: 10px; color: #7F8C8D !important; font-weight: normal; }
.category-badge { position: absolute; top: 10px; right: 10px; background: var(--primary-color); color: white; padding: 5px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid #148F77; }
.info-strip { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.8), rgba(0,0,0,0)); padding: 40px 10px 10px 10px; color: #f1f1f1; font-size: 11px; text-align: right; pointer-events: none; }

/* BUTONLAR (Geleneksel) */
.stButton button { border-radius: 4px !important; font-weight: 600 !important; transition: all 0.3s ease !important; border: 1px solid transparent !important; }
.stButton button[kind="primary"] { background-color: var(--primary-color) !important; color: white !important; box-shadow: 0 2px 5px rgba(211, 84, 0, 0.3) !important; border: 1px solid #117A65 !important; }
.stButton button[kind="primary"]:hover { background-color: #148F77 !important; transform: scale(1.02) !important; box-shadow: 0 4px 8px rgba(211, 84, 0, 0.4) !important; }
.stButton button[kind="secondary"] { background-color: #FFF !important; color: var(--text-dark) !important; border: 1px solid #BDC3C7 !important; }
.stButton button[kind="secondary"]:hover { border-color: var(--secondary-color) !important; color: var(--secondary-color) !important; background-color: #FEF9E7 !important; }

/* PROFİL */
.profile-header { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(211, 84, 0, 0.1); display: flex; align-items: center; gap: 25px; margin-bottom: 20px; border-left: 6px solid var(--secondary-color); border-right: 6px solid var(--secondary-color); }
.profile-avatar { width: 90px; height: 90px; border-radius: 50%; border: 3px solid #FEF9E7; object-fit: cover; }
.profile-info { flex-grow: 1; }
.profile-name { font-size: 26px; font-weight: 800; color: var(--text-dark) !important; margin: 0; }
.stat-box { background: #FEF9E7; padding: 8px 15px; border-radius: 4px; font-weight: bold; border: 1px solid #F5CBA7; color: var(--secondary-color); }

/* CHALLENGE */
.challenge-board { background: #2C3E50; color: #ECF0F1; padding: 25px; border: 4px double var(--secondary-color); border-radius: 8px; font-family: 'Courier New', monospace; box-shadow: 0 4px 15px rgba(0,0,0,0.2); text-align: center; margin-bottom: 20px; position: relative; overflow: hidden; }
.challenge-title { font-size: 28px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; color: var(--secondary-color); letter-spacing: 2px; }
.challenge-entry-card { background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(211, 84, 0, 0.1); overflow: hidden; margin-bottom: 15px; border: 1px solid #EAECEE; transition: transform 0.2s; border-bottom: 3px solid var(--primary-color); }
.challenge-entry-card:hover { transform: translateY(-3px); }
.challenge-img { width: 100%; height: 200px; object-fit: cover; }
.challenge-text { padding: 12px; font-size: 14px; font-style: italic; color: #555; border-left: 4px solid var(--secondary-color); background: #FEF9E7; margin: 10px; border-radius: 0 4px 4px 0; font-family: 'Merriweather', serif; }
.challenge-user { padding: 0 10px 10px 10px; font-weight: bold; font-size: 12px; color: #333; display: flex; justify-content: space-between; }

/* DİĞER */
.system-announcement { background-color: #E8F6F3; color: #0E6251; padding: 15px; border-radius: 4px; margin-bottom: 20px; border: 1px solid var(--primary-color); display: flex; align-items: center; gap: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.product-link-btn { display: inline-block; background: var(--secondary-color); color: white; padding: 6px 12px; border-radius: 20px; font-size: 11px; text-decoration: none; margin-top: 8px; font-weight: bold; box-shadow: 0 3px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }
.product-link-btn:hover { transform: scale(1.05); color: white; background: #BA4A00; }

/* GASTRO CARD */
.gastro-card {
    background-color: #FEF9E7; 
    border: 2px solid var(--secondary-color); 
    padding: 20px; 
    border-radius: 8px; 
    margin-bottom: 20px; 
    box-shadow: 0 4px 6px rgba(211, 84, 0, 0.1);
    color: #333;
    background-image: url('https://www.transparenttextures.com/patterns/cubes.png');
}
.gastro-title { font-weight: 800; font-size: 18px; color: var(--secondary-color); margin-bottom: 8px; display: flex; align-items: center; gap: 10px; text-decoration: underline; text-decoration-color: var(--primary-color); }
.gastro-item { margin-bottom: 5px; font-size: 14px; }

/* ANKET */
.poll-box { background: white !important; padding: 20px; border-radius: 8px; margin-top: 20px; border-top: 5px solid var(--primary-color); box-shadow: 0 4px 6px rgba(211, 84, 0, 0.1); border: 1px solid #EAECEE; }
.poll-title { font-weight: bold; margin-bottom: 10px; font-size: 16px; color: var(--text-dark) !important; }

.sponsor-pool-box { background: linear-gradient(135deg, #2C3E50, #34495E); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 2px solid var(--secondary-color); }
.winner-card { border: 1px solid #eee; border-radius: 8px; padding: 10px; margin-bottom: 10px; background: #fff; display: flex; align-items: center; gap: 10px; border-left: 4px solid var(--primary-color); }

/* ROTA KARTLARI */
.route-card-horizontal { display: flex; flex-direction: column; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(211, 84, 0, 0.1); border: 1px solid #EAECEE; margin-bottom: 30px; border-top: 4px solid var(--secondary-color); }
.route-header-collage { display: flex; height: 220px; width: 100%; position: relative; }
.collage-left { width: 60%; height: 100%; position: relative; }
.collage-right { width: 40%; height: 100%; display: flex; flex-direction: column; }
.collage-img-main { width: 100%; height: 100%; object-fit: cover; }
.collage-img-small { width: 100%; height: 50%; object-fit: cover; border-left: 2px solid white; }
.collage-img-small:first-child { border-bottom: 2px solid white; }
.route-header-single { position: relative; height: 200px; width: 100%; }
.route-overlay-info { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.5) 70%, transparent 100%); padding: 20px 15px 12px 15px; color: white; }
.route-title { font-size: 22px; font-weight: 800; margin-bottom: 6px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.route-meta { font-size: 12px; display: flex; gap: 15px; opacity: 0.95; align-items: center; font-family: 'Lato', sans-serif; }
.route-body { padding: 20px; }
.route-summary { font-size: 15px; color: #555; line-height: 1.7; margin-bottom: 20px; font-family: 'Merriweather', serif; }
.timeline-container { display: flex; align-items: flex-start; overflow-x: auto; padding-bottom: 10px; gap: 0px; }
.timeline-step { display: flex; align-items: center; flex-shrink: 0; }
.timeline-box { background: #F8F9F9; border: 1px solid #E5E8E8; border-radius: 4px; padding: 8px 12px; min-width: 140px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 4px; transition: transform 0.2s; }
.timeline-box:hover { transform: scale(1.02); border-color: var(--primary-color); background: #E8F6F3; }
.t-icon { font-size: 20px; }
.t-name { font-size: 12px; font-weight: bold; color: #333; }
.t-price { font-size: 10px; color: #666; background: #eee; padding: 2px 6px; border-radius: 4px; }
.timeline-arrow { color: #BDC3C7; font-size: 18px; margin: 0 5px; display: flex; align-items: center; height: 100%; }
.comment-box { background: #FDFEFE; padding: 10px; border-radius: 4px; margin-bottom: 8px; border: 1px solid #F2F3F4; }
.comment-user { font-weight: bold; font-size: 12px; color: var(--primary-color); }
.comment-text { font-size: 13px; color: #555; }
.coffee-btn-container { margin-top: 20px; padding-top: 15px; border-top: 1px dashed #ddd; text-align: center; }
.route-card-summary { display: flex; flex-direction: column; height: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(211, 84, 0, 0.1); border: 1px solid #EAECEE; transition: transform 0.2s; border-top: 3px solid var(--secondary-color); }
.route-card-summary:hover { transform: translateY(-3px); box-shadow: 0 8px 15px rgba(211, 84, 0, 0.2); }
.route-cover-small { width: 100%; height: 160px; object-fit: cover; }
.route-info-box { padding: 12px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
.route-title-small { font-size: 16px; font-weight: bold; color: #2C3E50; margin-bottom: 5px; line-height: 1.3; font-family: 'Merriweather', serif; }
.route-meta-small { font-size: 11px; color: #7F8C8D; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.route-badge { background: #E8F6F3; color: var(--primary-color); padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }

/* EMPTY STATE */
.empty-state-box { text-align: center; padding: 40px; color: #95A5A6; background: #fff; border-radius: 8px; border: 2px dashed #BDC3C7; margin: 20px 0; }
.empty-state-icon { font-size: 60px; display: block; margin-bottom: 10px; opacity: 0.7; }
.sidebar-box { background: white; border: 1px solid #EAECEE; border-radius: 8px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(211, 84, 0, 0.1); }
.sidebar-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; border-bottom: 2px solid var(--secondary-color); display: inline-block; padding-bottom: 2px; color: var(--text-dark) !important; }
.conquest-grid { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 15px; }
.city-badge { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-align: center; transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.city-visited { background-color: var(--primary-color); color: white; border: 1px solid #148F77; }
.city-not-visited { background-color: #ECF0F1; color: #95A5A6; border: 1px solid #BDC3C7; }
.city-badge:hover { transform: scale(1.05); }

::placeholder { color: #BDC3C7 !important; opacity: 1; }

/* STATS CARD (Selçuklu) */
.stats-card {
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 4px 15px rgba(211, 84, 0, 0.15);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    border-radius: 8px;
    border: 2px solid var(--primary-color);
    padding: 10px;
    text-align: center;
    color: var(--text-dark);
    font-weight: bold;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin-bottom: 20px;
    background-image: url('https://www.transparenttextures.com/patterns/arabesque.png');
}
.stats-item { display: flex; flex-direction: column; }
.stats-value { font-size: 18px; color: var(--secondary-color); font-family: 'Merriweather', serif; }
.stats-label { font-size: 10px; color: #7F8C8D; text-transform: uppercase; letter-spacing: 1px; }

/* --- SIDEBAR TASARIMI (Selçuklu Sütunu) --- */
[data-testid="stSidebar"] {
    background-color: transparent !important;
}
[data-testid="stSidebar"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: url('https://i.ibb.co/4gP3CzGW/7b74f3f6bf76afc8c76178a74f75867b.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0.65;
    z-index: -1;
    filter: sepia(20%) contrast(95%);
}

/* --- OKUNABİLİRLİK AYARLARI --- */

/* 1. Tüm genel yazıları (paragraf, liste, span) koyu yap */
html, body, p, li, .stMarkdown, .caption, div, span, label {
    color: #2C3E50 !important;
}

/* 2. Başlıkları daha belirgin ve koyu yap */
h1, h2, h3, h4, h5, h6, .stHeading {
    color: #1a252f !important;
    font-weight: 800 !important;
    text-shadow: 0px 1px 0px rgba(255,255,255,0.5);
}

/* 3. Sidebar (Sol Menü) içindeki yazılar (Resim üstünde okunması için HARE ekle) */
[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] span, 
[data-testid="stSidebar"] div, 
[data-testid="stSidebar"] label {
    color: #000000 !important;
    font-weight: 700 !important;
    text-shadow: 0px 0px 8px rgba(255, 255, 255, 0.9), 0px 0px 3px rgba(255, 255, 255, 1);
}

/* 4. Metin Giriş Alanları (Inputlar) */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF !important; /* Zemin Beyaz */
    color: #000000 !important;            /* Yazı Siyah */
    border: 1px solid #16A085 !important; /* Çerçeve Turkuaz */
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

/* 5. Placeholder (Silik yazılar) Rengini Düzelt */
::placeholder {
    color: #555 !important;
    opacity: 0.7 !important;
}

/* 6. Metrikler ve İstatistikler */
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    color: #2C3E50 !important;
}
/* Selectbox Dark Mode Fix - Aggressive */
div[data-baseweb="select"] > div {
    background-color: #FAF9F6 !important;
    color: #2C3E50 !important;
    border-color: #EAECEE !important;
}
div[data-baseweb="menu"], div[data-baseweb="popover"], ul[role="listbox"] {
    background-color: #FAF9F6 !important;
    color: #2C3E50 !important;
}
div[data-baseweb="option"], li[role="option"] {
    color: #2C3E50 !important;
    background-color: #FAF9F6 !important;
}
div[data-baseweb="option"]:hover, li[role="option"]:hover, li[aria-selected="true"] {
    background-color: #E8F6F3 !important;
    color: #16A085 !important;
}

/* INPUT METİN GÖRÜNÜRLÜĞÜ İÇİN EK KURAL */
input[type="text"], .stSelectbox [data-baseweb="select"] div {
    color: #2C3E50 !important;
    -webkit-text-fill-color: #2C3E50 !important; /* Chrome/Safari için zorlama */
    caret-color: #2C3E50 !important; /* İmleç rengi */
}
/* Dropdown input alanı */
div[data-baseweb="select"] input {
    color: #2C3E50 !important;
}

/* Scrollbar Tweaks */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: var(--primary-color); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--secondary-color); }
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
    p = user_data # Renamed for brevity as in the provided snippet
    points = p['points']
    role = p['role']
    next_level_points = RANK_SYSTEM['evliya_celebi']['min'] if role == 'evliya_celebi' else (RANK_SYSTEM['kultur_elcisi']['min'] if points < 1000 else (RANK_SYSTEM['evliya_celebi']['min'] if points < 5000 else 100000))
    progress = 100 if role == 'evliya_celebi' else min(100, int((points / next_level_points) * 100))
    
    rank_html = get_badge_html(role)
    avatar_url = p.get('avatar') or f"https://ui-avatars.com/api/?name={p['nick']}&background=random&color=fff&size=128"
    
    # Guild Icon Logic
    guild_id = p.get('guild')
    guild_icon = GUILDS.get(guild_id, {}).get('icon', '')
    display_nick = f"{p['nick']} {guild_icon}" if guild_icon else p['nick']
    
    followers_count = len(p.get('followers', []))
    following_count = len(p.get('following', []))
    
    return f"""
    <div class="profile-header">
        <img src="{avatar_url}" class="profile-avatar">
        <div class="profile-info">
            <h1 class="profile-name">{display_nick}</h1>
            <div style="margin-top:5px;">{rank_html}</div>
            <div style="margin-top:10px; font-size:14px; color:#555;">
                📍 {p.get('city', 'Dünya')} &nbsp;|&nbsp; 🎂 {p.get('join_date', '')[:10]}
            </div>
            <div class="profile-stats">
                <div class="stat-box">💰 {p.get('balance', 0)} TL</div>
                <div class="stat-box">⭐ {points} Puan</div>
                <div class="stat-box">👥 {followers_count} Takipçi</div>
                <div class="stat-box">👣 {following_count} Takip</div>
            </div>
            <div style="margin-top:10px;">
                <div style="font-size:10px; color:#666; margin-bottom:2px;">Seviye İlerlemesi: %{progress}</div>
                <div style="width:100%; background:#eee; height:8px; border-radius:4px;">
                    <div style="width:{progress}%; background:linear-gradient(90deg, #1E81B0, #3498db); height:100%; border-radius:4px;"></div>
                </div>
            </div>
        </div>
    </div>"""

# --- 3. BACKEND SERVİSİ ---
class FirebaseService:
    def __init__(self):
        self.auth_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        self.db_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
        self.commit_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:commit?key={FIREBASE_API_KEY}"

    def sign_in_anonymously(self):
        try: 
            return requests.post(f"{self.auth_url}:signUp?key={FIREBASE_API_KEY}", json={"returnSecureToken": True}).json()
        except Exception as e: return self._log_error("Anonim Giriş", e)

    def _log_error(self, operation, error):
        print(f"⚠️ [HATA RAPORU - {operation}]: {error}")
        return None

    def sign_in(self, email, password):
        try: 
            r = requests.post(f"{self.auth_url}:signInWithPassword?key={FIREBASE_API_KEY}", json={"email": email, "password": password, "returnSecureToken": True})
            if r.status_code != 200: return None
            return r.json()
        except Exception as e: return self._log_error("Giriş Yapma", e)

    def sign_up(self, email, password, nickname):
        try:
            # 1. Auth Create
            r = requests.post(f"{self.auth_url}:signUp?key={FIREBASE_API_KEY}", json={"email": email, "password": password, "returnSecureToken": True})
            if r.status_code != 200: 
                err_msg = r.json().get('error', {}).get('message', 'Bilinmeyen Hata')
                if "EMAIL_EXISTS" in err_msg: return False, "Bu e-posta adresi zaten kullanımda."
                if "WEAK_PASSWORD" in err_msg: return False, "Şifre çok zayıf (en az 6 karakter)."
                return False, f"Kayıt Hatası: {err_msg}"
            
            data = r.json()
            localId = data['localId']
            
            # 2. Firestore User Doc Create
            user_payload = {"fields": {
                "nickname": {"stringValue": nickname},
                "email": {"stringValue": email},
                "role": {"stringValue": "caylak"},
                "wallet_balance": {"integerValue": 0},
                "earnings": {"integerValue": 0},
                "points": {"integerValue": 100}, # Hoşgeldin bonusu
                "avatar": {"stringValue": ""},
                "join_date": {"stringValue": str(datetime.now())[:10]},
                # Legal Consent
                "terms_accepted": {"booleanValue": True},
                "terms_version": {"stringValue": "v1.0"},
                "terms_accepted_at": {"stringValue": datetime.now().isoformat()}
            }}
            
            requests.patch(f"{self.db_url}/users/{localId}?key={FIREBASE_API_KEY}", json=user_payload)
            return True, "Kayıt Başarılı"
        except Exception as e: 
            self._log_error("Kayıt Olma", e)
            return False, "Sistem Hatası"

    def validate_session(self, token):
        try:
            r = requests.post(f"{self.auth_url}:lookup?key={FIREBASE_API_KEY}", json={'idToken': token})
            if r.status_code == 200:
                data = r.json()
                if 'users' in data:
                    user = data['users'][0]
                    return {'uid': user['localId'], 'token': token}
            return None
        except: return None
    
    def get_profile(self, uid):
        try:
            r = requests.get(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}")
            if r.status_code != 200:
                return {"nick": "Misafir", "balance": 0, "earnings": 0, "role": "misafir", "points": 0, "visited_cities": [], "saved_routes": [], "followers": [], "following": []}
            
            f = r.json().get('fields', {})
            return {
                "nick": f.get('nickname',{}).get('stringValue','Adsız'), 
                "balance": int(f.get('wallet_balance',{}).get('integerValue',0)), 
                "pending_balance": float(f.get('pending_balance',{}).get('doubleValue',0.0)),
                "withdrawable_balance": float(f.get('withdrawable_balance',{}).get('doubleValue',0.0)),
                "iban": f.get('iban',{}).get('stringValue',''),
                "full_name": f.get('full_name',{}).get('stringValue',''),
                "earnings": int(f.get('earnings',{}).get('integerValue',0)), 
                "points": int(f.get('points',{}).get('integerValue',0)), 
                "role": f.get('role',{}).get('stringValue','caylak'), 
                "avatar": f.get('avatar',{}).get('stringValue',''),
                "visited_cities": [x.get('stringValue') for x in f.get('visited_cities',{}).get('arrayValue',{}).get('values',[])], 
                "saved_routes": [x.get('stringValue') for x in f.get('saved_routes',{}).get('arrayValue',{}).get('values',[])],
                "followers": [x.get('stringValue') for x in f.get('followers',{}).get('arrayValue',{}).get('values',[])],
                "following": [x.get('stringValue') for x in f.get('following',{}).get('arrayValue',{}).get('values',[])],
                "guild": f.get('guild',{}).get('stringValue',''), # YENİ: Lonca bilgisi
                "city": f.get('city',{}).get('stringValue',''), # YENİ: Şehir bilgisi
                "join_date": f.get('join_date',{}).get('stringValue','') # YENİ: Katılım tarihi
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
            mask_query = "&mask.fieldPaths=nickname&mask.fieldPaths=email&mask.fieldPaths=role&mask.fieldPaths=wallet_balance&mask.fieldPaths=earnings&mask.fieldPaths=points&mask.fieldPaths=avatar&mask.fieldPaths=guild" # YENİ: guild eklendi
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
                    "avatar": f.get('avatar',{}).get('stringValue',''),
                    "guild": f.get('guild',{}).get('stringValue','') # YENİ: guild eklendi
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

    # --- İÇERİK YÖNETİMİ ---
    def add_story(self, data):
        st.cache_data.clear()
        allowed, msg = self.check_daily_limit_and_update(data['uid'], 'story')
        if not allowed: st.error(msg); return
        
        # 1. Hikaye Oluştur
        payload = { "fields": { 
            "title": {"stringValue": html.escape(data['title'])}, 
            "city": {"stringValue": html.escape(data['city'])}, 
            "img": {"stringValue": data['img']},
            "images_list": {"arrayValue": {"values": [{"stringValue": x} for x in data.get('images_list',[])]}},
            "summary": {"stringValue": html.escape(data['summary'])},
            "category": {"stringValue": data.get('category', 'Genel')},
            "budget": {"integerValue": data.get('budget', 0)},
            "stops": {"arrayValue": {"values": [{"mapValue": {"fields": {"place": {"stringValue": s['place']}, "type": {"stringValue": s['type']}, "price": {"integerValue": s['price']}}}} for s in data.get('stops', [])]}},
            "author": {"stringValue": data['author']}, 
            "uid": {"stringValue": data['uid']}, 
            "likes": {"arrayValue": {"values": []}}, 
            "view_count": {"integerValue": 0},
            "date": {"timestampValue": datetime.utcnow().isoformat() + "Z"},
            "tags": {"arrayValue": {"values": [{"stringValue": t} for t in data.get('tags',[])]}},
            # YENİ: Sorumluluk Beyanı
            "responsibility_accepted": {"booleanValue": True},
            "responsibility_accepted_at": {"stringValue": datetime.now().isoformat()}
        }}
        
        r = requests.post(f"{self.db_url}/stories?key={FIREBASE_API_KEY}", json=payload)
        
        # 2. Kullanıcı Profiline "Son Onay Tarihi" İşle (Admin Takibi İçin)
        self.update_user_last_content_consent(data['uid'])

    def update_user_last_content_consent(self, uid):
        try:
            requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=last_content_consent", json={"fields": {"last_content_consent": {"stringValue": datetime.now().isoformat()}}})
        except: pass

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
        # Initial status: pending_payment. Expiry not set yet.
        payload = {"fields": { 
            "business_name": {"stringValue": data['business_name']}, 
            "link": {"stringValue": data['link']}, 
            "image": {"stringValue": data['image']}, 
            "email": {"stringValue": data.get('email', '-')}, # YENİ: E-posta alanı
            "status": {"stringValue": "pending_payment"}, 
            "owner_uid": {"stringValue": data['uid']}, 
            "date": {"stringValue": str(datetime.now())[:19]}
        }}
        requests.post(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}", json=payload)

    def mark_ad_paid(self, ad_id):
        # User clicked "I Paid", move to "pending_approval"
        requests.patch(f"{self.db_url}/sidebar_ads/{ad_id}?updateMask.fieldPaths=status&key={FIREBASE_API_KEY}", json={"fields": {"status": {"stringValue": "pending_approval"}}})

    def approve_main_ad(self, ad_id):
        # Admin approved -> Set 48h expiry from NOW
        expiry = (datetime.now() + timedelta(hours=48)).isoformat()
        payload = {"fields": {
            "status": {"stringValue": "active"}, 
            "approved_at": {"stringValue": datetime.now().isoformat()},
            "expiry_date": {"stringValue": expiry}
        }}
        requests.patch(f"{self.db_url}/sidebar_ads/{ad_id}?updateMask.fieldPaths=status&updateMask.fieldPaths=approved_at&updateMask.fieldPaths=expiry_date&key={FIREBASE_API_KEY}", json=payload)

    def get_ads_by_status(self, status_list):
        try:
            r = requests.get(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}")
            res = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    st_val = f.get('status',{}).get('stringValue')
                    if st_val in status_list:
                        res.append({
                            "id": doc['name'].split('/')[-1],
                            "business_name": f.get('business_name',{}).get('stringValue',''),
                            "link": f.get('link',{}).get('stringValue',''),
                            "image": f.get('image',{}).get('stringValue',''),
                            "email": f.get('email',{}).get('stringValue','-'), # YENİ
                            "created_at": f.get('date',{}).get('stringValue',''),
                            "status": st_val
                        })
            return res
        except: return []

    def get_pending_ads(self): return self.get_ads_by_status(['pending_approval'])

    def get_active_main_ad(self):
        try:
            r = requests.get(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}")
            now_str = datetime.now().isoformat()
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('status',{}).get('stringValue') == 'active':
                         exp = f.get('expiry_date', {}).get('stringValue', '2000-01-01')
                         if exp > now_str:
                             return {"image": f.get('image',{}).get('stringValue',''), "link": f.get('link',{}).get('stringValue','#'), "business_name": f.get('business_name',{}).get('stringValue','Bu bir işletmedir'), "type": "user_ad"}
            return None
        except: return None

    def add_gurme_offer(self, data):
        # Expiry is set upon approval
        payload = {"fields": { 
            "business_name": {"stringValue": data['business_name']}, 
            "city": {"stringValue": html.escape(data['city'])}, 
            "address": {"stringValue": data.get('address', '')}, 
            "offer_title": {"stringValue": data['offer_title']}, 
            "discount_code": {"stringValue": data.get('discount_code', '')}, 
            "link": {"stringValue": data.get('link', '')},
            "img": {"stringValue": data.get('img', '')},
            "referrer_uid": {"stringValue": data.get('referrer_uid', '')}, 
            "referrer_nick": {"stringValue": data.get('referrer_nick', '')}, 
            "status": {"stringValue": "pending"}, 
            "owner_uid": {"stringValue": data['uid']}, 
            "date": {"stringValue": str(datetime.now())[:19]} 
        }}
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
                        # date alanı yoksa, 'expiry_date' veya varsayılan bir değer kullanabiliriz, ama id genelde sıralı gitmeyebilir.
                        # En doğrusu date alanı eklemekti ama mevcut yapıda 'expiry_date' veya eklenme sırası önemli.
                        # Eğer veritabanında 'date' alanı varsa kullanalım, yoksa boş string.
                        # add_gurme_offer metodunda 'date' alanı eklenmişti (bkz: line 1119 payload).
                        date_str = f.get('date', {}).get('stringValue', '')
                        offers.append({ 
                            "id": doc['name'].split('/')[-1], 
                            "business_name": f.get('business_name',{}).get('stringValue','-'), 
                            "city": f.get('city',{}).get('stringValue','-'), 
                            "address": f.get('address',{}).get('stringValue','-'), 
                            "offer_title": f.get('offer_title',{}).get('stringValue','-'), 
                            "discount_code": f.get('discount_code',{}).get('stringValue','****'), 
                            "referrer_uid": f.get('referrer_uid',{}).get('stringValue',''), 
                            "referrer_nick": f.get('referrer_nick',{}).get('stringValue','Yok'), 
                            "expiry_date": exp[:10],
                            "date": date_str 
                        })
            # TARİHE GÖRE TERSTEN SIRALA (En yeni en başa)
            # Eğer date alanı boşsa en sona atar.
            return sorted(offers, key=lambda x: x.get('date', ''), reverse=True)
        except: return []
    def approve_gurme_offer(self, offer_id, referrer_uid):
        # 1. Status -> Active, Expiry -> Now + 5 Days
        expiry_date = (datetime.now() + timedelta(days=5)).isoformat()
        requests.patch(f"{self.db_url}/gurme_offers/{offer_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status&updateMask.fieldPaths=expiry_date", json={"fields": {"status": {"stringValue": "active"}, "expiry_date": {"stringValue": expiry_date}}})
        
        # 2. Reward Referrer (Dynamic Amount)
        if referrer_uid: 
            try:
                # Referansın rolünü çek
                ref_profile = self.get_profile(referrer_uid)
                role = ref_profile.get('role', 'caylak')
                
                # Ödül Tutarı: Evliya Çelebi -> 75 TL, Diğerleri -> 50 TL
                reward_amount = 75.0 if role == 'evliya_celebi' else 50.0
                
                # 'pending_balance' artır
                requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{referrer_uid}", "fieldTransforms": [{"fieldPath": "pending_balance", "increment": {"doubleValue": reward_amount}}]}}]})
                
                # Bildirim
                self.send_message("Sistem", referrer_uid, f"🎉 Tebrikler! Referans olduğun bir ilan onaylandı. {int(reward_amount)} TL ödül (Rütbe Bonusu) bekleyen bakiyene eklendi.", "GeziStory Yönetim")
            except Exception as e: 
                print(f"Reward error: {e}")
        return True
    
    def add_forum_post(self, data):
        st.cache_data.clear() 
        allowed, msg = self.check_daily_limit_and_update(data['uid'], 'post')
        if not allowed: st.error(msg); return
        payload = { "fields": { 
            "kategori": {"stringValue": data['cat']}, "baslik": {"stringValue": html.escape(data['title'])}, "icerik": {"stringValue": html.escape(data['body'])}, 
            "yazar": {"stringValue": data['author']}, "uid": {"stringValue": data['uid']}, "tarih": {"stringValue": str(datetime.now())[:19]},
            "city": {"stringValue": html.escape(data.get('city', ''))}, "from_where": {"stringValue": html.escape(data.get('from_where', ''))}, "to_where": {"stringValue": html.escape(data.get('to_where', ''))},
            # YENİ: Sorumluluk Beyanı
            "responsibility_accepted": {"booleanValue": True},
            "responsibility_accepted_at": {"stringValue": datetime.now().isoformat()}
        }}
        r = requests.post(f"{self.db_url}/forum_posts?key={FIREBASE_API_KEY}", json=payload)
        if r.status_code != 200: st.error(f"Hata oluştu: {r.text}")
        else: 
            self.add_points(data['uid'], 10) # GÜNCELLENDİ: 10 Puan
            self.update_user_last_content_consent(data['uid'])

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
                new_c = {"mapValue": {"fields": {"user": {"stringValue": st.session_state.user_nick}, "text": {"stringValue": html.escape(data['text'])}, "date": {"stringValue": str(datetime.now())}}}}
                current = data.get('current_comments', [])
                all_c = [{"mapValue": {"fields": {"user": {"stringValue": c['user']}, "text": {"stringValue": c['text']}, "date": {"stringValue": "old"}}}} for c in current] + [new_c]
                requests.patch(f"{self.db_url}/forum_posts/{post_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=comments", json={"fields": {"comments": {"arrayValue": {"values": all_c}}}})
                self.add_points(st.session_state.user_uid, 3)
        except Exception as e: 
            print(f"Hata Detayi: {e}")
            st.error("İşlem sırasında bir hata oluştu.")

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
                new_comment = {"mapValue": {"fields": {"user": {"stringValue": comment_data['user']}, "text": {"stringValue": html.escape(comment_data['text'])}, "date": {"stringValue": str(datetime.now())}}}}
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
        except Exception as e: 
            print(f"Hata Detayi: {e}")
            st.error("Puan eklenirken bir hata oluştu.")

    # --- CHALLENGE METHODS ---
    def update_active_challenge(self, ch_id, title, desc, reward, img_url=None):
        try:
            payload = {"fields": { "id": {"stringValue": str(ch_id)}, "title": {"stringValue": title}, "desc": {"stringValue": desc}, "reward": {"stringValue": reward}, "active": {"booleanValue": True} }}
            if img_url: payload["fields"]["img"] = {"stringValue": img_url}
            requests.patch(f"{self.db_url}/challenges/active_one?key={FIREBASE_API_KEY}", json=payload)
        except Exception as e: 
            print(f"Hata Detayi: {e}")
            st.error("Yarışma güncellenemedi.")

    def get_active_challenge(self):
        try:
            r = requests.get(f"{self.db_url}/challenges/active_one?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                f = r.json().get('fields', {})
                return {
                    "id": f.get('id', {}).get('stringValue', '1'),
                    "title": f.get('title', {}).get('stringValue', 'Henüz Yarışma Yok'),
                    "desc": f.get('desc', {}).get('stringValue', 'Beklemede kalın...'),
                    "reward": f.get('reward', {}).get('stringValue', '-'),
                    "img": f.get('img', {}).get('stringValue', '')
                }
            return None
        except: return None

    def add_challenge_entry(self, ch_id, data):
        try:
            self.get_challenge_entries_cached.clear()
            requests.post(f"{self.db_url}/challenge_entries?key={FIREBASE_API_KEY}", json={"fields": {
                "challenge_id": {"stringValue": str(ch_id)},
                "user": {"stringValue": data['user']},
                "text": {"stringValue": html.escape(data['text'])},
                "city": {"stringValue": html.escape(data['city'])},
                "img": {"stringValue": data['img']},
                "likes": {"arrayValue": {"values": []}}, 
                "date": {"stringValue": str(datetime.now())[:19]}
            }})
            self.add_points(st.session_state.user_uid, 20) # GÜNCELLENDİ: 20 Puan
        except Exception as e: 
            print(f"Hata Detayi: {e}")
            st.error("Katılım sırasında bir hata oluştu.")

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

    # --- ŞEHİR REHBERİ (GASTRO-INTEL) ---
    def initialize_city_guides(self):
        # Sadece ilk çalışmada (veya collection boşsa) doldurur
        try:
            r = requests.get(f"{self.db_url}/city_guides?key={FIREBASE_API_KEY}")
            if 'documents' not in r.json():
                # Boşsa doldur
                for city, data in FULL_81_CITY_GUIDE.items():
                    payload = {"fields": {
                        "name": {"stringValue": city},
                        "yemek": {"stringValue": data['yemek']},
                        "butce": {"stringValue": data['butce']},
                        "tuyo": {"stringValue": data['tuyo']}
                    }}
                    requests.patch(f"{self.db_url}/city_guides/{city}?key={FIREBASE_API_KEY}", json=payload)
                return True
            return False
        except Exception as e: print(f"Guide init err: {e}"); return False

    def get_city_guide(self, city_name):
        try:
            r = requests.get(f"{self.db_url}/city_guides/{city_name}?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                f = r.json().get('fields', {})
                return {
                    "yemek": f.get('yemek', {}).get('stringValue', 'Veri yok'),
                    "butce": f.get('butce', {}).get('stringValue', 'Veri yok'),
                    "tuyo": f.get('tuyo', {}).get('stringValue', 'Veri yok'),
                    "gourmet_note": f.get('gourmet_note', {}).get('stringValue', '')
                }
            return FULL_81_CITY_GUIDE.get(city_name, {"yemek": "-", "butce": "-", "tuyo": "Bu şehir için henüz tüyo girilmemiş.", "gourmet_note": ""})
        except: 
            return FULL_81_CITY_GUIDE.get(city_name, {"yemek": "-", "butce": "-", "tuyo": "Bu şehir için henüz tüyo girilmemiş.", "gourmet_note": ""})

    def update_city_guide(self, city_name, data):
        try:
            payload = {"fields": {
                "name": {"stringValue": city_name},
                "yemek": {"stringValue": data['yemek']},
                "butce": {"stringValue": data['butce']},
                "tuyo": {"stringValue": data['tuyo']},
                "gourmet_note": {"stringValue": data.get('gourmet_note', '')}
            }}
            requests.patch(f"{self.db_url}/city_guides/{city_name}?key={FIREBASE_API_KEY}", json=payload)
            return True
        except: return False

    # --- FİNANSAL İŞLEMLER VE YÖNETİCİ RAPORLARI ---
    def initialize_legal_texts(self):
        try:
            r = requests.get(f"{self.db_url}/system/legal?key={FIREBASE_API_KEY}")
            if r.status_code != 200: # Doküman yoksa
                payload = {"fields": {
                    "text": {"stringValue": LEGAL_TEXT_KVKK},
                    "last_updated": {"stringValue": str(datetime.now())[:10]}
                }}
                requests.patch(f"{self.db_url}/system/legal?key={FIREBASE_API_KEY}", json=payload)
        except: pass

    def get_legal_texts(self):
        try:
            r = requests.get(f"{self.db_url}/system/legal?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                return r.json().get('fields', {}).get('text', {}).get('stringValue', LEGAL_TEXT_KVKK)
            else:
                return LEGAL_TEXT_KVKK
        except: return LEGAL_TEXT_KVKK

    def search_user(self, query):
        try:
            # Firestore'da 'startswith' benzeri sorgu için range filtreleri kullanılır.
            # query >= "sıl" AND query < "sıl\uf8ff"
            end_query = query + "\uf8ff"
            res_docs = {} # Deduplication için dict (name -> doc)

            # 1. Nickname ile Ara
            payload_nick = {
                "structuredQuery": {
                    "from": [{"collectionId": "users"}],
                    "where": {"compositeFilter": {"op": "AND", "filters": [
                        {"fieldFilter": {"field": {"fieldPath": "nickname"}, "op": "GREATER_THAN_OR_EQUAL", "value": {"stringValue": query}}},
                        {"fieldFilter": {"field": {"fieldPath": "nickname"}, "op": "LESS_THAN", "value": {"stringValue": end_query}}}
                    ]}},
                    "limit": 5
                }
            }
            try:
                r = requests.post(f"{self.db_url}:runQuery?key={FIREBASE_API_KEY}", json=payload_nick)
                if r.status_code == 200:
                    for item in r.json():
                        if 'document' in item: res_docs[item['document']['name']] = item['document']
            except: pass
            
            # 2. Email ile Ara
            payload_email = {
                "structuredQuery": {
                    "from": [{"collectionId": "users"}],
                    "where": {"compositeFilter": {"op": "AND", "filters": [
                        {"fieldFilter": {"field": {"fieldPath": "email"}, "op": "GREATER_THAN_OR_EQUAL", "value": {"stringValue": query}}},
                        {"fieldFilter": {"field": {"fieldPath": "email"}, "op": "LESS_THAN", "value": {"stringValue": end_query}}}
                    ]}},
                    "limit": 5
                }
            }
            try:
                r = requests.post(f"{self.db_url}:runQuery?key={FIREBASE_API_KEY}", json=payload_email)
                if r.status_code == 200:
                    for item in r.json():
                        if 'document' in item: res_docs[item['document']['name']] = item['document']
            except: pass

            res = list(res_docs.values())

            # Sonuçları formatla
            users = []
            for d in res:
                f = d.get('fields', {})
                users.append({
                    "uid": d['name'].split('/')[-1],
                    "nick": f.get('nickname',{}).get('stringValue','-'),
                    "email": f.get('email',{}).get('stringValue','-'),
                    "role": f.get('role',{}).get('stringValue','caylak'),
                    "balance": int(f.get('wallet_balance',{}).get('integerValue',0)),
                    "earnings": int(f.get('earnings',{}).get('integerValue',0)),
                    "points": int(f.get('points',{}).get('integerValue',0)),
                    "avatar": f.get('avatar',{}).get('stringValue',''),
                    "guild": f.get('guild',{}).get('stringValue',''),
                    # Yasal Onay Bilgileri
                    "terms_accepted": f.get('terms_accepted',{}).get('booleanValue', False),
                    "terms_version": f.get('terms_version',{}).get('stringValue', '-'),
                    "terms_accepted_at": f.get('terms_accepted_at',{}).get('stringValue', '-'),
                    "policy_accepted": f.get('policy_accepted',{}).get('booleanValue', False),
                    "policy_accepted_at": f.get('policy_accepted_at',{}).get('stringValue', '-'),
                    "last_content_consent": f.get('last_content_consent',{}).get('stringValue', '-')
                })
            return users
        except Exception as e:
            print(f"Search Err: {e}") 
            return []

    def update_profile(self, uid, new_nick, new_avatar):
        try:
            # Sadece Nick ve Avatar güncellenebilir
            payload = {"fields": {}}
            if new_nick: payload["fields"]["nickname"] = {"stringValue": new_nick}
            if new_avatar: payload["fields"]["avatar"] = {"stringValue": new_avatar}
            
            requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=nickname&updateMask.fieldPaths=avatar", json=payload)
            return True, "Profil güncellendi."
        except Exception as e:
            return False, str(e)

        except Exception as e:
            return False, str(e)

    def get_financial_report(self):
        try:
            r = requests.get(f"{self.db_url}/financial_tx?key={FIREBASE_API_KEY}")
            txs = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    txs.append({
                        "id": doc['name'].split('/')[-1],
                        "to_uid": f.get('to_uid', {}).get('stringValue', ''),
                        "amount": float(f.get('amount', {}).get('doubleValue', 0.0)),
                        "desc": f.get('desc', {}).get('stringValue', ''),
                        "status": f.get('status', {}).get('stringValue', 'pending'),
                        "date": f.get('date', {}).get('stringValue', '')
                    })
            return sorted(txs, key=lambda x: x['date'], reverse=True)
        except: return []

    def approve_transaction(self, tx_id, to_uid, amount):
        try:
            # Durumu onayla
            requests.patch(f"{self.db_url}/financial_tx/{tx_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status", json={"fields": {"status": {"stringValue": "approved"}}})
            # Bakiyeye ekle (pending -> withdrawable)
            requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{to_uid}", "fieldTransforms": [{"fieldPath": "withdrawable_balance", "increment": {"doubleValue": amount}}, {"fieldPath": "pending_balance", "increment": {"doubleValue": -amount}}]}}]})
            self.send_message("Sistem", to_uid, f"💰 {amount} TL tutarındaki hakedişin onaylandı ve çekilebilir bakiyene eklendi.", "Finans Ekibi")
            return True
        except Exception as e: print(f"Approve Error: {e}"); return False

    def reject_transaction(self, tx_id, to_uid, amount):
        try:
            requests.patch(f"{self.db_url}/financial_tx/{tx_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status", json={"fields": {"status": {"stringValue": "rejected"}}})
            # Pending'den düş
            requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{to_uid}", "fieldTransforms": [{"fieldPath": "pending_balance", "increment": {"doubleValue": -amount}}]}}]})
            self.send_message("Sistem", to_uid, f"❌ {amount} TL tutarındaki hakedişin reddedildi.", "Finans Ekibi")
            return True
        except: return False

    def request_withdrawal(self, uid, amount, iban, fname):
        try:
            # Bakiye kontrolü (Client tarafında yapıldı ama double check iyidir)
            p = self.get_profile(uid)
            if p.get('withdrawable_balance', 0) < amount: return False, "Yetersiz bakiye."

            # Kayıt Oluştur
            payload = {"fields": {
                "to_uid": {"stringValue": uid},
                "amount": {"doubleValue": amount},
                "desc": f"Para Çekme Talebi ({fname} - {iban})",
                "status": {"stringValue": "pending_withdraw"},
                "date": {"stringValue": str(datetime.now())[:19]}
            }}
            requests.post(f"{self.db_url}/financial_tx?key={FIREBASE_API_KEY}", json=payload)
            
            # Bakiyeden düş
            requests.post(self.commit_url, json={"writes": [{"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}", "fieldTransforms": [{"fieldPath": "withdrawable_balance", "increment": {"doubleValue": -amount}}]}}]})
            
            # IBAN Güncelle
            requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=iban&updateMask.fieldPaths=full_name", json={"fields": {"iban": {"stringValue": iban}, "full_name": {"stringValue": fname}}})
            
            return True, "Talebin alındı."
        except Exception as e: return False, f"Hata: {e}"

    def mark_withdrawal_paid(self, tx_id):
        requests.patch(f"{self.db_url}/financial_tx/{tx_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status", json={"fields": {"status": {"stringValue": "paid"}}})

    def get_user_transactions(self, uid):
        try:
            # Filtreleme client tarafında veya sorgu ile (Burada basitçe hepsini çekip filtreliyoruz firebase rest api query karmaşık olmasın diye)
            all_tx = self.get_financial_report()
            return [t for t in all_tx if t['to_uid'] == uid]
        except: return []

    def get_sponsor_applications(self, status=None):
        try:
            r = requests.get(f"{self.db_url}/sponsor_apps?key={FIREBASE_API_KEY}")
            apps = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    s = f.get('status',{}).get('stringValue','pending')
                    if status is None or s == status:
                         apps.append(f)
            return apps
        except: return []

    def update_sponsor_app_status(self, uid, new_status):
        try:
            # Belge ID'si UID olmadığı için sorgulamamız lazım, ama add metodunda ID olarak ne kullandık?
            # add metodunda post kullanıldı, yani auto-id. Bu sorun yaratır. UID ile bulmamız lazım.
            # Düzeltme: UID ile query yapıp ID'yi bulacağız.
            
            # 1. Dokümanı Bul
            all_apps = requests.get(f"{self.db_url}/sponsor_apps?key={FIREBASE_API_KEY}").json()
            doc_id = None
            if 'documents' in all_apps:
                for doc in all_apps['documents']:
                    if doc['fields']['uid']['stringValue'] == uid:
                        doc_id = doc['name'].split('/')[-1]
                        break
            
            if doc_id:
                requests.patch(f"{self.db_url}/sponsor_apps/{doc_id}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=status", json={"fields": {"status": {"stringValue": new_status}}})
                return True
            return False
        except: return False

    def add_sponsor_application(self, data):
        try:
            payload = {"fields": {
                "uid": {"stringValue": data['uid']},
                "name": {"stringValue": data['name']},
                "email": {"stringValue": data.get('email', '-')}, # E-posta Eklendi
                "uni": {"stringValue": data['uni']},
                "target": {"stringValue": data['target']},
                "why": {"stringValue": data['why']},
                "status": {"stringValue": "pending"},
                "date": {"stringValue": str(datetime.now())[:19]}
            }}
            requests.post(f"{self.db_url}/sponsor_apps?key={FIREBASE_API_KEY}", json=payload)
            return True
        except: return False

    # --- REKLAM / SPONSOR AD YÖNETİMİ ---
    def get_active_sidebar_ads(self, limit=4, ad_type="sidebar"):
        try:
            r = requests.get(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}")
            ads = []
            if 'documents' in r.json():
                documents = r.json().get('documents', [])
                random.shuffle(documents)
                
                now = datetime.now()

                for doc in documents:
                    f = doc.get('fields', {})
                    # Tip ve Status Kontrolü
                    current_type = f.get('ad_type', {}).get('stringValue', 'sidebar') # Varsayılan sidebar
                    status = f.get('status',{}).get('stringValue')

                    if status == 'active' and current_type == ad_type:
                        # VADE KONTROLÜ (OTOMATİK SİLME / GİZLEME)
                        # Eğer expire_date varsa ve geçmişse, gösterme (veya status update et)
                        expire_str = f.get('expire_date', {}).get('stringValue')
                        if expire_str:
                            try:
                                exp_date = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                                if now > exp_date:
                                    # Süresi dolmuş!
                                    # Status update yapabiliriz ama read işleminde write yapmak yavaşlatır.
                                    # Sadece göstermeyelim. Background job olmadığı için pasif kalsın.
                                    continue
                            except: pass

                        ads.append({
                            "id": doc['name'].split('/')[-1],
                            "business_name": f.get('business_name',{}).get('stringValue','-'),
                            "link": f.get('link',{}).get('stringValue','#'),
                            "image": f.get('image',{}).get('stringValue',''),
                            "text": f.get('text',{}).get('stringValue',''),
                            "email": f.get('email',{}).get('stringValue','-')
                        })
                        if len(ads) >= limit: break
            return ads
        except: return []

    def get_ads_by_status(self, statuses, ad_type=None):
        try:
            r = requests.get(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}")
            ads = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    
                    # Tip Filtresi (Opsiyonel)
                    current_type = f.get('ad_type', {}).get('stringValue', 'sidebar')
                    if ad_type and current_type != ad_type:
                        continue

                    if f.get('status',{}).get('stringValue') in statuses:
                        # Kalan Gün Hesabı
                        days_left = "-"
                        expire_str = f.get('expire_date', {}).get('stringValue')
                        if expire_str:
                            try:
                                exp_date = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                                delta = exp_date - datetime.now()
                                if delta.days < 0: days_left = "Süresi Doldu"
                                else: days_left = f"{delta.days} Gün"
                            except: pass

                        ads.append({
                            "id": doc['name'].split('/')[-1],
                            "business_name": f.get('business_name',{}).get('stringValue','-'),
                            "link": f.get('link',{}).get('stringValue','#'),
                            "image": f.get('image',{}).get('stringValue',''),
                            "status": f.get('status',{}).get('stringValue','pending'),
                            "uid": f.get('uid',{}).get('stringValue',''),
                            "email": f.get('email',{}).get('stringValue','-'),
                            "date": f.get('date',{}).get('stringValue',''),
                            "ad_type": current_type,
                            "days_left": days_left
                        })
            return ads
        except: return []

    def add_sidebar_ad(self, data):
        try:
            payload = {"fields": {
                "uid": {"stringValue": data['uid']},
                "business_name": {"stringValue": data['business_name']},
                "link": {"stringValue": data['link']},
                "image": {"stringValue": data['image']},
                "email": {"stringValue": data.get('email', '-')},
                "ad_type": {"stringValue": data.get('ad_type', 'sidebar')}, # sidebar veya route_ad
                "status": {"stringValue": "pending_approval"},
                "date": {"stringValue": str(datetime.now())[:19]}
            }}
            requests.post(f"{self.db_url}/sidebar_ads?key={FIREBASE_API_KEY}", json=payload)
            return True
        except: return False
    
    def update_ad_status(self, ad_id, new_status):
        try:
             # Eğer Active yapılıyorsa, expire_date'i şu andan 30 gün sonraya ayarla
             update_fields = {"status": {"stringValue": new_status}}
             mask = "updateMask.fieldPaths=status"

             if new_status == 'active':
                 expire_date = datetime.now() + timedelta(days=30)
                 expire_str = expire_date.strftime("%Y-%m-%d %H:%M:%S")
                 update_fields["expire_date"] = {"stringValue": expire_str}
                 mask += "&updateMask.fieldPaths=expire_date"
             
             requests.patch(f"{self.db_url}/sidebar_ads/{ad_id}?key={FIREBASE_API_KEY}&{mask}", json={"fields": update_fields})
             return True
        except Exception as e: 
            print(f"Update Ad Err: {e}")
            return False


    # --- YENİ SİTE İSTATİSTİKLERİ ---
    # --- YENİ SİTE İSTATİSTİKLERİ ---
    # --- YENİ SİTE İSTATİSTİKLERİ ---
    def update_site_stats(self):
        try:
            # Firestore field path hatası (Invalid property path) almamak için "-" kullanmıyoruz.
            # YYYYMMDD formatı: 20251206
            today_str = datetime.now().strftime("%Y%m%d") 
            
            # 1. Önce Dokümanı Kontrol Et (GET)
            check_url = f"{self.db_url}/system/site_stats?key={FIREBASE_API_KEY}"
            r_check = requests.get(check_url)
            
            doc_exists = (r_check.status_code == 200)
            
            if not doc_exists:
                # 2. Doküman Yoksa: YARAT
                init_body = {
                    "fields": {
                        "total_visits": {"integerValue": "1"},
                        f"visits_{today_str}": {"integerValue": "1"}
                    }
                }
                r_create = requests.patch(check_url, json=init_body)
                if r_create.status_code not in [200, 201]:
                    st.toast(f"Sayaç Başlangıç Hatası: {r_create.status_code}", icon="⚠️")
            else:
                # 3. Doküman Varsa: ATOMİK ARTIR
                doc_ref = f"projects/{PROJECT_ID}/databases/(default)/documents/system/site_stats"
                payload = {
                    "writes": [
                        {
                            "transform": {
                                "document": doc_ref,
                                "fieldTransforms": [
                                    {"fieldPath": "total_visits", "increment": {"integerValue": "1"}},
                                    {"fieldPath": f"visits_{today_str}", "increment": {"integerValue": "1"}}
                                ]
                            }
                        }
                    ]
                }
                r_inc = requests.post(self.commit_url, json=payload)
                if r_inc.status_code != 200:
                    st.toast(f"Sayaç Artırma Hatası ({r_inc.status_code}): {r_inc.text}", icon="🐛")
                    print(f"Stats Error: {r_inc.text}")

        except Exception as e:
            st.toast(f"Kritik Sayaç Hatası: {e}", icon="🔥")

    def get_site_stats(self):
        """
        Dönüş: { 'total': int, 'today': int }
        """
        try:
            today_str = datetime.now().strftime("%Y%m%d")
            r = requests.get(f"{self.db_url}/system/site_stats?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                fields = r.json().get('fields', {})
                total = int(fields.get('total_visits', {}).get('integerValue', 0))
                today = int(fields.get(f"visits_{today_str}", {}).get('integerValue', 0))
                return {"total": total, "today": today}
            else:
                return {"total": 0, "today": 0}
        except:
            return {"total": 0, "today": 0}

    # --- LONCA (GUILD) METODLARI ---
    def join_guild(self, uid, guild_id):
        # Profilde 'guild' alanını güncelle
        try:
            # Sadece 'guild' alanını patch et
            return requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=guild", json={"fields": {"guild": {"stringValue": guild_id}}}).status_code == 200
        except: return False

    def leave_guild(self, uid):
        # 'guild' alanını silmek yerine boş string veya null yapabiliriz ama delete field mask daha temiz
        # Basitlik için boş string yapalım, böylece 'join' logic ile aynı kalır.
        try:
             return requests.patch(f"{self.db_url}/users/{uid}?key={FIREBASE_API_KEY}&updateMask.fieldPaths=guild", json={"fields": {"guild": {"stringValue": ""}}}).status_code == 200
        except: return False

    def send_guild_message(self, guild_id, channel, user_nick, avatar, text):
        try:
            payload = {"fields": {
                "guild_id": {"stringValue": guild_id},
                "channel": {"stringValue": channel},
                "user": {"stringValue": user_nick},
                "avatar": {"stringValue": avatar or ""},
                "text": {"stringValue": text},
                "timestamp": {"stringValue": datetime.now().isoformat()}
            }}
            requests.post(f"{self.db_url}/guild_messages?key={FIREBASE_API_KEY}", json=payload)
            return True
        except: return False

    def get_guild_messages(self, guild_id, channel):
        try:
            # Filtreleme için structuredQuery kullanmak gerekebilir ama basitlik için tümünü çekip filtreleyelim (Performans notu: İlerde query'e çevrilmeli)
            # Firebase REST API ile basic filtering yapalım: 
            # Not: Firestore REST basic filtering biraz karışıktır, basit client-side filter MVP için yeterli.
            # Ancak çok mesaj olursa yavaşlar. Şimdilik MVP.
            r = requests.get(f"{self.db_url}/guild_messages?key={FIREBASE_API_KEY}")
            res = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('guild_id',{}).get('stringValue') == guild_id and f.get('channel',{}).get('stringValue') == channel:
                        res.append({
                            "id": doc['name'].split('/')[-1],
                            "user": f.get('user',{}).get('stringValue','Anonim'),
                            "avatar": f.get('avatar',{}).get('stringValue',''),
                            "text": f.get('text',{}).get('stringValue',''),
                            "timestamp": f.get('timestamp',{}).get('stringValue','')
                        })
            # Tarihe göre sırala
            return sorted(res, key=lambda x: x['timestamp'])
        except: return []

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

    # --- CHALLENGE POLL (YARIŞMA ANKETİ) ---
    def create_challenge_poll(self, question, options):
        # options: list of 4 strings
        try:
            fields = {
                "question": {"stringValue": question},
                "voted_uids": {"arrayValue": {"values": []}}
            }
            # 4 Seçenek için alanları oluştur
            for i, opt in enumerate(options):
                # Boş seçenekleri de kaydedelim ki indeks yapısı bozulmasın, ama UI'da dolu olanları gösteririz.
                fields[f"opt_{i}"] = {"stringValue": opt}
                fields[f"count_{i}"] = {"integerValue": 0}
            
            requests.patch(f"{self.db_url}/challenges/active_poll?key={FIREBASE_API_KEY}", json={"fields": fields})
            return True
        except: return False

    def delete_challenge_poll(self):
        try:
            return requests.delete(f"{self.db_url}/challenges/active_poll?key={FIREBASE_API_KEY}").status_code == 200
        except: return False

    def get_challenge_poll(self):
        try:
            r = requests.get(f"{self.db_url}/challenges/active_poll?key={FIREBASE_API_KEY}")
            if r.status_code == 200:
                f = r.json().get('fields', {})
                options = []
                for i in range(4):
                    opt_text = f.get(f"opt_{i}", {}).get('stringValue', '')
                    if opt_text:
                        options.append({
                            "index": i,
                            "text": opt_text,
                            "count": int(f.get(f"count_{i}", {}).get('integerValue', 0))
                        })
                
                voted_uids = [x.get('stringValue') for x in f.get('voted_uids', {}).get('arrayValue', {}).get('values', [])]
                
                return {
                    "question": f.get('question', {}).get('stringValue', ''),
                    "options": options,
                    "voted_uids": voted_uids
                }
            return None
        except: return None

    def vote_challenge_poll(self, opt_index, uid):
        try:
            # Atomic update: Increment count AND add uid to voted_uids
            writes = [
                {"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/challenges/active_poll", "fieldTransforms": [{"fieldPath": f"count_{opt_index}", "increment": {"integerValue": 1}}]}},
                {"transform": {"document": f"projects/{PROJECT_ID}/databases/(default)/documents/challenges/active_poll", "fieldTransforms": [{"fieldPath": "voted_uids", "appendMissingElements": {"values": [{"stringValue": uid}]}}]}}
            ]
            r = requests.post(self.commit_url, json={"writes": writes})
            return r.status_code == 200
        except: return False





    # --- CHALLENGE ARCHIVE METHODS ---
    def archive_and_start_new_challenge(self, new_id, new_title, new_desc, new_reward, new_img_url=None):
        try:
            # 1. Mevcut Aktif Yarışmayı Al (Backup için)
            current_ch = self.get_active_challenge()
            current_id = current_ch['id'] if current_ch else f"old_{int(time.time())}"
            
            # 2. Mevcut Yarışmayı 'past_challenges' koleksiyonuna kaydet (Başlıklarıyla listeleyebilmek için)
            if current_ch:
                payload_archive = {
                    "fields": {
                        "id": {"stringValue": current_id},
                        "title": {"stringValue": current_ch['title']},
                        "date": {"stringValue": str(datetime.now())[:10]}
                    }
                }
                # Belge ID'si challenge ID'si olsun
                requests.patch(f"{self.db_url}/past_challenges/{current_id}?key={FIREBASE_API_KEY}", json=payload_archive)

            # 3. YENİ Yarışmayı Aktif Yap (active_one güncelle)
            payload_new = {
                "fields": { 
                    "id": {"stringValue": str(new_id)}, 
                    "title": {"stringValue": new_title}, 
                    "desc": {"stringValue": new_desc}, 
                    "reward": {"stringValue": new_reward}, 
                    "active": {"booleanValue": True} 
                }
            }
            if new_img_url: payload_new["fields"]["img"] = {"stringValue": new_img_url}
            
            requests.patch(f"{self.db_url}/challenges/active_one?key={FIREBASE_API_KEY}", json=payload_new)
            
            # NOT: Entryler zaten 'challenge_id' ile etiketli olduğu için veritabanında bir şey taşımaya gerek yok.
            # Sadece 'get_challenge_entries' metodunda 'current_id' ile çağırınca günceller, 
            # eski id ile çağırınca eskiler gelir. Sistem yorulmaz.
            
            # Cache Temizliği
            st.cache_data.clear()
            return True
        except Exception as e:
            print(f"Archive Err: {e}")
            return False

    def get_past_challenges_list(self):
        try:
            r = requests.get(f"{self.db_url}/past_challenges?key={FIREBASE_API_KEY}")
            res = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    res.append({
                        "id": f.get('id', {}).get('stringValue', ''),
                        "title": f.get('title', {}).get('stringValue', 'İsimsiz Yarışma'),
                        "date": f.get('date', {}).get('stringValue', '')
                    })
            return sorted(res, key=lambda x: x['id'], reverse=True)
        except: return []

    # --- ZİYARETÇİ SAYACI ---
    def increment_daily_visits(self):
        try:
            today_str = str(datetime.now().date())
            doc_ref = f"{self.db_url}/system/stats?key={FIREBASE_API_KEY}"
            r = requests.get(doc_ref)
            
            current_date = ""
            if r.status_code == 200:
                f = r.json().get('fields', {})
                current_date = f.get('date', {}).get('stringValue', '')
            
            if current_date != today_str:
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    status = f.get('status',{}).get('stringValue','-')
                    if status in ['pending', 'pending_withdraw']:
                        txs.append({
                            "id": doc['name'].split('/')[-1],
                            "type": f.get('type',{}).get('stringValue','-'),
                            "amount": f.get('amount',{}).get('doubleValue',0.0),
                            "status": status,
                            "to_uid": f.get('to_uid',{}).get('stringValue','-'),
                            "order_id": f.get('order_id',{}).get('stringValue','-'),
                            "date": f.get('date',{}).get('stringValue',''),
                            "desc": f.get('description',{}).get('stringValue','')
                        })
            return txs
        except: return []

    def get_user_transactions(self, uid):
        try:
            r = requests.get(f"{self.db_url}/transactions?key={FIREBASE_API_KEY}")
            txs = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    if f.get('to_uid',{}).get('stringValue') == uid:
                        txs.append({
                            "id": doc['name'].split('/')[-1],
                            "type": f.get('type',{}).get('stringValue','-'),
                            "amount": f.get('amount',{}).get('doubleValue',0.0),
                            "status": f.get('status',{}).get('stringValue','-'),
                            "date": f.get('date',{}).get('stringValue',''),
                            "desc": f.get('description',{}).get('stringValue','')
                        })
            return sorted(txs, key=lambda x: x['date'], reverse=True)
        except: return []

    def get_badge_html(self, role):
        badges = {
            "admin": "<span style='background:#000; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>👑 Yönetici</span>",
            "mod": "<span style='background:#6c757d; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>🛡️ Moderatör</span>",
            "evliya_celebi": "<span style='background:#FFD700; color:black; padding:2px 6px; border-radius:4px; font-size:10px;'>🌟 Evliya Çelebi</span>",
            "kultur_elcisi": "<span style='background:#17a2b8; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>🌍 Kültür Elçisi</span>",
            "gezgin": "<span style='background:#28a745; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>🎒 Gezgin</span>",
            "caylak": "<span style='background:#6c757d; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>🌱 Çaylak</span>"
        }
        return badges.get(role, badges['caylak'])

    # --- ADMIN CONTENT MANAGEMENT ---
    def admin_get_latest_contents(self, content_type="stories", limit=20):
        # content_type: 'stories' or 'forum_posts'
        try:
            url = f"{self.db_url}/{content_type}?key={FIREBASE_API_KEY}&pageSize={limit}"
            r = requests.get(url)
            res = []
            if 'documents' in r.json():
                for doc in r.json().get('documents', []):
                    f = doc.get('fields', {})
                    # Ortak alanları al
                    item = {
                        "id": doc['name'].split('/')[-1],
                        "uid": f.get('uid', {}).get('stringValue', '-'),
                        "author": f.get('yazar',{}).get('stringValue') or f.get('author',{}).get('stringValue') or 'Anonim',
                        "date": f.get('tarih',{}).get('stringValue') or f.get('date',{}).get('stringValue') or f.get('date',{}).get('timestampValue') or '-',
                    }
                    
                    if content_type == 'stories':
                        item["title"] = f.get('baslik',{}).get('stringValue','-')
                        item["city"] = f.get('sehir',{}).get('stringValue','-')
                    else: # forum
                        item["title"] = f.get('baslik',{}).get('stringValue') or f.get('title',{}).get('stringValue','-')
                        item["body"] = f.get('icerik',{}).get('stringValue') or f.get('body',{}).get('stringValue','')
                    
                    res.append(item)
            return res # Sıralama varsayılan (ID veya eklenme sırası) gelir
        except: return []

    def admin_search_content(self, content_type, query):
        # content_type: 'stories' or 'forum_posts'
        # Başlığa göre arama (Title)
        try:
            field_name = "baslik" if content_type == "stories" else "title"
            # Forum postlarında title bazen 'baslik' bazen 'title' olabilir, ama yeni yapıda 'title' kullanıyoruz.
            # Eski kayıtlar için 'baslik' da olabilir. Bu karmaşıklık için çift sorgu gerekebilir ama şimdilik standart 'baslik' (story) ve 'title' (forum) varsayalım.
            
            end_query = query + "\uf8ff"
            payload = {
                "structuredQuery": {
                    "from": [{"collectionId": content_type}],
                    "where": {"compositeFilter": {"op": "AND", "filters": [
                        {"fieldFilter": {"field": {"fieldPath": field_name}, "op": "GREATER_THAN_OR_EQUAL", "value": {"stringValue": query}}},
                        {"fieldFilter": {"field": {"fieldPath": field_name}, "op": "LESS_THAN", "value": {"stringValue": end_query}}}
                    ]}},
                    "limit": 10
                }
            }
            r = requests.post(f"{self.db_url}:runQuery?key={FIREBASE_API_KEY}", json=payload)
            res = []
            if r.status_code == 200:
                for item in r.json():
                     if 'document' in item:
                        doc = item['document']
                        f = doc.get('fields', {})
                        res.append({
                            "id": doc['name'].split('/')[-1],
                            "title": f.get(field_name,{}).get('stringValue','-'),
                            "author": f.get('yazar',{}).get('stringValue') or f.get('author',{}).get('stringValue') or 'Anonim',
                            "uid": f.get('uid', {}).get('stringValue', '-')
                        })
            return res
        except: return []

    def admin_delete_content(self, content_type, doc_id):
        try:
            requests.delete(f"{self.db_url}/{content_type}/{doc_id}?key={FIREBASE_API_KEY}")
            st.cache_data.clear() # Cache temizle
            return True
        except: return False
def upload_to_imgbb(file):
    try: return requests.post("https://api.imgbb.com/1/upload", data={"key": IMGBB_API_KEY}, files={"image": file.getvalue()}).json()["data"]["url"]
    except: return None

def render_login_register_form(fb, key_suffix=""):
    t1, t2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    with t1:
        with st.form(f"modal_login_{key_suffix}"):
            m = st.text_input("E-posta", key=f"login_email_{key_suffix}")
            p = st.text_input("Şifre", type="password", key=f"login_pass_{key_suffix}")
            if st.form_submit_button("Giriş Yap", type="secondary"): 
                u = fb.sign_in(m, p)
                if u and 'localId' in u:
                    profile_data = fb.get_profile(u['localId'])
                    st.session_state.update(user_token=u['idToken'], user_uid=u['localId'], user_nick=profile_data['nick'], user_balance=profile_data['balance'], user_pending=profile_data.get('pending_balance',0.0), user_withdrawable=profile_data.get('withdrawable_balance',0.0), user_role=profile_data['role'], user_points=profile_data['points'], user_saved_routes=profile_data['saved_routes'])
                    st.query_params['session'] = u['idToken']
                    st.rerun() 
                elif u is None:
                    st.error("Giriş başarısız! E-posta veya şifre hatalı olabilir.")
    with t2:
        with st.form(f"modal_register_inner_{key_suffix}"):
            n = st.text_input("Kullanıcı Adı (Zorunlu)", key=f"reg_nick_{key_suffix}")
            mm = st.text_input("E-posta", key=f"reg_email_{key_suffix}")
            pp = st.text_input("Şifre", type="password", key=f"reg_pass_{key_suffix}")
            
            # Yasal Metin Oku Butonu
            terms = st.checkbox("Kullanıcı Sözleşmesi'ni ve Gizlilik Politikasını okudum, kabul ediyorum.", key=f"terms_chk_{key_suffix}")
            with st.expander("📄 Sözleşmeyi Görüntüle"):
                st.markdown(fb.get_legal_texts())
            
            if st.form_submit_button("Kayıt Ol", type="primary"):
                if not n: st.error("Lütfen kendinize bir kullanıcı adı belirleyin!")
                elif not mm or not pp: st.error("E-posta ve şifre boş olamaz.")
                elif not terms: st.error("Lütfen kullanıcı sözleşmesini onaylayın.")
                else:
                    ok, msg = fb.sign_up(mm, pp, n)
                    if ok: st.success("Kayıt Başarılı! Giriş sekmesinden girebilirsin."); time.sleep(2)
                    else: st.error(msg)

# --- 4. SAYFA GÖRÜNÜMLERİ ---
# GİRİŞ PENCERESİ TANIMLAMASI
if hasattr(st, "dialog"):
    @st.dialog("✨ GeziStory Giriş Kapısı")
    def entry_dialog(fb):
        render_login_register_form(fb, key_suffix="dialog")
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("✨ GeziStory Giriş Kapısı")
    def entry_dialog(fb):
        render_login_register_form(fb, key_suffix="dialog")
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

# --- DIALOG DEFINITIONS (MOVED UP FOR SCOPE SAFETY) ---
if hasattr(st, "dialog"):


    @st.dialog("⚠️ Üye Girişi Gerekli")
    def guest_warning_dialog():
        st.warning("Bu özellikten yararlanmak için sitemize üye olmalısın.")
        st.info("Ücretsiz üye olarak puan toplayabilir, yorum yapabilir ve gezgin topluluğuna katılabilirsin!")
        # LOGIN FORM GÖMÜLDÜ - KULLANICI İSTEĞİ
        
    @st.dialog("📢 Sponsor Ol / Reklam Ver")
    def render_ad_application_dialog(fb_svc):
        # Session state temini (Form datası için)
        if 'ad_form_data' not in st.session_state: st.session_state.ad_form_data = {}
        if 'show_payment_buttons' not in st.session_state: st.session_state.show_payment_buttons = False

        st.markdown("Markanızı tanıtmak ve 'Vitrin Reklamları' alanında yer almak için formu doldurun.")
        st.caption("250 TL karşılığı ilanınız 1 ay boyunca tüm rotalarda görüntülenir.")
        
        # --- ADIM 1: FORM ---
        if not st.session_state.show_payment_buttons:
            with st.form("ad_app_form"):
                b_name = st.text_input("Marka / İşletme Adı", value=st.session_state.ad_form_data.get('b_name',''))
                b_link = st.text_input("Yönlendirilecek Link (Website/Instagram)", value=st.session_state.ad_form_data.get('b_link',''))
                
                b_email = st.text_input("İletişim E-posta", value=st.session_state.ad_form_data.get('b_email',''))
                st.caption("🔒 İletişim bilgileriniz sadece yönetici tarafından görülür, vitrinde yayınlanmaz.")
                
                b_img_file = st.file_uploader("Reklam Görseli (Tercihen Yatay/Dikdörtgen)", type=['png', 'jpg', 'jpeg'])
                
                if st.form_submit_button("Ödeme Adımına Geç"):
                    if not b_name or not b_link or not b_email:
                        st.error("Lütfen gerekli alanları doldurun.")
                    else:
                        # Görsel İşleme
                        img_url = ""
                        if b_img_file:
                             img_url = upload_to_imgbb(b_img_file)
                        elif st.session_state.ad_form_data.get('b_image'): # Daha önce yüklendiyse
                             img_url = st.session_state.ad_form_data.get('b_image')

                        if not img_url:
                            # Demo
                            img_url = "https://via.placeholder.com/300x150?text=REKLAM"

                        # Verileri Kaydet ve İlerle
                        st.session_state.ad_form_data = {
                            "b_name": b_name, "b_link": b_link, 
                            "b_email": b_email, "b_image": img_url
                        }
                        st.session_state.show_payment_buttons = True
                        st.rerun()
        
        # --- ADIM 2: ÖDEME VE ONAY ---
        else:
            st.success("✅ Bilgiler alındı! Şimdi ödeme adımındasınız.")
            st.markdown(f"""
            <div style="background:#e8f5e9; padding:15px; border-radius:10px; border:1px solid #c8e6c9;">
                <h4>💳 Ödeme Yap</h4>
                <p>Reklamınızın yayına girmesi için Shopier üzerinden güvenle ödeme yapabilirsiniz.</p>
                <a href="{SHOPIER_LINK_REKLAM}" target="_blank" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; display:inline-block; font-weight:bold;">Shopier ile Öde (250 TL)</a>
            </div>
            """, unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                 if st.button("⬅️ Düzenle"):
                     st.session_state.show_payment_buttons = False
                     st.rerun()
            with col_b2:
                 if st.button("Ödemeyi Yaptım / Onaya Gönder", type="primary"):
                     fdata = st.session_state.ad_form_data
                     data = {
                        "uid": st.session_state.user_uid or "guest",
                        "business_name": fdata['b_name'],
                        "link": fdata['b_link'],
                        "email": fdata['b_email'],
                        "image": fdata['b_image'],
                        "ad_type": "route_ad" # Rotalar için özel tip
                     }
                     
                     if fb_svc.add_sidebar_ad(data):
                         st.success("✅ Başvurunuz alındı! Yönetici onayı sonrası yayına girecektir.")
                         # Temizlik
                         st.session_state.show_payment_buttons = False
                         st.session_state.ad_form_data = {}
                         time.sleep(2)
                         st.rerun()
                     else:
                         st.error("Bir hata oluştu.")
        st.markdown("---")
        # Biz burada `fb` nesnesine erişemiyoruz direkt olarak, bu yüzden bu dialogu render_challenge içinde tanımlamak veya fb'yi global/session üzerinden almak daha mantıklı olabilir.
        # Ancak basitlik için form login/register fonksiyonunu çağıracağız. Fakat o fonksiyon fb istiyor.
        # Bu fonksiyon `fb` argümanı almıyor. Bu yüzden burada basit bir yönlendirme veya fb'yi session'a kaydetme lazım.
        # En temizi render_challenge içinde local bir dialog tanımlamak.
        # Şimdilik burayı basit bırakıp, esas işi render_challenge içindeki özel dialogda yapacağız.
        st.error("Lütfen giriş yapın.")
        if st.button("Kapat", use_container_width=True): st.rerun()

    @st.dialog("💬 Yorumlar")
    def view_comments_dialog(story, fb): render_comments_content(story, fb)

elif hasattr(st, "experimental_dialog"):


    @st.experimental_dialog("⚠️ Üye Girişi Gerekli")
    def guest_warning_dialog():
        st.warning("Bu özellikten yararlanmak için sitemize üye olmalısın.")
        if st.button("Kapat"): st.rerun()

    @st.experimental_dialog("💬 Yorumlar")
    def view_comments_dialog(story, fb): render_comments_content(story, fb)

else:

    def guest_warning_dialog(): st.error("Giriş yapmalısın!")
    def view_comments_dialog(s, f): pass

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
    try:
        # NESTED DIALOG WORKAROUND: Simulate Modal Logic within the Dialog
        # STRICT ACCESS CONTROL: Guests cannot view details
        if not st.session_state.user_token:
            # IN-PLACE LOGIN FORM (To avoid nested dialog error)
            gate_key = f"gate_login_{story['id']}"
            if st.session_state.get(gate_key, False):
                st.markdown("#### 🔑 Giriş Yap / Kayıt Ol")
                render_login_register_form(fb_service)
                if st.button("🔙 İptal", key=f"cncl_login_{story['id']}"):
                     st.session_state[gate_key] = False
                     st.rerun()
            else:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.warning("⚠️ Üye Girişi Gerekli", icon="🔒")
                st.info("Bu rotanın detaylarını görmek için sitemize üye olmalısın.")
                st.markdown("""
                <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; border: 1px solid #ddd;">
                    <h4 style="color:#000;">🚀 Gezgin Topluluğuna Katıl!</h4>
                    <p style="color:#555;">Ücretsiz üye ol, puan topla, gezilerini paylaş.</p>
                </div>
                """, unsafe_allow_html=True)
                
                c_reg, c_cls = st.columns(2)
                if c_reg.button("✨ Hemen Üye Ol", type="primary", use_container_width=True, key=f"btn_reg_gate_{story['id']}"):
                     st.session_state[gate_key] = True
                     st.rerun()
                
                # Close button logic: Since we can't force close the dialog easily from inside without a trigger, 
                # we'll use a rerun which might reset if the parent condition changes, aka "Close" might just be a refresh 
                # or we can try to inject JS. But for now, let's keep it simple. 
                # Actually, simple way: Just do nothing? Use X?
                # User specifically asked for a 'Close' button.
                # If we click it and do nothing, it's weird.
                # Since we are inside a dialog function called by st.dialog, st.rerun() reruns the dialog.
                # Best bet: Just tell user to use X if we can't close.
                # BUT, wait. If we rely on session state in the PARENT to show/hide the dialog, then we can toggle it off!
                # But here the dialog is called directly in an imperative way.
                # So we can't toggle it off from inside easily. 
                # Let's add a visual button that says "Kapat" but maybe just reruns to "refresh" or effectively does nothing 
                # but show a toast "Pencereyi sağ üstten kapatabilirsiniz".
                if c_cls.button("❌ Kapat", use_container_width=True, key=f"btn_cls_gate_{story['id']}"):
                     st.toast("ℹ️ Pencereyi kapatmak için sağ üstteki X işaretini veya ESC tuşunu kullanabilirsin.")
            return

        # RESİM GALERİSİ
        images = story.get('images_list', []) or ([story['img']] if story.get('img') else [])
        if images:
            st.markdown(f"**📸 Rota Fotoğrafları ({len(images)})**")
            cols = st.columns(min(len(images), 3)) 
            for i, img in enumerate(images):
                cols[i % 3].image(img, use_container_width=True)
        
        st.divider()
        st.markdown(f"### {story['title']}", unsafe_allow_html=True)
        st.caption(f"📍 {story['city']} | 💰 {story['budget']} TL | 📅 {story.get('date', '')[:10]}")
        
        # YAZAR KART
        p = fb_service.get_profile(story['uid'])
        avatar = p.get('avatar') or f"https://ui-avatars.com/api/?name={story['author']}&background=random"
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; background:#f8f9fa; padding:10px; border-radius:10px; border:1px solid #eee;">
            <img src="{avatar}" style="width:50px; height:50px; border-radius:50%;">
            <div>
                <div style="font-weight:bold;">{story['author']}</div>
                <div style="font-size:12px; color:gray;">{fb_service.get_badge_html(p.get('role','caylak'))}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 📝 Gezi Notları")
        st.write(story['summary'])
        
        stops = story.get('stops', [])
        if stops:
            st.markdown("#### 📍 Duraklar & Harcamalar")
            st.markdown(get_route_detail_timeline_html(stops), unsafe_allow_html=True)

        st.divider()

        st.divider()
        # ETKİLEŞİM BUTONLARI
        c1, c2, c3 = st.columns(3)
        
        # BEĞENİ
        is_liked = st.session_state.user_uid in story.get('likes', []) if st.session_state.user_token else False
        is_saved = story['id'] in st.session_state.user_saved_routes if st.session_state.user_token else False
        
        btn_label = f"❤️ {len(story.get('likes', []))}" if is_liked else f"🖤 {len(story.get('likes', []))}"
        if c1.button(btn_label, key=f"d_like_{story['id']}", use_container_width=True):
            if not st.session_state.user_token:
                st.session_state[warning_key] = True
                st.rerun()
            else:
                fb_service.update_interaction(story['id'], "like", current_likes=story.get('likes', []))
                st.rerun()
            
        # KAYDET
        save_lbl = "💾 Kaydedildi" if is_saved else "🔖 Kaydet"
        if c2.button(save_lbl, key=f"d_save_{story['id']}", use_container_width=True):
            if not st.session_state.user_token:
                 st.session_state[warning_key] = True
                 st.rerun()
            else:
                if is_saved:
                    st.session_state.user_saved_routes.remove(story['id'])
                    fb_service.manage_saved_route(st.session_state.user_uid, story['id'], False)
                    st.toast("Kaydedilenlerden çıkarıldı.")
                else:
                    st.session_state.user_saved_routes.append(story['id'])
                    fb_service.manage_saved_route(st.session_state.user_uid, story['id'], True)
                    st.toast("Rota kaydedildi!")
                st.rerun()

        # YORUM YAP
        if c3.button(f"💬 {len(story.get('comments', []))}", key=f"d_comm_{story['id']}", use_container_width=True):
             if not st.session_state.user_token:
                  st.session_state[warning_key] = True
                  st.rerun()
             else:
                 view_comments_dialog(story, fb_service)

        # KAHVE - Yasal nedenlerle kaldırıldı
        # st.markdown("### ☕ Yazara Destek Ol")
        # payment_dialog kodları kaldırıldı.
        
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
        print(f"Detail Error: {e}")



# --- MAIN ROUTE DETAIL DIALOG FUNCTION (Must be defined AFTER content) ---
if hasattr(st, "dialog"):
    @st.dialog("🗺️ Rota Detayları")
    def view_route_detail_dialog(story, fb): render_route_detail_content(story, fb)
elif hasattr(st, "experimental_dialog"):
    @st.experimental_dialog("🗺️ Rota Detayları")
    def view_route_detail_dialog(story, fb): render_route_detail_content(story, fb)
else:
    def view_route_detail_dialog(s,f): pass

def render_create_route_section(fb):
    user_role = st.session_state.get('user_role', 'caylak')
    min_rank_idx = RANK_HIERARCHY.index('kultur_elcisi')
    user_rank_idx = RANK_HIERARCHY.index(user_role) if user_role in RANK_HIERARCHY else 0
    
    if user_rank_idx < min_rank_idx:
        st.warning(f"🔒 **Erişim Kısıtlı:** Rota oluşturma özelliği sadece **'Kültür Elçisi'** ve üzeri rütbeler için aktiftir.")
        st.info(f"💡 **Neden?** GeziStory topluluğunda paylaşılan rotaların kalitesini ve güvenilirliğini korumak için öncelikle **'Kültür Elçisi'** rütbesine gelmelisin. Puan toplayıp rütbeni yükselterek sen de aramıza katılabilirsin! (Senin Rütben: {RANK_SYSTEM.get(user_role, {}).get('label')})")
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
        # İÇERİK SORUMLULUK BEYANI
        responsibility_check = st.checkbox("Paylaştığım içeriğin (yazı/görsel) tüm sorumluluğunun bana ait olduğunu beyan ederim.", key="resp_check_route")
        
        if st.button("🚀 Rotayı Yayınla", type="primary", use_container_width=True):
            if not responsibility_check:
                st.error("Lütfen içerik sorumluluk beyanını onaylayın.")
            else:
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

def render_single_post(p, fb, key_prefix=""):
    """Tek bir forum postunu render eder. Kod tekrarını önlemek için eklendi."""
    extra_info = ""
    if p.get('city'): extra_info = f" ({p['city']})"
    if p.get('from_where'): extra_info = f" ({p['from_where']} ➝ {p['to_where']})"
    
    # Highlight modunda (key_prefix varsa) varsayılan olarak açık gelsin (expanded=True)
    is_expanded = True if key_prefix else False
    
    with st.expander(f"📌 {p['title']}{extra_info}  |  👤 {p['author']}  |  🕒 {p['date'][:10]}", expanded=is_expanded):
        c_del, c_profile = st.columns([1, 6])
        if st.session_state.user_uid == p['uid']:
            if c_del.button("🗑️ Sil", key=f"{key_prefix}del_fp_{p['id']}"): fb.delete_forum_post(p['id']); st.rerun()
        if c_profile.button(f"👤 {p['author']}'ın Profiline Bak", key=f"{key_prefix}vp_fp_{p['id']}"):
            st.session_state.view_target_uid = p['uid']
            st.session_state.active_tab = "public_profile"
            st.rerun()

        st.markdown(f"**{p['body']}**"); st.divider()
        c_like, c_comm_count = st.columns([1, 5])
        is_liked = st.session_state.user_uid in p['likes'] if st.session_state.user_uid else False
        if c_like.button(f"{'❤️' if is_liked else '🤍'} {len(p['likes'])}", key=f"{key_prefix}f_like_{p['id']}"):
            if st.session_state.user_token: fb.update_forum_interaction(p['id'], "like", data={'current_likes': p['likes']}); st.rerun()
            else: st.toast("Giriş yapmalısın!")
        c_comm_count.caption(f"💬 {len(p['comments'])} Yorum")
        for c in p['comments']: st.markdown(f"<div style='background:#f9f9f9; padding:8px; border-radius:5px; margin-bottom:5px; font-size:13px;'><b>{c['user']}:</b> {c['text']}</div>", unsafe_allow_html=True)
        if st.session_state.user_token:
            with st.form(key=f"{key_prefix}f_comm_form_{p['id']}", clear_on_submit=True):
                new_c = st.text_input("Cevap Yaz (+3 Puan)", placeholder="Fikrini belirt...")
                if st.form_submit_button("Gönder", type="secondary") and new_c:
                    fb.update_forum_interaction(p['id'], "comment", data={'text': new_c, 'current_comments': p['comments']}); st.toast("Cevaplandı! +3 Puan"); time.sleep(1); st.rerun()

def render_forum(fb):
    st.markdown("### 🗣️ Gezgin Forumu")

    # --- HIGHLIGHTED POST (ARANAN KONU) ---
    if 'forum_focus' in st.session_state and st.session_state.forum_focus:
        # Performans için sadece ilgili post'u bulmaya çalışalım ama get_forum_posts cacheli değilse mecburen hepsini çekiyoruz
        # FirebaseService yapısına göre şimdilik hepsini çekip filter yapalım.
        all_posts_temp = fb.get_forum_posts()
        target_post = next((x for x in all_posts_temp if x['id'] == st.session_state.forum_focus), None)
        
        if target_post:
            st.markdown("""
            <div style="background-color:#fff3e0; padding:10px; border-radius:8px; border-left:5px solid #ff9800; margin-bottom:20px;">
                <h5 style="margin:0; color:#e65100;">🔍 Aradığınız Konu</h5>
            </div>
            """, unsafe_allow_html=True)
            
            # Özel render (Key prefix: 'hl_')
            render_single_post(target_post, fb, key_prefix="hl_")
            
            if st.button("❌ İşaretlemeyi Kaldır / Tümünü Göster", key="cls_focus_btn"):
                del st.session_state.forum_focus
                st.rerun()
            
            st.divider()
        else:
            st.info("Aradığınız konu bulunamadı veya silinmiş.")
            if st.button("Tüm Konulara Dön"):
                del st.session_state.forum_focus
                st.rerun()

    
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
                
                # Sorumluluk Beyanı - YENİ
                resp_check_forum = st.checkbox("Paylaştığım içeriğin (yazı/görsel) tüm sorumluluğunun bana ait olduğunu beyan ederim.", key="resp_check_forum")
                
                if st.form_submit_button("Yayınla", type="primary"):
                    if not c_title or not body:
                        st.warning("Lütfen başlık ve içerik giriniz.")
                    elif not resp_check_forum:
                        st.error("Lütfen içerik sorumluluk beyanını onaylayın.")
                    else:
                        if cat == "Yol Arkadaşı" and (not f_from or not f_to): st.warning("Lütfen nereden ve nereye gideceğinizi yazın.")
                        else:
                            with st.spinner("Yayınlanıyor..."):
                                fb.add_forum_post({ "cat": cat, "title": c_title, "body": body, "author": st.session_state.user_nick, "uid": st.session_state.user_uid, "city": f_city, "from_where": f_from, "to_where": f_to })
                                st.toast("Konu açıldı! Puan hanene +15 eklendi. 🚀"); time.sleep(1.5); st.rerun()
    
    st.divider()
    posts = fb.get_forum_posts(); cats = ["Genel", "Yol Arkadaşı", "Vize Sorunları", "Ekipman", "Şehir Dedikoduları"]; tabs = st.tabs(cats)
    for i, cat in enumerate(cats):
        with tabs[i]:
            cat_posts = [p for p in posts if p['cat'] == cat]
            if not cat_posts: 
                render_empty_state("Bu kategoride henüz ses yok...", "📭")
            else:
                for p in cat_posts:
                    render_single_post(p, fb)

def render_gurme(fb):
    st.markdown("### 🎟️ Fırsatlar Dünyası")
    
    # --- FİLTRELEME ALANI (Yeni) ---
    st.markdown("###### 🔍 Fırsat Filtresi")
    selected_filter = st.selectbox("Görmek istediğiniz fırsat türünü seçin:", ["Web"] + ["İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"], key="gurme_main_filter")
    st.caption("bulunduğun yerde ki mekanların indirimlerini görmek için seç")
    st.divider()
    
    # --- REKLAM ALANI & FORM ---
    # Ortalanmış Ekleme Alanı
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        with st.expander("📢 Reklam Ver / İşletmeni Ekle (+)", expanded=False):
            st.markdown("""
            <div style="background-color:#E8F8F5; border: 1px solid #D1F2EB; padding:15px; border-radius:8px; text-align:center;">
                <h4 style="color:#0E6655; margin:0;">🚀 İlanınız En Üstte!</h4>
                <p style="margin:5px 0;">5 gün boyunca yayında kalır.</p>
                <div style="font-weight:bold; font-size:18px; color:#117864;">Fiyat: 500 TL</div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- REFERANS SEÇİMİ (FORM DIŞI / İNTERAKTİF) ---
            if 'gurme_ref_user' not in st.session_state: st.session_state.gurme_ref_user = None

            st.markdown("##### 🤝 Referans Ekle (Opsiyonel)")
            if st.session_state.gurme_ref_user:
                # Seçili Referans Gösterimi
                r = st.session_state.gurme_ref_user
                st.success(f"✅ Seçili Referans: **{r['nick']}** ({r['role'].replace('_',' ').title()})")
                if st.button("değiştir / kaldır", type="secondary", key="rm_ref_btn"):
                    st.session_state.gurme_ref_user = None
                    st.rerun()
            else:
                # Arama Kutusu
                c_search, c_btn = st.columns([3, 1])
                search_q = c_search.text_input("Kültür Elçisi / Evliya Çelebi Ara", placeholder="Kullanıcı adı giriniz...", key="ref_search_input")
                if c_btn.button("Ara", key="ref_search_btn"):
                    if len(search_q) < 2:
                        st.warning("En az 2 karakter giriniz.")
                    else:
                        st.session_state.ref_search_results = []
                        # Backend'den çek ve filtrele
                        # Not: Tam teşekküllü sorgu olmadığı için yine fetch yapıyoruz ama kullanıcıya "arama" hissi veriyoruz.
                        all_u = fb.get_all_users(limit=500)
                        q_lower = search_q.lower()
                        for u in all_u:
                             if u.get('role') in ['kultur_elcisi', 'evliya_celebi'] and u['uid'] != st.session_state.user_uid:
                                 if q_lower in u['nick'].lower():
                                     st.session_state.ref_search_results.append(u)
            
            # Sonuçları Göster
            if 'ref_search_results' in st.session_state and st.session_state.ref_search_results and not st.session_state.gurme_ref_user:
                st.info(f"🔍 Eşleşen Öneriler ({len(st.session_state.ref_search_results)})")
                for res in st.session_state.ref_search_results:
                    c_r1, c_r2 = st.columns([3, 1])
                    c_r1.markdown(f"**{res['nick']}** ({res['role'].replace('_',' ').title()})")
                    if c_r2.button("Seç", key=f"sel_ref_{res['uid']}"):
                        st.session_state.gurme_ref_user = res
                        st.session_state.ref_search_results = [] # Temizle
                        st.rerun()
            elif 'ref_search_results' in st.session_state and not st.session_state.ref_search_results and search_q and not st.session_state.gurme_ref_user:
                 st.warning("Bu isme benzer uygun bir referans (Kültür Elçisi/Evliya Çelebi) bulunamadı.")

            st.divider()

            with st.form("gurme_add_form_v2"):
                bn = st.text_input("İşletme / Kampanya Adı (Kısa & Öz)")
                ot = st.text_input("Fırsat Başlığı (Örn: %20 İndirim)")
                ct = st.selectbox("Şehir", ["Web", "İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"])
                img_file = st.file_uploader("Kampanya Görseli", type=['jpg', 'png'])
                lnk = st.text_input("Yönlendirme Linki (Opsiyonel)", placeholder="https://...")
                dc = st.text_input("İndirim Kodu (Opsiyonel)")
                adr = st.text_area("Adres / Detay (Opsiyonel)")
                
                # Hidden Reference Info
                ref_info = "Yok"
                if st.session_state.gurme_ref_user:
                    ref_info = f"{st.session_state.gurme_ref_user['nick']} (ID: {st.session_state.gurme_ref_user['uid']})"
                st.caption(f"Referans: {ref_info}")

                if st.form_submit_button("Onaya Gönder"):
                    if bn and ot:
                        u_img = "https://via.placeholder.com/300x200?text=Firsat"
                        if img_file:
                            upl = upload_to_imgbb(img_file)
                            if upl: u_img = upl
                        
                        ref_uid = ""; ref_nick = "Yok"
                        if st.session_state.gurme_ref_user: 
                            ref_uid = st.session_state.gurme_ref_user['uid']
                            ref_nick = st.session_state.gurme_ref_user['nick']
                        
                        fb.add_gurme_offer({ "business_name": bn, "city": ct, "offer_title": ot, "discount_code": dc, "link": lnk, "img": u_img, "address": adr, "referrer_uid": ref_uid, "referrer_nick": ref_nick, "uid": st.session_state.user_uid if st.session_state.user_uid else "guest" })
                        
                        # Reset State
                        st.session_state.gurme_ref_user = None
                        st.success("✅ İlanınız yönetici onayına gönderildi. Onaylandığında 5 gün boyunca yayında kalacak!"); time.sleep(2); st.rerun()
                    else: st.warning("İşletme adını ve başlığı girmelisiniz.")

    st.divider()

    # --- KART LİSTELEME GRID ---
    all_offers = fb.get_gurme_offers(status="active")
    
    # FİLTRELEME MANTIĞI
    if selected_filter == "Web":
        offers = [o for o in all_offers if o.get('city') == "Web"]
    else:
        offers = [o for o in all_offers if o.get('city') == selected_filter]
    
    if not offers:
        st.info(f"📢 {selected_filter} kategorisinde şu an aktif fırsat yok.")
    
    # Grid Slot Sayısı (Örn: 9 Dolu Kart veya Placeholder)
    TOTAL_SLOTS = 9
    
    # Aktif İlanlar + Placeholderlar ile listeyi tamamla
    display_list = offers[:TOTAL_SLOTS] # Max 9 aktif gösterelim (sayfalama yoksa)
    
    # 3'erli satırlar
    # Eğer toplam eleman display_list kadar ise, geri kalanı placeholder yapalım mı?
    # Kullanıcı "üzerinde reklam olan kartı geçip... yerleşsin" dedi.
    # Bu yüzden toplam slot sayısına tamamlayana kadar placeholder ekleyelim.
    
    placeholders_needed = max(0, 6 - len(display_list)) # Minimum 6 kart gösterelim
    
    final_list = display_list + [{"type": "placeholder"}] * placeholders_needed
    
    cols = st.columns(3)
    for i, item in enumerate(final_list):
        with cols[i % 3]:
            if item.get("type") == "placeholder":
                # Placeholder Kartı
                st.markdown("""
                <div style="background:#f8f9fa; border:2px dashed #ccc; border-radius:10px; height:300px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; color:#888; margin-bottom:20px; transition:0.3s;">
                    <div style="font-size:40px;">📢</div>
                    <div style="font-weight:bold; font-size:18px; margin-top:10px;">Senin Reklamını<br>Bekliyoruz</div>
                    <div style="font-size:12px; margin-top:5px;">Burada yer almak için<br>yukarıdaki (+) butonuna tıkla</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Dolu Kart
                offer = item
                img_src = offer.get('img') or "https://via.placeholder.com/300x200?text=Firsat"
                link_html = ""
                if offer.get('link'):
                    link_html = f'<a href="{offer["link"]}" target="_blank" style="display:block; text-align:center; background:#27ae60; color:white; text-decoration:none; padding:5px; border-radius:5px; margin-top:5px; font-size:12px;">👉 Fırsata Git</a>'
                
                # Kod Gösterimi
                code_html = ""
                if offer.get('discount_code'):
                     code_html = f'<div style="background:#eee; padding:5px; text-align:center; letter-spacing:1px; font-family:monospace; margin-top:5px; font-size:12px; border:1px dashed #aaa;">KOD: <b>{offer["discount_code"]}</b></div>'
                
                # Kart HTML
                st.markdown(f"""
                <div class="gurme-card" style="height:300px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div style="height:140px; overflow:hidden; border-radius:8px 8px 0 0;">
                        <img src="{img_src}" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    <div style="padding:10px; flex-grow:1;">
                        <div style="font-size:12px; color:#e67e22; font-weight:bold;">{offer['city']}</div>
                        <div style="font-weight:bold; font-size:15px; margin:2px 0; line-height:1.2;">{offer['business_name']}</div>
                        <div style="font-size:13px; color:#555;">{offer['offer_title']}</div>
                        {code_html}
                        {link_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_sponsor(fb):
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%); color:white; padding:30px; border-radius:15px; text-align:center; margin-bottom:20px;">
        <h1 style="color:white; margin:0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">🌍 GEZGİN ÖĞRENCİ FONU</h1>
        <h3 style="color:white; margin-top:10px; font-weight:lighter;">"Her Reklam, Bir Bilet"</h3>
        <p style="font-size:18px; margin-top:15px; max-width:600px; margin-left:auto; margin-right:auto;">
            Sitemize verilen reklam gelirleri ve sponsorluklarla her ay bir üniversite öğrencisini hayalindeki şehre gönderiyoruz.
            Burada satış yok, dayanışma var!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- GOOGLE ADSENSE PLACEHOLDER (YÜKSEK GELİRLİ ALAN) ---
    # --- GOOGLE ADSENSE (YÜKSEK GELİRLİ ALAN) ---
    components.html("""
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8177405180533300"
         crossorigin="anonymous"></script>
    <!-- yatay görüntülü -->
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-8177405180533300"
         data-ad-slot="7430881961"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>
         (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
    """, height=150)

    # --- GEZGİN VİTRİNİ (Görsel Galeri) ---
    st.markdown("### 📸 Bizden Kareler (Gezgin Albümü)")
    
    winners = fb.get_past_winners()
    if not winners:
        st.info("Henüz ilk gezginimizi yolcu etmedik. Belki de o sensin? 👇")
    else:
        # Carousel benzeri yan yana kartlar
        cols = st.columns(3)
        for i, w in enumerate(winners):
            with cols[i % 3]:
                # Görsel olmadığı için rastgele seyahat görseli veya placeholder
                rand_img = f"https://source.unsplash.com/300x200/?travel,trip,student&sig={i}"
                st.markdown(f"""
                <div style="background:white; border-radius:10px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1); margin-bottom:15px;">
                    <img src="{rand_img}" style="width:100%; height:150px; object-fit:cover;">
                    <div style="padding:15px;">
                        <div style="font-weight:bold; color:#333;">🎉 {w['nick']}</div>
                        <div style="color:#666; font-size:13px; margin:5px 0;">📍 Rota: {w['route']}</div>
                        <div style="font-size:12px; color:#999;">📅 {w['date']}</div>
                        <div style="margin-top:10px; font-style:italic; font-size:12px; color:#555;">"Teşekkürler GeziStory!"</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()

    # --- BAŞVURU ALANI ---
    c_app1, c_app2 = st.columns([1, 1])
    
    with c_app1:
        # DİNAMİK GÖRSEL (Backend'den veya varsayılan)
        sc = fb.get_sidebar_content()
        # Default görsel
        def_img = "https://plus.unsplash.com/premium_photo-1677343210638-5d3ce6ddbf85?q=80&w=2574&auto=format&fit=crop"
        final_img = sc.get('sponsor_hero_img', def_img)
        
        # 250px GENİŞLİK SABİTLEME (HTML ile)
        st.markdown(f"""
        <div style="display:flex; justify-content:center; align-items:center;">
            <img src="{final_img}" style="width:250px; border-radius:10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        </div>
        <div style="text-align:center; font-size:12px; color:#666; margin-top:5px;">{sc.get('sponsor_img_caption', 'Sırt çantanı hazırla!')}</div>
        """, unsafe_allow_html=True)
    
    with c_app2:
        st.markdown("### 🎒 Sıradaki Gezgin Sen Ol!")
        st.write("Üniversite öğrencisi misin? Gezme tutkun var ama bütçen mi yok? Başvurunu yap, sıradaki talihli sen ol.")
        
        with st.form("sponsor_application_form"):
            name = st.text_input("Adın Soyadın")
            email = st.text_input("E-posta Adresin (Sonuç için)") # YENİ ALAN
            uni = st.text_input("Okuduğun Üniversite & Bölüm")
            target = st.text_input("Gitmek İstediğin Şehir (Yurt içi)")
            why = st.text_area("Neden seni seçmeliyiz? (Kısaca hayalinden bahset)", height=100)
            
            if st.form_submit_button("Başvurumu Gönder 🚀"):
                if not st.session_state.user_token:
                    st.error("Başvuru yapmak için giriş yapmalısın.")
                elif len(name) < 3 or len(why) < 10 or "@" not in email:
                    st.warning("Lütfen alanları eksiksiz doldurun ve geçerli bir e-posta girin.")
                else:
                    ok = fb.add_sponsor_application({
                        "uid": st.session_state.user_uid,
                        "name": name,
                        "email": email,
                        "uni": uni,
                        "target": target,
                        "why": why
                    })
                    if ok:
                        st.balloons()
                        st.success("✅ Başvurun alındı! Sonuçlar her ayın 1'inde açıklanır.")
                    else:
                        st.error("Bir hata oluştu. Lütfen tekrar dene.")
def render_kesfet(stories, fb, search_term=""):
    stories = [s for s in stories if not s.get('stops') or len(s['stops']) < 3]
    user_name = st.session_state.user_nick if st.session_state.user_nick else "Gezgin"
    
    # Otomatik Konum Tespiti
    if get_geolocation and "auto_location_set" not in st.session_state:
        try: 
            loc = get_geolocation()
            if loc and "coords" in loc:
                lat = loc["coords"]["latitude"]; lon = loc["coords"]["longitude"]
                detected_city = get_city_from_coordinates(lat, lon)
                if detected_city:
                    all_cities = sorted(list(set(s['city'] for s in stories)))
                    # "Province", "City" temizliği
                    detected_city = detected_city.replace(" Province", "").replace(" City", "")
                    if detected_city in all_cities:
                        st.session_state.active_city = detected_city
                        st.toast(f"📍 Konumun tarayıcıdan alındı: {detected_city}")
                    else:
                        st.session_state.active_city = "Tümü"
                        st.toast(f"📍 {detected_city} konumundasın ama burada henüz hikaye yok.")
                st.session_state.auto_location_set = True
                st.rerun()
        except: pass

    c_head, c_sel = st.columns([2,1])
    
    # LOGIN BUTTON (User Request: Above City Select)
    if not st.session_state.user_token:
        with c_sel:
            if st.button("🔑 Giriş Yap / Kayıt Ol", use_container_width=True, type="primary"): 
                entry_dialog(fb)
    
    # UPDATE: Şehir listesi tüm illerden gelsin
    if 'active_city' not in st.session_state: st.session_state.active_city = "Tümü"
    sel_city = c_sel.selectbox("Şehir Seç:", ["Tümü"] + sorted(ALL_PROVINCES), key="city_selector")
    st.session_state.active_city = sel_city 
    
    # --- ŞEHİR DEDEKTİFİ (GASTRO-INTEL) DISPLAY (SOLA HİZALI & EN ÜST) ---
    if sel_city != "Tümü":
        guide = fb.get_city_guide(sel_city)
        # GURME GEZGİN NOTU HTML HAZIRLIĞI
        gourmet_html = ""
        if guide.get('gourmet_note'):
            gourmet_html = f"""<div style="margin-top:10px; padding:10px; border-left: 4px solid #e67e22; background-color: #fff5e6; color:#d35400; font-size:14px; border-radius: 0 4px 4px 0;"><b style="display:block; margin-bottom:4px;">👨‍🍳 Gurme Gezgin Notu:</b><i>"{guide['gourmet_note']}"</i></div>"""

        # Kart Tasarımı (Doğrudan c_head içine, sol tarafa)
        c_head.markdown(f"""
        <div style="background-color:#fff3cd; border-left: 5px solid #ffecb3; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="margin:0; color:#856404; display:flex; align-items:center; gap:8px;">🕵️ Şehir Dedektifi: {sel_city}</h4>
            <div style="margin-top:10px; font-size:14px; display:flex; flex-wrap:wrap; gap:15px;">
                 <span style="background:rgba(255,255,255,0.7); padding:4px 8px; border-radius:4px;"><b>🍽️ Ne Yenir:</b> {guide['yemek']}</span>
                 <span style="background:rgba(255,255,255,0.7); padding:4px 8px; border-radius:4px;"><b>💰 Bütçe:</b> {guide['butce']}</span>
            </div>
            <div style="margin-top:8px; font-size:14px; font-style:italic; background:#fff; padding:6px; border-radius:4px; border:1px dashed #ddd;">
                <b>💡 Tüyosu:</b> "{guide['tuyo']}"
            </div>
            {gourmet_html}
        </div>
        """, unsafe_allow_html=True)
        
        # DÜZENLEME BUTONU (Sadece Admin ve Evliya Çelebi)
        user_role = st.session_state.get('user_role', 'caylak')
        if user_role in ['admin', 'evliya_celebi']:
            with c_head.expander("✏️ Racon Kes (Düzenle)"):
                with st.form(key="edit_guide_form"):
                    ny = st.text_input("Ne Yenir", value=guide['yemek'])
                    bu = st.text_input("Bütçe Bilgisi", value=guide['butce'])
                    ty = st.text_area("Şehir Tüyosu (Racon)", value=guide['tuyo'])
                    gn = st.text_area("👨‍🍳 Gurme Gezgin Notu (Opsiyonel)", value=guide.get('gourmet_note', ''))
                    if st.form_submit_button("Güncelle"):
                        success = fb.update_city_guide(sel_city, {"yemek": ny, "butce": bu, "tuyo": ty, "gourmet_note": gn})
                        if success: st.success("Racon güncellendi!"); time.sleep(1); st.rerun()
                        else: st.error("Hata oluştu.")
    else:
        # Şehir seçilmemişse yine c_head alanını boş bırakmamak veya varsayılan bir şey göstermek adına
        # Kullanıcı "Hoşgeldin" yazısını kaldırmamızı istediği için burayı boş geçiyoruz.
        # Alternatif: Genel bir "Hoş geldiniz" mesajı veya slogan.
        c_head.markdown(f"### 👋 Merhaba, {user_name}! Keşfetmeye başla.")
 
    
    if 'active_mood' not in st.session_state: st.session_state.active_mood = "Hepsi"
    col_count = 5 if st.session_state.user_token else 4
    m_cols = st.columns(col_count)
    
    def mood_btn(label, mood_key, col):
        style = "primary" if st.session_state.active_mood == mood_key else "secondary"
        if col.button(label, key=f"btn_{mood_key}", type=style, use_container_width=True):
            st.session_state.active_mood = mood_key; st.rerun()
    
    mood_btn("🌍 Hepsi", "Hepsi", m_cols[0])
    if st.session_state.user_token:
        mood_btn("👥 Takip", "Takip", m_cols[1]); mood_btn("💸 Parasızım", "Parasiz", m_cols[2]); mood_btn("📸 Fotoğraf", "Foto", m_cols[3]); mood_btn("🍽️ Lezzet", "Acim", m_cols[4])
    else:
        mood_btn("💸 Parasızım", "Parasiz", m_cols[1]); mood_btn("📸 Fotoğraf", "Foto", m_cols[2]); mood_btn("🍽️ Lezzet", "Acim", m_cols[3])
        if st.session_state.active_mood == "Takip": st.session_state.active_mood = "Hepsi"; st.rerun()

    mood = st.session_state.active_mood
    
    main_col, side_col = st.columns([0.7, 0.3])
    with main_col:
        filtered = stories
        if search_term:
            filtered = [s for s in stories if search_term.lower() in s['title'].lower() or search_term.lower() in s['city'].lower()]
        else:
            if sel_city != "Tümü": filtered = [s for s in filtered if s['city'] == sel_city]
            if mood == "Parasiz": 
                filtered = [s for s in filtered if s.get('budget', 0) <= 300]
                filtered.sort(key=lambda x: x.get('budget', 0))
                st.info("💸 Bütçe dostu rotalar.")
            elif mood == "Foto": 
                filtered = [s for s in filtered if s['category'] in ['Manzara', 'Doğa', 'Mekan']]
                st.info("📸 Galeri Modu.")
            elif mood == "Acim": 
                filtered = [s for s in filtered if s['category'] in ['Gurme', 'Kafe', 'Yemek', 'Mekan']]
                st.info("🍽️ Lezzet durakları.")
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
                else:
                    with st.form("p_f"):
                        c=st.selectbox("Şehir",["İstanbul","Ankara","İzmir","Nevşehir","Antalya","Mardin","Rize","Diğer"]); i=st.file_uploader("Foto"); t=st.text_input("Başlık"); 
                        s=st.text_area("Not"); tags_input = st.text_input("Etiketler"); k=st.radio("Kategori",["Gurme","Tarih","Doğa","Mekan","Manzara"],horizontal=True); cost = st.number_input("Tahmini Harcama (TL)", min_value=0, step=10)
                        
                        # YENİ: Sorumluluk Beyanı
                        resp_check_single = st.checkbox("Paylaştığım içeriğin (yazı/görsel) tüm sorumluluğunun bana ait olduğunu beyan ederim.", key="resp_check_single")

                        submitted = st.form_submit_button("Paylaş", type="secondary")
                        if submitted:
                            if not i or not t or not s: st.warning("Eksik bilgi girdiniz.")
                            elif not resp_check_single: st.error("Lütfen içerik sorumluluk beyanını onaylayın.")
                            else:
                                u=upload_to_imgbb(i)
                                tags_processed = [tag.strip().replace("#", "") for tag in tags_input.split(",") if tag.strip()]
                                if u: 
                                    fb.add_story({"title":t, "city":c, "img":u, "summary":s, "category":k, "budget":cost, "stops":[], "author":st.session_state.user_nick, "uid":st.session_state.user_uid, "tags": tags_processed})
                                    fb.add_points(st.session_state.user_uid, 30)
                                    st.success("Yayınlandı! (+30 Puan)"); time.sleep(1); st.rerun()

        # --- SAYFALAMA (LOAD MORE) ---
        if 'kesfet_limit' not in st.session_state: st.session_state.kesfet_limit = 10
        
        display_stories = filtered[:st.session_state.kesfet_limit]
        
        st.markdown(f"##### 🔥 İçerikler ({len(filtered)})")
        for i in range(0, len(display_stories), 2):
            for col, story in zip(st.columns(2), display_stories[i:i+2]):
                with col:
                    st.markdown(get_discover_card_html(story), unsafe_allow_html=True)
                    b1, b2, b3 = st.columns(3)
                    if b1.button(f"{'❤️' if story.get('liked_by_me') else '🤍'} {story['like_count']}", key=f"k_lk_{story['id']}"):
                         if st.session_state.user_token: fb.update_interaction(story['id'], "like", current_likes=story.get('likes', [])); st.rerun()
                         else: guest_warning_dialog()
                    if b2.button(f"💬 {len(story.get('comments', []))}", key=f"k_cm_{story['id']}"):
                         if not st.session_state.user_token: guest_warning_dialog()
                         else: fb.update_interaction(story['id'], "view"); view_comments_dialog(story, fb)
                    if b3.button(f"👤 {story['author']}", key=f"vp_st_{story['id']}"): st.session_state.view_target_uid = story['uid']; st.session_state.active_tab = "public_profile"; st.rerun()
                    if st.session_state.user_uid == story['uid']:
                        if st.button("🗑️ Sil", key=f"del_st_{story['id']}"): fb.delete_story(story['id']); st.rerun()

        if len(filtered) > st.session_state.kesfet_limit:
            if st.button("👇 Daha Fazla Göster (+10)", key="kesfet_load_more", type="primary", use_container_width=True):
                st.session_state.kesfet_limit += 10
                st.rerun()

    with side_col:
        sys_data = fb.get_sidebar_content()
        
        # 1. Durum: Sistem Duyurusu Varsa -> HTML içine göm
        if sys_data.get('ann_text') or sys_data.get('ann_img'):
            html_out = '<div class="sidebar-box" style="min-height: 250px;"><div class="sidebar-title">📢 Duyuru - Son Aktivite</div>'
            
            if sys_data.get('ann_img'):
                html_out += f'<img src="{sys_data["ann_img"]}" style="width:100%; border-radius:5px; margin-bottom:10px;">'
                
            if sys_data.get('ann_text'):
                # st.info benzeri stil
                html_out += f'''
                <div style="background-color:#e1f5fe; border-left: 5px solid #0288d1; color:#01579b; padding:10px; border-radius:4px; font-size:14px; margin-top:5px;">
                    {sys_data["ann_text"]}
                </div>
                '''
            html_out += '</div>'
            st.markdown(html_out, unsafe_allow_html=True)
            
        # 2. Durum: Duyuru Yoksa -> Son Aktiviteler (Eski Yöntem)
        else:
            # HTML Link Yapısına Dönüştürüldü (Kutu içi görünüm için)
            # Yükseklik sabitlendi ve taşmalar gizlendi (overflow:hidden)
            html_out = '<div class="sidebar-box" style="height: 280px; overflow: hidden; display: flex; flex-direction: column;"><div class="sidebar-title" style="margin-bottom: 5px;">📢 Duyuru - Son Aktivite</div>'
            html_out += '<div style="font-size:12px; color:#666; margin-bottom:10px;">Son Aktiviteler:</div>'
            
            # Son 5 aktivite (Kullanıcı İsteği: 5'e çıkarıldı)
            for p in fb.get_forum_posts()[:5]:
                # Metni kısalt
                display_title = f"{p['title'][:25]}..." if len(p['title']) > 25 else p['title']
                
                # HTML Link (Boşluksuz yapı) & Cookie Consent Fix
                html_out += f'''<div style="margin-bottom:6px; border-bottom:1px solid #eee; padding-bottom:4px;"><a href="?tab=forum&focus_post={p['id']}&cookie_consent=true" target="_self" style="text-decoration:none; color:#2C3E50; font-weight:bold; font-size:13px; display: block;">💬 {display_title}</a></div>'''
                
            html_out += '</div>'
            st.markdown(html_out, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-box"><div class="sidebar-title">✨ Sponsor</div></div>', unsafe_allow_html=True)
        
        # --- 1. REKLAM VERME ALANI (ÜSTE TAŞINDI) ---
        with st.expander("📢 Buraya Reklam Ver"):
            st.markdown("""
            <div style="background-color:#FEF9E7; border-left: 4px solid #D35400; padding:15px; border-radius:4px; margin-bottom:15px; color:#2C3E50;">
                <h5 style="margin:0; color:#D35400; font-weight:bold;">📢 Vitrin İlanı (48 Saat)</h5>
                <p style="margin:5px 0 0 0; font-size:14px;">Gezginlerin rotasında öne çıkın.</p>
                <div style="margin-top:5px; font-weight:bold; font-size:16px;">Ücret: 250 TL</div>
            </div>
            """, unsafe_allow_html=True)
            
            # SESSION STATE INIT (Sidebar Formu İçin)
            if 'sidebar_ad_form' not in st.session_state: st.session_state.sidebar_ad_form = {}
            if 'show_sidebar_payment' not in st.session_state: st.session_state.show_sidebar_payment = False

            # 1. ADIM: FORM
            if not st.session_state.show_sidebar_payment:
                with st.form("sidebar_user_ad_form"):
                    bn = st.text_input("İşletme / Kampanya Adı", value=st.session_state.sidebar_ad_form.get('bn', ''))
                    lnk = st.text_input("Yönlendirilecek Link", value=st.session_state.sidebar_ad_form.get('lnk', ''))
                    em = st.text_input("E-Posta Adresiniz (Admin görür, yayınlanmaz)", value=st.session_state.sidebar_ad_form.get('em', ''))
                    img_file = st.file_uploader("Görsel (Kare/Dikey önerilir)", type=['jpg','png'])
                    
                    submitted = st.form_submit_button("✅ Reklamı Onayla (Ödeme Adımı)", type="primary")
                    
                    if submitted:
                        if bn and lnk and em:
                            img_url = ""
                            if img_file: img_url = upload_to_imgbb(img_file)
                            elif st.session_state.sidebar_ad_form.get('img_url'): img_url = st.session_state.sidebar_ad_form.get('img_url')

                            if not img_url: img_url = "https://via.placeholder.com/300x250?text=REKLAM" # Demo Fallback

                            st.session_state.sidebar_ad_form = {"bn": bn, "lnk": lnk, "em": em, "img_url": img_url}
                            st.session_state.show_sidebar_payment = True
                            st.rerun()
                        else: st.warning("Lütfen zorunlu alanları doldurun.")
            
            # 2. ADIM: ÖDEME
            else:
                st.success("✅ Taslak oluşturuldu! Şimdi ödeme adımındasınız.")
                st.markdown(f"""
                <div style="background:#e8f5e9; padding:15px; border-radius:10px; border:1px solid #c8e6c9; margin-bottom:10px;">
                    <h4>💳 Ödeme Yap</h4>
                    <p>Reklamınızın yayına girmesi için Shopier üzerinden güvenle ödeme yapabilirsiniz.</p>
                    <a href="{SHOPIER_LINK_REKLAM}" target="_blank" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; display:inline-block; font-weight:bold;">Shopier ile Öde (250 TL)</a>
                </div>
                """, unsafe_allow_html=True)
                
                c_back, c_pay = st.columns(2)
                if c_back.button("⬅️ Düzenle", key="sb_back"):
                    st.session_state.show_sidebar_payment = False
                    st.rerun()
                
                if c_pay.button("Ödemeyi Yaptım, Onaya Gönder", key="sb_pay_ok", type="primary"):
                    fdata = st.session_state.sidebar_ad_form
                    # NEW METHOD: add_sidebar_ad (Consistent with Admin Panel)
                    # Status will be 'pending_approval'
                    data = {
                        "uid": st.session_state.user_uid or "guest",
                        "business_name": fdata['bn'],
                        "link": fdata['lnk'],
                        "email": fdata['em'],
                        "image": fdata['img_url'],
                        "ad_type": "sidebar" # Vitrin Reklamı
                    }
                    if fb.add_sidebar_ad(data):
                        st.balloons()
                        st.success("Talebiniz yöneticiye iletildi! Onaylandıktan sonra yayına girecektir.")
                        st.session_state.show_sidebar_payment = False
                        st.session_state.sidebar_ad_form = {}
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Bir hata oluştu.")
        
        # --- 2. AKTİF REKLAM GÖRSELİ (300px Sabit Yükseklik) ---
        active_user_ads = fb.get_active_sidebar_ads(limit=1, ad_type="sidebar")
        
        ad_html = '<div style="width:100%; height:300px; border-radius:8px; overflow:hidden; border:1px solid #ddd; position:relative; margin-top:15px;">'

        if active_user_ads:
            ad = active_user_ads[0]
            ad_html += f'''
            <a href="{ad['link']}" target="_blank" style="text-decoration:none; display:block; height:100%;">
                <img src="{ad['image']}" style="width:100%; height:100%; object-fit:cover;">
                <div style="position:absolute; bottom:0; left:0; width:100%; background:linear-gradient(to top, rgba(0,0,0,0.8), transparent); color:white; padding:10px 5px 5px 5px; text-align:center; font-size:12px; font-weight:bold;">
                    {ad.get('business_name', 'Fırsat')}
                </div>
            </a>
            '''
        elif sys_data.get('ad_youtube'): 
            # Video özel durum (iframe)
            # st.video HTML içine gömülemez, bu yüzden placeholder içinde video
             ad_html += '<div style="width:100%; height:100%; background:#000; display:flex; align-items:center; justify-content:center; color:white;">Video İçeriği</div>'
             # Not: Video varsa HTML yerine st.video kullanılabilir ama 300px zorlaması için HTML iframe gerek.
             # Şimdilik video varsa dışarıda kalsın veya basit img kullanalım.
             # Kullanıcı sadece görselden bahsetti. 
             pass
        elif sys_data.get('ad_img'): 
            ad_html += f'''
            <a href="{sys_data.get('ad_link', '#')}" target="_blank" style="text-decoration:none; display:block; height:100%;">
                <img src="{sys_data['ad_img']}" style="width:100%; height:100%; object-fit:cover;">
            </a>
            '''
        else: 
            ad_html += '''
            <div style="width:100%; height:100%; background:#f9f9f9; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#888;">
                <div style="font-size:40px;">📢</div>
                <div style="margin-top:10px; font-weight:bold;">Reklam Alanı</div>
                <div style="font-size:12px;">Sizin markanız burada olabilir</div>
            </div>
            '''
        
        ad_html += '</div>'
        st.markdown(ad_html, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

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

    # 5. LİSTELEME & DÜZEN (ROTA BAZLI SATIRLAR)
    if not routes and selected_city != "Tümü":
        msg = f"{selected_city} için henüz planlanmış bir rota yok."
        render_empty_state(msg, "🎒")
    else:
        if not routes: render_empty_state("Henüz planlanmış bir rota yok.", "🎒"); return

        st.markdown("##### 🎒 Tüm Rotalar ve Fırsatlar")

        # --- OPTİMİZASYON: Reklamları Döngü Dışında Çek ---
        # 1. Havuzu Doldur (Route Ads)
        all_route_ads = fb.get_active_sidebar_ads(limit=50, ad_type="route_ad") 
        if not all_route_ads: all_route_ads = [] 
        random.shuffle(all_route_ads)
        
        # --- SAYFALAMA (LOAD MORE) ---
        if 'rotalar_limit' not in st.session_state: st.session_state.rotalar_limit = 10
        display_routes = routes[:st.session_state.rotalar_limit]

        ad_pool_index = 0

        for route in display_routes:
            with st.container():
                # YENİ DÜZEN: 50% Rota Kartı | 50% Sponsor Alanı
                c_route, c_sponsor = st.columns(2, gap="medium")
                
                # --- SOL: ROTA KARTI ---
                with c_route:
                    st.markdown(get_route_card_html(route), unsafe_allow_html=True)
                    if st.button("🔍 İNCELE", key=f"r_vw_{route['id']}", use_container_width=True):
                         fb.update_interaction(route['id'], "view")
                         view_route_detail_dialog(route, fb)

                # --- SAĞ: SPONSOR ALANI ---
                with c_sponsor:
                    # 1. Sponsor / Reklam Butonu
                    if st.button("📢 Sponsor Ol / Reklam Ver", key=f"sp_btn_{route['id']}", type="secondary", use_container_width=True):
                         render_ad_application_dialog(fb)
                    
                    st.info("250 TL karşılığı reklamın 1 ay vitrinde kalsın. Rota sahibi de kazansın.")
                    
                    st.caption("✨ Vitrin Reklamları")

                    # 2. Reklam Slotları (2 Adet - Döngüsel Dağıtım)
                    slots = []
                    # Sadece aktif reklam varsa dağıt
                    if all_route_ads:
                        for _ in range(2):
                            slots.append(all_route_ads[ad_pool_index % len(all_route_ads)])
                            ad_pool_index += 1
                    
                    # Eğer yetmezse placeholder ekle
                    while len(slots) < 2:
                        slots.append(None) 
                    
                    c_ad1, c_ad2 = st.columns(2)
                    
                    for i, ad in enumerate(slots):
                        target_col = c_ad1 if i == 0 else c_ad2
                        with target_col:
                            if ad:
                                # Aktif Reklam
                                st.markdown(f"""
                                <div style="background:white; border:1px solid #eee; border-radius:6px; overflow:hidden; box-shadow:0 1px 2px rgba(0,0,0,0.05); text-align:center;">
                                    <a href="{ad['link']}" target="_blank" style="text-decoration:none; color:inherit; display:block;">
                                        <img src="{ad['image']}" style="width:100%; height:140px; object-fit:cover;">
                                        <div style="padding:5px; font-size:10px; font-weight:bold;">{ad['business_name']}</div>
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Placeholder
                                st.markdown(f"""
                                <div style="background:#f9f9f9; border:1px dashed #ccc; border-radius:6px; height:160px; display:flex; flex-direction:column; align-items:center; justify-content:center; color:#aaa; font-size:10px;">
                                    <div style="font-size:24px;">📢</div>
                                    <div>Reklam Ver</div>
                                </div>
                                """, unsafe_allow_html=True)

            st.divider()

        if len(routes) > st.session_state.rotalar_limit:
            if st.button("👇 Daha Fazla Göster (+10)", key="rotalar_load_more", type="primary", use_container_width=True):
                st.session_state.rotalar_limit += 10
                st.rerun()

    # ÖZEL DIALOG: Misafir Uyarısı (Challenge İçin)
    # Bu kısım render_challenge fonksiyonuna aittir.

def render_challenge(fb):
    st.markdown("### 🏆 MEYDAN OKUMA (Challenge)")
    
    # --- GOOGLE ADSENSE (Yatay Banner) ---
    components.html("""
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8177405180533300"
         crossorigin="anonymous"></script>
    <!-- yatay görüntülü -->
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-8177405180533300"
         data-ad-slot="7430881961"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>
         (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
    """, height=100)

    if hasattr(st, "dialog"):
        @st.dialog("⚠️ Yarışmaya Katılmak İçin Giriş Yap")
        def challenge_login_dialog(fb_svc):
             st.warning("Yarışma heyecanına ortak olmak için üye olmalısın!")
             render_login_register_form(fb_svc)
             if st.button("Kapat"): st.rerun()
    elif hasattr(st, "experimental_dialog"):
        @st.experimental_dialog("⚠️ Yarışmaya Katılmak İçin Giriş Yap")
        def challenge_login_dialog(fb_svc):
             st.warning("Yarışma heyecanına ortak olmak için üye olmalısın!")
             render_login_register_form(fb_svc)
             if st.button("Kapat"): st.rerun()
    else:
        def challenge_login_dialog(fb_svc): st.error("Giriş yapmalısın!")

    # 3 SEKME YAPISI
    tab1, tab2, tab3 = st.tabs(["🚀 YARIŞMA (Aktif)", "📸 GÜNCEL KATILIMLAR", "🗄️ GEÇMİŞ ARŞİV"])
    
    active_ch = fb.get_active_challenge()
    
    # --- TAB 1: YARIŞMA & KATILIM ---
    with tab1:
        c_left, c_right = st.columns([1, 1])
        with c_left:
            # YÖNETİM PANELİ
            if st.session_state.user_role in ['admin', 'mod']:
                with st.expander("⚙️ Yönetim Paneli (Yeni Yarışma & Arşivleme)"):
                    st.info("ℹ️ Yeni yarışma başlattığınızda, mevcut yarışma ve katılımları otomatik olarak 'Arşiv' sekmesine taşınır.")
                    with st.form("new_ch_form"):
                        ch_id_input = st.number_input("Yeni Hafta No (ID)", min_value=int(active_ch['id'])+1 if active_ch else 1, value=int(active_ch['id'])+1 if active_ch else 1)
                        ch_title = st.text_input("Yeni Başlık")
                        ch_desc = st.text_area("Yeni Açıklama")
                        ch_reward = st.text_input("Yeni Ödül")
                        ch_img_file = st.file_uploader("Yeni Görsel", type=['jpg', 'png']) 
                        
                        if st.form_submit_button("🚀 Arşivle ve Yenisini Başlat"):
                            if ch_title and ch_reward:
                                img_url = None
                                if ch_img_file: img_url = upload_to_imgbb(ch_img_file)
                                
                                ret = fb.archive_and_start_new_challenge(ch_id_input, ch_title, ch_desc, ch_reward, img_url)
                                if ret: st.success("Eski yarışma arşivlendi, yenisi başladı!"); time.sleep(1.5); st.rerun()
                                else: st.error("Hata oluştu.")
                            else: st.warning("Bilgileri eksiksiz giriniz.")
            
            # AKTİF YARIŞMA KARTI
            if active_ch:
                img_html = ""
                if active_ch.get('img'):
                    # GÖRSEL BOYUTU: 250px
                    img_html = f'<img src="{active_ch["img"]}" style="width:100%; height:250px; object-fit:cover; border-radius:5px; margin-bottom:10px; border:2px solid #fff;">'
                
                st.markdown(f"""<div class="challenge-board"><div class="challenge-title">🔥 CHALLENGE #{active_ch['id']} 🔥</div>{img_html}<h2 style="color:white; margin-top:5px;">{active_ch['title']}</h2><p style="color:#ddd;">{active_ch['desc']}</p><div style="background:#FFD700; color:black; padding:5px; border-radius:5px; font-weight:bold; display:inline-block; margin-top:10px;">🎁 ÖDÜL: {active_ch['reward']}</div></div>""", unsafe_allow_html=True)
            else: render_empty_state("Aktif bir görev yok.", "💤")
            
            # ANKET ALANI
            poll = fb.get_challenge_poll()
            if poll:
                st.markdown("---")
                st.markdown(f"### 🗳️ {poll['question']}")
                has_voted = False
                if st.session_state.user_token: has_voted = st.session_state.user_uid in poll['voted_uids']
                total_votes = sum(o['count'] for o in poll['options'])
                for opt in poll['options']:
                    col_p1, col_p2 = st.columns([3, 1])
                    with col_p1:
                         if has_voted or not st.session_state.user_token:
                             percentage = int((opt['count'] / total_votes * 100)) if total_votes > 0 else 0
                             st.markdown(f"**{opt['text']}**"); st.progress(percentage / 100); st.caption(f"%{percentage} ({opt['count']} oy)")
                         else:
                             if st.button(f"Oy Ver: {opt['text']}", key=f"vote_{opt['index']}", use_container_width=True):
                                 if fb.vote_challenge_poll(opt['index'], st.session_state.user_uid):
                                     st.success("Kaydedildi!"); time.sleep(1); st.rerun()
                if not st.session_state.user_token: st.info("Oy kullanmak için giriş yapın.")
                elif has_voted: st.success("✅ Oy kullandınız.")
        
        with c_right:
            if st.session_state.get(f"ch_submitted_{active_ch['id']}", False):
                st.success("✅ Raporun iletildi! 'Güncel Katılımlar' sekmesinden görebilirsin.")
            else:
                st.markdown("##### 🎯 Senin Sıran!")
                with st.form("ch_entry_form"):
                    e_img = st.file_uploader("Kanıt Fotoğrafı", type=['jpg', 'png'])
                    e_text = st.text_area("Hikayen")
                    e_city = st.selectbox("Nerede?", ["Seçiniz"] + ALL_PROVINCES)
                    
                    submitted = st.form_submit_button("Katıl ve Raporla")
                    if submitted:
                        if not st.session_state.user_token: challenge_login_dialog(fb)
                        else:
                            u = upload_to_imgbb(e_img)
                            if u: 
                                fb.add_challenge_entry(active_ch['id'], {"user": st.session_state.user_nick, "text": e_text, "city": e_city, "img": u})
                                st.session_state[f"ch_submitted_{active_ch['id']}"] = True
                                st.rerun()
                            else:
                                if not e_img: st.warning("Kanıt fotoğrafı şart!")
                                else: st.error("Yükleme hatası.")

    # --- TAB 2: GÜNCEL KATILIMLAR ---
    with tab2:
        if active_ch:
            st.markdown(f"### 📸 Bu Haftanın ({active_ch['title']}) Katılımları")
            entries = fb.get_challenge_entries(active_ch['id'])
            if not entries: render_empty_state("Henüz kimse katılmadı. İlk sen ol!", "🚀")
            else:
                cols = st.columns(3)
                for i, entry in enumerate(entries):
                    with cols[i % 3]:
                        st.markdown(f"""<div style="border:1px solid #ddd; border-radius:8px; overflow:hidden; margin-bottom:15px;"><img src="{entry['img']}" style="width:100%; height:200px; object-fit:cover;"><div style="padding:10px;"><div style="font-weight:bold;">{entry['user']}</div><div style="font-size:12px; color:#555;">{entry['text']}</div><div style="font-size:10px; color:#888; text-align:right;">📍 {entry['city']}</div></div></div>""", unsafe_allow_html=True)
        else:
            render_empty_state("Aktif yarışma yok.", "🌙")

    # --- TAB 3: GEÇMİŞ ARŞİV ---
    with tab3:
        st.markdown("### 🗄️ Yarışma Arşivi")
        past_list = fb.get_past_challenges_list()
        
        if not past_list:
            render_empty_state("Henüz arşivlenmiş bir yarışma yok.", "📦")
        else:
            # Seçim Kutusu
            labels = [f"#{p['id']} - {p['title']} ({p['date']})" for p in past_list]
            selected_label = st.selectbox("Hangi yarışmayı incelemek istersin?", labels)
            
            if selected_label:
                # ID'yi parse et
                sel_id = selected_label.split(" - ")[0].replace("#", "")
                st.divider()
                st.markdown(f"##### 📜 '{selected_label}' Katılımları")
                
                archived_entries = fb.get_challenge_entries(sel_id)
                if not archived_entries:
                    st.info("Bu yarışma için kayıt bulunamadı.")
                else:
                    acols = st.columns(4)
                    for i, entry in enumerate(archived_entries):
                        with acols[i % 4]:
                            st.image(entry['img'], use_container_width=True)
                            st.caption(f"👤 {entry['user']}")

def render_admin(fb):
    st.header("👑 Yönetici"); 
    if 'user_limit' not in st.session_state: st.session_state.user_limit = 20
    s = fb.get_stories(); 
    if st.session_state.user_role not in ['admin', 'mod']: st.error("Yetkisiz Giriş!"); return

    pending_offers = fb.get_gurme_offers(status="pending")
    
    t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs(["Üyeler","İçerik","Duyuru","📢 Vitrin","🎟️ Fırsatlar","Reklam","Sponsor","💰 KASA"])
    with t1:
        st.markdown("### 👥 Kullanıcı Yönetimi (Arama Modu)")
        st.info("Performans için sadece aradığınız kullanıcının bilgileri getirilir.")
        
        # ARAMA KUTUSU (HİBRİT)
        st.markdown("**1. Adım: Filtrele**")
        search_query = st.text_input("🔍 İsim veya E-posta Yazın (En az 3 harf)", placeholder="örn: sıl, ali, mehmet...")
        
        target_user = None
        if len(search_query) > 2:
            results = fb.search_user(search_query)
            if results:
                # Sonuçları Selectbox için hazırla
                # Format: "Nickname (Email)"
                st.markdown("**2. Adım: Listeden Seç**")
                user_options = {f"{u['nick']} ({u['email']})": u for u in results}
                
                selected_option = st.selectbox(
                    f"✅ {len(results)} Kişi Bulundu:", 
                    options=list(user_options.keys()),
                    index=None, # Varsayılan boş olsun
                    placeholder="Sonuçlardan bir kullanıcı seçin..."
                )
                
                if selected_option:
                    target_user = user_options[selected_option]
            else:
                st.warning("🔍 Eşleşen kullanıcı bulunamadı.")

        
        # Seçilen Kullanıcıyı Göster ve Düzenle
        if target_user:
            st.divider()
            c_u1, c_u2 = st.columns([1, 3])
            with c_u1:
                st.image(target_user.get('avatar') or f"https://ui-avatars.com/api/?name={target_user['nick']}&background=random", width=100)
            with c_u2:
                st.subheader(f"{target_user['nick']}")
                st.markdown(f"**E-posta:** `{target_user['email']}`")
                st.info(f"Mevcut Rütbe: **{RANK_SYSTEM.get(target_user['role'], {}).get('label', target_user['role'])}** | Bakiye: {target_user['balance']} TL | Puan: {target_user['points']}")
                
                # YASAL ONAY DURUMU
                st.markdown("---") 
                st.caption("⚖️ YASAL ONAY DURUMU (LOG KAYITLARI)")
                col_leg1, col_leg2, col_leg3 = st.columns(3)
                
                with col_leg1:
                    st.markdown("**Kullanım Koşulları**")
                    if target_user.get('terms_accepted'):
                        st.success(f"✅ Onaylı\n\nVersiyon: `{target_user.get('terms_version', '-')}`\n\nTarih: `{target_user.get('terms_accepted_at', '-')}`")
                    else:
                        st.error("❌ Onay Yok")

                with col_leg2:
                    st.markdown("**Gizlilik Politikası**")
                    if target_user.get('policy_accepted'):
                        st.success(f"✅ Onaylı\n\nTarih: `{target_user.get('policy_accepted_at', '-')}`")
                    else:
                         st.error("❌ Onay Yok")
                
                with col_leg3:
                    st.markdown("**Son İçerik Sorumluluk Beyanı**")
                    lcc = target_user.get('last_content_consent', '-')
                    if lcc and lcc != '-':
                        st.info(f"📝 Son Beyan Tarihi:\n\n`{lcc}`")
                    else:
                        st.warning("⚠️ Henüz içerik girişi yok")
                
                st.markdown("---")

                # RBAC (YETKİLENDİRME) KONTROLÜ
                current_role = st.session_state.user_role
                target_role = target_user['role']
                
                can_edit = True
                warning_msg = ""
                
                # Kural 1: Modlar, Adminleri düzenleyemez
                if current_role == 'mod' and target_role == 'admin':
                    can_edit = False
                    warning_msg = "⚠️ Moderatörler, Yöneticilerin yetkilerine müdahale edemez."
                
                # Kural 3: Kimse kendi rütbesini değiştiremez (Admin dahil, güvenlik için)
                if st.session_state.user_uid == target_user['uid']:
                    can_edit = False
                    warning_msg = "⚠️ Kendi rütbenizi değiştiremezsiniz."

                if can_edit:
                    # Yeni Rütbe Seçimi
                    possible_roles = list(RANK_SYSTEM.keys())
                    # Kural 2: Modlar, kimseye 'admin' yetkisi veremez
                    if current_role == 'mod':
                        if 'admin' in possible_roles: possible_roles.remove('admin')
                    
                    new_role_sel = st.selectbox("Yeni Rütbe Ata", possible_roles, index=possible_roles.index(target_role) if target_role in possible_roles else 0)
                    
                    if st.button("Rütbeyi Güncelle"):
                        if new_role_sel == target_role:
                            st.warning("Zaten bu rütbede.")
                        else:
                            success = fb.update_user_role(target_user['uid'], new_role_sel)
                            if success: st.success(f"{target_user['nick']} artık {new_role_sel}!"); time.sleep(1); st.rerun()
                            else: st.error("Hata oluştu.")
                else:
                    st.error(warning_msg)

    with t2:
        st.markdown("### 🗂️ İçerik Yönetimi")
        ct1, ct2 = st.tabs(["Hikayeler (Rotalar)", "Forum Gönderileri"])
        
        def render_content_manager(c_type, c_label):
            st.caption(f"{c_label} için işlem yapın.")
            
            # 1. ARAMA / ID SİLME
            with st.expander("🔍 İçerik Ara veya ID ile Sil", expanded=True):
                col_s1, col_s2 = st.columns([3, 1])
                search_q = col_s1.text_input("Başlık Ara", key=f"s_q_{c_type}")
                if col_s2.button("Ara", key=f"s_btn_{c_type}"):
                    if len(search_q) < 3: st.warning("En az 3 harf.")
                    else:
                        st.session_state[f"search_res_{c_type}"] = fb.admin_search_content(c_type, search_q)
                
                # Arama Sonuçları
                if f"search_res_{c_type}" in st.session_state and st.session_state[f"search_res_{c_type}"]:
                    st.info(f"{len(st.session_state[f'search_res_{c_type}'])} sonuç bulundu.")
                    for item in st.session_state[f"search_res_{c_type}"]:
                        c_res1, c_res2 = st.columns([4, 1])
                        c_res1.markdown(f"**{item['title']}** (Yazar: {item['author']})")
                        c_res1.caption(f"ID: `{item['id']}`")
                        if c_res2.button("🗑️ SİL", key=f"del_search_{item['id']}"):
                             fb.admin_delete_content(c_type, item['id'])
                             st.success("Silindi! (Cache temizlendi)"); time.sleep(1); st.rerun()

            st.divider()
            
            # 2. İŞLEM (ID İLE DİREKT SİLME)
            with st.expander("💣 ID ile Direkt Sil (Keskin Nişancı Modu)"):
                del_id = st.text_input("Silinecek İçerik ID'si", key=f"direct_del_id_{c_type}")
                if st.button("Bu ID'yi Kalıcı Olarak Sil", key=f"btn_del_id_{c_type}", type="primary"):
                    if fb.admin_delete_content(c_type, del_id):
                        st.success("İçerik uçuruldu 🚀"); time.sleep(1); st.rerun()
                    else:
                        st.error("Silinemedi (ID hatalı olabilir).")

            st.divider()

            # 3. Son 20 Gönderi (GÖZETİM KULESİ)
            st.subheader(f"Gözetim Kulesi: Son 20 {c_label}")
            latest = fb.admin_get_latest_contents(c_type, limit=20)
            if not latest:
                st.info("İçerik yok.")
            else:
                for item in latest:
                    with st.container():
                        c_l1, c_l2 = st.columns([5, 1])
                        c_l1.markdown(f"**{item['title']}** | 👤 {item['author']}")
                        c_l1.caption(f"📅 {item.get('date','-')[:10]} | ID: `{item['id']}`")
                        if c_l2.button("Sil", key=f"del_lst_{item['id']}"):
                            fb.admin_delete_content(c_type, item['id'])
                            st.rerun()
                        st.markdown("---")

        with ct1: render_content_manager("stories", "Hikaye")
        with ct2: render_content_manager("forum_posts", "Forum Postu")
    with t3:
        st.markdown("### 📢 Duyuru - Son Aktivite Yönetimi")
        sc = fb.get_sidebar_content()
        with st.form("ann_manage_form"):
            new_ann_text = st.text_area("Duyuru Metni", value=sc.get('ann_text', ''))
            new_ann_img = st.text_input("Duyuru Görsel Linki", value=sc.get('ann_img', ''))
            
            c_upd, c_del = st.columns(2)
            if c_upd.form_submit_button("Duyuruyu Güncelle"):
                fb.update_sidebar_content({"ann_text": new_ann_text, "ann_img": new_ann_img})
                st.success("Duyuru güncellendi!"); time.sleep(1); st.rerun()
                
            if c_del.form_submit_button("🗑️ Duyuruyu Kaldır"):
                fb.update_sidebar_content({"ann_text": "", "ann_img": ""})
                st.warning("Duyuru kaldırıldı. (Son aktiviteler görünecek)"); time.sleep(1); st.rerun()
    with t4:
        st.markdown("### 📢 Vitrin Yönetimi")
        sc = fb.get_sidebar_content()
        with st.form("sidebar_upd_form"):
            an_txt = st.text_area("Duyuru Metni", value=sc.get('ann_text',''))
            an_img = st.text_input("Duyuru Görseli", value=sc.get('ann_img',''))
            st.divider()
            ad_link = st.text_input("Reklam Linki", value=sc.get('ad_link',''))
            ad_img = st.text_input("Reklam Görseli", value=sc.get('ad_img',''))
            ad_yt = st.text_input("Youtube Embed Linki", value=sc.get('ad_youtube',''))
            
            if st.form_submit_button("Vitrini Güncelle"):
                fb.update_sidebar_content({"ann_text": an_txt, "ann_img": an_img, "ad_link": ad_link, "ad_img": ad_img, "ad_youtube": ad_yt})
                st.success("Vitrin güncellendi!"); st.rerun()
                
    with t5:
        st.markdown("### 🍷 Gurme Başvuruları")
        if not pending_offers: st.info("Bekleyen başvuru yok.")
        for o in pending_offers:
            st.warning(f"Kullanıcı: {o['user']}")
            if st.button("Onayla", key=f"app_{o['uid']}"):
                fb.update_user_role(o['uid'], 'gurme')
                fb.update_gurme_offer_status(o['uid'], 'approved')
                st.success("Onaylandı!"); st.rerun()

    with t6:
        st.markdown("### 📢 Reklam Yönetimi")
        
        # ÜST SEKMELER: SİDEBAR VİTRİN | ROTALAR VİTRİN
        type_tab1, type_tab2 = st.tabs(["Sidebar Vitrin (Ana Sayfa)", "Rotalar Vitrin (Rota İçi)"])

        # --- YARDIMCI FONSİYON: AD LİSTELEME VE YÖNETME ---
        def render_ad_manager(ad_type, type_label):
            st.info(f"{type_label} Yönetimi")
            sub_t1, sub_t2 = st.tabs(["⏳ Onay Bekleyenler", "✅ Yayındaki İlanlar"])
            
            # 1. ONAY BEKLEYENLER
            with sub_t1:
                pending_ads = fb.get_ads_by_status(['pending_approval'], ad_type=ad_type)
                if not pending_ads: st.info("Onay bekleyen başvuru yok.")
                else:
                    for ad in pending_ads:
                        with st.expander(f"🏢 {ad['business_name']} ({ad['date']})"):
                            col_img, col_info = st.columns([1, 2])
                            with col_img: st.image(ad['image'], caption="Reklam Görseli", use_column_width=True)
                            with col_info:
                                st.markdown(f"**Link:** {ad['link']}")
                                st.markdown(f"**E-Posta:** `{ad.get('email', '-')}`")
                                st.info("Kullanıcı ödeme onayı verdi.")
                                
                                c1, c2 = st.columns(2)
                                if c1.button("✅ ONAYLA (Süreyi Başlat)", key=f"app_{ad['id']}"):
                                    fb.update_ad_status(ad['id'], 'active')
                                    st.success("Reklam yayına alındı! Süre başladı.")
                                    time.sleep(1); st.rerun()
                                if c2.button("❌ REDDET", key=f"rej_{ad['id']}"):
                                    fb.update_ad_status(ad['id'], 'rejected')
                                    st.error("Reddedildi.")
                                    time.sleep(1); st.rerun()

            # 2. YAYINDAKİLER
            with sub_t2:
                active_ads = fb.get_ads_by_status(['active'], ad_type=ad_type)
                if not active_ads: st.info("Yayında olan reklam yok.")
                else:
                    for ad in active_ads:
                        with st.expander(f"🟢 {ad['business_name']} (Kalan: {ad.get('days_left', '-')})"):
                            st.image(ad['image'], height=100)
                            st.write(f"Link: {ad['link']}")
                            if st.button("Yayından Kaldır (Arşivle)", key=f"arch_{ad['id']}"):
                                fb.update_ad_status(ad['id'], 'archived')
                                st.success("Arşivlendi.")
                                time.sleep(1); st.rerun()

        with type_tab1: render_ad_manager("sidebar", "Ana Sayfa Sidebar")
        with type_tab2: render_ad_manager("route_ad", "Rota İçi")

    with t7: 
        st.markdown("### 🎒 Gezgin Öğrenci Başvuruları Yönetimi")
        
        tab_img, tab_pen, tab_pool, tab_arc = st.tabs(["🖼️ Görsel Ayarları", "⏳ Bekleyenler", "✅ Onaylananlar (Havuz)", "📦 Arşiv"])
        
        # --- 1. GÖRSEL AYARLARI ---
        with tab_img:
            sc = fb.get_sidebar_content()
            curr_img = sc.get('sponsor_hero_img', 'https://plus.unsplash.com/premium_photo-1677343210638-5d3ce6ddbf85?q=80&w=2574&auto=format&fit=crop')
            with st.form("sponsor_img_form"):
                new_img_url = st.text_input("Yeni Görsel URL", value=curr_img)
                if st.form_submit_button("Görseli Güncelle"):
                    sc['sponsor_hero_img'] = new_img_url
                    fb.update_sidebar_content(sc)
                    st.success("Görsel güncellendi!"); st.rerun()

        # --- 2. BEKLEYENLER ---
        with tab_pen:
            pending_apps = fb.get_sponsor_applications(status='pending')
            if not pending_apps: st.info("Bekleyen yeni başvuru yok.")
            else: 
                for app in pending_apps:
                    with st.expander(f"🆕 {app.get('name')} ({app.get('uni')})"):
                        st.markdown(f"**Hedef:** {app.get('target')} | **E-Posta:** {app.get('email')}")
                        st.info(f"Motivasyon: {app.get('why')}")
                        st.caption(f"Tarih: {app.get('date')}")
                        if st.button("✅ Onayla (Havuza Aktar)", key=f"app_pool_{app.get('uid')}"):
                            fb.update_sponsor_app_status(app.get('uid'), 'approved_pool')
                            st.success("Başvuru havuza alındı."); time.sleep(1); st.rerun()
                            
        # --- 3. ONAYLANANLAR (HAVUZ) ---
        with tab_pool:
            pool_apps = fb.get_sponsor_applications(status='approved_pool')
            st.info("ℹ️ Buradaki adaylar değerlendirme havuzundadır (Bekleme Süresi: 1 Ay). Seçildiklerinde veya süreleri dolduğunda arşivleyebilirsiniz.")
            if not pool_apps: st.warning("Havuzda aday yok.")
            else:
                for app in pool_apps:
                    with st.expander(f"🌟 {app.get('name')} - {app.get('target')}"):
                        st.write(f"E-Posta: {app.get('email')}")
                        st.write(f"Okul: {app.get('uni')}")
                        c_p1, c_p2 = st.columns(2)
                        with c_p1:
                            if st.button("📩 İletişime Geçildi", key=f"contact_{app.get('uid')}"): st.toast("Not alındı.")
                        with c_p2:
                            if st.button("📦 Arşivle (Süreci Bitir)", key=f"arc_{app.get('uid')}"):
                                fb.update_sponsor_app_status(app.get('uid'), 'archived')
                                st.success("Başvuru arşivlendi."); time.sleep(1); st.rerun()

        # --- 4. ARŞİV ---
        with tab_arc:
            archived_apps = fb.get_sponsor_applications(status='archived')
            if not archived_apps: st.info("Arşiv boş.")
            else:
                for app in archived_apps: st.markdown(f"**{app.get('name')}** - {app.get('target')} ({app.get('date')})")

    with t8:
        st.markdown("### 💰 Kasa Yönetimi")
        fin_tabs = st.tabs(["⏳ Bekleyen Bildirimler", "💸 Para Çekme Talepleri", "📋 Finansal Rapor"])
        report = fb.get_financial_report() 
        
        # 1. Bekleyen Bildirimler
        with fin_tabs[0]:
            pending_tx = [x for x in report if x['status'] == 'pending']
            if not pending_tx: st.info("Onay bekleyen ödeme bildirimi yok.")
            else:
                for tx in pending_tx:
                    with st.expander(f"BİLDİRİM: {tx['amount']:.2f} TL (Net) | {tx['desc']}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Onayla", key=f"app_tx_{tx['id']}", use_container_width=True):
                                fb.approve_transaction(tx['id'], tx['to_uid'], tx['amount'])
                                st.success("Onaylandı!"); time.sleep(1); st.rerun()
                        with c2:
                             if st.button("❌ Reddet", key=f"rej_tx_{tx['id']}", use_container_width=True):
                                 fb.reject_transaction(tx['id'], tx['to_uid'], tx['amount'])
                                 st.error("Reddedildi."); time.sleep(1); st.rerun()

        # 2. Para Çekme Talepleri
        with fin_tabs[1]:
            withdraw_tx = [x for x in report if x['status'] == 'pending_withdraw']
            if not withdraw_tx: st.info("Bekleyen para çekme talebi yok.")
            else:
                for wt in withdraw_tx:
                     with st.expander(f"ÇEKİM TALEBİ: {wt['amount']:.2f} TL | {wt['desc']}"):
                        st.warning("⚠️ Lütfen ödemeyi yaptıktan sonra 'Ödendi' olarak işaretleyin.")
                        if st.button("✅ Ödendi Olarak İşaretle", key=f"pd_{wt['id']}", use_container_width=True):
                            fb.mark_withdrawal_paid(wt['id'])
                            st.success("İşlem tamamlandı."); st.rerun()

        # 3. Finansal Rapor
        with fin_tabs[2]: st.dataframe(report)

def render_conquest_map(visited_cities):
    st.markdown("### 🗺️ Fetih Paneli")
    progress = len(visited_cities) / 81
    st.progress(progress)
    html_content = '<div class="conquest-grid">'
    for city in ALL_PROVINCES:
        is_visited = city in visited_cities
        css_class = "city-visited" if is_visited else "city-not-visited"
        icon = "✅" if is_visited else "⬜"
        html_content += f'<div class="city-badge {css_class}">{icon} {city}</div>'
    html_content += '</div>'
    st.markdown(html_content, unsafe_allow_html=True)

def render_profile(fb):
    p = fb.get_profile(st.session_state.user_uid)
    if p.get('nick') == "Adsız": st.warning("⚠️ Hey Gezgin! Seni 'Adsız' olarak tanıyoruz. Lütfen aşağıdan kendine bir isim seç.")
    
    # --- PROFİL DÜZENLEME ---
    with st.expander("✏️ Profil Resmini ve İsmini Düzenle"):
        with st.form("edit_profile_form"):
            new_nick = st.text_input("Kullanıcı Adı", value=p.get('nick', ''))
            new_avatar = st.text_input("Avatar URL (Resim Linki)", value=p.get('avatar', ''), placeholder="https://... (ImgBB veya başka bir link)")
            if st.form_submit_button("Kaydet"):
                ok, msg = fb.update_profile(st.session_state.user_uid, new_nick, new_avatar)
                if ok: st.success(msg); time.sleep(1); st.rerun()
                else: st.error(msg)
    
    # Profil Başlığı
    st.markdown(get_profile_header_html(p), unsafe_allow_html=True)
    
    tab_wallet, tab_map, tab_content = st.tabs(["💰 CÜZDAN & HAKEDİŞ", "🗺️ FETİH PANELİ", "📸 İÇERİKLERİM"])
    
    with tab_wallet:
        st.markdown("### 💼 Cüzdanım ve Hakediş Durumu")
        
        # 1. BAKİYE KARTLARI
        c_pending, c_withdraw = st.columns(2)
        with c_pending:
            st.markdown(f"""
            <div style="background-color:#FFF3CD; padding:15px; border-radius:10px; border:2px solid #FFEEBA; text-align:center;">
                <h4 style="margin:0; color:#856404;">⏳ Bekleyen Bakiye</h4>
                <h2 style="margin:5px 0; color:#856404;">{p.get('pending_balance', 0.0):.2f} TL</h2>
                <div style="font-size:11px; color:#856404;">(Onay Sürecinde)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_withdraw:
            st.markdown(f"""
            <div style="background-color:#D4EDDA; padding:15px; border-radius:10px; border:2px solid #C3E6CB; text-align:center;">
                <h4 style="margin:0; color:#155724;">✅ Çekilebilir Bakiye</h4>
                <h2 style="margin:5px 0; color:#155724;">{p.get('withdrawable_balance', 0.0):.2f} TL</h2>
                <div style="font-size:11px; color:#155724;">(Hemen Çekilebilir)</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        
        # 2. PARA ÇEKME ALANI (Progress Bar)
        w_bal = p.get('withdrawable_balance', 0.0)
        progress = min(w_bal / 1000.0, 1.0)
        
        st.write(f"**Para Çekme İlerlemesi:** Limit 1000 TL ({w_bal:.2f} / 1000 TL)")
        st.progress(progress)
        
        if w_bal < 1000:
            st.info(f"🔒 Para çekmek için {1000 - w_bal:.2f} TL daha birikmesi gerekiyor.")
            st.button("💸 Para Çek", disabled=True)
        else:
            st.success("🎉 Tebrikler! 1000 TL barajını aştın. Paranızı çekebilirsiniz.")
            with st.expander("💸 Para Çekme Talep Formu", expanded=True):
                with st.form("withdraw_form"):
                    iban = st.text_input("IBAN Adresi (TR ile başlayan)", value=p.get('iban', ''), max_chars=32)
                    fname = st.text_input("Ad Soyad (IBAN Sahibi)", value=p.get('full_name', ''))
                    w_amount = st.number_input("Çekilecek Tutar", min_value=1000.0, max_value=float(w_bal), step=10.0)
                    
                    if st.form_submit_button("Talebi Gönder", type="primary"):
                        if not iban.startswith("TR"):
                            st.error("Geçerli bir IBAN giriniz.")
                        elif not fname:
                            st.error("Ad Soyad giriniz.")
                        else:
                            ok, msg = fb.request_withdrawal(st.session_state.user_uid, w_amount, iban, fname)
                            if ok:
                                st.success(msg)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
        
        st.divider()
        st.markdown("##### 📜 İşlem Geçmişi")
        txs = fb.get_user_transactions(st.session_state.user_uid)
        if not txs:
            st.info("Henüz işlem yok.")
        else:
            st.markdown(f"**Toplam İşlem:** {len(txs)}")
            for t in txs:
                icon = "⏳" if "pending" in t['status'] else ("✅" if t['status'] == "approved" or t['status'] == "paid" else "❌")
                st.markdown(f"**{t['date'][:10]}** | {icon} {t['status'].upper()} | **{t['amount']:.2f} TL** | _{t['desc']}_")

    with tab_map:
        render_conquest_map(p.get('visited_cities', []))
        with st.expander("Şehir Ekle"):
             sel = st.multiselect("Şehirler", ALL_PROVINCES)
             if st.button("Kaydet"): fb.update_visited_cities(st.session_state.user_uid, sel); st.rerun()

    with tab_content:
        my_stories, my_posts = fb.get_user_content(st.session_state.user_uid)
        st.write(f"Hikaye: {len(my_stories)} | Forum: {len(my_posts)}")

def render_public_profile(fb, target_uid):
    p = fb.get_profile(target_uid)
    
    # --- TAKİP ET / ÇIKAR BUTONU ---
    # Mevcut kullanıcının takip listesini kontrol et
    me = fb.get_profile(st.session_state.user_uid)
    am_i_following = target_uid in me.get('following', [])
    
    col_back, col_follow = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Geri"): st.session_state.active_tab = "kesfet"; st.rerun()
    with col_follow:
        if am_i_following:
            if st.button("🚫 Takipten Çık", type="secondary"):
                fb.unfollow_user(st.session_state.user_uid, target_uid)
                st.rerun()
        else:
            if st.button("➕ Takip Et", type="primary"):
                fb.follow_user(st.session_state.user_uid, target_uid)
                st.rerun()

    st.markdown(get_profile_header_html(p), unsafe_allow_html=True)
    render_conquest_map(p.get('visited_cities', []))
    st.divider()
    st.write("Paylaşımları:")
    stories, posts = fb.get_user_content(target_uid)
    for s in stories: st.write(f"- {s['title']}")

# --- LONCA (GUILD) ARAYÜZÜ ---
def render_loncalar(fb):
    st.markdown("## ⚔️ Loncalar Meclisi")
    
    # 1. Kullanıcının Loncasını Kontrol Et
    p = fb.get_profile(st.session_state.user_uid)
    my_guild_id = p.get('guild')
    
    # SENARYO A: Kullanıcı Bir Loncaya Üye Değilse
    if not my_guild_id:
        cols = st.columns(len(GUILDS))
        for i, (gid, gdata) in enumerate(GUILDS.items()):
            with cols[i]:
                # Kart Görünümü
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:8px; border-top:5px solid var(--secondary-color); text-align:center; box-shadow:0 4px 6px rgba(0,0,0,0.1); height:100%;">
                    <div style="font-size:40px;">{gdata['icon']}</div>
                    <div style="font-weight:bold; font-size:16px; margin:10px 0;">{gdata['name']}</div>
                    <div style="font-size:12px; color:#555; height:50px;">{gdata['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🚪 Kapıyı Çal", key=f"join_{gid}", use_container_width=True):
                    # Puan Kontrolü
                    if st.session_state.user_points < 500:
                        st.error("⛔ Bu kapıdan geçmek için heybende en az 500 Puan olmalı!")
                    else:
                        success = fb.join_guild(st.session_state.user_uid, gid)
                        if success:
                            st.balloons()
                            st.success(f"Tebrikler! Artık bir {gdata['name']} üyesisin.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Bir hata oluştu. Kapı açılmadı.")

    # SENARYO B: Kullanıcı Üye İse
    else:
        guild_data = GUILDS.get(my_guild_id, {"name": "Bilinmeyen Lonca", "icon": "❓"})
        
        # Header
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.markdown(f"### {guild_data['icon']} {guild_data['name']} MECLİSİ")
        with col_h2:
            if st.button("Loncadan Ayrıl", type="secondary"):
                fb.leave_guild(st.session_state.user_uid)
                st.warning("Loncadan ayrıldın. Yolların açık olsun.")
                time.sleep(1)
                st.rerun()
        
        # Kanallar
        tab1, tab2, tab3 = st.tabs(["💬 Muhabbet", "📅 Planlama", "🆘 Yardım"])
        # Helper to render chat
        def render_channel_chat(channel_name):
            messages = fb.get_guild_messages(my_guild_id, channel_name)
            st.caption(f"{guild_data['name']} - {channel_name.upper()} Kanalı")
            
            # Mesaj Alanı Container (Height fixed scrollable would be nice but simple list is robust)
            with st.container(height=400):
                for msg in messages:
                   with st.chat_message("user", avatar=msg.get('avatar') or "👤"):
                       st.write(f"**{msg['user']}**: {msg['text']}")
                       st.caption(f"_{msg['timestamp'][11:16]}_")
            
            if prompt := st.chat_input(f"{channel_name} kanalına yaz...", key=f"chat_{channel_name}"):
                fb.send_guild_message(my_guild_id, channel_name, st.session_state.user_nick, None, prompt)
                st.rerun()
                
        with tab1: render_channel_chat("muhabbet")
        with tab2: render_channel_chat("planlama")
        with tab3: render_channel_chat("yardim")

@st.dialog("📜 Yasal Metinler & Gizlilik Politikası")
def view_legal_text_dialog(fb):
    st.markdown(fb.get_legal_texts())

def sidebar(fb):
    with st.sidebar:
        if st.session_state.user_token:
            st.write(f"Hoş geldin, **{st.session_state.user_nick}**"); st.caption(f"Bakiye: {st.session_state.user_balance} TL")
            if st.button("Çıkış"): st.query_params.clear(); st.session_state.clear(); st.rerun()
        else: st.info("Hoş geldin! Giriş yapabilirsin.")
        
        st.markdown("---")
        if st.button("⚖️ Kullanım Şartları | Gizlilik | Çerez", key="sidebar_legal_btn", use_container_width=True):
             view_legal_text_dialog(fb)
        st.caption("© 2024 GeziStory - Tüm Hakları Saklıdır.")

def render_cookie_consent():
    # 1. URL Query Params ile "Tarayıcı Bazlı" Kalıcılık Kontrolü (Sayfa yenilendiğinde hatırlasın)
    # Streamlit'te local storage'a erişmek zordur, bu yüzden URL parametresi ("hilesi") kullanıyoruz.
    qp = st.query_params
    
    # Eğer önceden kabul edildiyse veya URL'de işaretliyse geç
    if qp.get("cookie_consent") == "true":
        return

    # 2. Eğer kullanıcı giriş yapmışsa Profilinden kontrol et (Firebase)
    # (Bu kısım opsiyonel, eğer backend'de 'cookie_accepted' tutuyorsak)
    
    # 3. Henüz kabul edilmediyse göster (Köşede / Altta)
    # Streamlit'te "Fixed Bottom" zordur ama expander veya container ile yapabiliriz.
    # Kullanıcı "Köşede bir defa" dediği için Toast mesajı mantıklı ama buton ekleyemiyoruz.
    # Bu yüzden sidebar'ın en altına veya ana sayfanın en üstüne şık bir kutu koyalım.
    
    with st.container():
        # HTML/CSS ile biraz daha "Banner" havası verelim
        st.markdown("""
        <div style="background-color:#2c3e50; color:white; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border:1px solid #34495e; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size:24px;">🍪</div>
            <div style="font-size:13px; margin:5px 0;">
                Sitemizde deneyiminizi iyileştirmek için çerezler kullanılmaktadır.
                Devam ederek <b>Çerez Politikamızı</b> kabul etmiş sayılırsınız.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns([1, 4])
        # Butona basınca URL param güncellenecek
        if st.button("Anladım & Kabul Ediyorum", key="cookie_accept_btn", type="primary", use_container_width=True):
            st.query_params["cookie_consent"] = "true" # URL'e ?cookie_consent=true ekler
            st.session_state.cookie_consent = True # Session state'i de güncelle
            st.rerun()

def main():
    # Çerez Onayı Kontrolü (En üstte)
    render_cookie_consent()

    # CSS'i Yükle
    st.markdown(get_app_css(), unsafe_allow_html=True)
    if 'user_token' not in st.session_state: st.session_state.update(user_token=None, user_uid=None, user_nick=None, user_balance=0, user_role='caylak', user_points=0, active_tab="kesfet", user_saved_routes=[], active_mood="Hepsi", seen_msgs_count=0)

    # --- URL PARAMETRE KONTROLÜ (TAŞINDI: Varsayılan değerlerden SONRA çalışmalı) ---
    # Bu kod, yukarıdaki active_tab="kesfet" atamasını ezer.
    qp = st.query_params
    if "tab" in qp:
        st.session_state.active_tab = qp["tab"]
        if "focus_post" in qp:
            st.session_state.forum_focus = qp["focus_post"]
        # Parametreleri temizle (Temiz URL için)
        st.query_params.clear()
    fb = FirebaseService()
    if "visit_counted" not in st.session_state: fb.increment_daily_visits(); st.session_state.visit_counted = True
    
    # --- GASTRONOMİ REHBERİ BAŞLAT (One-Time) ---
    if 'guides_init' not in st.session_state:
        fb.initialize_city_guides()
        st.session_state.guides_init = True
    
    # Ziyaretçi Sayacını Artır (Her sayfa yüklemesinde - YENİ SİSTEM)
    fb.update_site_stats()

    # --- PERSISTENT LOGIN CHECK ---
    # Eğer token yoksa ama URL'de session varsa, onu dene
    if not st.session_state.user_token and 'session' in st.query_params:
        sess_data = fb.validate_session(st.query_params['session'])
        if sess_data:
            # Oturum geçerli, bilgileri çek ve giriş yap
            p = fb.get_profile(sess_data['uid'])
            if 'nick' in p:
                st.session_state.update(user_token=sess_data['token'], user_uid=sess_data['uid'], user_nick=p['nick'], user_balance=p['balance'], user_role=p['role'], user_points=p['points'])
                st.toast(f"Tekrar hoş geldin, {p['nick']}!")
        else:
            # Geçersiz session, parametreyi temizle
            st.query_params.clear()

    if not st.session_state.user_token: fb.sign_in_anonymously()
    
    if st.session_state.user_token:
        p = fb.get_profile(st.session_state.user_uid)
        st.session_state.update(user_role=p['role'], user_nick=p['nick'], user_balance=p['balance'])

    # Header / Logo Area
    c_logo, c_login = st.columns([3, 1])
    # Custom Styled Logo
    c_logo.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
    .gezi-logo {
        font-family: 'Pacifico', cursive;
        font-size: 48px;
        background: -webkit-linear-gradient(45deg, #FF512F, #DD2476, #FF9966);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        padding: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .logo-emoji {
        font-size: 40px;
        -webkit-text-fill-color: initial; /* Emoji rengini koru */
    }
    </style>
    <div class="gezi-logo">GeziStory <span class="logo-emoji">🧿</span></div>
    """, unsafe_allow_html=True)




    # GLOBAL SEARCH BAR & STATS PANEL
    c_search, c_stats = st.columns([3, 1])
    
    search_query = c_search.text_input("🔍 GeziStory'de Ara...", placeholder="Kullanıcı, Şehir veya Hikaye ara...", label_visibility="collapsed")
    
    # STATS PANEL (YENİ SİSTEM)
    stats = fb.get_site_stats()
    
    st.markdown("""
    <style>
    .stats-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: white;
        padding: 8px 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #eee;
    }
    .stat-item {
        text-align: center;
        line-height: 1.2;
    }
    .stat-val {
        font-weight: 800;
        font-size: 16px;
        color: #2C3E50;
    }
    .stat-lbl {
        font-size: 10px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stat-sep {
        width: 1px;
        height: 25px;
        background: #eee;
    }
    </style>
    """, unsafe_allow_html=True)

    c_stats.markdown(f"""
    <div class="stats-container">
        <div class="stat-item">
            <div class="stat-val">{stats['today']}</div>
            <div class="stat-lbl">Bugün</div>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-item">
            <div class="stat-val">{stats['total']}</div>
            <div class="stat-lbl">Toplam</div>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-item">
            <div class="stat-val">✅</div>
            <div class="stat-lbl">Aktif</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if search_query:
        st.info(f"🔎 Arama Sonuçları: '{search_query}'")
        res_col1, res_col2 = st.columns(2)
        
        # 1. Search Users
        all_users = fb.get_all_users(limit=50) # Basitlik için limitli
        found_users = [u for u in all_users if search_query.lower() in u.get('nick','').lower()]
        
        with res_col1:
            st.markdown("##### 👤 Kullanıcılar")
            if found_users:
                for fu in found_users:
                    with st.expander(f"{fu['nick']} ({fu.get('role', 'caylak')})"):
                        st.caption(f"Puan: {fu.get('points',0)}")
                        if st.button("Profiline Git", key=f"s_u_{fu['uid']}"):
                            st.session_state.view_target_uid = fu['uid']
                            st.session_state.active_tab = "public_profile"
                            st.rerun()
            else:
                st.caption("Kullanıcı bulunamadı.")

        # 2. Search Stories
        all_stories = fb.get_stories()
        found_stories = [s for s in all_stories if search_query.lower() in s['title'].lower() or search_query.lower() in s['city'].lower() or search_query.lower() in s['author'].lower()]
        
        with res_col2:
            st.markdown("##### 📸 İçerikler")
            if found_stories:
                for fs in found_stories:
                    st.markdown(f"**{fs['title']}** ({fs['city']}) - _{fs['author']}_")
                    if st.button("İncele", key=f"s_s_{fs['id']}"):
                         # Ön izleme veya detay açma
                         view_route_detail_dialog(fs, fb)
            else:
                st.caption("İçerik bulunamadı.")
        
        st.divider() # Arama sonuçları ile içerik arasına çizgi

    st.divider()
    
    # NAVIGATION BUTTONS
    c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns(9) 
    
    # Helper to clean code
    def nav_btn(col, label, tab_name):
        style = "primary" if st.session_state.active_tab == tab_name else "secondary"
        if col.button(label, key=f"nav_{tab_name}", type=style, use_container_width=True):
            st.session_state.active_tab = tab_name
            st.rerun()

    nav_btn(c1, "🎲 KEŞFET", "kesfet")
    nav_btn(c2, "🗺️ ROTALAR", "rotalar")
    nav_btn(c3, "🏆 YARIŞMA", "challenge")
    nav_btn(c4, "🗣️ FORUM", "forum")
    nav_btn(c5, "🎟️ FIRSATLAR", "gurme") # Label Değişti (Eski: Gurme)
    nav_btn(c6, "🎓 SPONSOR", "sponsor")
    nav_btn(c7, "⚔️ LONCALAR", "loncalar")
    
    # Conditional Buttons based on Login/Role
    if st.session_state.user_token:
        nav_btn(c8, "👤 PROFİL", "profil")
        
        # Admin Button Logic
        if st.session_state.user_role in ['admin', 'mod']:
             nav_btn(c9, "👑 YÖNETİM", "admin")

    # CONTENT RENDERING
    stories = fb.get_stories()
    
    if st.session_state.active_tab == "kesfet": render_kesfet(stories, fb)
    elif st.session_state.active_tab == "rotalar": render_rotalar(stories, fb, "")
    elif st.session_state.active_tab == "challenge": render_challenge(fb)
    elif st.session_state.active_tab == "forum": render_forum(fb)
    elif st.session_state.active_tab == "gurme": render_gurme(fb)
    elif st.session_state.active_tab == "sponsor": render_sponsor(fb)
    elif st.session_state.active_tab == "loncalar":
        render_loncalar(fb)
    elif st.session_state.active_tab == "profil": render_profile(fb)
    elif st.session_state.active_tab == "public_profile": render_public_profile(fb, st.session_state.view_target_uid)
    elif st.session_state.active_tab == "admin": render_admin(fb)

    sidebar(fb)

if __name__ == "__main__": main()

