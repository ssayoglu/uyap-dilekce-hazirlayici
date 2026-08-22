import zipfile, os
from datetime import datetime

OUTPUT_DIR = "/Users/serkan/Desktop/Dilekçe Şablonları"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_udf(paragraphs, output_file):
    full_text = ""
    elements_xml = []
    current_offset = 0
    
    for align, lspacing, sbelow, findent, tabset, runs in paragraphs:
        p_attr = []
        if align is not None: p_attr.append(f'Alignment="{align}"')
        if lspacing is not None: p_attr.append(f'LineSpacing="{lspacing}"')
        if sbelow is not None: p_attr.append(f'SpaceBelow="{sbelow}"')
        if findent is not None: p_attr.append(f'FirstLineIndent="{findent}"')
        if tabset is not None: p_attr.append(f'TabSet="{tabset}"')
        
        attr_str = " ".join(p_attr)
        p_xml = f"<paragraph {attr_str}>" if attr_str else "<paragraph>"
        
        for text, bold, italic, underline in runs:
            length = len(text)
            c_attr = ['resolver="hvl-default"']
            if bold: c_attr.append('bold="true"')
            if italic: c_attr.append('italic="true"')
            if underline: c_attr.append('underline="true"')
            c_attr.append(f'startOffset="{current_offset}"')
            c_attr.append(f'length="{length}"')
            
            c_str = " ".join(c_attr)
            p_xml += f"<content {c_str} />"
            full_text += text
            current_offset += length
            
        p_xml += "</paragraph>\n"
        elements_xml.append(p_xml)
        
    template_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<template format_id="1.8">
  <content><![CDATA[{full_text}]]></content>
  <properties><pageFormat mediaSizeName="1" leftMargin="70.8661413192749" rightMargin="42.51968479156494" topMargin="42.51968479156494" bottomMargin="42.51968479156494" paperOrientation="1" headerFOffset="14.17322826385498" footerFOffset="19.84251956939697" /></properties>
  <elements resolver="hvl-default">
{''.join(elements_xml)}  </elements>
  <styles><style name="default" description="Geçerli" family="Dialog" size="12" bold="false" italic="false" foreground="-13421773" FONT_ATTRIBUTE_KEY="javax.swing.plaf.FontUIResource[family=Dialog,name=Dialog,style=plain,size=12]" /><style name="hvl-default" family="Times New Roman" size="12" description="Gövde" /></styles>
  <data></data>
