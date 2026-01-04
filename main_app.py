import customtkinter as ctk  # Arayüz için standart tkinter çok demode duruyordu, modern görünsün diye CustomTkinter kullandım.
import threading             # Arayüz donmasın diye ağır işlemleri (PDF okuma vs.) arka planda (thread) çalıştırıyorum.
from tkinter import filedialog, messagebox # Dosya seçme penceresi ve hata uyarıları için standart araçlar.
import os                    # Dosya yollarını (path) bulmak ve yönetmek için sistem kütüphanesi.
import re                    # (Regex) Yapay zekadan gelen metindeki gereksiz sembolleri temizlemek için şart.
import json                  # AI bana veriyi "Liste" formatında versin ki Python ile parçalayabileyim.
import time                  # Veritabanına isim verirken anlık zamanı kullanıyorum ki çakışma olmasın.
from datetime import datetime # Kayıt alırken dosya ismine tarih/saat eklemek için.
from difflib import SequenceMatcher # Cevap kontrolünde harf hatalarını tolere etmek için (Benzerlik algoritması).
import copy                  # Verileri yedeklerken "Deep Copy" yapıyorum, yoksa asıl veriyi bozabilirim.

# --- KÜTÜPHANE KONTROLÜ (Program patlamasın diye önlem) ---
# Programı başkası çalıştırırsa ve kütüphaneleri eksikse direkt kapanmasın, uyarı versin istedim.
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES # Dosyayı sürükle-bırak yapmak için gerekli.
    from langchain_groq import ChatGroq           # Kullandığım yapay zeka modeli (Groq - Llama 3). Çok hızlı ve ücretsiz.
    from langchain_chroma import Chroma           # Vektör veritabanı. PDF'teki metinleri sayıya çevirip burada saklıyorum.
    from langchain_huggingface import HuggingFaceEmbeddings # Metni vektöre (sayıya) çeviren model.
    from langchain_community.document_loaders import PyPDFLoader # PDF dosyasını okuyan araç.
    from langchain_text_splitters import RecursiveCharacterTextSplitter # Metni koca bir blok halinde değil, küçük parçalar halinde işliyorum.
    
    # SES VE PLAYER İÇİN SEÇTİĞİM KÜTÜPHANELER
    import edge_tts  # Microsoft'un ses motoru. Diğerleri çok robotik, bu nefes alarak konuşuyor.
    import asyncio   # Ses indirme işlemi asenkron çalışıyor, arayüzü kilitlememesi için lazım.
    import pygame    # Sesi oynatmak, durdurmak ve ileri sarmak için en sağlam kütüphane bu.
    from mutagen.mp3 import MP3 # Ses dosyasının toplam süresini (kaç dakika) olduğunu öğrenmek için.
except ImportError as e:
    # Eğer biri eksikse, program hata verip kapanmasın, konsola ne yapması gerektiğini yazsın.
    class TkinterDnD:
        class DnDWrapper: pass
    print(f"Eksik Kütüphane Var: {e}")
    print("Çözüm: Terminale 'pip install edge-tts pygame mutagen' yazıp enterla.")

# --- AYARLAR ---
# API anahtarım. 
GROQ_API_KEY = "" 

# --- TASARIM TERCİHLERİM ---
ctk.set_appearance_mode("Light") # Aydınlık mod seçtim, okuması daha kolay.
ctk.set_default_color_theme("dark-blue") # Mavi tonları güven ve profesyonellik hissi veriyor.

# Renk Paleti (Hepsini değişken yaptım ki rengi değiştirmek istersem tek yerden değiştirebileyim)
COLOR_PRIMARY = "#0D47A1"     # Ana renk (Koyu Mavi) - Başlıklar için.
COLOR_ACCENT = "#1976D2"      # Vurgu rengi (Açık Mavi) - Butonlar için.
COLOR_BG = "#F5F7FA"          # Arka plan (Hafif gri) - Göz yormasın diye tam beyaz yapmadım.
COLOR_WHITE = "#FFFFFF"       # Kartların rengi.
COLOR_TEXT = "#263238"        # Yazı rengi (Tam siyah yerine koyu gri daha estetik duruyor).
COLOR_SUBTEXT = "#546E7A"     # Alt yazı rengi.
COLOR_SUCCESS = "#2E7D32"     # Yeşil (Doğru cevap).
COLOR_ERROR = "#C62828"       # Kırmızı (Yanlış cevap).
COLOR_ERROR_BG = "#FFEBEE"    # Hata kutusu arka planı.
COLOR_SUCCESS_BG = "#E8F5E9"  # Başarı kutusu arka planı.

# Sohbet balonları için renkler
COLOR_USER_LABEL = "#1565C0"  # Benim yazdıklarım mavi.
COLOR_BOT_LABEL = "#E65100"   # Asistanın yazdıkları turuncu (Ayırt edilsin diye).
COLOR_HEADER_BIG = "#0D47A1"  # AI çıktısındaki ana başlıklar.
COLOR_HEADER_SMALL = "#1976D2" # AI çıktısındaki alt başlıklar.

# Yazı Tipleri (Tüm uygulamada tutarlılık olsun diye fontları burada tanımladım)
FONT_FAMILY = "Segoe UI Semibold" # Windows'un modern fontu. Okunaklı ve şık.
FONT_HERO = (FONT_FAMILY, 42, "bold")      # Giriş ekranındaki dev başlık.
FONT_LOGO = (FONT_FAMILY, 32, "bold")      # Sol üstteki logo.
FONT_H1 = (FONT_FAMILY, 20, "bold")        # Ana başlıklar (Çok büyük olmasın diye 20 yaptım).
FONT_H2 = (FONT_FAMILY, 17, "bold")        # Alt başlıklar.
FONT_FEATURE_TITLE = (FONT_FAMILY, 18, "bold") # Özellik kartı başlıkları.
FONT_BODY = (FONT_FAMILY, 15)              # Normal metin boyutu.
FONT_BOLD = (FONT_FAMILY, 15, "bold")      # Kalın metin.
FONT_BTN = (FONT_FAMILY, 15, "bold")       # Buton içindeki yazılar.

