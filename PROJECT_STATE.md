# 🧭 UYAP Dilekçe Hazırlayıcı: Proje Durumu & Geliştirici Devir Kılavuzu (v1.5.0)

Bu kılavuz, diğer bilgisayarınızdaki **Antigravity** ile geliştirmeye kaldığınız yerden eksiksiz ve hızlı bir şekilde devam edebilmeniz için mimariyi, repo yapısını ve son durumu özetlemektedir.

---

## 📦 1. GitHub Depoları & Çalışma Alanları

Proje 3 farklı amaca göre ayrıştırılmış ve GitHub ile tam senkronize edilmiştir:

| Repo Adı | Görünürlük | Açıklama & Yol |
| :--- | :--- | :--- |
| **`ssayoglu/uyap-dilekce-hazirlayici`** | **Public** | **Ana macOS Sürümü:** Açık kaynaklı, macOS yerel Swift sarmalayıcılı (`DilekceApp`), Menubar Hızlı Mazeret popover'lı ana repo. |
| **`ssayoglu/uyap-dilekce-windows`** | **Public** | **Windows Sürümü:** `os.startfile`, `win_app.py` (Edge/Chrome app mode) ve PowerShell installer (`install.ps1`) içeren sürüm. |
| **`ssayoglu/uyap-dilekce-pro`** | **Private** | **Ticari / Lisanslı Sürüm:** Çevrimdışı donanım kilitli (`HWID / HMAC-SHA256`) lisans motoru, `keygen.py` ve `Landing_Page` web sitesi içeren gizli repo. |

---

## 🚀 2. v1.5.0 Sürümünde Tamamlanan Özellikler (Aktif Durum)

1. **✨ Yapay Zekâ Destekli Dilekçe Oluşturucu (Gemini 3.6 Flash / Flash-Lite Havuzu):**
   - Serbest doğal dille anlatılan olay örgüsünü Türk mevzuatı, Yargıtay ve AYM içtihatları çerçevesinde inceleyip eksiksiz UYAP dilekçesi formatına dönüştürür.
   - Hukuk dalı ve mahkeme türü seçicisi (Ceza, Hukuk, İcra, İş, Aile, Ticaret, İdare vb.) ile entegre.
2. **⚠️ Kırmızı Hukuki Risk & Süre Tespiti:**
   - Zamanaşımı, hak düşürücü süreler, delil karartma/silinme riskleri parantez içinde kırmızı yazıyla (`(DİKKAT / HUKUKİ RİSK: ...)`) dilekçe bentlerine eklenir.
   - Hem web arayüzünde hem de UYAP Doküman Editörü XML standardında kırmızı renkle (`foreground="-65536"`, `bold="true"`) açılır.
3. **🏛️ Evrensel Tutukluluk ve Tahliye İtiraz Şablonu:**
   - 8 temel hukuki bent ve kademeli netice-i talep ile standardize edilen ceza şablonu.
4. **🔄 Güçlendirilmiş Güncelleme Sistemi:**
   - Uygulama menüsünden tek tıkla HTTP tabanlı doğrudan GitHub güncellemesi.
   - Terminal için bağımsız tek satırlık güncelleme komutu (`update.sh`).
5. **⚡ macOS Menü Çubuğu (Menubar ⚖️) Hızlı Mazeret Modülü:**
   - Ekranın üst çubuğundaki `⚖️` simgesine sol tıklandığında mini mazeret penceresi açılır. Mahkeme, dosya no ve saat girilip 3 saniyede UYAP Mazeret UDF'i üretilir.
6. **🔢 Dinamik UYAP Sıralı Liste & İki Yana Yaslama:**
   - Açıklamalar maddeleri UYAP Doküman Editörü'nün yerel XML şeması (`Numbered="true"`, `NumberType="NUMBER_TYPE_NUMBER_DOT"`, `LeftIndent="25.0"`, `Alignment="3"`) ile üretilir.
7. **💰 Canlı Harç, Masraf & Kademeli AAÜT Vekâlet Ücreti Motoru:**
   - Formda Dava Değeri (H.E.D.) girildiği anda Peşin Harç (1/4), Başvuru Harcı, %20 İcra İnkâr Tazminatı ve kademeli AAÜT vekâlet ücreti anlık hesaplanır.
8. **👥 Yerel Müvekkil Rehberi (Local CRM):**
   - `localStorage` tabanlı. Müvekkillerin T.C., unvan ve adresleri kaydedilir; form doldururken tek tıkla aktarılır.

---

## 🛠️ 3. Dosya & Kod Yapısı Haritası

```text
├── server.py             # HTTP Backend (Port: 5678) + build_udf (XML Motoru) + Gemini AI + HTML_PAGE
├── main.swift            # macOS Native Cocoa/WebKit Wrapper + Menubar StatusItem & Popover + Güncelleyici
├── build_app.sh          # Swift'i derleyip .app paketini oluşturan betik
├── update.sh             # Tek satırla GitHub'dan güncelleyici betik
├── version.json          # Sürüm kontrol ve otomatik güncelleme bildirim dosyası (v1.5.0)
├── install.sh            # macOS tek satır sıfır bağımlı kurulum betiği (cURL | bash)
└── AppIcon.icns          # macOS retina uygulama simgesi
```

---

## 💻 4. Diğer Bilgisayarda Antigravity'ye Verilecek İlk Komut / İstek

Diğer bilgisayarınızdaki Antigravity'yi açtığınızda projeyi çekmek için:

```bash
git clone https://github.com/ssayoglu/uyap-dilekce-hazirlayici.git
cd uyap-dilekce-hazirlayici
./build_app.sh
```

---

## 🎯 5. Sırada Bekleyen Geliştirme Fikirleri (Roadmap)
* 📥 **Özel UDF Şablon İçe Aktarma:** Kullanıcının kendi hazırladığı bir `.udf` dosyasını sürükle-bırak yaparak sisteme yeni şablon olarak kaydetmesi.
* ⚖️ **İcra Kapak Hesabı & Kıdem Tazminatı:** İcra takip talepleri ve İş Mahkemesi dilekçeleri için ek hesaplama modülleri.
* ⌨️ **Global Kısayol (`⌥ + Space`):** Hangi ekranda olunursa olunsun klavye kısayolu ile Spotlight gibi açılan dilekçe arama penceresi.
