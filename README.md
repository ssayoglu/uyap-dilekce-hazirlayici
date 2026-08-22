# ⚖️ UYAP Dilekçe & Şablon Yöneticisi (macOS)

Avukatlar ve hukuk büroları için özel olarak geliştirilmiş; **milimetrik TabSet hizalı**, **başlık altı kesintisiz çizgili**, **Harca Esas Değer (H.E.D.)**, **Hukuki Deliller** ve **Hukuki Sebepler** standartlarına tam uyumlu yerel macOS UYAP UDF dilekçe oluşturucu ve yöneticisi.

---

## 📋 Güncelleme Notları (Changelog)

### 🚀 Sürüm 1.3.0 (2026-08-22)
- 🏛️ **Yeni Kategori ve Alt Kategori Mimarisi:**
  - **Hukuk Mahkemeleri:** Asliye Hukuk, Sulh Hukuk, İcra Hukuk.
  - **Özel Dava Türleri:** Alacak & Maddi Tazminat, İş Mahkemesi, Boşanma/Aile, Tüketici ve Tapu İptal davaları özel kategoride toplandı.
  - **Ceza & Savcılık:** Asliye Ceza, Ağır Ceza, İcra Ceza, Cumhuriyet Başsavcılığı (Soruşturma).
- 🔍 **Akıllı Genel Arama:** Arama kutusuna örneğin `Savunma` yazıldığında *Asliye Ceza Savunma*, *Ağır Ceza Savunma*, *İcra Ceza Savunma* ve *Savcılık Savunma* dilekçeleri anında tüm kategorilerden listelenir.
- ⚖️ **İstinaf Başlık Uyarlamaları:** Hukuk dosyalarında `İlgili Hukuk Dairesine`, Ceza dosyalarında `İlgili Ceza Dairesine` gönderim başlıkları standartlaştırıldı.
- 🏙️ **Dinamik Şehir & BAM Yönetimi:** Ayarlar panelinden seçilen yerel şehir *(Örn: Mersin)* ve bağlı Bölge Adliye Mahkemesi şehri *(Örn: Adana)* tüm şablonlara otomatik yansıtılır.
- 📑 **Avukatlık Yetki Belgesi:** 1136 sayılı Kanun m. 56'ya tam uyumlu 4 bölümlü resmi Yetki Belgesi şablonu eklendi.
- 📏 **Tipografi ve Satır Aralığı:** `KONU` ve tüm başlık satır aralıkları standart 1.0 (tek satır) olarak eşitlendi.
- 🧹 **Temiz Arayüz:** Gereksiz talep başlıkları temizlendi; sadece ihtiyati tedbir, tehir-i icra, tahliye vb. ivedi talepler korundu.

---

## ✨ Temel Özellikler

- ⚡️ **Çift Modlu Kullanım:**
  - **`⚡️ Doğrudan Aç`**: Form doldurmadan şablonu anında UYAP Doküman Editörü'nde açar.
  - **`✏️ Formla Düzenle`**: Müvekkil, mahkeme ve dosya bilgilerini tek ekrandan girerek milimetrik hizalı UDF üretir.
- ⭐ **Sık Kullanılanlar Çubuğu:** En çok kullandığınız şablonları üstte tutar, dilediğiniz şablonu yıldızlayabilirsiniz.
- 👤 **Dinamik Avukat ve Şehir Profili:** Avukat adı, UETS bilgisi, yerel il ve bağlı BAM şehri tek ekrandan değiştirilir; tüm dilekçelerde ve imza bloklarında otomatik olarak güncellenir.
- 📐 **Mükemmel UDF Tipografisi:**
  - Başlıktan iki noktaya (`:`) kadar uzanan kesintisiz alt çizgi (`DAVACI ____________ :`).
  - Konu (`KONU`) paragrafında tam **1.0 satır aralığı**.
  - İki yana yaslı metinler, standart Times New Roman 12 punto ve girintili paragraflar.
- 🔄 **Sessiz Otomatik Güncelleme:** Uygulama her açıldığında arka planda GitHub üzerinden güncelleme kontrolü yapar.

---

## 🚀 Hızlı Kurulum (Tek Komut)

Terminal uygulamanızı açın ve aşağıdaki komutu yapıştırıp `Enter` tuşuna basın:

```bash
curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/install.sh | bash
```

> **Kurulum tamamlandığında:**
> - `/Applications/Dilekçe Hazırlayıcı.app` yüklenir.
> - Masaüstünüze `Dilekçe Hazırlayıcı.app` yerleştirilir. Tüm şablonlar ve UDF oluşturma işlemleri doğrudan uygulama içerisinden yönetilir.

---

## 🔄 Güncelleme

Uygulama her açılışında güncellemeleri otomatik denetler. İsterseniz elle güncellemek için:

```bash
curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/update.sh | bash
```

---

## 🗑️ Kaldırma (Tek Komut)

Uygulamayı ve tüm ilişkili dosyaları sisteminizden tamamen kaldırmak için:

```bash
curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/uninstall.sh | bash
```

---

## ⚖️ Lisans ve Geliştirici

- **Geliştirici:** Av. Lütfi Serkan SAYOĞLU
- **Lisans:** MIT
