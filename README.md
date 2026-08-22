# ⚖️ UYAP Dilekçe & Şablon Yöneticisi (macOS)

Avukatlar ve hukuk büroları için özel olarak geliştirilmiş; **milimetrik TabSet hizalı**, **başlık altı kesintisiz çizgili**, **Harca Esas Değer (H.E.D.)**, **Hukuki Deliller** ve **Hukuki Sebepler** standartlarına tam uyumlu yerel macOS UYAP UDF dilekçe oluşturucu ve yöneticisi.

---

## ✨ Temel Özellikler

- ⚡️ **Çift Modlu Kullanım:**
  - **`⚡️ Doğrudan Aç`**: Form doldurmadan şablonu anında UYAP Doküman Editörü'nde açar.
  - **`✏️ Formla Düzenle`**: Müvekkil, mahkeme ve dosya bilgilerini tek ekrandan girerek milimetrik hizalı UDF üretir.
- ⭐ **Sık Kullanılanlar Çubuğu:** En çok kullandığınız şablonları üstte tutar, dilediğiniz şablonu yıldızlayabilirsiniz.
- 👤 **Dinamik Avukat Profili:** Avukat adı ve UETS/iletişim bilgisi tek tıkla değiştirilir; tüm dilekçelerde ve imza bloklarında otomatik olarak güncellenir.
- 📐 **Mükemmel UDF Tipografisi:**
  - Başlıktan iki noktaya (`:`) kadar uzanan kesintisiz alt çizgi (`DAVACI ____________ :`).
  - Konu (`KONU`) paragrafında tam **1.0 satır aralığı**.
  - İki yana yaslı metinler, standart Times New Roman 12 punto ve girintili paragraflar.
- 📊 **Güncel Mevzuat Şablonları:**
  - `HMK m. 109/4` Talep Artırım Dilekçesi *(Islah hakkını tüketmeyen özel format)*
  - `HMK m. 176` Islah Dilekçesi
  - `HMK m. 127` Süre Uzatım (Mehil) Talebi
  - Delil Bildirme, Tanık Bildirme, Boşanma, Kira Tahliye/Tespit, İtirazın İptali, İcra Şikayet, Suç Duyurusu, KYOK İtiraz, Tutukluluk İtiraz ve onlarca şablon.
- 🔄 **Sessiz Otomatik Güncelleme:** Uygulama her açıldığında arka planda GitHub üzerinden güncelleme kontrolü yapar. İnternet bağlantısı yoksa bekleme yapmadan sessizce atlar.

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

## 🛠️ Manuel Derleme ve Geliştirme

```bash
# Projeyi klonlayın
git clone https://github.com/ssayoglu/uyap-dilekce-hazirlayici.git
cd uyap-dilekce-hazirlayici

# Uygulamayı derleyin
./build_app.sh

# Çalıştırın
open "Dilekçe Hazırlayıcı.app"
```

---

## ⚖️ Lisans ve Geliştirici

- **Geliştirici:** Av. Lütfi Serkan SAYOĞLU
- **Lisans:** MIT