</template>"""

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("content.xml", template_xml.encode("utf-8"))

tab_setting = "130:0:0,145:0:0"
date_str = datetime.now().strftime("%d.%m.%Y")
vekil_info = "Av. Lütfi Serkan SAYOĞLU - UETS [16153-51280-36854]"

def make_template(filename, mahkeme, talep, dosya, m_sifat, m_ad, m_adres, k_sifat, k_ad, k_vekil, konu, aciklamalar, sonuc):
    p = []
    for line in mahkeme.split("\n"):
        if line.strip():
            p.append((1, 0, "8.5", None, None, [(f"{line.strip()}\n", True, False, False)]))
    p[-1] = (1, 0, "14.17", None, None, p[-1][5])
    
    if talep:
        p.append((2, 0, "14.17", None, None, [(f"{talep}\n", True, False, False)]))
        
    if dosya:
        dosya_lbl = "İCRA DOSYA NO" if ("İcra" in dosya or "İcra" in mahkeme) else "DOSYA NO"
        p.append((0, "0.5", "5.0", None, tab_setting, [
            (dosya_lbl, True, False, True),
            ("\t:\t", False, False, False),
            (f"{dosya}\n", False, False, False)
        ]))
        
    if m_sifat and m_ad:
        p.append((0, "0.5", "0.0" if m_adres else "5.0", None, tab_setting, [
            (m_sifat, True, False, True),
            ("\t:\t", False, False, False),
            (f"{m_ad}\n", True, False, False)
        ]))
        if m_adres:
            p.append((0, "0.5", "5.0", None, tab_setting, [
                ("", False, False, False),
                ("\t\t", False, False, False),
                (f"{m_adres}\n", False, True, False)
            ]))
            
    p.append((0, "0.5", "5.0", None, tab_setting, [
        ("VEKİLİ", True, False, True),
        ("\t:\t", False, False, False),
        (f"{vekil_info}\n", False, False, False)
    ]))
    
    if k_sifat and k_ad:
        p.append((0, "0.5", "0.0" if k_vekil else "5.0", None, tab_setting, [
            (k_sifat, True, False, True),
            ("\t:\t", False, False, False),
            (f"{k_ad}\n", False, False, False)
        ]))
        if k_vekil:
            p.append((0, "0.5", "5.0", None, tab_setting, [
                ("VEKİLİ", True, False, True),
                ("\t:\t", False, False, False),
                (f"{k_vekil}\n", False, False, False)
            ]))
            
    if konu:
        p.append((0, "0.5", "14.17", None, tab_setting, [
            ("KONU", True, False, True),
            ("\t:\t", False, False, False),
            (f"{konu}\n", False, False, False)
        ]))
        
    p.append((0, 0, "8.5", None, None, [
        ("AÇIKLAMALAR:", True, False, True),
        ("\n", False, False, False)
    ]))
    
    for line in aciklamalar:
        p.append((3, 0, "8.5", "35.43", None, [(f"{line}\n", False, False, False)]))
        
    p.append((0, 0, "8.5", None, None, [
        ("SONUÇ VE İSTEM:", True, False, True),
        ("\n", False, False, False)
    ]))
    
    p.append((3, 0, "14.17", "35.43", None, [
        (f"{sonuc} {date_str}\n", False, False, False)
    ]))
    
    unvan = f"{m_sifat.title()} Vekili" if m_sifat else "Vekil"
    p.append((2, 0, "0.0", None, None, [(f"{unvan}\n", True, False, False)]))
    p.append((2, 0, "0.0", None, None, [("Av. Lütfi Serkan SAYOĞLU\n", True, False, False)]))
    p.append((2, 0, "0.0", None, None, [("(e-imzalıdır)\n", False, True, False)]))
    
    out_file = os.path.join(OUTPUT_DIR, filename)
    build_udf(p, out_file)
    print(f"Created: {filename}")

# 1. İcra Şikayet
make_template(
    "01 - İcra Mahkemesi Şikayet Dilekçesi.udf",
    "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
    "İCRANIN DURDURULMASI TALEPLİDİR",
    "Mersin ... İcra Dairesi - 2026/... E.",
    "ŞİKAYET EDEN", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "Yapılan usulsüz tebligatın şikayeti ile takibin iptali ve durdurulması talebimizi içerir.",
    [
        "1- Mersin ... İcra Dairesi'nin 2026/... Esas sayılı dosyasında müvekkil aleyhine icra takibi başlatılmış ve ödeme emri düzenlenmiştir.",
        "2- Söz konusu ödeme emri müvekkilin MERNİS adresine usulüne uygun şekilde tebliğ edilmemiş olup, Tebligat Kanunu hükümlerine aykırı olarak usulsüz tebliğ edilmiştir. Müvekkil takipten ... tarihinde haricen haberdar olmuştur.",
        "3- Yasal süresi içinde usulsüz tebligatın iptalini ve takibin tedbiren durdurulmasını talep etme zorunluluğu hasıl olmuştur."
    ],
    "Yukarıda arz ve izah edilen nedenlerle; öncelikle icra takibinin TEDBİREN DURDURULMASINA, yapılan tebligatın USULSÜZ OLMASI NEDENİYLE İPTALİNE, öğrenme tarihinin tebliğ tarihi olarak kabulüne, yargılama giderleri ile vekâlet ücretinin karşı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 2. İcra İtiraz
make_template(
    "02 - İcra Takibine İtiraz Dilekçesi.udf",
    "MERSİN ... İCRA DAİRESİNE",
    "TAKİBİN DURDURULMASI TALEBİDİR",
    "2026/... Esas",
    "BORÇLU (İTİRAZ EDEN)", "[Müvekkil Borçlu Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "ALACAKLI", "[Alacaklı Adı Soyadı / Unvanı]", "[Alacaklı Vekili]",
    "Ödeme emrine, borca, faize, vekalet ücretine ve tüm fer'ilerine itirazlarımızın sunulmasıdır.",
    [
        "1- Alacaklı tarafından müvekkil aleyhine başlatılan ilamsız icra takibine ilişkin ödeme emri müvekkile ... tarihinde tebliğ edilmiştir.",
        "2- Müvekkilin alacaklı tarafa herhangi bir borcu bulunmamaktadır. Borcun tamamına, ana paraya, işletilen faize ve tüm ferilerine açıkça itiraz ediyoruz."
    ],
    "Yasal süresi içinde yaptığımız itirazlarımızın kabulü ile müvekkil aleyhine başlatılan icra takibinin DURDURULMASINA karar verilmesini vekâleten saygıyla talep ederiz."
)

# 3. Dava Dilekçesi
make_template(
    "03 - Hukuk Dava Dilekçesi (Davacı).udf",
    "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
    "İHTİYATİ TEDBİR TALEPLİDİR",
    "",
    "DAVACI", "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]", "[Davacı Müvekkil Adresi]",
    "DAVALI", "[Davalı Adı Soyadı / Unvanı - T.C. / Vergi No]", "[Varsa Davalı Vekili]",
    "[Dava konusunun ve talebin açık, kısa özeti]",
    [
        "1- [Müvekkil ile davalı taraf arasındaki uyuşmazlığın kronolojik özeti ve temel vakıalar]",
        "2- [Müvekkilin haklılığını ve alacağını/talebini ispatlayan maddi deliller ve hukuki dayanaklar]",
        "3- [Davalının haksız tutumu ve dava açma zorunluluğunun doğması]"
    ],
    "Yukarıda açıklanan ve Sayın Mahkemenizce re'sen gözetilecek nedenlerle; DAVAMIZIN KABULÜNE, yargılama giderleri ve vekâlet ücretinin davalı tarafa yükletilmesine karar verilmesini saygıyla vekâleten arz ve talep ederiz."
)

# 4. Cevap Dilekçesi
make_template(
    "04 - Cevap Dilekçesi (Davalı).udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVALI", "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]", "[Davalı Müvekkil Adresi]",
    "DAVACI", "[Davacı Adı Soyadı / Unvanı]", "[Davacı Vekili]",
    "Dava dilekçesine karşı yasal süresi içinde usule ve esasa ilişkin cevaplarımızın sunulmasından ibarettir.",
    [
        "USULE İLİŞKİN İTİRAZLARIMIZ:\n1- [Yetki, görev, zamanaşımı ve dava şartı yokluğu itirazları]",
        "ESASA İLİŞKİN CEVAPLARIMIZ:\n2- Davacının dava dilekçesinde ileri sürdüğü iddialar gerçeği yansıtmamakta olup, hukuki dayanaktan yoksundur.\n3- [Olayın gerçek mahiyeti ve davacının haksızlığını gösteren açıklamalar]"
    ],
    "Yukarıda arz ve izah edilen nedenlerle; öncelikle USULE İLİŞKİN İTİRAZLARIMIZIN KABULÜ İLE DAVANIN USULDEN REDDİNE, Mahkemeniz aksi kanaatte ise HAKSIZ VE MESNETSİZ DAVANIN ESASTAN REDDİNE, yargılama giderleri ile vekâlet ücretinin davacı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 5. Cevaba Cevap
make_template(
    "05 - Cevaba Cevap (Replik) Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVACI", "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]", "[Davacı Adresi]",
    "DAVALI", "[Davalı Adı Soyadı / Unvanı]", "[Davalı Vekili]",
    "Davalının cevap dilekçesine karşı süresi içinde cevaba cevaplarımızın sunulmasıdır.",
    [
        "1- Davalının cevap dilekçesinde ileri sürdüğü usuli ve esasa ilişkin itirazların tamamı yersiz olup reddi gerekmektedir.",
        "2- Davalı taraf borcun/edimin ifa edildiğini veya sorumluluğunun bulunmadığını yasal delillerle ispatlayamamıştır.",
        "3- Dava dilekçemizdeki haklı iddialarımızı yineliyor ve davalının mesnetsiz savunmalarını kabul etmiyoruz."
    ],
    "Yukarıda açıklanan ve re'sen nazara alınacak nedenlerle; davalının haksız cevap ve itirazlarının reddi ile DAVAMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 6. İkinci Cevap
make_template(
    "06 - İkinci Cevap (Düplik) Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVALI", "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]", "[Davalı Adresi]",
    "DAVACI", "[Davacı Adı Soyadı / Unvanı]", "[Davacı Vekili]",
    "Davacının cevaba cevap dilekçesine karşı ikinci cevaplarımızın (düplik) sunulmasıdır.",
    [
        "1- Davacının cevaba cevap dilekçesindeki soyut ve çelişkili iddiaları hukuki dayanaktan yoksundur.",
        "2- Müvekkilimizin sorumluluğu bulunmadığı tarafımızca sunulan delillerle teyit edilmiştir.",
        "3- İddia edilen vakıaların aksine davacı taraf edimlerini yerine getirmemiştir."
    ],
    "Yukarıda arz edilen nedenlerle; davanın reddi talebimizi yineler, haksız ve hukuki dayanaktan yoksun DAVANIN REDDİNE karar verilmesini vekâleten arz ve talep ederiz."
)

# 7. Tanık Bildirme
make_template(
    "07 - Tanık Bildirme Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVACI / DAVALI", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "Mahkemenizin ara kararı uyarınca tanık listemizin sunulmasıdır.",
    [
        "Mahkemenizin ... tarihli duruşmasında tarafımıza verilen kesin süre uyarınca, dava konusu vakıaları bizzat gören ve bilen tanıklarımızın isim ve adres bilgileri aşağıda sunulmuştur:",
        "TANIKLARIMIZ:\n1- [Tanık 1 Adı Soyadı - T.C. No] - [Adres Bilgisi] (Hangi konuda dinleneceği: ...)\n2- [Tanık 2 Adı Soyadı - T.C. No] - [Adres Bilgisi] (Hangi konuda dinleneceği: ...)"
    ],
    "Yukarıda isim ve adresleri bildirilen tanıklarımızın duruşma günü davetiye tebliği suretiyle dinlenilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 8. Delil Bildirme
make_template(
    "08 - Delil Bildirme Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVACI / DAVALI", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "Mahkemeniz ara kararı uyarınca delil listemizin ve delillerimizin sunulmasıdır.",
    [
        "Sayın Mahkemenizin ... tarihli ara kararı doğrultusunda, iddia ve savunmalarımızı ispatlayan delil listemiz aşağıdadır:",
        "DELİL LİSTEMİZ:\n1- [Delil 1: Sözleşme / Yazışmalar / Fatura vb.] (Ek-1)\n2- [Delil 2: Banka Dekontları / Kamera Kaydı vb.] (Ek-2)\n3- İlgili kurumlardan celbi talep edilen müzekkere cevapları\n4- Tanık, Bilirkişi incelemesi, Keşif, Yemin ve her türlü yasal delil."
    ],
    "Ekli delillerimizin dosya arasına alınmasına, celbi gereken deliller için ilgili kurumlara müzekkere yazılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 9. Mehil Talebi
make_template(
    "09 - Süre Uzatım (Mehil) Talep Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVALI / DAVACI", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "Dava dilekçesine / ara karara cevap süremizin HMK m. 127 uyarınca uzatılması talebidir.",
    [
        "1- Mahkemenizin yukarıda esas numarası yazılı dosyasında dava dilekçesi / tensip zaptı tarafımıza ... tarihinde tebliğ edilmiştir.",
        "2- Dava konusu uyuşmazlığın kapsamı, toplanması gereken belge ve kayıtların çokluğu ve henüz müvekkilden temin edilememiş olması nedeniyle yasal 2 haftalık süre içinde cevap dilekçesi sunmamız fiilen imkânsızdır.",
        "3- HMK m. 127 gereğince cevap süremizin uzatılmasını talep etme zorunluluğu doğmuştur."
    ],
    "Yukarıda açıklanan nedenlerle; cevap süremizin HMK 127. maddesi uyarınca ilk sürenin bitiminden itibaren BİR AY SÜREYLE UZATILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 10. İstinaf
make_template(
    "10 - İstinaf Başvuru Dilekçesi (Tehiri İcra).udf",
    "MERSİN BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\nGönderilmek Üzere\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "TEHİR-İ İCRA (İCRANIN GERİ BIRAKILMASI) TALEPLİDİR",
    "2026/... E. - 2026/... K.",
    "İSTİNAF EDEN (DAVALI)", "[İstinaf Eden Müvekkil - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF (DAVACI)", "[Davacı Karşı Taraf Adı Soyadı / Unvanı]", "[Davacı Vekili]",
    "Mersin .. Asliye Hukuk Mahkemesi'nin ... tarih ve ... E., ... K. sayılı haksız ve hukuka aykırı kararının istinafen incelenerek BOZULMASI ve KALDIRILMASI talebimizdir.",
    [
        "1- Yerel mahkemece eksik inceleme ve hatalı delil değerlendirmesi sonucunda usul ve yasaya aykırı karar verilmiştir.",
        "2- [Yerel mahkeme kararındaki somut maddi ve hukuki hata gerekçeleri]",
        "3- Karar usul ve esas yönünden hukuka aykırı olup istinaf incelemesiyle kaldırılması gerekmektedir."
    ],
    "Yukarıda arz ve izah edilen nedenlerle; istinaf başvurumuzun KABULÜ ile yerel mahkeme kararının KALDIRILMASINA ve davanın reddine, tehiri icra talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 11. Genel Talep
make_template(
    "11 - Genel Talep ve Beyan Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVACI / DAVALI", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "Mahkemeniz ara kararı doğrultusunda beyanlarımızın ve taleplerimizin sunulmasıdır.",
    [
        "1- Mahkemenizin ... tarihli duruşmasında kurulan ara karar uyarınca beyanda bulunmaktayız.",
        "2- [Konuya ilişkin somut açıklamalar ve talepler]",
        "3- Dosyadaki eksikliklerin giderilerek yargılamaya devam olunmasını talep ederiz."
    ],
    "Yukarıda arz edilen hususlar doğrultusunda işlem tesis edilmesini ve taleplerimizin kabulünü vekâleten saygıyla arz ve talep ederiz."
)

# 12. Suç Duyurusu
make_template(
    "12 - Müşteki Suç Duyurusu Dilekçesi.udf",
    "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
    "",
    "",
    "MÜŞTEKİ", "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müşteki Adresi]",
    "ŞÜPHELİ / ŞÜPHELİLER", "[Şüpheli Adı Soyadı / Kimliği Belirlenecek Şahıslar]", "",
    "Şüpheli/ler hakkında TCK m. ... (Suç Adı) uyarınca kamu davası açılması talepli suç duyurumuzdur.",
    [
        "SUÇ : [Örn: Dolandırıcılık, Tehdit, Hakaret vb.]\nSUÇ TARİHİ : .../.../2026",
        "1- Şüpheli şahıs ... tarihinde müvekkile karşı atılı suçu işlemiştir.",
        "2- Olayın gerçekleşme şekli, tanık beyanları ve ekteki delillerle sabittir.",
        "3- Şüphelinin cezalandırılması için hakkında kamu davası açılması zorunluluğu doğmuştur."
    ],
    "Yukarıda açıklanan ve resen tespit edilecek nedenlerle; şüpheli hakkında gerekli soruşturmanın yapılarak KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 13. KYOK İtiraz
make_template(
    "13 - KYOK (Takipsizlik) Kararına İtiraz.udf",
    "MERSİN NÖBETÇİ SULH CEZA HÂKİMLİĞİNE\nGönderilmek Üzere\nMERSİN CUMHURİYET BAŞSAVCILIĞINA",
    "",
    "Soruşturma No: 2026/... - Karar No: 2026/...",
    "İTİRAZ EDEN (MÜŞTEKİ)", "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müşteki Adresi]",
    "ŞÜPHELİ", "[Şüpheli Adı Soyadı]", "",
    "Mersin Cumhuriyet Başsavcılığı'nın ... tarihli Kovuşturmaya Yer Olmadığına Dair Kararına (KYOK) itirazlarımızın sunulmasıdır.",
    [
        "1- Başsavcılıkça dosya kapsamında toplanması gereken temel deliller toplanmadan, eksik soruşturma ile takipsizlik kararı verilmiştir.",
        "2- [Soruşturulmayan deliller, dinlenmeyen tanıklar ve somut delil durumu]",
        "3- CMK m. 172-173 uyarınca kamu davası açılması için yeterli şüphe mevcuttur."
    ],
    "Yukarıda açıklanan nedenlerle; Mersin Cumhuriyet Başsavcılığı'nın KYOK kararının KALDIRILMASINA ve şüpheli hakkında KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 14. Tutukluluğa İtiraz
make_template(
    "14 - Tutukluluğa İtiraz ve Tahliye Dilekçesi.udf",
    "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\nGönderilmek Üzere\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
    "TAHLİYE TALEPLİDİR",
    "Sorgu No: 2026/... Sorgu",
    "ŞÜPHELİ / SANIK", "[Müvekkil Şüpheli/Sanık - T.C. 12345678901]", "[Müvekkil Adresi / Cezaevi Bilgisi]",
    "MÜŞTEKİ", "[Müşteki Adı Soyadı]", "[Müşteki Vekili]",
    "Mersin .. Sulh Ceza Hâkimliği'nin ... tarihli tutuklama kararına itirazımız ve TAHLİYE talebimizdir.",
    [
        "1- Müvekkil hakkında verilen tutuklama kararı CMK 100 ve devamı maddelerine aykırıdır.",
        "2- Müvekkilin sabit ikametgah sahibi olması, delilleri karartma veya kaçma şüphesinin bulunmaması gözetilmemiştir.",
        "3- Tutuklama bir tedbirdir ve ölçülülük ilkesi gereği adli kontrol hükümleri uygulanmalıdır."
    ],
    "Yukarıda açıklanan nedenlerle; TUTUKLAMA KARARININ KALDIRILARAK MÜVEKKİLİN TAHLİYESİNE, Mahkemeniz aksi kanaatte ise adli kontrol hükümleri uygulanarak serbest bırakılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 15. Adli Kontrol İtiraz
make_template(
    "15 - Adli Kontrol Kararına İtiraz Dilekçesi.udf",
    "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\nGönderilmek Üzere\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
    "ADLİ KONTROLÜN KALDIRILMASI TALEPLİDİR",
    "2026/... Sorgu (veya Esas)",
    "ŞÜPHELİ / SANIK", "[Müvekkil Şüpheli/Sanık - T.C. 12345678901]", "[Müvekkil Adresi]",
    "MÜŞTEKİ", "[Müşteki Adı Soyadı]", "",
    "Müvekkil hakkında uygulanan adli kontrol tedbirinin (imza yükümlülüğü / yurtdışı çıkış yasağı vb.) kaldırılması talebimizdir.",
    [
        "1- Müvekkil hakkında tesis edilen adli kontrol kararı çalışma ve seyahat hürriyetini ölçüsüz biçimde kısıtlamaktadır.",
        "2- Müvekkil tüm adli kontrol tedbirlerine eksiksiz uymuş olup kaçma veya delil karartma şüphesi kalmamıştır.",
        "3- Tedbirin devamında hukuki yarar bulunmamaktadır."
    ],
    "Yukarıda açıklanan nedenlerle; müvekkil hakkındaki ADLİ KONTROL TEDBİRLERİNİN KALDIRILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 16. Ceza Savunma
make_template(
    "16 - Ceza Mahkemesi Savunma ve Beraat.udf",
    "MERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
    "BERAAT TALEPLİDİR",
    "2026/... Esas",
    "SANIK", "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]", "[Sanık Adresi]",
    "KATILAN / MÜŞTEKİ", "[Katılan/Müşteki Adı Soyadı]", "[Katılan Vekili]",
    "Esas hakkındaki mütalaaya karşı savunmalarımız ve BERAAT talebimizin sunulmasıdır.",
    [
        "1- İddianamede ve mütalaada isnat edilen fiillerin müvekkil tarafından işlendiğine dair somut, kesin ve inandırıcı hiçbir delil bulunmamaktadır.",
        "2- Suçun yasal ve manevi unsurları oluşmamış olup 'şüpheden sanık yararlanır' evrensel ilkesi geçerlidir.",
        "3- Müvekkilin atılı suçtan beraatine karar verilmesi gerekmektedir."
    ],
    "Yukarıda açıklanan gerekçelerle; müvekkil sanığın BERAATİNE, Mahkemeniz aksi kanaatte ise lehe olan yasal hükümlerin uygulanmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

print("All 16 templates successfully generated.")
