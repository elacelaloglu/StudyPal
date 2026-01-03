 StudyPal: Yapay Zeka Destekli Akıllı Öğrenme Asistanı

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/Durum-Tamamlandı-success)
![Course](https://img.shields.io/badge/Ders-BOZ213_OOP-orange)

StudyPal, biz öğrencilerin en büyük derdi olan yüzlerce sayfalık,  sıkıcı PDF ders notlarını; konuşan, soru soran ve özetleyen interaktif bir çalışma arkadaşına dönüştüren masaüstü uygulamasıdır.

Bu proje,  OOP prensipleri ve modern yapay zeka teknolojileri (RAG Mimarisi) birleştirilerek geliştirilmiştir.

---

 Projenin Amacı
Ders çalışırken PDF'ler arasında kaybolmak yerine, notlarla "sohbet edebileceğimiz" bir ortam yaratmayı hedefledim. StudyPal sadece bir özet çıkarıcı değil; aynı zamanda dersi size bir podcast gibi anlatan, sizi sınav yapan ve eksiklerinizi kapatan sanal bir asistandır.

 Neler Yapabiliyor?

 RAG Mimarisi (Akıllı Analiz):** PDF'i yüklediğinizde tüm metni vektörlere ayırır. Bir soru sorduğunuzda yapay zeka uydurmaz, sadece dokümandaki bilgiye dayanarak cevap verir.
 Podcast Modu (Favorim!):** Ders notlarını esprili ve samimi bir radyo programı senaryosuna dönüştürür. Ardından **Microsoft Edge-TTS** teknolojisiyle, nefes alan ve tonlama yapan doğal bir insan sesiyle (Ahmet/Neslihan) size anlatır.
 Profesör Modunda Özet:** Karmaşık akademik dili, anlaşılır maddeler haline getirir.
 Sınav (Quiz) Robotu:** İçerikten otomatik test soruları üretir. Yanlış yaparsanız "Bak şundan dolayı yanlış" diyerek doğrusunu öğretir.
 Flashcards:** Ezberlenmesi gereken terimleri otomatik yakalar ve çalışma kartlarına dönüştürür.

---

 Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları takip edebilirsiniz.

 1. Projeyi Klonlayın
```bash
git clone [https://github.com/KULLANICI_ADINIZ/StudyPal.git](https://github.com/KULLANICI_ADINIZ/StudyPal.git)
cd StudyPal

2. Gerekli Kütüphaneleri Yükleyin
Projenin çalışması için requirements.txt içindeki kütüphanelerin yüklü olması gerekir:

Bash

pip install -r requirements.txt
3. API Anahtarı Ayarı (Önemli!) 
Bu proje Groq (Llama-3) modelini kullanmaktadır. Güvenlik nedeniyle API anahtarı koddan kaldırılmıştır.

main.py dosyasını açın.

GROQ_API_KEY satırını bulun.

Kendi ücretsiz Groq API anahtarınızı (https://console.groq.com) oraya yapıştırın.

4. Başlatın
Bash

python main.py
 Teknik Detaylar (Nasıl Çalışıyor?)
Projeyi geliştirirken "Spagetti Kod" olmaması için Nesne Yönelimli Programlama (OOP) kurallarına sadık kaldım:

Mimari: Proje, Arayüz (StudyPalApp) ve İş Mantığı (Backend) olmak üzere iki ana sınıfa ayrılmıştır. Bu sayede kod yönetilebilir ve geliştirilebilir haldedir.

Teknolojiler:

Dil: Python 3.10

GUI: CustomTkinter (Modern arayüz için)

AI & NLP: LangChain, Groq, HuggingFace Embeddings

Veritabanı: ChromaDB (Vektör veritabanı)

Ses Motoru: Edge-TTS & Pygame

Algoritmalar: Threading (Paralel işlem) ile arayüz donmaları engellenmiş, SequenceMatcher ile akıllı cevap kontrolü sağlanmıştır.

👤 Geliştirici
Bu proje Ela Nur Celaloğlu tarafından  hazırlanmıştır. Sorularınız veya önerileriniz için ulaşabilirsiniz! 