# =============================================================================
# BACKEND (İŞİN MUTFAĞI)
# =============================================================================
# Arayüz kodlarıyla mantık kodları karışmasın diye "Class" yapısı kullandım. (OOP Prensibi)
class Backend:
    def __init__(self):
        # [OOP - KAPSÜLLEME (Encapsulation)]
        # Bu değişkenleri (self.db, self.llm) sınıfın içine gizledim.
        # Dışarıdan rastgele değiştirilmesini engelliyorum, sadece sınıfın fonksiyonları bunları yönetiyor.
        self.db = None    
        # [VERİ YAPISI - LİSTE]
        # Yüklenen dosyaların isimlerini tutmak için Python'ın yerleşik 'List' yapısını kullandım.# Veritabanı başlangıçta boş.
        self.dosya_listesi = [] # Yüklenen dosyaları hafızada tutuyorum.
        self.llm = None         # Yapay zeka modelini burada saklayacağım.
        
        # API anahtarını kontrol edip modeli başlatıyorum.
        if "BURAYA" not in GROQ_API_KEY and len(GROQ_API_KEY) > 10:
            try:
                # ChatGroq modelini başlatıyorum. Temperature 0.3 seçtim ki çok uydurmasın, tutarlı olsun.
                self.llm = ChatGroq(
                    temperature=0.3, 
                    model_name="llama-3.3-70b-versatile", 
                    api_key=GROQ_API_KEY
                )
            except Exception as e:
                print(f"API Hatası: {e}") 
    
    # Yeni dosya yükleyince eski verileri temizliyorum ki karışmasın.
    def db_sifirla(self):
        self.db = None
        self.dosya_listesi = []

    # PDF Yükleme ve RAG Mimarisi (Projenin en kritik fonksiyonu)
    # Dokümanı yükleyip parçalara ayırma ve vektörleştirme.
    def toplu_yukle(self, paths, status_cb):
        try:
            status_cb("AI Okuyor...") # Kullanıcıya işlem başladığını söylüyorum.
            # Embedding: Metni sayılara çeviren model (HuggingFace kullandım, ücretsiz).
            embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            all_splits = [] 
            
            for i, path in enumerate(paths):
                name = os.path.basename(path) 
                if name in self.dosya_listesi: continue # Dosya zaten varsa tekrar yükleme.
                
                status_cb(f"İşleniyor: {name}...")
                loader = PyPDFLoader(path) # PDF'i okuyan araç.
                docs = loader.load()
                
                # Chunking: Metni 1000 karakterlik parçalara bölüyorum. Yoksa AI'ın hafızası yetmez.
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = splitter.split_documents(docs)
                all_splits.extend(splits) 
                self.dosya_listesi.append(name)

            if not all_splits: return True, "Dosya boş."

            status_cb("Veritabanı Oluşturuluyor...")
            # Her seferinde benzersiz isim veriyorum ki ChromaDB hata vermesin.
            unique_collection_name = f"pdf_koleksiyon_{int(time.time())}_{len(self.dosya_listesi)}"
            
            # Vektör veritabanına yazma işlemi.
            if self.db is None:
                self.db = Chroma.from_documents(
                    all_splits, 
                    embedding, 
                    collection_name=unique_collection_name
                )
            else:
                self.db.add_documents(all_splits) # Varsa üzerine ekle.
            
            return True, "TAMAM"
        except Exception as e:
            return False, str(e)

    # Yapay zekaya soru sorma kısmı.
    def sor(self, prompt):
        if not self.llm: return None, "API Anahtarı yok."
        if not self.db: return None, "Önce PDF yüklemen lazım."
        try:
            response = self.llm.invoke(prompt) # Soruyu modele gönder.
            return response.content, None      # Cevabı al.
        except Exception as e:
            return None, str(e)

    # RAG Mantığı: Kullanıcının sorusuna en benzer metin parçalarını bulup getiriyorum.
    def get_context(self, query):
        if not self.db: return ""
        docs = self.db.similarity_search(query, k=20) # En alakalı 20 parçayı bul.
        return "\n".join([d.page_content for d in docs]) # Hepsini birleştirip tek metin yap.

    # AI bazen JSON çıktısının yanına gereksiz yazılar ekliyor, onları temizliyorum.
    def json_temizle(self, text):
        if not text: return []
        text = re.sub(r'```json', '', text) 
        text = re.sub(r'```', '', text)
        match = re.search(r'\[.*\]', text, re.DOTALL) # Köşeli parantez arasını (listeyi) bul.
        if match:
            try: return json.loads(match.group()) # Python listesine çevir.
            except: return []
        return []

    # Fuzzy Matching: Cevap kontrolünde %100 aynılık aramak yerine benzerlik oranına bakıyorum.
    def benzerlik_hesapla(self, a, b):
        return int(SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100)
    
    # --- PODCAST SENARYOSU ---
    # Metni direkt okutursam çok sıkıcı oluyor. O yüzden önce "Podcast Sunucusu" rolü yapmasını istiyorum.
    def podcast_senaryosu_al(self, context):
        prompt = f"""
        Aşağıdaki metni bir PODCAST SUNUCUSU gibi anlat.
        Hedef Kitle: Üniversite öğrencileri.
        Ton: Çok samimi, enerjik, esprili ve akıcı. "Kanka", "Arkadaşlar", "İnanabiliyor musunuz?" gibi ifadeler kullan.
        
        Metni sıkıcı bir ders gibi değil, sanki bir arkadaşına dedikodu anlatır gibi anlat.
        Konuyu özetle ama araya espri sıkıştır.
        
        METİN: {context}
        """
        script, err = self.sor(prompt)
        return script

