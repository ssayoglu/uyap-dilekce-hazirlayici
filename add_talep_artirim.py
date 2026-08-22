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

p = [
    (1, 0, "14.17", None, None, [("MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE\n", True, False, False)]),
    (2, 0, "14.17", None, None, [("TALEP ARTIRIMI VE TAMAMLAMA HARCI TALEBİDİR (ISLAH DEĞİLDİR)\n", True, False, False)]),
    (0, "0.5", "5.0", None, tab_setting, [
        ("DOSYA NO", True, False, True),
        ("\t:\t", False, False, False),
        ("2026/... Esas\n", False, False, False)
    ]),
    (0, "0.5", "0.0", None, tab_setting, [
        ("DAVACI", True, False, True),
        ("\t:\t", False, False, False),
        ("[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]\n", True, False, False)
    ]),
    (0, "0.5", "5.0", None, tab_setting, [
        ("", False, False, False),
        ("\t\t", False, False, False),
        ("[Davacı Adresi]\n", False, True, False)
    ]),
    (0, "0.5", "5.0", None, tab_setting, [
        ("VEKİLİ", True, False, True),
        ("\t:\t", False, False, False),
        (f"{vekil_info}\n", False, False, False)
    ]),
    (0, "0.5", "0.0", None, tab_setting, [
        ("DAVALI", True, False, True),
        ("\t:\t", False, False, False),
        ("[Davalı Adı Soyadı / Unvanı]\n", False, False, False)
    ]),
    (0, "0.5", "5.0", None, tab_setting, [
        ("VEKİLİ", True, False, True),
        ("\t:\t", False, False, False),
        ("[Davalı Vekili]\n", False, False, False)
    ]),
    (0, "0.5", "5.0", None, tab_setting, [
        ("DAVA DEĞERİ (H.E.D.)", True, False, True),
        ("\t:\t", False, False, False),
        ("[... TL Artırılan Miktar / Toplam: ... TL]\n", False, False, False)
    ]),
    (0, "0.5", "14.17", None, tab_setting, [
        ("KONU", True, False, True),
        ("\t:\t", False, False, False),
        ("Bilirkişi raporu doğrultusunda belirlenen alacak miktarımız uyarınca HMK m. 107/2 gereğince TALEP ARTIRIM DİLEKÇEMİZİN ve tamamlama harcımızın sunulmasıdır.\n", False, False, False)
    ]),
    (0, 0, "8.5", None, None, [
        ("AÇIKLAMALAR:", True, False, True),
        ("\n", False, False, False)
    ]),
    (3, 0, "8.5", "35.43", None, [
        ("1- Mahkemeniz dosyasına sunulan ... tarihli bilirkişi raporu ile dava konusu alacağımızın tam ve kesin miktarı tespit edilmiştir.\n", False, False, False)
    ]),
    (3, 0, "8.5", "35.43", None, [
        ("2- Dava dilekçemizde fazlaya ilişkin haklarımız saklı tutularak gösterilen geçici/kısmi talep sonucumuz, HMK m. 107/2 hükmü uyarınca (ISLAH HAKKIMIZ SAKLI KALMAK KAYDIYLA) artırılmaktadır.\n", False, False, False)
    ]),
    (3, 0, "8.5", "35.43", None, [
        ("3- Bu kapsamda dava değerimiz ... TL artırılarak toplam ... TL'ye yükseltilmiş olup, tamamlama harcı mahkeme veznesine yatırılmıştır.\n", False, False, False)
    ]),
    (3, 0, "8.5", "35.43", None, [
        ("4- İşbu dilekçemiz HMK m. 107 kapsamında talep artırım dilekçesi mahiyetinde olup, ıslah niteliğinde değildir.\n", False, False, False)
    ]),
    (0, "0.5", "5.0", None, tab_setting, [
        ("HUKUKİ SEBEPLER", True, False, True),
        ("\t:\t", False, False, False),
        ("HMK m. 107/2, Harçlar Kanunu, TBK ve ilgili mevzuat.\n", False, False, False)
    ]),
    (0, "0.5", "14.17", None, tab_setting, [
        ("HUKUKİ DELİLLER", True, False, True),
        ("\t:\t", False, False, False),
        ("Bilirkişi raporu, harç tamamlama makbuzu, tanık, bilirkişi, yemin ve sair hukuki deliller.\n", False, False, False)
    ]),
    (0, 0, "8.5", None, None, [
        ("SONUÇ VE İSTEM:", True, False, True),
        ("\n", False, False, False)
    ]),
    (3, 0, "14.17", "35.43", None, [
        (f"Yukarıda açıklanan nedenlerle; TALEP ARTIRIM DİLEKÇEMİZİN KABULÜ ile toplam ... TL alacağımızın dava/temerrüt tarihinden itibaren işleyecek faiziyle birlikte davalıdan tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz. {date_str}\n", False, False, False)
    ]),
    (2, 0, "0.0", None, None, [("Davacı Vekili\n", True, False, False)]),
    (2, 0, "0.0", None, None, [("Av. Lütfi Serkan SAYOĞLU\n", True, False, False)]),
    (2, 0, "0.0", None, None, [("(e-imzalıdır)\n", False, True, False)])
]

build_udf(p, os.path.join(OUTPUT_DIR, "17 - Talep Artırım Dilekçesi (HMK 107).udf"))
print("Created: 17 - Talep Artırım Dilekçesi (HMK 107).udf")
