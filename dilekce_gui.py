#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import zipfile
import os
import subprocess
from datetime import datetime

# --- UDF BUILDER ENGINE ---
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


# --- ŞABLON VERİTABANI ---
TEMPLATES = {
    "📌 İcra Mahkemesi Şikayet Dilekçesi": {
        "mahkeme": "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
        "talep": "İCRANIN DURDURULMASI TALEPLİDİR",
        "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
        "m_sifat": "ŞİKAYET EDEN",
        "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "KARŞI TARAF",
        "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
        "k_vekil": "[Varsa Karşı Taraf Vekili]",
        "konu": "Yapılan usulsüz tebligatın şikayeti ile takibin iptali ve durdurulması talebimizi içerir.",
        "aciklama": "1- Mersin ... İcra Dairesi'nin 2026/... Esas sayılı dosyasında müvekkil aleyhine icra takibi başlatılmış ve ödeme emri düzenlenmiştir.\n2- Söz konusu ödeme emri müvekkilin MERNİS adresine usulüne uygun şekilde tebliğ edilmemiş olup, Tebligat Kanunu hükümlerine aykırı olarak usulsüz tebliğ edilmiştir. Müvekkil takipten ... tarihinde haricen haberdar olmuştur.\n3- Yasal süresi içinde usulsüz tebligatın iptalini ve takibin tedbiren durdurulmasını talep etme zorunluluğu hasıl olmuştur.",
        "sonuc": "Yukarıda arz ve izah edilen nedenlerle; öncelikle icra takibinin TEDBİREN DURDURULMASINA, yapılan tebligatın USULSÜZ OLMASI NEDENİYLE İPTALİNE, öğrenme tarihinin tebliğ tarihi olarak kabulüne, yargılama giderleri ile vekâlet ücretinin karşı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "📄 Hukuk Dava Dilekçesi (Davacı)": {
        "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
        "talep": "İHTİYATİ TEDBİR TALEPLİDİR",
        "dosya": "",
        "m_sifat": "DAVACI",
        "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Davacı Müvekkil Adresi]",
        "k_sifat": "DAVALI",
        "k_ad": "[Davalı Adı Soyadı / Unvanı - T.C. / Vergi No]",
        "k_vekil": "[Varsa Davalı Vekili]",
        "konu": "[Dava konusunun ve talebin açık, kısa özeti]",
        "aciklama": "1- [Müvekkil ile davalı taraf arasındaki uyuşmazlığın kronolojik özeti ve temel vakıalar]\n2- [Müvekkilin haklılığını ve alacağını/talebini ispatlayan maddi deliller ve hukuki dayanaklar]\n3- [Davalının haksız tutumu ve dava açma zorunluluğunun doğması]",
        "sonuc": "Yukarıda açıklanan ve Sayın Mahkemenizce re'sen gözetilecek nedenlerle; DAVAMIZIN KABULÜNE, [talep edilen hak/alacak/tedbir], yargılama giderleri ve vekâlet ücretinin davalı tarafa yükletilmesine karar verilmesini saygıyla vekâleten arz ve talep ederiz."
    },
    "💬 Cevap Dilekçesi (Davalı)": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVALI",
        "m_ad": "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Davalı Müvekkil Adresi]",
        "k_sifat": "DAVACI",
        "k_ad": "[Davacı Adı Soyadı / Unvanı]",
        "k_vekil": "[Davacı Vekili]",
        "konu": "Dava dilekçesine karşı yasal süresi içinde usule ve esasa ilişkin cevaplarımızın sunulmasından ibarettir.",
        "aciklama": "USULE İLİŞKİN İTİRAZLARIMIZ:\n1- [Yetki, görev, zamanaşımı ve dava şartı yokluğu itirazları]\n\nESASA İLİŞKİN CEVAPLARIMIZ:\n2- Davacının dava dilekçesinde ileri sürdüğü iddialar gerçeği yansıtmamakta olup, hukuki dayanaktan yoksundur.\n3- [Olayın gerçek mahiyeti ve davacının haksızlığını gösteren açıklamalar]",
        "sonuc": "Yukarıda arz ve izah edilen nedenlerle; öncelikle USULE İLİŞKİN İTİRAZLARIMIZIN KABULÜ İLE DAVANIN USULDEN REDDİNE, Mahkemeniz aksi kanaatte ise HAKSIZ VE MESNETSİZ DAVANIN ESASTAN REDDİNE, yargılama giderleri ile vekâlet ücretinin davacı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "📝 Cevaba Cevap (Replik) Dilekçesi (Davacı)": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVACI",
        "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Davacı Adresi]",
        "k_sifat": "DAVALI",
        "k_ad": "[Davalı Adı Soyadı / Unvanı]",
        "k_vekil": "[Davalı Vekili]",
        "konu": "Davalının cevap dilekçesine karşı süresi içinde cevaba cevaplarımızın sunulmasıdır.",
        "aciklama": "1- Davalının cevap dilekçesinde ileri sürdüğü usuli ve esasa ilişkin itirazların tamamı yersiz olup reddi gerekmektedir.\n2- Davalı taraf borcun/edimin ifa edildiğini veya sorumluluğunun bulunmadığını yasal delillerle ispatlayamamıştır.\n3- Dava dilekçemizdeki haklı iddialarımızı yineliyor ve davalının mesnetsiz savunmalarını kabul etmiyoruz.",
        "sonuc": "Yukarıda açıklanan ve re'sen nazara alınacak nedenlerle; davalının haksız cevap ve itirazlarının reddi ile DAVAMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "📑 İkinci Cevap (Düplik) Dilekçesi (Davalı)": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVALI",
        "m_ad": "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Davalı Adresi]",
        "k_sifat": "DAVACI",
        "k_ad": "[Davacı Adı Soyadı / Unvanı]",
        "k_vekil": "[Davacı Vekili]",
        "konu": "Davacının cevaba cevap dilekçesine karşı ikinci cevaplarımızın (düplik) sunulmasıdır.",
        "aciklama": "1- Davacının cevaba cevap dilekçesindeki soyut ve çelişkili iddiaları hukuki dayanaktan yoksundur.\n2- Müvekkilimizin sorumluluğu bulunmadığı tarafımızca sunulan delillerle teyit edilmiştir.\n3- İddia edilen vakıaların aksine davacı taraf edimlerini yerine getirmemiştir.",
        "sonuc": "Yukarıda arz edilen nedenlerle; davanın reddi talebimizi yineler, haksız ve hukuki dayanaktan yoksun DAVANIN REDDİNE karar verilmesini vekâleten arz ve talep ederiz."
    },
    "👥 Tanık Bildirme Dilekçesi": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVACI / DAVALI",
        "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "KARŞI TARAF",
        "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
        "k_vekil": "[Varsa Karşı Taraf Vekili]",
        "konu": "Mahkemenizin ara kararı uyarınca tanık listemizin sunulmasıdır.",
        "aciklama": "Mahkemenizin ... tarihli duruşmasında tarafımıza verilen kesin süre uyarınca, dava konusu vakıaları bizzat gören ve bilen tanıklarımızın isim ve adres bilgileri aşağıda sunulmuştur:\n\nTANIKLARIMIZ:\n1- [Tanık 1 Adı Soyadı - T.C. No] - [Adres Bilgisi] (Hangi konuda dinleneceği: ...)\n2- [Tanık 2 Adı Soyadı - T.C. No] - [Adres Bilgisi] (Hangi konuda dinleneceği: ...)",
        "sonuc": "Yukarıda isim ve adresleri bildirilen tanıklarımızın duruşma günü davetiye tebliği suretiyle dinlenilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "📁 Delil Bildirme Dilekçesi": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVACI / DAVALI",
        "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "KARŞI TARAF",
        "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
        "k_vekil": "[Varsa Karşı Taraf Vekili]",
        "konu": "Mahkemeniz ara kararı uyarınca delil listemizin ve delillerimizin sunulmasıdır.",
        "aciklama": "Sayın Mahkemenizin ... tarihli ara kararı doğrultusunda, iddia ve savunmalarımızı ispatlayan delil listemiz aşağıdadır:\n\nDELİL LİSTEMİZ:\n1- [Delil 1: Sözleşme / Yazışmalar / Fatura vb.] (Ek-1)\n2- [Delil 2: Banka Dekontları / Kamera Kaydı vb.] (Ek-2)\n3- İlgili kurumlardan celbi talep edilen müzekkere cevapları\n4- Tanık, Bilirkişi incelemesi, Keşif, Yemin ve her türlü yasal delil.",
        "sonuc": "Ekli delillerimizin dosya arasına alınmasına, celbi gereken deliller için ilgili kurumlara müzekkere yazılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "⏱️ Süre Uzatım (Mehil) Talep Dilekçesi": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVALI / DAVACI",
        "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "KARŞI TARAF",
        "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
        "k_vekil": "[Varsa Karşı Taraf Vekili]",
        "konu": "Dava dilekçesine / ara karara cevap süremizin HMK m. 127 uyarınca uzatılması talebidir.",
        "aciklama": "1- Mahkemenizin yukarıda esas numarası yazılı dosyasında dava dilekçesi / tensip zaptı tarafımıza ... tarihinde tebliğ edilmiştir.\n2- Dava konusu uyuşmazlığın kapsamı, toplanması gereken belge ve kayıtların çokluğu ve henüz müvekkilden temin edilememiş olması nedeniyle yasal 2 haftalık süre içinde cevap dilekçesi sunmamız fiilen imkânsızdır.\n3- HMK m. 127 gereğince cevap süremizin uzatılmasını talep etme zorunluluğu doğmuştur.",
        "sonuc": "Yukarıda açıklanan nedenlerle; cevap süremizin HMK 127. maddesi uyarınca ilk sürenin bitiminden itibaren BİR AY SÜREYLE UZATILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "📌 Genel Talep / Beyan Dilekçesi": {
        "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "",
        "dosya": "2026/... Esas",
        "m_sifat": "DAVACI / DAVALI",
        "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "KARŞI TARAF",
        "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
        "k_vekil": "[Varsa Karşı Taraf Vekili]",
        "konu": "Mahkemeniz ara kararı doğrultusunda beyanlarımızın ve taleplerimizin sunulmasıdır.",
        "aciklama": "1- Mahkemenizin ... tarihli duruşmasında kurulan ara karar uyarınca beyanda bulunmaktayız.\n2- [Konuya ilişkin somut açıklamalar ve talepler]\n3- Dosyadaki eksikliklerin giderilerek yargılamaya devam olunmasını talep ederiz.",
        "sonuc": "Yukarıda arz edilen hususlar doğrultusunda işlem tesis edilmesini ve taleplerimizin kabulünü vekâleten saygıyla arz ve talep ederiz."
    },
    "⚖️ İstinaf Başvuru Dilekçesi (Hukuk / Ceza)": {
        "mahkeme": "MERSİN BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\nGönderilmek Üzere\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
        "talep": "TEHİR-İ İCRA (İCRANIN GERİ BIRAKILMASI) TALEPLİDİR",
        "dosya": "2026/... E. - 2026/... K.",
        "m_sifat": "İSTİNAF EDEN (DAVALI)",
        "m_ad": "[İstinaf Eden Müvekkil - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "KARŞI TARAF (DAVACI)",
        "k_ad": "[Davacı Karşı Taraf Adı Soyadı / Unvanı]",
        "k_vekil": "[Davacı Vekili]",
        "konu": "Mersin .. Asliye Hukuk Mahkemesi'nin ... tarih ve ... E., ... K. sayılı haksız ve hukuka aykırı kararının istinafen incelenerek BOZULMASI ve KALDIRILMASI talebimizdir.",
        "aciklama": "1- Yerel mahkemece eksik inceleme ve hatalı delil değerlendirmesi sonucunda usul ve yasaya aykırı karar verilmiştir.\n2- [Yerel mahkeme kararındaki somut maddi ve hukuki hata gerekçeleri]\n3- Karar usul ve esas yönünden hukuka aykırı olup istinaf incelemesiyle kaldırılması gerekmektedir.",
        "sonuc": "Yukarıda arz ve izah edilen nedenlerle; istinaf başvurumuzun KABULÜ ile yerel mahkeme kararının KALDIRILMASINA ve davanın reddine, tehiri icra talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "👮 Müşteki Şikayet / Suç Duyurusu (Savcılık)": {
        "mahkeme": "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
        "talep": "",
        "dosya": "",
        "m_sifat": "MÜŞTEKİ",
        "m_ad": "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müşteki Adresi]",
        "k_sifat": "ŞÜPHELİ / ŞÜPHELİLER",
        "k_ad": "[Şüpheli Adı Soyadı / Kimliği Belirlenecek Şahıslar]",
        "k_vekil": "",
        "konu": "Şüpheli/ler hakkında TCK m. ... (Suç Adı) uyarınca kamu davası açılması talepli suç duyurumuzdur.",
        "aciklama": "SUÇ : [Örn: Dolandırıcılık, Tehdit, Hakaret vb.]\nSUÇ TARİHİ : .../.../2026\n\n1- Şüpheli şahıs ... tarihinde müvekkile karşı atılı suçu işlemiştir.\n2- Olayın gerçekleşme şekli, tanık beyanları ve ekteki delillerle sabittir.\n3- Şüphelinin cezalandırılması için hakkında kamu davası açılması zorunluluğu doğmuştur.",
        "sonuc": "Yukarıda açıklanan ve resen tespit edilecek nedenlerle; şüpheli hakkında gerekli soruşturmanın yapılarak KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "🚫 KYOK (Takipsizlik) Kararına İtiraz Dilekçesi": {
        "mahkeme": "MERSİN NÖBETÇİ SULH CEZA HÂKİMLİĞİNE\nGönderilmek Üzere\nMERSİN CUMHURİYET BAŞSAVCILIĞINA",
        "talep": "",
        "dosya": "Soruşturma No: 2026/... - Karar No: 2026/...",
        "m_sifat": "İTİRAZ EDEN (MÜŞTEKİ)",
        "m_ad": "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Müşteki Adresi]",
        "k_sifat": "ŞÜPHELİ",
        "k_ad": "[Şüpheli Adı Soyadı]",
        "k_vekil": "",
        "konu": "Mersin Cumhuriyet Başsavcılığı'nın ... tarihli Kovuşturmaya Yer Olmadığına Dair Kararına (KYOK) itirazlarımızın sunulmasıdır.",
        "aciklama": "1- Başsavcılıkça dosya kapsamında toplanması gereken temel deliller toplanmadan, eksik soruşturma ile takipsizlik kararı verilmiştir.\n2- [Soruşturulmayan deliller, dinlenmeyen tanıklar ve somut delil durumu]\n3- CMK m. 172-173 uyarınca kamu davası açılması için yeterli şüphe mevcuttur.",
        "sonuc": "Yukarıda açıklanan nedenlerle; Mersin Cumhuriyet Başsavcılığı'nın KYOK kararının KALDIRILMASINA ve şüpheli hakkında KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "⛓️ Tutukluluğa İtiraz ve Tahliye Dilekçesi": {
        "mahkeme": "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\nGönderilmek Üzere\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
        "talep": "TAHLİYE TALEPLİDİR",
        "dosya": "Sorgu No: 2026/... Sorgu",
        "m_sifat": "ŞÜPHELİ / SANIK",
        "m_ad": "[Müvekkil Şüpheli/Sanık - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi / Cezaevi Bilgisi]",
        "k_sifat": "MÜŞTEKİ",
        "k_ad": "[Müşteki Adı Soyadı]",
        "k_vekil": "[Müşteki Vekili]",
        "konu": "Mersin .. Sulh Ceza Hâkimliği'nin ... tarihli tutuklama kararına itirazımız ve TAHLİYE talebimizdir.",
        "aciklama": "1- Müvekkil hakkında verilen tutuklama kararı CMK 100 ve devamı maddelerine aykırıdır.\n2- Müvekkilin sabit ikametgah sahibi olması, delilleri karartma veya kaçma şüphesinin bulunmaması gözetilmemiştir.\n3- Tutuklama bir tedbirdir ve ölçülülük ilkesi gereği adli kontrol hükümleri uygulanmalıdır.",
        "sonuc": "Yukarıda açıklanan nedenlerle; TUTUKLAMA KARARININ KALDIRILARAK MÜVEKKİLİN TAHLİYESİNE, Mahkemeniz aksi kanaatte ise adli kontrol hükümleri uygulanarak serbest bırakılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "📋 Adli Kontrol Kararına İtiraz Dilekçesi": {
        "mahkeme": "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\nGönderilmek Üzere\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
        "talep": "ADLİ KONTROLÜN KALDIRILMASI TALEPLİDİR",
        "dosya": "2026/... Sorgu (veya Esas)",
        "m_sifat": "ŞÜPHELİ / SANIK",
        "m_ad": "[Müvekkil Şüpheli/Sanık - T.C. 12345678901]",
        "m_adres": "[Müvekkil Adresi]",
        "k_sifat": "MÜŞTEKİ",
        "k_ad": "[Müşteki Adı Soyadı]",
        "k_vekil": "",
        "konu": "Müvekkil hakkında uygulanan adli kontrol tedbirinin (imza yükümlülüğü / yurtdışı çıkış yasağı vb.) kaldırılması talebimizdir.",
        "aciklama": "1- Müvekkil hakkında tesis edilen adli kontrol kararı çalışma ve seyahat hürriyetini ölçüsüz biçimde kısıtlamaktadır.\n2- Müvekkil tüm adli kontrol tedbirlerine eksiksiz uymuş olup kaçma veya delil karartma şüphesi kalmamıştır.\n3- Tedbirin devamında hukuki yarar bulunmamaktadır.",
        "sonuc": "Yukarıda açıklanan nedenlerle; müvekkil hakkındaki ADLİ KONTROL TEDBİRLERİNİN KALDIRILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    },
    "🛡️ Ceza Mahkemesi Savunma / Esas Hakkında Beyan": {
        "mahkeme": "MERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
        "talep": "BERAAT TALEPLİDİR",
        "dosya": "2026/... Esas",
        "m_sifat": "SANIK",
        "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
        "m_adres": "[Sanık Adresi]",
        "k_sifat": "KATILAN / MÜŞTEKİ",
        "k_ad": "[Katılan/Müşteki Adı Soyadı]",
        "k_vekil": "[Katılan Vekili]",
        "konu": "Esas hakkındaki mütalaaya karşı savunmalarımız ve BERAAT talebimizin sunulmasıdır.",
        "aciklama": "1- İddianamede ve mütalaada isnat edilen fiillerin müvekkil tarafından işlendiğine dair somut, kesin ve inandırıcı hiçbir delil bulunmamaktadır.\n2- Suçun yasal ve manevi unsurları oluşmamış olup 'şüpheden sanık yararlanır' evrensel ilkesi geçerlidir.\n3- Müvekkilin atılı suçtan beraatine karar verilmesi gerekmektedir.",
        "sonuc": "Yukarıda açıklanan gerekçelerle; müvekkil sanığın BERAATİNE, Mahkemeniz aksi kanaatte ise lehe olan yasal hükümlerin uygulanmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
    }
}


class DilekceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚖️ UYAP Dilekçe & Üst Bilgi Oluşturucu")
        self.geometry("800x820")
        self.minsize(760, 740)
        self.configure(bg="#eceff1")
        
        self.create_ui()
        # İlk şablonu uygula
        first_tpl = list(TEMPLATES.keys())[0]
        self.combo_tpl.set(first_tpl)
        self.on_template_selected(first_tpl)

    def create_ui(self):
        # 1. Başlık Banner
        header_frame = tk.Frame(self, bg="#1a365d", height=50)
        header_frame.pack(fill="x", side="top")
        tk.Label(
            header_frame, 
            text="⚖️ UYAP Dilekçe & Üst Bilgi Oluşturucu", 
            font=("Helvetica", 16, "bold"), 
            fg="white", 
            bg="#1a365d"
        ).pack(pady=10)

        # 2. Şablon Seçici (Geniş Açılır Liste - Combobox)
        preset_bar = tk.LabelFrame(
            self, 
            text=" 📑 Dilekçe Şablonu Seçiniz (Seçtiğinizde form otomatik dolar) ", 
            font=("Helvetica", 11, "bold"), 
            bg="#eceff1", 
            fg="#1a365d"
        )
        preset_bar.pack(fill="x", padx=16, pady=8)

        self.combo_tpl = ttk.Combobox(
            preset_bar, 
            values=list(TEMPLATES.keys()), 
            state="readonly", 
            font=("Helvetica", 12, "bold"),
            width=50
        )
        self.combo_tpl.pack(fill="x", padx=12, pady=8)
        self.combo_tpl.bind("<<ComboboxSelected>>", lambda e: self.on_template_selected(self.combo_tpl.get()))

        # 3. Ana Form Alanı
        main_form = tk.Frame(self, bg="#eceff1")
        main_form.pack(fill="both", expand=True, padx=16, pady=2)

        # --- A. Mahkeme ve Dosya ---
        lf_court = tk.LabelFrame(main_form, text=" 1. Mahkeme ve Dosya Bilgileri ", font=("Helvetica", 11, "bold"), bg="#eceff1", fg="#1e40af")
        lf_court.pack(fill="x", pady=4)

        self.make_row(lf_court, 0, "Mahkeme Adı:", "ent_mahkeme", 58)
        self.make_row(lf_court, 1, "Özel Talep (Sağ Üst):", "ent_talep", 58)
        self.make_row(lf_court, 2, "Dosya / İcra No:", "ent_dosya", 58)

        # --- B. Taraflar ---
        lf_parties = tk.LabelFrame(main_form, text=" 2. Taraf ve Vekil Bilgileri ", font=("Helvetica", 11, "bold"), bg="#eceff1", fg="#1e40af")
        lf_parties.pack(fill="x", pady=4)

        self.make_row(lf_parties, 0, "Müvekkil Sıfatı:", "ent_m_sifat", 25, sticky_w=True)
        self.make_row(lf_parties, 1, "Müvekkil İsim / TC:", "ent_m_ad", 58)
        self.make_row(lf_parties, 2, "Müvekkil Adresi:", "ent_m_adres", 58)
        self.make_row(lf_parties, 3, "Vekili (Sabit):", "ent_vekil", 58, default="Av. Lütfi Serkan SAYOĞLU - UETS [16153-51280-36854]")
        self.make_row(lf_parties, 4, "Karşı Taraf Sıfatı:", "ent_k_sifat", 25, sticky_w=True)
        self.make_row(lf_parties, 5, "Karşı Taraf İsim:", "ent_k_ad", 58)
        self.make_row(lf_parties, 6, "Karşı Taraf Vekili:", "ent_k_vekil", 58)

        # --- C. Konu ve Açıklama ---
        lf_content = tk.LabelFrame(main_form, text=" 3. Konu ve Açıklama Özeti ", font=("Helvetica", 11, "bold"), bg="#eceff1", fg="#1e40af")
        lf_content.pack(fill="both", expand=True, pady=4)

        self.make_row(lf_content, 0, "Dilekçe Konusu:", "ent_konu", 58)

        tk.Label(lf_content, text="Açıklamalar:", font=("Helvetica", 10, "bold"), bg="#eceff1", fg="#374151").grid(row=1, column=0, sticky="nw", padx=8, pady=4)
        self.txt_aciklama = tk.Text(lf_content, height=4, width=54, font=("Helvetica", 11), relief="solid", bd=1)
        self.txt_aciklama.grid(row=1, column=1, padx=8, pady=4, sticky="we")

        # 4. Alt Butonlar
        bottom_bar = tk.Frame(self, bg="#eceff1")
        bottom_bar.pack(fill="x", side="bottom", padx=16, pady=10)

        btn_open = tk.Button(
            bottom_bar,
            text="✨ UDF Oluştur ve UYAP'ta Aç",
            font=("Helvetica", 12, "bold"),
            bg="#1d4ed8",
            fg="white",
            activebackground="#1e40af",
            activeforeground="white",
            padx=18,
            pady=8,
            relief="raised",
            cursor="pointinghand",
            command=lambda: self.generate_udf(open_after=True)
        )
        btn_open.pack(side="right", padx=6)

        btn_save = tk.Button(
            bottom_bar,
            text="💾 Masaüstüne Kaydet",
            font=("Helvetica", 11),
            bg="#047857",
            fg="white",
            activebackground="#065f46",
            activeforeground="white",
            padx=14,
            pady=7,
            relief="raised",
            cursor="pointinghand",
            command=lambda: self.generate_udf(open_after=False)
        )
        btn_save.pack(side="right", padx=6)

    def make_row(self, parent, row_idx, label_text, attr_name, width, default="", sticky_w=False):
        tk.Label(parent, text=label_text, font=("Helvetica", 10, "bold"), bg="#eceff1", fg="#374151").grid(row=row_idx, column=0, sticky="w", padx=8, pady=3)
        ent = tk.Entry(parent, width=width, font=("Helvetica", 11), relief="solid", bd=1)
        if default:
            ent.insert(0, default)
        if sticky_w:
            ent.grid(row=row_idx, column=1, sticky="w", padx=8, pady=3)
        else:
            ent.grid(row=row_idx, column=1, sticky="we", padx=8, pady=3)
        setattr(self, attr_name, ent)

    def on_template_selected(self, tpl_name):
        tpl = TEMPLATES.get(tpl_name)
        if not tpl:
            return
        
        self.ent_mahkeme.delete(0, tk.END)
        self.ent_mahkeme.insert(0, tpl.get("mahkeme", ""))

        self.ent_talep.delete(0, tk.END)
        self.ent_talep.insert(0, tpl.get("talep", ""))

        self.ent_dosya.delete(0, tk.END)
        self.ent_dosya.insert(0, tpl.get("dosya", ""))

        self.ent_m_sifat.delete(0, tk.END)
        self.ent_m_sifat.insert(0, tpl.get("m_sifat", ""))

        self.ent_m_ad.delete(0, tk.END)
        self.ent_m_ad.insert(0, tpl.get("m_ad", ""))

        self.ent_m_adres.delete(0, tk.END)
        self.ent_m_adres.insert(0, tpl.get("m_adres", ""))

        self.ent_k_sifat.delete(0, tk.END)
        self.ent_k_sifat.insert(0, tpl.get("k_sifat", ""))

        self.ent_k_ad.delete(0, tk.END)
        self.ent_k_ad.insert(0, tpl.get("k_ad", ""))

        self.ent_k_vekil.delete(0, tk.END)
        self.ent_k_vekil.insert(0, tpl.get("k_vekil", ""))

        self.ent_konu.delete(0, tk.END)
        self.ent_konu.insert(0, tpl.get("konu", ""))

        self.txt_aciklama.delete("1.0", tk.END)
        self.txt_aciklama.insert("1.0", tpl.get("aciklama", ""))

    def generate_udf(self, open_after=True):
        mahkeme = self.ent_mahkeme.get().strip()
        talep = self.ent_talep.get().strip()
        dosya = self.ent_dosya.get().strip()
        m_sifat = self.ent_m_sifat.get().strip()
        m_ad = self.ent_m_ad.get().strip()
        m_adres = self.ent_m_adres.get().strip()
        vekil = self.ent_vekil.get().strip()
        k_sifat = self.ent_k_sifat.get().strip()
        k_ad = self.ent_k_ad.get().strip()
        k_vekil = self.ent_k_vekil.get().strip()
        konu = self.ent_konu.get().strip()
        aciklama = self.txt_aciklama.get("1.0", tk.END).strip()

        if not mahkeme:
            messagebox.showwarning("Uyarı", "Lütfen Mahkeme Başlığını giriniz.")
            return

        tab_setting = "130:0:0,145:0:0"
        paragraphs = []

        # 1. Mahkeme Başlığı (Ortalı, Kalın)
        for line in mahkeme.split("\n"):
            if line.strip():
                paragraphs.append((1, 0, "8.5", None, None, [(f"{line.strip()}\n", True, False, False)]))
        paragraphs[-1] = (1, 0, "14.17", None, None, paragraphs[-1][5])

        # 2. Özel Talep (Sağa Yaslı, Kalın)
        if talep:
            paragraphs.append((2, 0, "14.17", None, None, [(f"{talep}\n", True, False, False)]))

        # 3. Dosya No
        if dosya:
            dosya_etiket = "İCRA DOSYA NO" if ("İcra" in dosya or "İcra" in mahkeme) else "DOSYA NO"
            paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                (dosya_etiket, True, False, True),
                ("\t:\t", False, False, False),
                (f"{dosya}\n", False, False, False)
            ]))

        # 4. Müvekkil
        if m_sifat and m_ad:
            paragraphs.append((0, "0.5", "0.0" if m_adres else "5.0", None, tab_setting, [
                (m_sifat, True, False, True),
                ("\t:\t", False, False, False),
                (f"{m_ad}\n", True, False, False)
            ]))
            if m_adres:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("", False, False, False),
                    ("\t\t", False, False, False),
                    (f"{m_adres}\n", False, True, False)
                ]))

        # 5. Vekili
        if vekil:
            paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                ("VEKİLİ", True, False, True),
                ("\t:\t", False, False, False),
                (f"{vekil}\n", False, False, False)
            ]))

        # 6. Karşı Taraf
        if k_sifat and k_ad:
            paragraphs.append((0, "0.5", "0.0" if k_vekil else "5.0", None, tab_setting, [
                (k_sifat, True, False, True),
                ("\t:\t", False, False, False),
                (f"{k_ad}\n", False, False, False)
            ]))
            if k_vekil:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("VEKİLİ", True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{k_vekil}\n", False, False, False)
                ]))

        # 7. Konu
        if konu:
            paragraphs.append((0, "0.5", "14.17", None, tab_setting, [
                ("KONU", True, False, True),
                ("\t:\t", False, False, False),
                (f"{konu}\n", False, False, False)
            ]))

        # 8. Açıklamalar Başlığı
        paragraphs.append((0, 0, "8.5", None, None, [
            ("AÇIKLAMALAR:", True, False, True),
            ("\n", False, False, False)
        ]))

        # 9. Açıklama Paragrafları
        if aciklama:
            for line in aciklama.split("\n"):
                if line.strip():
                    paragraphs.append((3, 0, "8.5", "35.43", None, [(f"{line.strip()}\n", False, False, False)]))
        else:
            paragraphs.append((3, 0, "8.5", "35.43", None, [("1- [Açıklamalarınızı buraya yazabilirsiniz.]\n", False, False, False)]))

        # 10. Sonuç ve İstem Başlığı
        paragraphs.append((0, 0, "8.5", None, None, [
            ("SONUÇ VE İSTEM:", True, False, True),
            ("\n", False, False, False)
        ]))

        # 11. Sonuç Cümlesi
        selected_tpl = TEMPLATES.get(self.combo_tpl.get(), {})
        custom_sonuc = selected_tpl.get("sonuc", "Yukarıda arz ve izah olunan nedenlerle; taleplerimizin kabulü ile yargılama giderleri ve vekâlet ücretinin karşı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz.")
        date_str = datetime.now().strftime("%d.%m.%Y")
        paragraphs.append((3, 0, "14.17", "35.43", None, [
            (f"{custom_sonuc} {date_str}\n", False, False, False)
        ]))

        # 12. İmza Bloğu
        imza_unvan = f"{m_sifat.title()} Vekili" if m_sifat else "Vekil"
        paragraphs.append((2, 0, "0.0", None, None, [(f"{imza_unvan}\n", True, False, False)]))
        paragraphs.append((2, 0, "0.0", None, None, [("Av. Lütfi Serkan SAYOĞLU\n", True, False, False)]))
        paragraphs.append((2, 0, "0.0", None, None, [("(e-imzalıdır)\n", False, True, False)]))

        desktop_dir = os.path.expanduser("~/Desktop")
        clean_title = mahkeme.split("MAHKEMESİ")[0].replace("\n", " ").strip() if "MAHKEMESİ" in mahkeme else "Dilekce"
        safe_filename = f"{clean_title} - {self.combo_tpl.get().split(' ')[1]}.udf"
        safe_filename = "".join(c for c in safe_filename if c not in r'\/:*?"<>|')

        out_path = os.path.join(desktop_dir, safe_filename)

        try:
            build_udf(paragraphs, out_path)
            if open_after:
                subprocess.Popen(["open", "-a", "Uyap Doküman Editörü", out_path])
                messagebox.showinfo("Başarılı", f"Dilekçe UDF oluşturuldu ve UYAP'ta açıldı!\n\nDosya: {safe_filename}")
            else:
                messagebox.showinfo("Başarılı", f"Dilekçe UDF olarak Masaüstüne kaydedildi:\n\n{out_path}")
        except Exception as ex:
            messagebox.showerror("Hata", f"UDF oluşturulurken bir hata oluştu:\n{ex}")

if __name__ == "__main__":
    app = DilekceApp()
    app.mainloop()
