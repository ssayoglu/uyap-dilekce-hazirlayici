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

tab_setting = "140:0:0,155:0:0"
date_str = datetime.now().strftime("%d.%m.%Y")
vekil_info = "Av. Lütfi Serkan SAYOĞLU - UETS [16153-51280-36854]"

def make_template(filename, mahkeme, talep, dosya, m_sifat, m_ad, m_adres, k_sifat, k_ad, k_vekil, hed, konu, aciklamalar, hukuki_sebepler, hukuki_deliller, sonuc):
    p = []
    # Mahkeme
    for line in mahkeme.split("\n"):
        if line.strip():
            p.append((1, 0, "8.5", None, None, [(f"{line.strip()}\n", True, False, False)]))
    p[-1] = (1, 0, "14.17", None, None, p[-1][5])
    
    # Talep
    if talep:
        p.append((2, 0, "14.17", None, None, [(f"{talep}\n", True, False, False)]))
        
    # Dosya
    if dosya:
        dosya_lbl = "İCRA DOSYA NO" if ("İcra" in dosya or "İcra" in mahkeme) else "DOSYA NO"
        p.append((0, "0.5", "5.0", None, tab_setting, [
            (dosya_lbl, True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{dosya}\n", False, False, False)
        ]))
        
    # Müvekkil
    if m_sifat and m_ad:
        p.append((0, "0.5", "0.0" if m_adres else "5.0", None, tab_setting, [
            (m_sifat, True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{m_ad}\n", True, False, False)
        ]))
        if m_adres:
            p.append((0, "0.5", "5.0", None, tab_setting, [
                ("", False, False, False),
                ("\t\t", False, False, False),
                (f"{m_adres}\n", False, True, False)
            ]))
            
    # Vekili
    p.append((0, "0.5", "5.0", None, tab_setting, [
        ("VEKİLİ", True, False, True),
        ("\t", False, False, True),
        (":\t", False, False, False),
        (f"{vekil_info}\n", False, False, False)
    ]))
    
    # Karşı Taraf
    if k_sifat and k_ad:
        p.append((0, "0.5", "0.0" if k_vekil else "5.0", None, tab_setting, [
            (k_sifat, True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{k_ad}\n", False, False, False)
        ]))
        if k_vekil:
            p.append((0, "0.5", "5.0", None, tab_setting, [
                ("VEKİLİ", True, False, True),
                ("\t", False, False, True),
                (":\t", False, False, False),
                (f"{k_vekil}\n", False, False, False)
            ]))
            
    # Harca Esas Değer
    if hed:
        p.append((0, "0.5", "5.0", None, tab_setting, [
            ("DAVA DEĞERİ (H.E.D.)", True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{hed}\n", False, False, False)
        ]))
        
    # KONU - Satır Aralığı 1.0 & Altı çizili sekme
    if konu:
        p.append((0, "1.0", "14.17", None, tab_setting, [
            ("KONU", True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{konu}\n", False, False, False)
        ]))
        
    # Açıklamalar Başlığı
    p.append((0, 0, "8.5", None, None, [
        ("AÇIKLAMALAR:", True, False, True),
        ("\n", False, False, False)
    ]))
    
    # Açıklamalar
    for line in aciklamalar:
        p.append((3, 0, "8.5", "35.43", None, [(f"{line}\n", False, False, False)]))
        
    # Hukuki Sebepler
    if hukuki_sebepler:
        p.append((0, "0.5", "5.0", None, tab_setting, [
            ("HUKUKİ SEBEPLER", True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{hukuki_sebepler}\n", False, False, False)
        ]))
        
    # Hukuki Deliller
    if hukuki_deliller:
        p.append((0, "0.5", "14.17", None, tab_setting, [
            ("HUKUKİ DELİLLER", True, False, True),
            ("\t", False, False, True),
            (":\t", False, False, False),
            (f"{hukuki_deliller}\n", False, False, False)
        ]))
        
    # Sonuç Başlığı
    p.append((0, 0, "8.5", None, None, [
        ("SONUÇ VE İSTEM:", True, False, True),
        ("\n", False, False, False)
    ]))
    
    # Sonuç Metni
    p.append((3, 0, "14.17", "35.43", None, [
        (f"{sonuc} {date_str}\n", False, False, False)
    ]))
    
    # İmza
    unvan = f"{m_sifat.title()} Vekili" if m_sifat else "Vekil"
    p.append((2, 0, "0.0", None, None, [(f"{unvan}\n", True, False, False)]))
    p.append((2, 0, "0.0", None, None, [("Av. Lütfi Serkan SAYOĞLU\n", True, False, False)]))
    p.append((2, 0, "0.0", None, None, [("(e-imzalıdır)\n", False, True, False)]))
    
    out_file = os.path.join(OUTPUT_DIR, filename)
    build_udf(p, out_file)
    print(f"Rebuilt with continuous underline: {filename}")

deliller_std = "Sözleşmeler, faturalar, banka kayıtları, ticari defterler, tanık, bilirkişi, yemin ve sair hukuki deliller."
sebepler_std = "HMK, TBK, TTK, TMK, İİK ve ilgili mevzuat."

# 1. İcra Şikayet
make_template(
    "01 - İcra Mahkemesi Şikayet Dilekçesi.udf",
    "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
    "İCRANIN DURDURULMASI TALEPLİDİR",
    "Mersin ... İcra Dairesi - 2026/... E.",
    "ŞİKAYET EDEN", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "",
    "Yapılan usulsüz tebligatın şikayeti ile takibin iptali ve durdurulması talebimizi içerir.",
    [
        "1- Mersin ... İcra Dairesi'nin 2026/... Esas sayılı dosyasında müvekkil aleyhine icra takibi başlatılmış ve ödeme emri düzenlenmiştir.",
        "2- Söz konusu ödeme emri müvekkilin MERNİS adresine usulüne uygun şekilde tebliğ edilmemiş olup, Tebligat Kanunu hükümlerine aykırı olarak usulsüz tebliğ edilmiştir. Müvekkil takipten ... tarihinde haricen haberdar olmuştur.",
        "3- Yasal süresi içinde usulsüz tebligatın iptalini ve takibin tedbiren durdurulmasını talep etme zorunluluğu hasıl olmuştur."
    ],
    "İİK m. 16, Tebligat Kanunu m. 10, 21, 32 ve ilgili mevzuat.",
    "İcra takip dosyası, tebligat mazbatası, tanık, bilirkişi, yemin ve sair hukuki deliller.",
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
    "",
    "Ödeme emrine, borca, faize, vekalet ücretine ve tüm fer'ilerine itirazlarımızın sunulmasıdır.",
    [
        "1- Alacaklı tarafından müvekkil aleyhine başlatılan ilamsız icra takibine ilişkin ödeme emri müvekkile ... tarihinde tebliğ edilmiştir.",
        "2- Müvekkilin alacaklı tarafa herhangi bir borcu bulunmamaktadır. Borcun tamamına, ana paraya, işletilen faize ve tüm ferilerine açıkça itiraz ediyoruz."
    ],
    "İİK m. 62 vd. ve ilgili mevzuat.",
    "Ödeme belgeleri, banka dekontları ve dosya kapsamı.",
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
    "10.000,00 TL (Fazlaya ilişkin haklarımız saklı kalmak kaydıyla)",
    "Müvekkilin ödenmeyen alacağının ve ticari/maddi tazminatın faiziyle birlikte tahsili talebidir.",
    [
        "1- [Müvekkil ile davalı taraf arasındaki uyuşmazlığın kronolojik özeti ve temel vakıalar]",
        "2- [Müvekkilin haklılığını ve alacağını/talebini ispatlayan maddi deliller ve hukuki dayanaklar]",
        "3- [Davalının haksız tutumu ve dava açma zorunluluğunun doğması]"
    ],
    sebepler_std,
    deliller_std,
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
    "",
    "Dava dilekçesine karşı yasal süresi içinde usule ve esasa ilişkin cevaplarımızın sunulmasından ibarettir.",
    [
        "USULE İLİŞKİN İTİRAZLARIMIZ:\n1- [Yetki, görev, zamanaşımı ve dava şartı yokluğu itirazları]",
        "ESASA İLİŞKİN CEVAPLARIMIZ:\n2- Davacının dava dilekçesinde ileri sürdüğü iddialar gerçeği yansıtmamakta olup, hukuki dayanaktan yoksundur.\n3- [Olayın gerçek mahiyeti ve davacının haksızlığını gösteren açıklamalar]"
    ],
    sebepler_std,
    deliller_std,
    "Yukarıda arz ve izah edilen nedenlerle; öncelikle USULE İLİŞKİN İTİRAZLARIMIZIN KABULÜ İLE DAVANIN USULDEN REDDİNE, Mahkemeniz aksi kanaatte ise HAKSIZ VE MESNETSİZ DAVANIN ESASTAN REDDİNE, yargılama giderleri ile vekâlet ücretinin davacı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 5. Delil Bildirme
make_template(
    "08 - Delil Bildirme Dilekçesi.udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "",
    "2026/... Esas",
    "DAVACI / DAVALI", "[Müvekkil Adı Soyadı - T.C. 12345678901]", "[Müvekkil Adresi]",
    "KARŞI TARAF", "[Karşı Taraf Adı Soyadı / Unvanı]", "[Varsa Karşı Taraf Vekili]",
    "",
    "Mahkemeniz ara kararı uyarınca delil listemizin ve delillerimizin sunulmasıdır.",
    [
        "Sayın Mahkemenizin ara kararı doğrultusunda, iddia ve savunmalarımızı ispatlayan delil listemiz aşağıdadır:",
        "DELİL LİSTEMİZ:\n1- [Delil 1: Sözleşme / Yazışmalar / Fatura vb.] (Ek-1)\n2- [Delil 2: Banka Dekontları / Kamera Kaydı vb.] (Ek-2)\n3- İlgili kurumlardan celbi talep edilen müzekkere cevapları\n4- Tanık, Bilirkişi incelemesi, Keşif, Yemin ve her türlü yasal delil."
    ],
    "HMK m. 199 vd. ve ilgili mevzuat.",
    deliller_std,
    "Ekli delillerimizin dosya arasına alınmasına, celbi gereken deliller için ilgili kurumlara müzekkere yazılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

# 6. Talep Artırım
make_template(
    "17 - Talep Artırım Dilekçesi (HMK 109-4).udf",
    "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
    "HMK m. 109/4 GEREĞİNCE TALEP ARTIRIMI VE TAMAMLAMA HARCI TALEBİDİR (ISLAH DEĞİLDİR)",
    "2026/... Esas",
    "DAVACI", "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]", "[Davacı Adresi]",
    "DAVALI", "[Davalı Adı Soyadı / Unvanı]", "[Davalı Vekili]",
    "[... TL Artırılan Miktar / Toplam: ... TL]",
    "Bilirkişi raporu doğrultusunda belirlenen alacak miktarımız uyarınca HMK m. 109/4 gereğince TALEP ARTIRIM DİLEKÇEMİZİN ve tamamlama harcımızın sunulmasıdır.",
    [
        "1- Mahkemeniz dosyasına sunulan ... tarihli bilirkişi raporu ile dava konusu alacağımızın tam ve kesin miktarı tespit edilmiştir.",
        "2- Dava dilekçemizde fazlaya ilişkin haklarımız saklı tutularak açılan kısmi davada talep sonucumuz, HMK m. 109/4 hükmü uyarınca (ISLAH HAKKIMIZ SAKLI KALMAK KAYDIYLA) artırılmaktadır.",
        "3- Bu kapsamda dava değerimiz ... TL artırılarak toplam ... TL'ye yükseltilmiş olup, tamamlama harcı mahkeme veznesine yatırılmıştır.",
        "4- İşbu dilekçemiz HMK m. 109/4 kapsamında talep artırım dilekçesi mahiyetinde olup, ıslah niteliğinde değildir."
    ],
    "HMK m. 109/4, Harçlar Kanunu, TBK ve ilgili mevzuat.",
    deliller_std,
    "Yukarıda açıklanan nedenlerle; HMK m. 109/4 uyarınca TALEP ARTIRIM DİLEKÇEMİZİN KABULÜ ile toplam ... TL alacağımızın dava/temerrüt tarihinden itibaren işleyecek faiziyle birlikte davalıdan tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
)

print("All UDFs rebuilt with continuous underline to colon.")
