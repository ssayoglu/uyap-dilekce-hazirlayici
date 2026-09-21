# ⚖️ UYAP Dilekçe & Şablon Yöneticisi (macOS)

Avukatlar ve hukuk büroları için geliştirilmiş; **Yapay Zekâ (Gemini 3.6 Flash)** ile doğal dilden mevzuata uygun adli dilekçe üreten, hukuki riskleri ve süreleri dilekçede ve UYAP'ta **kırmızı renkle** tespit eden, **milimetrik TabSet hizalı**, **başlık altı kesintisiz çizgili**, **Harca Esas Değer (H.E.D.)**, **Hukuki Deliller** ve **Hukuki Sebepler** standartlarına tam uyumlu yerel macOS UYAP UDF dilekçe oluşturucu ve yöneticisi.

---

## 🚀 Hızlı Kurulum (Tek Komutla Kurulum)

Terminal uygulamanızı açın (`Command + Space` basıp `Terminal` yazın), aşağıdaki komutu yapıştırıp `Enter` tuşuna basın:

```bash
curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/install.sh | bash
```

> **Kurulum tamamlandığında:**
> - `/Applications/Dilekçe Hazırlayıcı.app` yüklenir.
> - Masaüstünüze `Dilekçe Hazırlayıcı.app` kısayolu yerleştirilir.
> - Çift tıklayarak doğrudan kullanmaya başlayabilirsiniz!

---

## ✨ Öne Çıkan Özellikler

### 🤖 1. Yapay Zekâya Anlat, O Dilekçeyi Oluştursun (Gemini 3.6 Flash)
- **Doğal Dil ile Olay Girişi:** Olayı, şüpheli/müvekkil durumunu, delilleri ve talebinizi kendi serbest cümlelerinizle anlatın.
- **Tüm Hukuk Dallarına Uyum:**
  - **Ceza Hukuku:** Tutukluluk/adli kontrol itirazı, savunma, KYOK itirazı, alibi (mazeret) ve ölçülülük analizi.
  - **Hukuk Davaları:** Genel alacak, itirazın iptali, tazminat, tapu iptal, zorunlu arabuluculuk ve ihtiyati tedbir.
  - **İş Hukuku:** İşe iade, kıdem, ihbar, fazla mesai, 1 aylık arabuluculuk dava şartı.
  - **İcra & İflas:** İcra takibine itiraz, şikâyet, menfi tespit, %20 icra inkar tazminatı.
  - **Aile Hukuku:** Boşanma, nafaka, velayet, maddi/manevi tazminat ve delil hukuka uygunluk denetimi.
  - **Kira Hukuku:** Tahliye taahhüdü, ihtiyaç nedeniyle tahliye, kira tespiti ve arabuluculuk.
  - **İstinaf & Kanun Yolları:** Somut istinaf sebepleri, gerekçeli karar incelemesi.
- **⚠️ Kırmızı Hukuki Risk & Süre Bildirimleri:**
  - Zamanaşımı veya hak düşürücü süreler (CMK 268 7 günlük süre, işe iade 1 aylık süre vb.),
  - Delil silinme riskleri (iş yeri kamera kayıtları silinme periyodu ve ivedi müzekkere gereği),
  - Dava şartı eksiklikleri veya görev/yetki itirazları;
  dilekçenin bentleri içerisine `(DİKKAT / HUKUKİ RİSK: ...)` kalıbıyla eklenir.
  - **Hem Ekranda Hem UYAP'ta Kırmızı Metin:** UYAP XML standardında saf kırmızı Java rengi (`foreground="-65536"`) ve kalın (`bold="true"`) olarak işlenir; UYAP Doküman Editörü'nde doğrudan **kırmızı fontla** açılır!