# =============================================================================
# FRONTEND (ARAYÜZ KATMANI)
# =============================================================================
# Burası kullanıcının gördüğü her şey. CustomTkinter'dan miras alıyorum.
class StudyPalApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__() 
        self.TkdndVersion = TkinterDnD._require(self) # Sürükle bırak özelliğini başlat.
        self.backend = Backend() # Backend'i (Mutfak) çağır.
        
        # Player Değişkenleri: Müzik çalar mantığı için gerekli değişkenler.
        self.is_playing = False
        self.audio_file = "temp_podcast.mp3"
        self.total_duration = 0
        self.update_loop_id = None
        
        # Pygame'in ses motorunu başlatıyorum.
        try:
            pygame.mixer.init()
        except:
            pass

        self.title("StudyPal - Öğrenme Asistanı") 
        self.geometry("1300x850") 
        self.configure(fg_color=COLOR_BG) 
        
        self.menu_acik = False # Yan menü başta kapalı olsun.
        self.saved_sessions = {} # Kaydedilen oturumları burada tutacağım.
        self.current_data = {"ozet": "", "flash": [], "quiz": [], "tf": []} 
        self.aktif_dosya_adi = "" 

        # İki ana konteyner var: Biri Giriş (Intro), diğeri Ana Uygulama.
        self.welcome_container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.main_app_container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        
        self.setup_welcome_screen() 
        self.setup_main_app_structure()
        self.show_welcome() # Başlangıçta intro ekranını göster.

    # --- FORMATLAMA FONKSİYONU ---
    # AI'dan gelen metni renklendirmek ve başlıkları belirginleştirmek için bu fonksiyonu yazdım.
    def metni_formatla_ve_yaz(self, textbox, text):
        textbox.configure(state="normal")
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("-"): # Tire ile başlıyorsa BÜYÜK BAŞLIKTIR.
                clean_line = line.replace("-", "").strip()
                textbox.insert("end", f"{clean_line}\n", "header_big")
            elif re.match(r'^\d+\.', line) and len(line) < 100: # Rakamla başlıyorsa ve kısaysa ALT BAŞLIKTIR.
                textbox.insert("end", f"{line}\n", "header_small")
            else: # Diğerleri normal metindir.
                textbox.insert("end", f"{line}\n", "body")
        textbox.configure(state="disabled")

    # --- 1. GİRİŞ EKRANI (INTRO) ---
    def setup_welcome_screen(self):
        content_box = ctk.CTkFrame(self.welcome_container, fg_color="transparent")
        content_box.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9)

        ctk.CTkLabel(content_box, text="StudyPal", font=FONT_LOGO, text_color=COLOR_PRIMARY).pack(pady=(0, 20))
        ctk.CTkLabel(content_box, text="Öğrenmenin En Akıllıca Yolu", font=FONT_HERO, text_color=COLOR_TEXT).pack(pady=(0, 15))
        ctk.CTkLabel(content_box, text="Notlarını saniyeler içinde etkileşimli özetlere, testlere ve bilgi kartlarına dönüştür.", 
                     font=FONT_BODY, text_color=COLOR_SUBTEXT, justify="center").pack(pady=(0, 50))

        # Özellikleri gösteren kutular. 5 sütun yaptım çünkü Podcast'i de ekledim.
        features_grid = ctk.CTkFrame(content_box, fg_color="transparent")
        features_grid.pack(fill="x", pady=(0, 60))
        features_grid.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="a")

        # Kod tekrarı yapmamak için kart oluşturan bir yardımcı fonksiyon yazdım.
        def create_feature_card(parent, col, icon, title, desc):
            card = ctk.CTkFrame(parent, fg_color=COLOR_WHITE, corner_radius=15, border_color="#E1E8ED", border_width=1)
            card.grid(row=0, column=col, padx=5, sticky="nsew")
            ctk.CTkLabel(card, text=icon, font=("Arial", 36)).pack(pady=(25, 10))
            ctk.CTkLabel(card, text=title, font=FONT_FEATURE_TITLE, text_color=COLOR_PRIMARY).pack(pady=(0, 5))
            ctk.CTkLabel(card, text=desc, font=(FONT_FAMILY, 12), text_color=COLOR_SUBTEXT, wraplength=160).pack(pady=(0, 25), padx=10)

        create_feature_card(features_grid, 0, "⚡", "Anında Analiz", "PDF'leri sürükle bırak.")
        create_feature_card(features_grid, 1, "🧠", "Akıllı Özetler", "Karmaşık konuları basitleştir.")
        create_feature_card(features_grid, 2, "🎯", "Bol Soru", "Geniş kapsamlı testler.")
        create_feature_card(features_grid, 3, "💬", "7/24 Asistan", "Takıldığın yerleri sor.")
        create_feature_card(features_grid, 4, "🎧", "Podcast Modu", "Özetleri yolda dinle.") # Bunu yeni ekledim.

        self.btn_start = ctk.CTkButton(
            content_box, text="BAŞLAYALIM 🚀", font=FONT_BTN, height=60, width=280,
            fg_color=COLOR_ACCENT, hover_color=COLOR_PRIMARY, corner_radius=30,
            command=self.start_app 
        )
        self.btn_start.pack()

    def start_app(self):
        self.welcome_container.pack_forget() # Introyu gizle.
        self.main_app_container.pack(fill="both", expand=True) # Ana ekranı aç.

    def show_welcome(self):
        self.main_app_container.pack_forget()
        self.welcome_container.pack(fill="both", expand=True)

    # --- 2. ANA UYGULAMA DÜZENİ ---
    def setup_main_app_structure(self):
        # Ekranı ikiye böldüm: Solda menü (Sidebar), sağda içerik.
        self.main_app_container.grid_columnconfigure(1, weight=1)
        self.main_app_container.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_content_area()
        self.show_home_screen()

    # Sol Menü Tasarımı
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.main_app_container, fg_color=COLOR_PRIMARY, width=260, corner_radius=0)
        self.sidebar.grid_propagate(False) 

        ctk.CTkLabel(self.sidebar, text="StudyPal", font=FONT_LOGO, text_color=COLOR_WHITE).pack(pady=(40, 5))
        
        # Yeni dosya yüklemek için temizleme butonu.
        ctk.CTkButton(self.sidebar, text="🗑️ TEMİZLE & YENİ YÜKLE", fg_color=COLOR_SUCCESS, height=40, font=FONT_BTN, 
                      command=self.arayuzu_sifirla).pack(pady=(20, 20), padx=20, fill="x")
        
        # Geçmiş kayıtları burada listeleyeceğim.
        ctk.CTkLabel(self.sidebar, text="GEÇMİŞ", font=(FONT_FAMILY, 12, "bold"), text_color="#90CAF9", anchor="w").pack(padx=20, fill="x")
        self.scroll_archive = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent") 
        self.scroll_archive.pack(fill="both", expand=True, padx=10, pady=10)

    # Arayüzü sıfırlama (Yeni dosya için temizlik)
    def arayuzu_sifirla(self):
        answer = messagebox.askyesno("Yeni Dosya", "Eski çalışma tamamen silinsin mi?")
        if answer:
            self.stop_player() # Eğer podcast çalıyorsa sustur.
            self.backend.db_sifirla() # Hafızayı temizle.
            self.current_data = {"ozet": "", "flash": [], "quiz": [], "tf": []} 
            self.frame_study.grid_forget() # Çalışma ekranını gizle.
            self.frame_home.grid(row=1, column=0, sticky="nsew") # Yükleme ekranına dön.
            self.btn_upload.configure(state="normal") 
            self.lbl_status.configure(text="")

    # Menüyü açıp kapama (Hamburger menü)
    def toggle_menu(self):
        if self.menu_acik:
            self.sidebar.grid_forget()
            self.btn_menu.configure(text="☰")
        else:
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.btn_menu.configure(text="✕")
        self.menu_acik = not self.menu_acik

    # Sağ taraf (İçerik Alanı)
    def setup_content_area(self):
        self.content_area = ctk.CTkFrame(self.main_app_container, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(1, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Üst Bar (Header)
        self.top_bar = ctk.CTkFrame(self.content_area, fg_color=COLOR_WHITE, height=60, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        self.btn_menu = ctk.CTkButton(self.top_bar, text="☰", width=50, fg_color="transparent", text_color=COLOR_PRIMARY, font=("Arial", 24), hover_color="#E3F2FD", command=self.toggle_menu)
        self.btn_menu.pack(side="left", padx=20, pady=10)
        
        ctk.CTkButton(self.top_bar, text="💾 Kaydet", fg_color=COLOR_ERROR, width=120, command=self.oturumu_kaydet).pack(side="right", padx=20)

        # İki ana ekranımız var: Home (Yükleme) ve Study (Çalışma)
        self.frame_home = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frame_study = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        self.populate_home_screen()

    def show_home_screen(self):
        self.frame_study.grid_forget()
        self.frame_home.grid(row=1, column=0, sticky="nsew")

    # --- DOSYA YÜKLEME EKRANI ---
    def populate_home_screen(self):
        # Sürükle bırak alanı
        drop = ctk.CTkFrame(self.frame_home, fg_color=COLOR_WHITE, corner_radius=20, border_color="#B3E5FC", border_width=2)
        drop.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.6)
        
        # TkinterDnD ile sürükle bırak özelliğini bağlıyorum.
        drop.drop_target_register(DND_FILES)
        drop.dnd_bind('<<Drop>>', self.dosya_birakildi) 

        ctk.CTkLabel(drop, text="☁️", font=("Arial", 60)).pack(pady=(60, 10))
        ctk.CTkLabel(drop, text="PDF'i Buraya Sürükle", font=FONT_H1, text_color=COLOR_PRIMARY).pack()
        
        self.btn_upload = ctk.CTkButton(drop, text="Bilgisayardan Seç", font=FONT_BTN, height=50, width=200, fg_color=COLOR_ACCENT, command=self.dosya_sec)
        self.btn_upload.pack(pady=20)
        
        self.lbl_status = ctk.CTkLabel(drop, text="", font=FONT_BODY, text_color=COLOR_ACCENT)
        self.lbl_status.pack(pady=10)

    # Sürükleme olayı gerçekleşince bu çalışır.
    def dosya_birakildi(self, event):
        path = event.data
        if path.startswith('{') and path.endswith('}'): path = path[1:-1] # Windows bazen parantez ekliyor, siliyorum.
        
        if path.lower().endswith(".pdf"): 
            # Eski veri varsa soruyorum.
            if self.backend.db is not None:
                cevap = messagebox.askyesno("Yeni Dosya", "ESKİ PDF SİLİNSİN Mİ?\n\n'Evet' -> Hafıza temizlenir.\n'Hayır' -> Birleştirilir.")
                if cevap:
                    self.backend.db_sifirla()
                    self.current_data = {"ozet": "", "flash": [], "quiz": [], "tf": []}
            self.baslat_yukleme([path])

    # Manuel dosya seçme.
    def dosya_sec(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if path:
            if self.backend.db is not None:
                cevap = messagebox.askyesno("Yeni Dosya", "ESKİ PDF SİLİNSİN Mİ?\n\n'Evet' -> Hafıza temizlenir.")
                if cevap:
                    self.backend.db_sifirla()
                    self.current_data = {"ozet": "", "flash": [], "quiz": [], "tf": []}
            self.baslat_yukleme([path])

    # Yüklemeyi Thread (Arka plan) olarak başlatıyorum, yoksa arayüz donar.
    def baslat_yukleme(self, paths):
        self.btn_upload.configure(state="disabled") 
        threading.Thread(target=self.yukleme_thread, args=(paths,)).start()

    # Arka planda çalışan yükleme fonksiyonu.
    def yukleme_thread(self, paths):
        try:
            self.lbl_status.configure(text="Sistem kontrol ediliyor...")
            
            if paths:
                base_name = os.path.basename(paths[0])
                self.aktif_dosya_adi = os.path.splitext(base_name)[0] 

            def cb(m): self.lbl_status.configure(text=m) # Durum mesajını güncellemek için callback.
            
            ok, msg = self.backend.toplu_yukle(paths, cb) # Backend'i çağır.
            
            self.btn_upload.configure(state="normal")
            
            if ok:
                self.frame_home.grid_forget() 
                self.populate_study_screen() 
                self.frame_study.grid(row=1, column=0, sticky="nsew") # Çalışma ekranına geç.
            else:
                messagebox.showerror("Hata", f"Yükleme Başarısız:\n{msg}")
                
        except Exception as e:
            self.btn_upload.configure(state="normal")
            import traceback
            traceback.print_exc() 
            messagebox.showerror("Kritik Hata", f"Beklenmeyen bir hata:\n{e}")

    # --- ÇALIŞMA PANELİ (SEKMELER) ---
    def populate_study_screen(self):
        # Önceki içeriği temizle.
        for widget in self.frame_study.winfo_children(): widget.destroy()

        # Sekmeli yapı (Tabview) oluşturdum.
        self.tabs = ctk.CTkTabview(self.frame_study, fg_color="transparent", segmented_button_selected_color=COLOR_PRIMARY, text_color="white", corner_radius=10)
        self.tabs.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Sekmeleri ekliyorum.
        self.tab_ozet = self.tabs.add("  📝 Özet  ")
        self.tab_flash = self.tabs.add("  ⚡ Kartlar  ")
        self.tab_quiz = self.tabs.add("  ✅ Sınav  ")
        self.tab_chat = self.tabs.add("  💬 Asistan  ")
        self.tab_podcast = self.tabs.add("  🎧 Podcast  ") # Podcast sekmesi burada.

        # Her sekmenin içini dolduran fonksiyonları çağırıyorum.
        self.setup_ozet_ui()
        self.setup_flash_ui()
        self.setup_quiz_ui()
        self.setup_chat_ui()
        self.setup_podcast_ui() 

    # -- ÖZET SEKMESİ --
    def setup_ozet_ui(self):
        btn = ctk.CTkButton(self.tab_ozet, text="✨ Profesör Modunda Özetle", font=FONT_BTN, height=50, fg_color=COLOR_ACCENT, command=self.ozet_baslat)
        btn.pack(pady=20, fill="x", padx=50)

        self.txt_ozet = ctk.CTkTextbox(self.tab_ozet, font=FONT_BODY, fg_color=COLOR_WHITE, text_color=COLOR_TEXT)
        self.txt_ozet.pack(fill="both", expand=True, padx=20, pady=10)

        # Metin kutusuna renk etiketlerini (tag) ekliyorum.
        try:
            self.txt_ozet._textbox.tag_config("header_big", foreground=COLOR_HEADER_BIG, font=FONT_H1, spacing3=10)
            self.txt_ozet._textbox.tag_config("header_small", foreground=COLOR_HEADER_SMALL, font=FONT_H2, spacing3=5)
            self.txt_ozet._textbox.tag_config("body", foreground="black", font=FONT_BODY) 
        except: pass

    def ozet_baslat(self):
        self.txt_ozet.delete("0.0", "end")
        self.txt_ozet.insert("0.0", "AI analiz ediyor...")
        def run():
            ctx = self.backend.get_context("özet")
            # Prompt Engineering: Modele format kurallarını öğretiyorum.
            prompt = f"""Metni çok akıcı ve profesyonel bir dille Türkçe olarak özetle.
            KURALLAR:
            1. Büyük ana başlıkların başına SADECE '-' (tire) işareti koy. Yıldız kullanma.
            2. Alt başlıkların başına '1.', '2.' gibi sayılar koy.
            3. Metin bir üniversite ders kitabı gibi resmi ve açıklayıcı olsun.
            Metin: {ctx}"""
            
            res, err = self.backend.sor(prompt)
            self.txt_ozet.delete("0.0", "end")
            if err: self.txt_ozet.insert("0.0", f"Hata: {err}")
            else: 
                self.metni_formatla_ve_yaz(self.txt_ozet, res)
                self.current_data["ozet"] = res
        threading.Thread(target=run).start()

    # --- PODCAST ARAYÜZÜ (PLAYER MODU) ---
    def setup_podcast_ui(self):
        # Ortadaki beyaz kutu.
        self.pod_container = ctk.CTkFrame(self.tab_podcast, fg_color=COLOR_WHITE, corner_radius=20)
        self.pod_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.7)

        # 1. Durum: Hazırla Butonu (İlk açılışta bu görünür)
        self.pod_init_frame = ctk.CTkFrame(self.pod_container, fg_color="transparent")
        self.pod_init_frame.pack(expand=True)

        ctk.CTkLabel(self.pod_init_frame, text="🎙️", font=("Arial", 60)).pack(pady=10)
        ctk.CTkLabel(self.pod_init_frame, text="AI Podcast Oluşturucu", font=FONT_H1, text_color=COLOR_PRIMARY).pack(pady=10)
        
        self.btn_pod_create = ctk.CTkButton(self.pod_init_frame, text="Senaryoyu Yaz ve Seslendir", font=FONT_BTN, height=50, width=250, fg_color="#F57C00", command=self.podcast_olustur)
        self.btn_pod_create.pack(pady=20)
        self.lbl_pod_status = ctk.CTkLabel(self.pod_init_frame, text="", text_color=COLOR_SUBTEXT)
        self.lbl_pod_status.pack()

        # 2. Durum: Player (Ses oluşunca bu görünür)
        self.pod_player_frame = ctk.CTkFrame(self.pod_container, fg_color="transparent")
        
        ctk.CTkLabel(self.pod_player_frame, text="🎧 Now Playing", font=(FONT_FAMILY, 14), text_color=COLOR_SUBTEXT).pack(pady=(20,5))
        ctk.CTkLabel(self.pod_player_frame, text="StudyPal AI Özeti", font=FONT_H1, text_color=COLOR_TEXT).pack(pady=(0,30))

        # Zaman Göstergeleri ve Slider
        self.lbl_curr_time = ctk.CTkLabel(self.pod_player_frame, text="00:00", font=("Consolas", 14), text_color=COLOR_PRIMARY)
        self.lbl_curr_time.pack(anchor="w", padx=40)
        
        # Slider'ı sese sarabilmek için koydum.
        self.slider_pod = ctk.CTkSlider(self.pod_player_frame, from_=0, to=100, number_of_steps=1000, progress_color=COLOR_PRIMARY)
        self.slider_pod.pack(fill="x", padx=40, pady=5)
        self.slider_pod.bind("<ButtonRelease-1>", self.seek_audio) # Bıraktığımda o saniyeye git.

        self.lbl_total_time = ctk.CTkLabel(self.pod_player_frame, text="00:00", font=("Consolas", 14), text_color=COLOR_PRIMARY)
        self.lbl_total_time.pack(anchor="e", padx=40)

        # Kontroller (Geri sar, Oynat, İleri sar)
        ctrl_box = ctk.CTkFrame(self.pod_player_frame, fg_color="transparent")
        ctrl_box.pack(pady=20)

        ctk.CTkButton(ctrl_box, text="⏪ 10sn", width=60, fg_color="transparent", text_color=COLOR_PRIMARY, border_width=1, command=lambda: self.skip(-10)).pack(side="left", padx=10)
        self.btn_play_pause = ctk.CTkButton(ctrl_box, text="⏸ Durdur", width=120, height=40, font=FONT_BTN, fg_color=COLOR_PRIMARY, command=self.toggle_play)
        self.btn_play_pause.pack(side="left", padx=10)
        ctk.CTkButton(ctrl_box, text="10sn ⏩", width=60, fg_color="transparent", text_color=COLOR_PRIMARY, border_width=1, command=lambda: self.skip(10)).pack(side="left", padx=10)

        # Sıfırlama butonu
        ctk.CTkButton(self.pod_player_frame, text="Yeni Podcast Hazırla", fg_color="transparent", text_color=COLOR_ERROR, hover_color=COLOR_ERROR_BG, command=self.reset_podcast_ui).pack(side="bottom", pady=20)

    # Player'ı kapatıp başa dönme.
    def reset_podcast_ui(self):
        self.stop_player()
        self.pod_player_frame.pack_forget()
        self.pod_init_frame.pack(expand=True)

    # Podcast oluşturma süreci (Senaryo + TTS).
    def podcast_olustur(self):
        self.btn_pod_create.configure(state="disabled")
        self.lbl_pod_status.configure(text="Senaryo yazılıyor...")
        
        def run():
            try:
                # 1. Metni çek
                ctx = self.backend.get_context("özet")
                if not ctx:
                    self.lbl_pod_status.configure(text="Hata: Metin yok.")
                    self.btn_pod_create.configure(state="normal")
                    return

                # 2. Senaryo yazdır
                script = self.backend.podcast_senaryosu_al(ctx)
                
                self.lbl_pod_status.configure(text="Seslendiriliyor (Ahmet)...")
                
                # Varsa eski dosyayı sil.
                if os.path.exists(self.audio_file):
                    try: os.remove(self.audio_file)
                    except: pass
                
                # 3. Sesi indir (Asenkron işlem). Edge-TTS kullanıyorum.
                async def create_voice():
                    # 'rate=+25%' diyerek sesi hızlandırdım, daha akıcı oldu.
                    communicate = edge_tts.Communicate(script, "tr-TR-AhmetNeural", rate="+25%") 
                    await communicate.save(self.audio_file)
                asyncio.run(create_voice())

                # 4. Süreyi hesapla (Mutagen kütüphanesi ile).
                audio = MP3(self.audio_file)
                self.total_duration = audio.info.length
                
                # 5. Arayüzü değiştir (Player'ı göster).
                self.pod_init_frame.pack_forget()
                self.pod_player_frame.pack(expand=True, fill="both")
                
                # Slider'ı ayarla.
                self.slider_pod.configure(to=self.total_duration)
                self.slider_pod.set(0)
                mins, secs = divmod(int(self.total_duration), 60)
                self.lbl_total_time.configure(text=f"{mins:02}:{secs:02}")

                # Oynatmaya başla.
                self.start_player()
                self.btn_pod_create.configure(state="normal")
                self.lbl_pod_status.configure(text="")

            except Exception as e:
                print(e)
                self.lbl_pod_status.configure(text=f"Hata: {e}")
                self.btn_pod_create.configure(state="normal")

        threading.Thread(target=run).start()

    # Oynatıcı fonksiyonları
    def start_player(self):
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()
        self.is_playing = True
        self.btn_play_pause.configure(text="⏸ Durdur")
        self.update_slider_loop() # Slider'ı ilerletmeye başla.

    def stop_player(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        if self.update_loop_id:
            self.after_cancel(self.update_loop_id) # Döngüyü kır.

    def toggle_play(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.btn_play_pause.configure(text="▶️ Oynat")
            self.is_playing = False
        else:
            pygame.mixer.music.unpause()
            self.btn_play_pause.configure(text="⏸ Durdur")
            self.is_playing = True
            self.update_slider_loop()

    def skip(self, sec):
        try:
            current = self.slider_pod.get()
            new_pos = max(0, min(self.total_duration, current + sec))
            self.slider_pod.set(new_pos)
            pygame.mixer.music.play(start=new_pos) # O saniyeden başlat.
            self.is_playing = True
            self.btn_play_pause.configure(text="⏸ Durdur")
        except: pass

    def seek_audio(self, event):
        pos = self.slider_pod.get()
        pygame.mixer.music.play(start=pos)
        self.is_playing = True
        self.btn_play_pause.configure(text="⏸ Durdur")

    # Slider'ı saniye saniye ilerleten döngü.
    def update_slider_loop(self):
        if self.is_playing:
            if pygame.mixer.music.get_busy():
                current_val = self.slider_pod.get()
                if current_val < self.total_duration:
                    self.slider_pod.set(current_val + 1)
                    
                    # Süreyi ekrana yazdır (00:00 formatında).
                    mins, secs = divmod(int(current_val + 1), 60)
                    self.lbl_curr_time.configure(text=f"{mins:02}:{secs:02}")
            else:
                # Müzik bitti.
                self.btn_play_pause.configure(text="▶️ Tekrar Oynat")
                self.is_playing = False
                self.slider_pod.set(0)

            # 1 saniye sonra bu fonksiyonu tekrar çalıştır (Recursive).
            self.update_loop_id = self.after(1000, self.update_slider_loop)

    # -- KARTLAR (FLASHCARDS) --
    def setup_flash_ui(self):
        self.flash_data = [] 
        self.flash_idx = 0   
        self.kart_yonu = "on" 

        ctk.CTkButton(self.tab_flash, text="Kart Oluştur", font=FONT_BTN, height=40, fg_color=COLOR_ACCENT, command=self.flash_baslat).pack(pady=10)
        
        # Kartın kendisi.
        self.flash_card = ctk.CTkFrame(self.tab_flash, fg_color=COLOR_WHITE, corner_radius=20, border_color="#B3E5FC", border_width=2)
        self.flash_card.pack(expand=True, fill="both", padx=50, pady=20)
        
        # Tıklayınca çevir özelliği.
        self.flash_card.bind("<Button-1>", self.kart_cevir)
        
        self.lbl_flash_content = ctk.CTkLabel(self.flash_card, text="Kart Yok", font=FONT_H1, wraplength=800)
        self.lbl_flash_content.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_flash_content.bind("<Button-1>", self.kart_cevir)

        # İleri geri butonları.
        nav = ctk.CTkFrame(self.tab_flash, fg_color="transparent")
        nav.pack(pady=20)
        ctk.CTkButton(nav, text="< Önceki", width=120, height=40, command=lambda: self.flash_nav(-1)).pack(side="left", padx=20)
        ctk.CTkButton(nav, text="Sonraki >", width=120, height=40, command=lambda: self.flash_nav(1)).pack(side="left", padx=20)

    def flash_baslat(self):
        self.lbl_flash_content.configure(text="Hazırlanıyor...", text_color="black")
        self.flash_card.configure(fg_color=COLOR_WHITE)
        def run():
            ctx = self.backend.get_context("terimler")
            # AI'dan JSON formatında çıktı istiyorum.
            prompt = """Metinden 5 önemli terim seç ve bunları soru-cevap formatına dönüştür. DİL TÜRKÇE OLSUN.
            SADECE JSON FORMATINDA VER: [ {"front": "Soru?", "back": "Cevap"} ] 
            Metin: """ + ctx
            res, _ = self.backend.sor(prompt)
            data = self.backend.json_temizle(res) 
            if data:
                self.flash_data = data
                self.current_data["flash"] = data
                self.flash_idx = 0
                self.kart_yonu = "on"
                self.flash_guncelle()
            else: self.lbl_flash_content.configure(text="AI Oluşturamadı.")
        threading.Thread(target=run).start()

    def flash_guncelle(self):
        if not self.flash_data: return
        self.kart_yonu = "on"
        self.flash_card.configure(fg_color=COLOR_WHITE)
        self.lbl_flash_content.configure(text=self.flash_data[self.flash_idx]['front'], text_color="black")

    # Kartı ters çevirme mantığı.
    def kart_cevir(self, event=None):
        if not self.flash_data: return
        
        if self.kart_yonu == "on":
            self.kart_yonu = "arka"
            self.flash_card.configure(fg_color=COLOR_ACCENT) # Arkası mavi olsun.
            self.lbl_flash_content.configure(
                text=self.flash_data[self.flash_idx]['back'],
                text_color="white" # Yazı beyaz olsun.
            )
        else:
            self.kart_yonu = "on"
            self.flash_card.configure(fg_color=COLOR_WHITE) # Önü beyaz olsun.
            self.lbl_flash_content.configure(
                text=self.flash_data[self.flash_idx]['front'],
                text_color="black" # Yazı siyah olsun.
            )

    def flash_nav(self, d):
        self.flash_idx = (self.flash_idx + d) % len(self.flash_data) if self.flash_data else 0
        self.flash_guncelle()

    # -- 3. SINAV (QUIZ) --
    def setup_quiz_ui(self):
        self.quiz_data = []
        self.quiz_idx = 0
        self.quiz_answers = {} 

        self.fr_quiz_start = ctk.CTkFrame(self.tab_quiz, fg_color="transparent")
        self.fr_quiz_start.pack(fill="both", expand=True)
        ctk.CTkButton(self.fr_quiz_start, text="Geniş Kapsamlı Sınavı Başlat (Min 15 Soru)", height=60, fg_color=COLOR_SUCCESS, font=FONT_BTN, command=self.quiz_baslat).pack(pady=100)
        
        self.fr_quiz_run = ctk.CTkFrame(self.tab_quiz, fg_color="transparent")
        self.lbl_quiz_q = ctk.CTkLabel(self.fr_quiz_run, text="", font=FONT_H2, wraplength=800)
        self.lbl_quiz_q.pack(pady=30)
        self.fr_opts = ctk.CTkFrame(self.fr_quiz_run, fg_color="transparent")
        self.fr_opts.pack(fill="x")

    def quiz_baslat(self):
        self.fr_quiz_start.pack_forget()
        self.fr_quiz_run.pack(fill="both", expand=True)
        self.lbl_quiz_q.configure(text="Sınav ve detaylı açıklamalar hazırlanıyor...")
        def run():
            ctx = self.backend.get_context("sınav tüm konular detaylı")
            # Explanation (Açıklama) alanını da istiyorum.
            prompt = """Metinden EN AZ 15 ADET çoktan seçmeli soru hazırla. Konuları iyice tara. DİL TÜRKÇE OLSUN.
            Format hatasız olmalı.
            SADECE JSON FORMATINDA VER: 
            [ 
              {"q": "Soru?", "opts": ["A) ..", "B) .."], "correct": "A) ..", "explanation": "Doğru cevabın neden bu olduğunu açıklayan detaylı metin."} 
            ] 
            Metin: """ + ctx
            res, _ = self.backend.sor(prompt)
            data = self.backend.json_temizle(res)
            if data and len(data) > 0:
                self.quiz_data = data
                self.current_data["quiz"] = data
                self.quiz_idx = 0
                self.quiz_answers = {}
                self.quiz_goster()
            else: self.lbl_quiz_q.configure(text="Soru oluşturulamadı.")
        threading.Thread(target=run).start()

    def quiz_goster(self):
        if self.quiz_idx >= len(self.quiz_data):
            self.quiz_bitir()
            return
        q = self.quiz_data[self.quiz_idx]
        self.lbl_quiz_q.configure(text=f"{self.quiz_idx+1}. {q['q']}")
        for w in self.fr_opts.winfo_children(): w.destroy()
        for opt in q['opts']:
            ctk.CTkButton(self.fr_opts, text=opt, fg_color="white", text_color="black", hover_color="#E3F2FD", command=lambda o=opt: self.quiz_cevap(o)).pack(pady=5, fill="x", padx=100)

    def quiz_cevap(self, ans):
        self.quiz_answers[self.quiz_idx] = ans
        self.quiz_idx += 1
        self.quiz_goster()

    def quiz_bitir(self):
        self.fr_quiz_run.pack_forget()
        self.fr_result = ctk.CTkScrollableFrame(self.tab_quiz, fg_color="transparent")
        self.fr_result.pack(fill="both", expand=True, padx=20, pady=20)
        
        correct_count = 0
        for i, q in enumerate(self.quiz_data):
            user_ans = self.quiz_answers.get(i, "Boş")
            real_ans = q['correct']
            explanation = q.get('explanation', 'Açıklama yok.')
            
            is_correct = user_ans == real_ans or (real_ans in user_ans)
            if is_correct: correct_count += 1
            
            # Soru Kartı
            card = ctk.CTkFrame(self.fr_result, fg_color=COLOR_WHITE, corner_radius=10, border_width=1, border_color="#DDD")
            card.pack(fill="x", pady=10)
            
            card.grid_columnconfigure(0, weight=0) 
            card.grid_columnconfigure(1, weight=1) 

            # Yuvarlak İkon (Tik veya Çarpı)
            icon_text = "✓" if is_correct else "✕"
            icon_color = COLOR_SUCCESS if is_correct else COLOR_ERROR
            btn_icon = ctk.CTkButton(card, text=icon_text, width=40, height=40, corner_radius=20, 
                                     fg_color=icon_color, state="disabled", text_color="white", font=FONT_H2)
            btn_icon.grid(row=0, column=0, rowspan=3, padx=15, pady=10, sticky="n")

            text_frame = ctk.CTkFrame(card, fg_color="transparent")
            text_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=5)
            
            ctk.CTkLabel(text_frame, text=f"{i+1}. {q['q']}", font=FONT_BOLD, text_color=COLOR_TEXT, wraplength=700, justify="left").pack(anchor="w", pady=2)
            ctk.CTkLabel(text_frame, text=f"Senin Cevabın: {user_ans}", font=FONT_BODY, text_color=COLOR_TEXT).pack(anchor="w")
            
            if not is_correct:
                ctk.CTkLabel(text_frame, text=f"Doğru Cevap: {real_ans}", font=FONT_BOLD, text_color=COLOR_SUCCESS).pack(anchor="w")
                # Yanlışsa açıklamayı göster.
                ctk.CTkLabel(text_frame, text=f"Neden?: {explanation}", font=(FONT_FAMILY, 13), text_color=COLOR_SUBTEXT, wraplength=700, justify="left").pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(self.fr_result, text=f"🎉 SKOR: {correct_count} / {len(self.quiz_data)}", font=FONT_HERO, text_color=COLOR_PRIMARY).pack(side="top", pady=20)
        ctk.CTkButton(self.fr_result, text="Yeniden Başlat", fg_color=COLOR_ACCENT, command=self.quiz_restart).pack(pady=20)

    def quiz_restart(self):
        self.fr_result.destroy()
        self.fr_quiz_start.pack(fill="both", expand=True)

    # -- 4. SOHBET (ASİSTAN) --
    def setup_chat_ui(self):
        self.txt_chat = ctk.CTkTextbox(self.tab_chat, state="disabled", font=FONT_BODY, fg_color="#ECEFF1", text_color="black")
        self.txt_chat.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sohbet renkleri.
        try:
            self.txt_chat._textbox.tag_config("user_label", justify="right", foreground=COLOR_USER_LABEL, font=FONT_BOLD)
            self.txt_chat._textbox.tag_config("user_msg", justify="right", foreground="black")
            self.txt_chat._textbox.tag_config("bot_label", justify="left", foreground=COLOR_BOT_LABEL, font=FONT_BOLD)
            
            self.txt_chat._textbox.tag_config("header_big", justify="left", foreground=COLOR_HEADER_BIG, font=FONT_H1, spacing3=10)
            self.txt_chat._textbox.tag_config("header_small", justify="left", foreground=COLOR_HEADER_SMALL, font=FONT_H2, spacing3=5)
            self.txt_chat._textbox.tag_config("body", justify="left", foreground="black") 
        except: pass 

        self.ent_chat = ctk.CTkEntry(self.tab_chat, height=40, placeholder_text="Bir soru sor...")
        self.ent_chat.pack(fill="x", padx=20, pady=(0, 10))
        self.ent_chat.bind("<Return>", self.chat_yolla)

    def chat_yolla(self, event=None):
        msg = self.ent_chat.get()
        if not msg: return
        self.ent_chat.delete(0, "end")
        
        # Önce benim mesajımı ekrana yaz.
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", "SEN:\n", "user_label")
        self.txt_chat.insert("end", f"{msg}\n\n", "user_msg")
        self.txt_chat.configure(state="disabled")
        
        def run():
            ctx = self.backend.get_context(msg) 
            prompt = f"""Şu bağlama göre Türkçe cevap ver: {ctx}
            Soru: {msg}
            KURALLAR:
            1. Ana başlıklar '-' ile başlasın.
            2. Alt başlıklar '1.', '2.' ile başlasın.
            3. Metin çok profesyonel ve akıcı olsun."""
            
            res, _ = self.backend.sor(prompt)
            
            # Sonra cevabı ekrana yaz (Formatlı).
            self.txt_chat.configure(state="normal")
            self.txt_chat.insert("end", "StudyPal:\n", "bot_label")
            self.metni_formatla_ve_yaz(self.txt_chat, res)
            self.txt_chat.insert("end", "\n\n", "body")
            self.txt_chat.configure(state="disabled")
            self.txt_chat.see("end")
        threading.Thread(target=run).start()

    # --- KAYDET VE YÜKLE ---
    def oturumu_kaydet(self):
        name = self.aktif_dosya_adi
        if not name:
            name = f"Oturum_{datetime.now().strftime('%H%M')}"
        
        self.saved_sessions[name] = copy.deepcopy(self.current_data)
        
        # Eğer zaten listede varsa tekrar ekleme.
        found = False
        for widget in self.scroll_archive.winfo_children():
            try:
                if widget.cget("text") == f"📂 {name}":
                    found = True
                    break
            except: pass
        
        if not found:
            btn = ctk.CTkButton(self.scroll_archive, text=f"📂 {name}", fg_color="#1E88E5", command=lambda n=name: self.oturumu_yukle(n))
            btn.pack(fill="x", pady=2)
            
        messagebox.showinfo("Kaydedildi", f"'{name}' olarak başarıyla kaydedildi.")

    def oturumu_yukle(self, name):
        data = self.saved_sessions.get(name)
        if not data: return
        
        self.current_data = data 
        self.frame_home.grid_forget()
        self.frame_study.grid(row=1, column=0, sticky="nsew")

        # Özeti geri yükle
        self.txt_ozet.delete("0.0", "end")
        self.metni_formatla_ve_yaz(self.txt_ozet, data.get("ozet", ""))

        # Kartları geri yükle
        self.flash_data = data.get("flash", [])
        self.flash_idx = 0
        self.flash_guncelle()

        # Sınavı geri yükle (Sıfırdan başlasın)
        self.quiz_data = data.get("quiz", [])
        self.quiz_idx = 0
        self.quiz_answers = {} 
        
        try:
            self.fr_result.pack_forget() 
            self.fr_quiz_start.pack_forget() 
        except: pass

        if self.quiz_data:
            self.fr_quiz_run.pack(fill="both", expand=True) 
            self.quiz_goster()
        else:
            self.fr_quiz_run.pack_forget()
            self.fr_quiz_start.pack(fill="both", expand=True)

        messagebox.showinfo("Yüklendi", f"'{name}' başarıyla yüklendi.")

# PROGRAMIN BAŞLANGIÇ NOKTASI
if __name__ == "__main__":
    app = StudyPalApp() # Uygulamayı oluştur.

    app.mainloop()      # Pencereyi açık tut.
