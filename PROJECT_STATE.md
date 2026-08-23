# 🧭 UYAP Dilekçe Hazırlayıcı: Proje Durumu & Geliştirici Devir Kılavuzu (v1.4.0)

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

## 🚀 2. v1.4.0 Sürümünde Tamamlanan Özellikler (Aktif Durum)

1. **⚡ macOS Menü Çubuğu (Menubar ⚖️) Hızlı Mazeret Modülü:**
   - Ekranın üst çubuğundaki `⚖️` simgesine sol tıklandığında mini mazeret penceresi açılır. Mahkeme, dosya no ve saat girilip 3 saniyede UYAP Mazeret UDF'i üretilir.
   - Sağ tıklandığında veya Dock'tan açıldığında ana galeri penceresi gelir.
2. **🔢 Dinamik UYAP Sıralı Liste & İki Yana Yaslama:**
   - Açıklamalar maddeleri UYAP Doküman Editörü'nün yerel XML şeması (`Numbered="true"`, `NumberType="NUMBER_TYPE_NUMBER_DOT"`, `LeftIndent="25.0"`, `Alignment="3"`) ile üretilir.
   - Kullanıcı UYAP'ta satır ekleyip sildikçe numaralar otomatik güncellenir.
3. **💰 Canlı Harç, Masraf & Kademeli AAÜT Vekâlet Ücreti Motoru:**
   - Formda Dava Değeri (H.E.D.) girildiği anda Peşin Harç (1/4), Başvuru Harcı, %20 İcra İnkâr Tazminatı ve kademeli AAÜT vekâlet ücreti anlık hesaplanır.
4. **👥 Yerel Müvekkil Rehberi (Local CRM):**
   - `localStorage` tabanlı. Müvekkillerin T.C., unvan ve adresleri kaydedilir; form doldururken tek tıkla aktarılır.
5. **⚙️ Hukuki Çip Yöneticisi:**
   - Hukuk ve Ceza mahkemeleri için hazır gerekçe bentleri (`Şüpheden Sanık Yararlanır`, `Kast Yokluğu`, `Tanık Dinletme`, `Banka Müzekkeresi` vb.). Kullanıcı dilediği gibi yeni çip ekleyebilir/düzenleyebilir.
6. **👁️ Canlı UYAP Önizleme (Live Preview):**
   - Form alanının yanında UYAP'ın 1.0 satır aralığını ve milimetrik hizalamasını eşzamanlı gösteren simülasyon.

---

## 🛠️ 3. Dosya & Kod Yapısı Haritası

```text
├── server.py             # HTTP Backend (Port: 5678) + build_udf (XML Motoru) + HTML_PAGE + MAZERET_HTML
├── main.swift            # macOS Native Cocoa/WebKit Wrapper + Menubar StatusItem & Popover
├── build_app.sh          # Swift'i derleyip .app paketini oluşturan betik
├── version.json          # Sürüm kontrol ve otomatik güncelleme bildirim dosyası (v1.4.0)
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