### 🏛️ 2. Evrensel Tutukluluk ve Tahliye İtiraz Şablonu
- Emsal ceza itirazları taranarak 8 temel hukuki bent (İstikrarlı savunma, CMK 100 somut delil yokluğu, kaçma şüphesi yokluğu, delil karartma imkansızlığı, katalog suçlarda dahi somutlaştırma zorunluluğu, ölçülülük/ultima ratio, adli kontrol önceliği ve AİHS m. 5/AYM içtihatları) ile evrenselleştirildi.

### ⚡ 3. macOS Menü Çubuğu (Menubar ⚖️) Hızlı Mazeret Modülü
- Duruşma mazeretlerini menü çubuğundan 3 saniyede UYAP uyumlu UDF olarak üretme ve doğrudan editörde açma.

### 💰 4. Canlı Harç, Masraf & AAÜT Vekâlet Ücreti Hesaplayıcı
- Dava değeri girildiği anda Peşin Harç (1/4), Başvuru Harcı, İcra İnkâr Tazminatı (%20) ve Kademeli AAÜT vekâlet ücreti otomatik hesaplanır.

### 👥 5. Yerel Müvekkil Rehberi (CRM)
- Sık çalışılan müvekkillerin T.C., unvan ve adreslerini tarayıcı hafızasında saklayıp tek tıkla forma aktarma.

### 📐 6. Milimetrik UYAP Dizgisi
- İki yana yaslı metinler, standart Times New Roman 12 punto, girintili paragraflar, UYAP yerel dinamik `1. 2. 3.` numaralandırma sistemi.

---

## 🔄 Güncelleme

Uygulamanızı iki kolay yoldan güncelleyebilirsiniz:

### 1. Uygulama İçinden (Tek Tıkla)
Uygulama açıkken üst menü çubuğundan **Dilekçe Hazırlayıcı** > **Güncellemeleri Denetle** (Kısayol: `⌘ + U`) seçeneğine tıklamanız yeterlidir. Yeni bir sürüm varsa uygulama arka planda güncellemeyi alıp yenilenecektir.

### 2. Terminal Üzerinden (Tek Komutla)
Terminal uygulamasında aşağıdaki komutu çalıştırarak en son sürüme anında yükseltebilirsiniz:

```bash
curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/update.sh | bash
```

---

## 🗑️ Kaldırma (Tek Komut)

Uygulamayı ve tüm ilişkili dosyaları Mac'inizden tamamen kaldırmak için:

```bash
curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/uninstall.sh | bash
```

---

## 📋 Sürüm Geçmişi (Changelog)

### 🚀 Sürüm 1.5.0 (2026-09-19)
- ✨ **Yapay Zekâ Destekli Dilekçe Oluşturucu:** Gemini 3.6 Flash entegrasyonu; serbest olay anlatımından Türk mevzuatına tam uyumlu UYAP dilekçesi üretimi.
- ⚠️ **Kırmızı Hukuki Risk & Süre Tespiti:** Tespit edilen süre, delil veya usul risklerinin dilekçede ve UYAP çıktısında kırmızı renkle gösterilmesi.
- 🎯 **Dilekçe Türü & Mahkeme Seçici:** Kullanıcının seçtiği veya otomatik algılanan hukuk dalına (Ceza, Hukuk, İcra, İş, Aile, Ticaret, İdare vb.) göre özelleştirilmiş hukuki tahlil.
- 🏛️ **Evrensel Tutukluluk İtiraz Şablonu:** 8 temel hukuki bent ve kademeli netice-i talep ile standardize edilen ceza şablonu.

### 🚀 Sürüm 1.4.0 (2026-08-23)
- ⚡ Menü Çubuğu (Menubar) Hızlı Mazeret Modülü.
- 🔢 Dinamik UYAP Sıralı Liste aracı entegrasyonu.
- 💰 Canlı Harç, Masraf ve Kademeli AAÜT hesaplayıcı.
- 👥 Yerel Müvekkil Rehberi (CRM).

---

## ⚖️ Lisans ve Geliştirici

- **Geliştirici:** Av. Lütfi Serkan SAYOĞLU
- **Lisans:** MIT

