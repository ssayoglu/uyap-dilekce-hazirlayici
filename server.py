#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.server
import socketserver
import json
import urllib.parse
import webbrowser
import zipfile
import os
import sys
import subprocess
from datetime import datetime

PORT = 5678

CURRENT_VERSION = "1.3.0"
VERSION_URL = "https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/version.json"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

def check_for_updates_silently():
    try:
        # 1. If installed as a git repo in ~/.dilekce-hazirlayici or current folder
        if os.path.exists(os.path.join(REPO_DIR, ".git")):
            subprocess.run(["git", "pull", "--quiet"], cwd=REPO_DIR, timeout=3, capture_output=True)
            return
        
        # 2. Otherwise check raw version from GitHub
        import urllib.request
        req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                remote_version = data.get("version", CURRENT_VERSION)
                if remote_version > CURRENT_VERSION:
                    raw_server_url = "https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/server.py"
                    req2 = urllib.request.Request(raw_server_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req2, timeout=3.0) as r2:
                        if r2.status == 200:
                            content = r2.read()
                            with open(os.path.join(REPO_DIR, "server.py"), "wb") as f:
                                f.write(content)
    except Exception:
        # Silently skip on offline / no internet / timeout
        pass


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

HTML_PAGE = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚖️ UYAP Dilekçe & Şablon Yöneticisi</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; user-select: none; }
        input, textarea, select { user-select: text; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
    </style>
</head>
<body class="bg-slate-100 min-h-screen text-slate-800 flex flex-col justify-between">

    <!-- Üst Başlık Barı -->
    <header class="bg-slate-900 text-white shadow-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
            <div class="flex items-center space-x-3 cursor-pointer" onclick="showGalleryView()">
                <span class="text-2xl">⚖️</span>
                <div>
                    <h1 class="text-lg font-bold tracking-tight">UYAP Dilekçe & Şablon Yöneticisi</h1>
                    <p class="text-xs text-slate-400">Milimetrik hizalı, H.E.D., Delil ve Hukuki Sebepler içeren UDF şablonları</p>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <button onclick="openLawyerModal()" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-900/60 hover:bg-blue-800 text-blue-300 border border-blue-700 transition shadow-sm" title="Avukat ve Şehir bilgilerini değiştirmek için tıklayın">
                    <span id="activeLawyerHeader">Av. Lütfi Serkan SAYOĞLU</span>
                    <span class="text-[10px] bg-blue-700/50 px-1.5 py-0.5 rounded text-blue-200">⚙️ Ayarlar</span>
                </button>
            </div>
        </div>
    </header>

    </header>

    <!-- Avukat ve Şehir Profili Modal -->
    <div id="lawyerModal" class="fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="font-bold text-slate-900 text-base flex items-center gap-2">
                    <span>⚙️</span> Avukat & Varsayılan Şehir Ayarları
                </h3>
                <button onclick="closeLawyerModal()" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">
                Buraya gireceğiniz bilgiler tüm dilekçelerde <strong>VEKİLİ</strong>, imza bloğu, <strong>Yerel Mahkemeler</strong> ve <strong>Bölge Adliye Mahkemesi (İstinaf)</strong> başlıklarında dinamik olarak kullanılır.
            </p>
            <div class="space-y-3">
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Avukat Adı Soyadı:</label>
                    <input type="text" id="modalLawyerName" placeholder="Örn: Av. Lütfi Serkan SAYOĞLU" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">UETS / Ek İletişim Bilgisi:</label>
                    <input type="text" id="modalLawyerExtra" placeholder="Örn: UETS [16153-51280-36854]" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="grid grid-cols-2 gap-3 pt-1">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-1">Varsayılan İl / Şehir:</label>
                        <input type="text" id="modalLawyerCity" placeholder="Örn: MERSİN" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-1">Bağlı Olduğu BAM (İstinaf):</label>
                        <input type="text" id="modalLawyerBamCity" placeholder="Örn: ADANA" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500">
                    </div>
                </div>
            </div>
            <div class="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button onclick="closeLawyerModal()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition">Vazgeç</button>
                <button onclick="saveLawyerProfile()" class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition">💾 Kaydet ve Uygula</button>
            </div>
        </div>
    </div>

    <!-- Bildirim Bildirisi -->
    <div id="toast" class="fixed bottom-6 right-6 z-50 hidden max-w-md p-4 rounded-xl shadow-xl text-sm font-semibold transition-all transform duration-300"></div>

    <!-- 1. GÖRÜNÜM: ŞABLON GALERİSİ -->
    <main id="galleryView" class="max-w-7xl mx-auto px-6 py-6 flex-1 w-full space-y-6">
        
        <!-- SIK KULLANILANLAR BÖLÜMÜ -->
        <div class="bg-gradient-to-r from-blue-900/10 via-indigo-900/5 to-slate-100 p-5 rounded-2xl border border-blue-200/60 shadow-sm">
            <div class="flex items-center justify-between mb-3.5">
                <div class="flex items-center gap-2">
                    <span class="text-lg">⭐</span>
                    <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wide">Sık Kullanılan Şablonlar</h2>
                </div>
                <span class="text-xs text-slate-500 font-medium">Hızlıca UYAP'ta açabilir veya düzenleyebilirsiniz</span>
            </div>
            <div id="favoritesGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <!-- Dinamik Favoriler Doldurulur -->
            </div>
        </div>

        <!-- Arama ve Filtreleme -->
        <div class="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div class="relative w-full md:w-80">
                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">🔍</span>
                <input type="text" id="searchInput" oninput="filterTemplates()" placeholder="Tüm şablonlarda ara..." class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition">
            </div>
            <div class="flex flex-col gap-2 w-full md:w-auto">
                <!-- Ana Kategoriler -->
                <div class="flex items-center gap-1.5 overflow-x-auto pb-1">
                    <button onclick="setMainCategory('all')" id="mcat_all" class="mcat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-600 text-white shadow-sm transition">Tümü</button>
                    <button onclick="setMainCategory('hukuk')" id="mcat_hukuk" class="mcat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">🏛️ Hukuk Mahkemeleri</button>
                    <button onclick="setMainCategory('ozel_dava')" id="mcat_ozel_dava" class="mcat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">💰 Özel Dava Türleri</button>
                    <button onclick="setMainCategory('ceza')" id="mcat_ceza" class="mcat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition">⚖️ Ceza & Savcılık</button>
                </div>
                <!-- Alt Kategoriler -->
                <div id="subCategoryBar" class="flex items-center gap-1.5 overflow-x-auto pt-1 border-t border-slate-100">
                    <button onclick="setCategory('all')" id="cat_all" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 text-white transition">Tümü</button>
                    <button onclick="setCategory('asliye_hukuk')" id="cat_asliye_hukuk" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Asliye Hukuk</button>
                    <button onclick="setCategory('sulh_hukuk')" id="cat_sulh_hukuk" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Sulh Hukuk</button>
                    <button onclick="setCategory('ozel_dava')" id="cat_ozel_dava" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Özel Davalar</button>
                    <button onclick="setCategory('icra_hukuk')" id="cat_icra_hukuk" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">İcra Hukuk</button>
                    <button onclick="setCategory('asliye_ceza')" id="cat_asliye_ceza" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Asliye Ceza</button>
                    <button onclick="setCategory('agir_ceza')" id="cat_agir_ceza" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Ağır Ceza</button>
                    <button onclick="setCategory('icra_ceza')" id="cat_icra_ceza" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">İcra Ceza</button>
                    <button onclick="setCategory('savcilik')" id="cat_savcilik" class="cat-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Savcılık</button>
                </div>
            </div>
        </div>

        <!-- Tüm Şablon Kartları Grid -->
        <div>
            <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 px-1">Tüm Şablon Kataloğu</h3>
            <div id="templateGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                <!-- Dinamik doldurulur -->
            </div>
        </div>
    </main>

    <!-- 2. GÖRÜNÜM: FORM DÜZENLEYİCİ -->
    <main id="formView" class="max-w-5xl mx-auto px-6 py-6 hidden flex-1 w-full">
        
        <div class="mb-4 flex items-center justify-between">
            <button onclick="showGalleryView()" class="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-sm font-semibold shadow-sm transition">
                ← Şablon Listesine Dön
            </button>
            <span id="formTitleBadge" class="text-sm font-bold text-blue-900 bg-blue-50 px-3 py-1.5 rounded-xl border border-blue-200"></span>
        </div>

        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-6">
            
            <!-- Bölüm 1: Mahkeme & Dosya -->
            <div>
                <h2 class="text-base font-bold text-slate-900 flex items-center gap-2 mb-3">
                    <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs">1</span>
                    Mahkeme ve Dosya Bilgileri
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="md:col-span-2">
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Mahkeme Başlığı (Ortalı, Kalın):</label>
                        <textarea id="mahkeme" rows="2" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500"></textarea>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Özel Talep (Sağ Üst Başlık):</label>
                        <input type="text" id="talep" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-semibold text-red-600 focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Dosya / İcra / Soruşturma No:</label>
                        <input type="text" id="dosya" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                    </div>
                </div>
            </div>

            <hr class="border-slate-200">

            <!-- Bölüm 2: Taraflar -->
            <div>
                <h2 class="text-base font-bold text-slate-900 flex items-center gap-2 mb-3">
                    <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs">2</span>
                    Taraf ve Vekil Bilgileri
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 mb-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Müvekkil Sıfatı:</label>
                        <input type="text" id="m_sifat" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-bold text-slate-800 bg-white">
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Müvekkil İsim / T.C. / Vergi No:</label>
                        <input type="text" id="m_ad" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 bg-white">
                    </div>
                    <div class="md:col-span-3">
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Müvekkil Adresi (İtalik yerleşir):</label>
                        <input type="text" id="m_adres" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm italic text-slate-700 bg-white">
                    </div>
                </div>

                <div class="mb-4">
                    <div class="flex items-center justify-between mb-1">
                        <label class="block text-xs font-semibold text-slate-600">Vekili:</label>
                        <button type="button" onclick="openLawyerModal()" class="text-[11px] text-blue-600 hover:underline font-semibold">⚙️ Avukat Bilgisini Güncelle</button>
                    </div>
                    <input type="text" id="vekil" class="w-full px-3.5 py-2 border border-blue-200 bg-blue-50/50 rounded-xl text-sm font-semibold text-blue-950">
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Karşı Taraf Sıfatı:</label>
                        <input type="text" id="k_sifat" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-bold text-slate-800 bg-white">
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Karşı Taraf İsim / Unvan:</label>
                        <input type="text" id="k_ad" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 bg-white">
                    </div>
                    <div class="md:col-span-3">
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Karşı Taraf Vekili (Varsa):</label>
                        <input type="text" id="k_vekil" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 bg-white">
                    </div>
                </div>
            </div>

            <hr class="border-slate-200">

            <!-- Bölüm 3: Konu, Harca Esas Değer, Deliller & Sebepler -->
            <div>
                <h2 class="text-base font-bold text-slate-900 flex items-center gap-2 mb-3">
                    <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs">3</span>
                    Konu, Dava Değeri, Deliller ve Açıklamalar
                </h2>
                <div class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="md:col-span-2">
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Dilekçe Konusu:</label>
                            <input type="text" id="konu" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Dava Değeri / Harca Esas Değer (H.E.D.):</label>
                            <input type="text" id="hed" placeholder="... TL (Fazlaya ilişkin haklarımız saklıdır)" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-semibold text-slate-600 mb-1">Açıklamalar (Madde Madde):</label>
                        <textarea id="aciklama" rows="5" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-normal text-slate-900 focus:ring-2 focus:ring-blue-500"></textarea>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Hukuki Sebepler:</label>
                            <input type="text" id="hukuki_sebepler" value="HMK, TBK, TTK, TMK, İİK ve ilgili mevzuat." class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Hukuki Deliller:</label>
                            <input type="text" id="hukuki_deliller" value="Sözleşmeler, banka kayıtları, yazışmalar, tanık, bilirkişi, yemin ve sair hukuki deliller." class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Butonlar -->
            <div class="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-end gap-3">
                <button type="button" onclick="generateFromForm(false)" class="w-full sm:w-auto px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-sm shadow-sm transition flex items-center justify-center gap-2">
                    💾 Masaüstüne Kaydet
                </button>
                <button type="button" onclick="generateFromForm(true)" class="w-full sm:w-auto px-7 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm shadow-md transition flex items-center justify-center gap-2">
                    ✨ UDF Oluştur ve UYAP'ta Aç
                </button>
            </div>

        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        UYAP Doküman Editörü UDF Oluşturucu • <span id="footerLawyer">Av. Lütfi Serkan SAYOĞLU</span>
    </footer>

    <script>
        const DELILLER_DEFAULT = "Sözleşmeler, faturalar, banka kayıtları, ticari defterler, tanık, bilirkişi, yemin ve sair hukuki deliller.";
        const SEBEPLER_DEFAULT = "HMK, TBK, TTK, TMK, İİK ve ilgili mevzuat.";

        // Güncelleme Notları Yönetimi
        const APP_VERSION = "1.3.0";

        function openChangelogModal() {
            document.getElementById("changelogModal").classList.remove("hidden");
        }

        function closeChangelogModal() {
            document.getElementById("changelogModal").classList.add("hidden");
            try {
                localStorage.setItem("dilekce_last_seen_version", APP_VERSION);
            } catch(e) {}
        }

        function checkNewVersionNotes() {
            try {
                const lastSeen = localStorage.getItem("dilekce_last_seen_version");
                if (!lastSeen || lastSeen !== APP_VERSION) {
                    openChangelogModal();
                }
            } catch(e) {}
        }

        // Avukat ve Şehir Profili Yönetimi
        const DEFAULT_LAWYER = {
            name: "Av. Lütfi Serkan SAYOĞLU",
            extra: "UETS [16153-51280-36854]",
            city: "MERSİN",
            bamCity: "ADANA"
        };

        function getLawyerProfile() {
            try {
                const lp = localStorage.getItem("dilekce_lawyer_profile");
                if (lp) {
                    const parsed = JSON.parse(lp);
                    return {
                        name: parsed.name || DEFAULT_LAWYER.name,
                        extra: parsed.extra !== undefined ? parsed.extra : DEFAULT_LAWYER.extra,
                        city: (parsed.city || DEFAULT_LAWYER.city).toUpperCase(),
                        bamCity: (parsed.bamCity || DEFAULT_LAWYER.bamCity).toUpperCase()
                    };
                }
                return DEFAULT_LAWYER;
            } catch (e) {
                return DEFAULT_LAWYER;
            }
        }

        function getLawyerFullText() {
            const lp = getLawyerProfile();
            return lp.extra ? `${lp.name} - ${lp.extra}` : lp.name;
        }

        function getLawyerSignatureName() {
            const lp = getLawyerProfile();
            return lp.name;
        }

        function formatMahkemeForCity(rawMahkeme) {
            if (!rawMahkeme) return "";
            const lp = getLawyerProfile();
            const city = lp.city || "MERSİN";
            const bamCity = lp.bamCity || "ADANA";

            let res = rawMahkeme;
            // 1. Replace BAM / Bölge Adliye mentions first with bamCity
            res = res.replace(/ADANA BÖLGE ADLİYE MAHKEMESİ/g, `${bamCity} BÖLGE ADLİYE MAHKEMESİ`);
            res = res.replace(/ADANA BÖLGE ADLİYE MAHKEMESİ/g, `${bamCity} BÖLGE ADLİYE MAHKEMESİ`);
            
            // 2. Replace Local city mentions
            res = res.replace(/MERSİN/g, city);
            return res;
        }

        function formatDataForCity(dataObj) {
            const copy = { ...dataObj };
            if (copy.mahkeme) copy.mahkeme = formatMahkemeForCity(copy.mahkeme);
            if (copy.konu) copy.konu = formatMahkemeForCity(copy.konu);
            if (copy.aciklama) copy.aciklama = formatMahkemeForCity(copy.aciklama);
            return copy;
        }

        function updateLawyerDisplay() {
            const lp = getLawyerProfile();
            document.getElementById("activeLawyerHeader").textContent = `${lp.name} (${lp.city})`;
            document.getElementById("footerLawyer").textContent = `${lp.name} • ${lp.city}`;
            const vekilInput = document.getElementById("vekil");
            if (vekilInput) {
                vekilInput.value = getLawyerFullText();
            }
        }

        function openLawyerModal() {
            const lp = getLawyerProfile();
            document.getElementById("modalLawyerName").value = lp.name;
            document.getElementById("modalLawyerExtra").value = lp.extra || "";
            document.getElementById("modalLawyerCity").value = lp.city || "MERSİN";
            document.getElementById("modalLawyerBamCity").value = lp.bamCity || "ADANA";
            document.getElementById("lawyerModal").classList.remove("hidden");
        }

        function closeLawyerModal() {
            document.getElementById("lawyerModal").classList.add("hidden");
        }

        function saveLawyerProfile() {
            const name = document.getElementById("modalLawyerName").value.trim() || DEFAULT_LAWYER.name;
            const extra = document.getElementById("modalLawyerExtra").value.trim();
            const city = (document.getElementById("modalLawyerCity").value.trim() || DEFAULT_LAWYER.city).toUpperCase();
            const bamCity = (document.getElementById("modalLawyerBamCity").value.trim() || DEFAULT_LAWYER.bamCity).toUpperCase();
            
            const lp = { name, extra, city, bamCity };
            localStorage.setItem("dilekce_lawyer_profile", JSON.stringify(lp));
            updateLawyerDisplay();
            renderFavorites();
            renderTemplates();
            
            closeLawyerModal();
            showToast(`✅ Bilgiler güncellendi: ${name} (${city} / BAM: ${bamCity})`, "success");
        }

        const TEMPLATES = [
            {
                        "id": "asliye_hukuk_dava",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "⚖️",
                        "title": "Asliye Hukuk Dava Dilekçesi",
                        "desc": "Asliye Hukuk Mahkemesi genel dava açılış dilekçesi (H.E.D., deliller, ihtiyati tedbir).",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "10.000,00 TL (Fazlaya ilişkin haklarımız saklıdır)",
                                    "konu": "Davamızın kabulü ile alacağımızın yasal faiziyle tahsili ve ihtiyati tedbir talebimizdir.",
                                    "aciklama": "1- Taraflar arasındaki hukuki ilişkiden doğan edimler davalı tarafından ifa edilmemiştir.\\n2- Müvekkilin uğradığı zararın tazmini amacıyla işbu davanın açılması zorunluluğu doğmuştur.\\n3- Alacağın temini için davalının malvarlığına ihtiyati tedbir konulmasını talep ederiz.",
                                    "hukuki_sebepler": "TBK, HMK, TTK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Sözleşme, faturalar, banka kayıtları, tanık, bilirkişi, yemin ve her türlü yasal delil.",
                                    "sonuc": "Davamızın KABULÜNE, alacağımızın temerrüt faiziyle tahsiline, tedbir talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "asliye_hukuk_cevap",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "📝",
                        "title": "Asliye Hukuk Cevap Dilekçesi",
                        "desc": "Asliye Hukuk Mahkemesi davalarına karşı ilk itirazlar ve esasa cevaplar.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVALI",
                                    "m_ad": "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davalı Adresi]",
                                    "k_sifat": "DAVACI",
                                    "k_ad": "[Davacı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davacı Vekili]",
                                    "hed": "",
                                    "konu": "Davacının haksız ve mesnetsiz dava dilekçesine karşı süresi içinde cevaplarımızın sunulmasıdır.",
                                    "aciklama": "1- Davacının iddiaları gerçeğe aykırı olup müvekkilin herhangi bir borcu bulunmamaktadır.\\n2- Davacı taraf iddialarını yasal delillerle ispatlayamamıştır.\\n3- Haksız açılan davanın esastan reddi gerekmektedir.",
                                    "hukuki_sebepler": "HMK, TBK, TTK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Banka kayıtları, ticari defterler, tanık, bilirkişi, yemin ve sair deliller.",
                                    "sonuc": "Haksız ve mesnetsiz DAVANIN REDDİNE, yargılama giderleri ve vekâlet ücretinin davacıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "asliye_hukuk_istinaf",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "⚖️",
                        "title": "Asliye Hukuk İstinaf Başvuru Dilekçesi",
                        "desc": "Asliye Hukuk Mahkemesi gerekçeli kararına karşı BAM İlgili Hukuk Dairesi'ne istinaf.",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "TEHİR-İ İCRA (İCRANIN GERİ BIRAKILMASI) TALEPLİDİR",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAF EDEN (DAVALI)",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF (DAVACI)",
                                    "k_ad": "[Davacı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davacı Vekili]",
                                    "hed": "[... TL (İstinafa Konu Değer)]",
                                    "konu": "Mersin [..]. Asliye Hukuk Mahkemesi'nin ... tarih ve ... E., ... K. sayılı ilamının istinafen incelenerek KALDIRILMASI talebimizdir.",
                                    "aciklama": "1- Yerel mahkemece eksik tahkikat ve hatalı değerlendirme ile karar verilmiştir.\\n2- [Karardaki somut maddi ve hukuki hata gerekçeleri].\\n3- Kararın kaldırılarak taleplerimiz doğrultusunda yeniden hüküm kurulmasını talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 341 vd., İİK m. 36 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yerel mahkeme dava dosyası, tanık, bilirkişi ve sair deliller.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile yerel mahkeme kararının KALDIRILMASINA ve tehir-i icra talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "asliye_hukuk_talep_artirim",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "📊",
                        "title": "Asliye Hukuk Talep Artırım Dilekçesi (HMK 109/4)",
                        "desc": "Bilirkişi raporu sonrası HMK 109/4 uyarınca müddeabihin artırılması (Islah değildir).",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davalı Vekili]",
                                    "hed": "[... TL (Artırılan Net Alacak)]",
                                    "konu": "HMK m. 109/4 gereğince bilirkişi raporu doğrultusunda dava değerinin artırılmasıdır. (Islah değildir).",
                                    "aciklama": "1- Alınan bilirkişi raporu ile müvekkilin toplam alacak tutarı kesinleşmiştir.\\n2- HMK m. 109/4 uyarınca talep artırımı yapıyoruz; harcı yatırılmıştır.",
                                    "hukuki_sebepler": "HMK m. 109/4 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Bilirkişi raporu, harç makbuzu ve dosya kapsamı.",
                                    "sonuc": "HMK m. 109/4 gereğince TALEP ARTIRIMIMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "sulh_hukuk_dava",
                        "category": "sulh_hukuk",
                        "main_cat": "hukuk",
                        "icon": "🏠",
                        "title": "Sulh Hukuk Dava Dilekçesi",
                        "desc": "Kira, tahliye, vesayet, ortaklığın giderilmesi ve genel Sulh Hukuk dava dilekçesi.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ SULH HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı - T.C. / Unvan]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[... TL (Dava Değeri)]",
                                    "konu": "Davamızın kabulü ile taleplerimiz doğrultusunda karar verilmesi talebimizdir.",
                                    "aciklama": "1- Uyuşmazlığa konu taşınır/taşınmaz veya kira ilişkisinde davalı taraf edimlerine aykırı davranmıştır.\\n2- Dava açma zarureti hasıl olmuştur.",
                                    "hukuki_sebepler": "TBK, TMK, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Sözleşme, dekontlar, tapu kayıtları, tanık, bilirkişi ve sair deliller.",
                                    "sonuc": "Davamızın KABULÜNE, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "sulh_hukuk_cevap",
                        "category": "sulh_hukuk",
                        "main_cat": "hukuk",
                        "icon": "📝",
                        "title": "Sulh Hukuk Cevap Dilekçesi",
                        "desc": "Sulh Hukuk davalarına karşı cevap ve itirazların sunulması.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. SULH HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVALI",
                                    "m_ad": "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davalı Adresi]",
                                    "k_sifat": "DAVACI",
                                    "k_ad": "[Davacı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davacı Vekili]",
                                    "hed": "",
                                    "konu": "Davacının haksız davasına karşı cevaplarımızın sunulması ile davanın reddi talebimizdir.",
                                    "aciklama": "1- Davacının ileri sürdüğü iddialar mesnetsizdir.\\n2- Müvekkil sözleşme ve yasa hükümlerine tam uymuştur.",
                                    "hukuki_sebepler": "TBK, TMK, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Kira kontratı, ödeme dekontları, tanık ve bilirkişi.",
                                    "sonuc": "Haksız davanın REDDİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "sulh_hukuk_istinaf",
                        "category": "sulh_hukuk",
                        "main_cat": "hukuk",
                        "icon": "⚖️",
                        "title": "Sulh Hukuk İstinaf Başvuru Dilekçesi",
                        "desc": "Sulh Hukuk Mahkemesi gerekçeli kararına karşı BAM İlgili Hukuk Dairesi'ne istinaf.",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. SULH HUKUK MAHKEMESİNE",
                                    "talep": "TEHİR-İ İCRA (İCRANIN GERİ BIRAKILMASI) TALEPLİDİR",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAF EDEN (DAVALI)",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "[... TL]",
                                    "konu": "Mersin [..]. Sulh Hukuk Mahkemesi'nin ... tarih ve ... E., ... K. sayılı ilamının istinafen KALDIRILMASI talebimizdir.",
                                    "aciklama": "1- Yerel mahkemece eksik tahkikatla karar verilmiştir.\\n2- Kararın kaldırılarak davanın reddi talep olunur.",
                                    "hukuki_sebepler": "HMK m. 341 vd., İİK m. 36 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Sulh Hukuk dava dosyası.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile yerel mahkeme kararının KALDIRILMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "ozel_alacak_dava",
                        "category": "ozel_dava",
                        "main_cat": "ozel_dava",
                        "icon": "💰",
                        "title": "Alacak ve Maddi Tazminat Dava Dilekçesi",
                        "desc": "Sözleşmeden, haksız fiilden veya sebepsiz zenginleşmeden doğan alacak ve tazminat davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "10.000,00 TL (Fazlaya ilişkin haklarımız saklı kalmak kaydıyla)",
                                    "konu": "Müvekkilin ödenmeyen alacağının ve maddi tazminatının temerrüt faiziyle birlikte tahsili talebidir.",
                                    "aciklama": "1- Müvekkil ile davalı arasındaki hukuki ilişkiden doğan alacak vadesinde ödenmemiştir.\\n2- Davalının edimini ifa etmemesi neticesinde müvekkil zarara uğramıştır.\\n3- Alacağın temini için davalının malvarlığı üzerine ihtiyati tedbir konulmasını talep ederiz.",
                                    "hukuki_sebepler": "TBK m. 112 vd., HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Sözleşmeler, faturalar, banka dekontları, tanık, bilirkişi ve sair deliller.",
                                    "sonuc": "Davamızın KABULÜ ile alacağımızın faiziyle tahsiline ve ihtiyati tedbir talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "ozel_is_mahkemesi_dava",
                        "category": "ozel_dava",
                        "main_cat": "ozel_dava",
                        "icon": "👷",
                        "title": "İş Mahkemesi Dava Dilekçesi (Kıdem, İhbar, Ücret)",
                        "desc": "Kıdem, ihbar, fazla mesai, UBGT, yıllık izin ve işçilik alacakları davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İŞ MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI (İŞÇİ)",
                                    "m_ad": "[Davacı İşçi Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI (İŞVEREN)",
                                    "k_ad": "[Davalı Şirket Unvanı / İşveren Adı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "1.000,00 TL (Kısmi Alacak - Fazlaya ilişkin haklarımız saklıdır)",
                                    "konu": "Kıdem tazminatı, ihbar tazminatı, fazla mesai, UBGT ve ödenmeyen işçilik alacaklarımızın en yüksek banka mevduat faiziyle tahsili talebidir.",
                                    "aciklama": "1- Müvekkil davalı işyerinde ... tarihleri arasında ... unvanıyla çalışmıştır.\\n2- İş akdi haksız ve bildirimsiz feshedilmiş, işçilik alacakları ödenmemiştir.\\n3- Arabuluculuk sürecinde anlaşma sağlanamamış olup işbu davanın açılması gerekmiştir.",
                                    "hukuki_sebepler": "4857 sayılı İş Kanunu, 7036 sayılı İş Mahkemeleri Kanunu, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "SGK kayıtları, işyeri şahsi sicil dosyası, arabuluculuk son tutanağı, maaş bordroları, emsal ücret araştırması, tanık, bilirkişi ve sair deliller.",
                                    "sonuc": "Davamızın KABULÜ ile kıdem, ihbar ve sair işçilik alacaklarımızın faiziyle tahsiline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "ozel_bosanma_dava",
                        "category": "ozel_dava",
                        "main_cat": "ozel_dava",
                        "icon": "💍",
                        "title": "Boşanma Dava Dilekçesi (Çekişmeli / Anlaşmalı)",
                        "desc": "Evlilik birliğinin temelinden sarsılması, nafaka, velayet ve maddi/manevi tazminat davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ AİLE MAHKEMESİNE",
                                    "talep": "TEDBİR NAFAKASI VE İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Eş Adı Soyadı - T.C. 12345678901]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[Maddi Tazminat: ... TL, Manevi Tazminat: ... TL]",
                                    "konu": "Evlilik birliğinin temelinden sarsılması nedeniyle BOŞANMA, velayet, nafaka ve tazminat taleplerimizdir.",
                                    "aciklama": "1- Taraflar ... tarihinde evlenmiş olup evlilik birliği davalının ağır kusurlu eylemleri nedeniyle temelinden sarsılmıştır.\\n2- Ortak çocukların velayetinin müvekkile verilmesi ve tedbir/iştirak nafakasına hükmedilmesi gerekmektedir.\\n3- Müvekkil lehine maddi ve manevi tazminata hükmedilmesini talep ederiz.",
                                    "hukuki_sebepler": "TMK m. 166 vd., HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Aile nüfus kaydı, mali durum araştırması, tanık beyanları, mesaj kayıtları, bilirkişi ve sair deliller.",
                                    "sonuc": "Tarafların BOŞANMALARINA, velayetin müvekkile verilmesine, nafakaya ve tazminata karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "ozel_tuketici_dava",
                        "category": "ozel_dava",
                        "main_cat": "ozel_dava",
                        "icon": "🛒",
                        "title": "Tüketici Mahkemesi Dava Dilekçesi",
                        "desc": "Ayıplı mal/hizmet, sözleşmeden dönme ve bedel iadesi talepli tüketici davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ TÜKETİCİ MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI (TÜKETİCİ)",
                                    "m_ad": "[Tüketici Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI (SATICI / SAĞLAYICI)",
                                    "k_ad": "[Davalı Şirket Unvanı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[... TL (Satış Bedeli İadesi)]",
                                    "konu": "Ayıplı mal nedeniyle sözleşmeden dönülerek ödenen bedelin yasal faiziyle iadesi talebidir.",
                                    "aciklama": "1- Müvekkilce satın alınan üründe gizli/açık ayıp ortaya çıkmıştır.\\n2- Ayıp ihbarında bulunulmuş ancak davalı sorumluluk almamıştır.\\n3- 6502 sayılı Kanun uyarınca bedel iadesini talep ederiz.",
                                    "hukuki_sebepler": "6502 sayılı TKHK, TBK, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Fatura, servis formları, arabuluculuk tutanağı, tanık, bilirkişi.",
                                    "sonuc": "ÖDENEN BEDELİN FAİZİYLE İADESİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "ozel_tapu_iptal",
                        "category": "ozel_dava",
                        "main_cat": "ozel_dava",
                        "icon": "📜",
                        "title": "Tapu İptali ve Tescil Dava Dilekçesi",
                        "desc": "Muris muvazaası / inançlı işlem / vekalet görevinin kötüye kullanılması nedeniyle tapu iptal ve tescil.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "TAPU KAYDINA İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[... TL (Taşınmazın Harca Esas Değeri)]",
                                    "konu": "Taşınmaz tapu kaydının iptali ile müvekkil adına tescili talebimizdir.",
                                    "aciklama": "1- Dava konusu taşınmaz hukuka aykırı ve muvazaalı devredilmiştir.\\n2- Üçüncü kişilere devrin önlenmesi için tapu kaydına tedbir konulması elzemdir.\\n3- Tapu kaydının iptali ile müvekkil adına tescilini talep ederiz.",
                                    "hukuki_sebepler": "TMK, TBK, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Tapu kayıtları, resmi senetler, mirasçılık belgesi, tanık, bilirkişi, keşif ve sair deliller.",
                                    "sonuc": "Taşınmaz üzerine İHTİYATİ TEDBİR KONULMASINA, tapu kaydının İPTALİ ile tesciline karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "icra_hukuk_dava",
                        "category": "icra_hukuk",
                        "main_cat": "hukuk",
                        "icon": "⚖️",
                        "title": "İcra Hukuk Dava Dilekçesi",
                        "desc": "Memur muamelesini şikayet, icra takibine itirazın kaldırılması ve genel İcra Hukuk davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
                                    "talep": "TAKİBİN DURDURULMASI TALEBİDİR",
                                    "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
                                    "m_sifat": "DAVACI (BORÇLU / ALACAKLI)",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "İcra müdürlüğünün kanuna aykırı işleminin iptali / itirazın kaldırılması talebimizdir.",
                                    "aciklama": "1- İcra müdürlüğü işlemi İİK amir hükümlerine aykırıdır.\\n2- Takibin tedbiren durdurulması ve işlemin iptali gerekmektedir.",
                                    "hukuki_sebepler": "İİK m. 16, 17, 68 vd. ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra takip dosyası ve sair deliller.",
                                    "sonuc": "Davamızın KABULÜ ile işlemin iptaline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "icra_hukuk_cevap",
                        "category": "icra_hukuk",
                        "main_cat": "hukuk",
                        "icon": "📝",
                        "title": "İcra Hukuk Cevap Dilekçesi",
                        "desc": "İcra Hukuk Mahkemesi şikayet ve davalarına karşı cevapların sunulması.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. İCRA HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVALI (ALACAKLI / BORÇLU)",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVACI",
                                    "k_ad": "[Davacı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davacı Vekili]",
                                    "hed": "",
                                    "konu": "Davacının haksız şikayetine/davasına karşı cevaplarımızın sunulmasıdır.",
                                    "aciklama": "1- İcra müdürlüğü işlemi usul ve yasaya tam uygundur.\\n2- Davacının iddiaları takibi sürüncemede bırakmaya matuftur.",
                                    "hukuki_sebepler": "İİK ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra takip dosyası.",
                                    "sonuc": "Haksız davanın REDDİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "icra_hukuk_istinaf",
                        "category": "icra_hukuk",
                        "main_cat": "hukuk",
                        "icon": "⚖️",
                        "title": "İcra Hukuk İstinaf Başvuru Dilekçesi",
                        "desc": "İcra Hukuk Mahkemesi kararına karşı BAM İlgili Hukuk Dairesi'ne istinaf başvurusu.",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. İCRA HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAF EDEN",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Mersin [..]. İcra Hukuk Mahkemesi kararının istinafen KALDIRILMASI talebimizdir.",
                                    "aciklama": "1- Yerel mahkeme kararı İİK hükümlerine aykırıdır.\\n2- İstinaf başvurumuzun kabulü gerekmektedir.",
                                    "hukuki_sebepler": "İİK m. 363 vd., HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Dava ve icra takip dosyası.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile kararın KALDIRILMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "asliye_ceza_savunma",
                        "category": "asliye_ceza",
                        "main_cat": "ceza",
                        "icon": "🛡️",
                        "title": "Asliye Ceza Savunma Dilekçesi",
                        "desc": "Asliye Ceza Mahkemesi esas hakkındaki mütalaaya karşı savunma ve beraat talebi.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "SANIK",
                                    "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KATILAN / MÜŞTEKİ",
                                    "k_ad": "[Katılan/Müşteki Adı Soyadı]",
                                    "k_vekil": "[Katılan Vekili]",
                                    "hed": "",
                                    "konu": "Esas hakkındaki mütalaaya karşı esasa ilişkin savunmalarımızın sunulması ve BERAAT talebimizdir.",
                                    "aciklama": "1- Müvekkil üzerine atılı suçun yasal unsurları oluşmamıştır.\\n2- Mahkumiyete yeterli kesin delil bulunmamaktadır; şüpheden sanık yararlanır ilkesi gereğince beraat verilmelidir.",
                                    "hukuki_sebepler": "TCK, CMK m. 223/2 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Duruşma tutanakları, tanık beyanları, kamera kayıtları ve dosya kapsamı.",
                                    "sonuc": "Müvekkilin BERAATİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "asliye_ceza_istinaf",
                        "category": "asliye_ceza",
                        "main_cat": "ceza",
                        "icon": "⚖️",
                        "title": "Asliye Ceza İstinaf Başvuru Dilekçesi",
                        "desc": "Asliye Ceza Mahkemesi mahkumiyet kararına karşı BAM İlgili Ceza Dairesi'ne istinaf.",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ CEZA DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "SANIK",
                                    "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KATILAN",
                                    "k_ad": "[Katılan Adı Soyadı]",
                                    "k_vekil": "[Katılan Vekili]",
                                    "hed": "",
                                    "konu": "Mersin [..]. Asliye Ceza Mahkemesi'nin usul ve yasaya aykırı mahkûmiyet hükmünün istinafen BOZULMASI ve BERAAT kararı verilmesi talebimizdir.",
                                    "aciklama": "1- Yerel mahkemece eksik inceleme ile usul ve yasaya aykırı karar verilmiştir.\\n2- Suç unsurları oluşmamıştır.",
                                    "hukuki_sebepler": "CMK m. 272 vd., TCK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Ceza dava dosyası.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile kararın BOZULMASINA ve müvekkilin BERAATİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "agir_ceza_savunma",
                        "category": "agir_ceza",
                        "main_cat": "ceza",
                        "icon": "🏛️",
                        "title": "Ağır Ceza Savunma Dilekçesi",
                        "desc": "Ağır Ceza Mahkemesi mütalaaya karşı son savunma, tahliye ve beraat talebi.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. AĞIR CEZA MAHKEMESİNE",
                                    "talep": "TAHLİYE TALEPLİDİR",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "SANIK",
                                    "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Cezaevi Bilgisi / Adres]",
                                    "k_sifat": "KATILAN",
                                    "k_ad": "[Katılan Adı Soyadı]",
                                    "k_vekil": "[Katılan Vekili]",
                                    "hed": "",
                                    "konu": "Esas hakkındaki mütalaaya karşı savunmalarımız ile müvekkilin TAHLİYESİ ve BERAATİ talebimizdir.",
                                    "aciklama": "1- Müvekkile isnat edilen suçun unsurları oluşmamıştır.\\n2- Tutuklulukta geçen süre gözetilerek öncelikle tahliyesine ve neticeten beraatine karar verilmelidir.",
                                    "hukuki_sebepler": "AİHS, Anayasa, TCK, CMK m. 100, 223/2 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Adli tıp raporları, tanık beyanları, HTS kayıtları ve dosya kapsamı.",
                                    "sonuc": "Müvekkilin öncelikle BİHAKKIN TAHLİYESİNE ve neticeten BERAATİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "agir_ceza_tutuklama_itiraz",
                        "category": "agir_ceza",
                        "main_cat": "ceza",
                        "icon": "⛓️",
                        "title": "Ağır Ceza Tutukluluğa İtiraz ve Tahliye Dilekçesi",
                        "desc": "Ağır Ceza tutukluluğun devamı kararına karşı itiraz ve tahliye talebi.",
                        "data": {
                                    "mahkeme": "MERSİN [..+1]. AĞIR CEZA MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. AĞIR CEZA MAHKEMESİNE",
                                    "talep": "TAHLİYE TALEPLİDİR",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "SANIK",
                                    "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Cezaevi Bilgisi / Adres]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Müşteki Adı Soyadı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Mahkemenizin ... tarihli tutukluluğun devamı kararına İTİRAZLARIMIZ ve TAHLİYE talebimizdir.",
                                    "aciklama": "1- Tutuklama tedbir niteliğinde olup deliller toplanmıştır.\\n2- Kaçma şüphesi bulunmamaktadır; adli kontrol tedbirleri yeterlidir.",
                                    "hukuki_sebepler": "CMK m. 100, 101, 109, 267 vd.",
                                    "hukuki_deliller": "Dosya kapsamı, ikametgah belgeleri.",
                                    "sonuc": "İtirazımızın KABULÜ ile tutuklama kararının kaldırılarak müvekkilin TAHLİYESİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "agir_ceza_istinaf",
                        "category": "agir_ceza",
                        "main_cat": "ceza",
                        "icon": "⚖️",
                        "title": "Ağır Ceza İstinaf Başvuru Dilekçesi",
                        "desc": "Ağır Ceza Mahkemesi hükmüne karşı BAM İlgili Ceza Dairesi'ne istinaf başvurusu.",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ CEZA DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. AĞIR CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "SANIK",
                                    "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KATILAN",
                                    "k_ad": "[Katılan Adı Soyadı]",
                                    "k_vekil": "[Katılan Vekili]",
                                    "hed": "",
                                    "konu": "Mersin [..]. Ağır Ceza Mahkemesi kararının istinafen incelenerek BOZULMASI talebimizdir.",
                                    "aciklama": "1- Yerel mahkemece eksik araştırma ile karar verilmiştir.\\n2- Suçun unsurları oluşmamıştır.",
                                    "hukuki_sebepler": "CMK m. 272 vd., TCK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Dava dosyası.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile kararın BOZULMASINA ve müvekkilin BERAATİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "icra_ceza_savunma",
                        "category": "icra_ceza",
                        "main_cat": "ceza",
                        "icon": "🛡️",
                        "title": "İcra Ceza Savunma Dilekçesi",
                        "desc": "Taahhüdü ihlal veya nafaka ödememe şikayetine karşı savunma ve beraat.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. İCRA CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "SANIK (BORÇLU)",
                                    "m_ad": "[Sanık Borçlu Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ (ALACAKLI)",
                                    "k_ad": "[Müşteki Alacaklı Adı Soyadı]",
                                    "k_vekil": "[Müşteki Vekili]",
                                    "hed": "",
                                    "konu": "Müştekinin haksız şikayetine karşı savunmalarımızın sunulması ve BERAAT talebimizdir.",
                                    "aciklama": "1- Şikayete konu taahhüt geçerlilik şartlarını taşımamaktadır.\\n2- Suç unsurları oluşmadığından tazyik hapsi cezası verilemez.",
                                    "hukuki_sebepler": "İİK m. 340, 344, CMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra takip dosyası, ödeme dekontları.",
                                    "sonuc": "Müvekkilin BERAATİNE ve şikayetin REDDİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "icra_ceza_sikayet",
                        "category": "icra_ceza",
                        "main_cat": "ceza",
                        "icon": "⚖️",
                        "title": "İcra Ceza Şikayet Dilekçesi (Taahhüdü İhlal / Nafaka)",
                        "desc": "İİK m. 340 taahhüdü ihlal veya m. 344 nafaka borcunu ödememe şikayeti.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İCRA CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
                                    "m_sifat": "MÜŞTEKİ (ALACAKLI)",
                                    "m_ad": "[Müşteki Alacaklı Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "SANIK (BORÇLU)",
                                    "k_ad": "[Borçlu Sanık Adı Soyadı - T.C. No]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Sanığın taahhüdünü ihlal etmesi / nafaka borcunu ödememesi nedeniyle İİK uyarınca CEZALANDIRILMASI talebidir.",
                                    "aciklama": "1- Sanık borçlu taksitleri ödememiştir.\\n2- İİK m. 340 uyarınca tazyik hapsi ile cezalandırılması gerekmektedir.",
                                    "hukuki_sebepler": "İİK m. 340, 344 ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra takip dosyası ve taahhüt tutanağı.",
                                    "sonuc": "Sanığın TAZYİK HAPSİ İLE CEZALANDIRILMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "icra_ceza_itiraz",
                        "category": "icra_ceza",
                        "main_cat": "ceza",
                        "icon": "📋",
                        "title": "İcra Ceza Kararına İtiraz Dilekçesi",
                        "desc": "İcra Ceza Mahkemesi tazyik hapsi kararına karşı Asliye Ceza Mahkemesi'ne itiraz.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE CEZA MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. İCRA CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas - 2026/... Karar",
                                    "m_sifat": "SANIK (BORÇLU)",
                                    "m_ad": "[Sanık Borçlu Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Müşteki Adı Soyadı]",
                                    "k_vekil": "[Müşteki Vekili]",
                                    "hed": "",
                                    "konu": "İcra Ceza Mahkemesi'nin ... tarihli tazyik hapsi kararına karşı İTİRAZLARIMIZIN sunulmasıdır.",
                                    "aciklama": "1- Yerel mahkemece hatalı değerlendirmeyle tazyik hapsi kararı verilmiştir.\\n2- İtirazımızın incelenerek kararın kaldırılması gerekmektedir.",
                                    "hukuki_sebepler": "İİK m. 353 ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra Ceza dava dosyası.",
                                    "sonuc": "İtirazımızın KABULÜ ile kararın KALDIRILMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "savcilik_suc_duyurusu",
                        "category": "savcilik",
                        "main_cat": "ceza",
                        "icon": "⚖️",
                        "title": "Savcılık Suç Duyurusu (Şikayet) Dilekçesi",
                        "desc": "Cumhuriyet Başsavcılığı'na suç duyurusu ve kamu davası açılması talebi.",
                        "data": {
                                    "mahkeme": "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "MÜŞTEKİ (ŞİKAYET EDEN)",
                                    "m_ad": "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "ŞÜPHELİ / ŞÜPHELİLER",
                                    "k_ad": "[Şüpheli Adı Soyadı - T.C. / Adres]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Şüpheli hakkında soruşturma yürütülerek KAMU DAVASI AÇILMASI talebimizdir.",
                                    "aciklama": "1- Şüpheli şahıs müvekkile karşı suç teşkil eden eylemlerde bulunmuştur.\\n2- Şüphelinin cezalandırılması için kamu davası açılmalıdır.",
                                    "hukuki_sebepler": "TCK, CMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yazışmalar, dekontlar, kamera kayıtları, tanık.",
                                    "sonuc": "Şüpheli hakkında KAMU DAVASI AÇILMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "savcilik_savunma",
                        "category": "savcilik",
                        "main_cat": "ceza",
                        "icon": "🛡️",
                        "title": "Savcılık Savunma Dilekçesi",
                        "desc": "Soruşturma dosyasında şüpheli müdafi olarak savunma sunumu ve KYOK (Takipsizlik) talebi.",
                        "data": {
                                    "mahkeme": "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "Soruşturma No: 2026/...",
                                    "m_sifat": "ŞÜPHELİ",
                                    "m_ad": "[Şüpheli Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Müşteki Adı Soyadı]",
                                    "k_vekil": "[Müşteki Vekili]",
                                    "hed": "",
                                    "konu": "Müştekinin soyut şikayetine karşı savunmalarımızın sunulması ve KOVUŞTURMAYA YER OLMADIĞINA DAİR KARAR (KYOK) verilmesi talebimizdir.",
                                    "aciklama": "1- Şikayet soyut ve asılsız iddialardan ibarettir.\\n2- Suçun unsurları oluşmamıştır.\\n3- CMK m. 172 uyarınca KYOK kararı verilmelidir.",
                                    "hukuki_sebepler": "TCK, CMK m. 170, 172 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Belgeler, yazışmalar, tanık beyanları.",
                                    "sonuc": "Müvekkil hakkında KOVUŞTURMAYA YER OLMADIĞINA DAİR KARAR (KYOK) verilmesini talep ederiz."
                        }
            },
            {
                        "id": "savcilik_kyok_itiraz",
                        "category": "savcilik",
                        "main_cat": "ceza",
                        "icon": "📑",
                        "title": "Savcılık KYOK (Takipsizlik) Kararına İtiraz Dilekçesi",
                        "desc": "Cumhuriyet Başsavcılığı takipsizlik kararına karşı Sulh Ceza Hakimliği'ne itiraz.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ SULH CEZA HÂKİMLİĞİNE\\nGönderilmek Üzere\\nMERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "Soruşturma No: 2026/... - Karar No: 2026/...",
                                    "m_sifat": "MÜŞTEKİ (İTİRAZ EDEN)",
                                    "m_ad": "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "ŞÜPHELİ",
                                    "k_ad": "[Şüpheli Adı Soyadı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Cumhuriyet Başsavcılığı'nın KYOK kararına İTİRAZLARIMIZIN sunulmasıdır.",
                                    "aciklama": "1- Eksik soruşturma ile takipsizlik kararı verilmiştir.\\n2- Kamu davası açılması için yeterli şüphe mevcuttur.",
                                    "hukuki_sebepler": "CMK m. 172, 173 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Soruşturma dosyası.",
                                    "sonuc": "KYOK kararının KALDIRILMASINA ve kamu davası açılmasına karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "savcilik_dijital_materyal_iade",
                        "category": "savcilik",
                        "main_cat": "ceza",
                        "icon": "💻",
                        "title": "Savcılık Dijital Materyallerin İadesi Dilekçesi",
                        "desc": "CMK m. 134 uyarınca el konulan dijital materyallerin ivedi iadesi talebi.",
                        "data": {
                                    "mahkeme": "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "Soruşturma No: 2026/...",
                                    "m_sifat": "ŞÜPHELİ",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Varsa Müşteki]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Müvekkilden el konulan dijital materyallerin CMK m. 134 uyarınca İVEDİ OLARAK İADESİ talebimizdir.",
                                    "aciklama": "1- Dijital cihazların imaj alma/adli bilişim incelemesi tamamlanmıştır.\\n2- CMK m. 134/4 gereğince materyallerin gecikmeksizin iadesi zorunludur.",
                                    "hukuki_sebepler": "CMK m. 131, 134 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Elkoyma tutanağı ve dosya kapsamı.",
                                    "sonuc": "Dijital materyallerin MÜVEKKİLE / VEKİLİNE İVEDİLİKLE İADESİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "yetki_belgesi_sunum",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "📑",
                        "title": "Avukatlık Yetki Belgesi",
                        "desc": "1136 sayılı Avukatlık Kanunu m. 56 uyarınca resmi Yetki Belgesi.",
                        "data": {
                                    "is_yetki_belgesi": true,
                                    "mahkeme": "YETKİ BELGESİ",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "YETKİ BELGESİ VEREN AVUKAT/AVUKATLIK ORTAKLIĞI",
                                    "m_ad": "Av. [Yetki Veren Avukat Adı Soyadı]",
                                    "m_adres": "[Yetki Veren Avukat Bürosu Adresi]",
                                    "m_baro": "Mersin Barosu - [Sicil No]",
                                    "m_vergi": "[Vergi Dairesi ve Sicil No]",
                                    "k_sifat": "YETKİLİ KILINAN AVUKAT",
                                    "k_ad": "Av. Lütfi Serkan SAYOĞLU",
                                    "k_adres": "[Yetkili Kılınan Avukat Adresi]",
                                    "k_baro": "Mersin Barosu - [Sicil No]",
                                    "k_vergi": "[Vergi Dairesi ve Sicil No]",
                                    "asil_ad": "[Vekil Eden Asil / Müvekkil Adı Soyadı - T.C.]",
                                    "asil_adres": "[Vekil Eden Adresi]",
                                    "dayanak_noter": "[Noterlik Adı, Tarih ve Yevmiye No]",
                                    "konu": "",
                                    "aciklama": "Bu yetki belgesi, 1136 sayılı Avukatlık Kanunu’nu değiştiren 4667 sayılı Kanun’un 36. maddesi ile 56. maddesine eklenen hüküm uyarınca, vekaletname yerine geçmek üzere, tarafımdan düzenlenmiştir.",
                                    "hukuki_sebepler": "",
                                    "hukuki_deliller": "",
                                    "sonuc": ""
                        }
            },
            {
                        "id": "vekillikten_cekilme",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "🚪",
                        "title": "Vekillikten Çekilme (İstifa) Dilekçesi",
                        "desc": "Avukatlık Kanunu m. 41 ve HMK m. 82 uyarınca vekillikten istifa bildirimi.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "VEKİLLİKTEN ÇEKİLEN VEKİL",
                                    "m_ad": "Av. Lütfi Serkan SAYOĞLU",
                                    "m_adres": "[Büro Adresi]",
                                    "k_sifat": "ASİL (MÜVEKKİL)",
                                    "k_ad": "[Vekillikten Çekilinen Müvekkil Adı Soyadı - T.C. No]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Görülen lüzum üzerine dosyadaki vekillik görevimizden İSTİFA ETTİĞİMİZİN bildirilmesidir.",
                                    "aciklama": "1- Dosyadaki vekillik görevimizden istifa ediyoruz.\\n2- Durumun asil müvekkile tebliğe çıkarılmasını talep ederiz.",
                                    "hukuki_sebepler": "1136 sayılı Avukatlık Kanunu m. 41, HMK m. 82.",
                                    "hukuki_deliller": "Vekaletname ve dosya kapsamı.",
                                    "sonuc": "Vekillikten çekilme talebimizin kabulü ile kaydımızın silinmesine ve durumun asile tebliğine karar verilmesini talep ederim."
                        }
            },
            {
                        "id": "davadan_feragat",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "🛑",
                        "title": "Davadan Feragat Dilekçesi",
                        "desc": "HMK m. 307 vd. uyarınca davadan feragat bildirimi.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davalı Vekili]",
                                    "hed": "",
                                    "konu": "Davamızdan HMK m. 307 vd. uyarınca FERAGAT ETTİĞİMİZİN bildirilmesidir.",
                                    "aciklama": "1- Vekaletnamemizdeki feragat yetkisine istinaden davadan FERAGAT EDİYORUZ.\\n2- Yargılama gideri ve vekâlet ücreti talebimiz yoktur.",
                                    "hukuki_sebepler": "HMK m. 307 vd.",
                                    "hukuki_deliller": "Vekaletname ve dosya.",
                                    "sonuc": "Davanın FERAGAT NEDENİYLE REDDİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "istinaftan_feragat",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "🛑",
                        "title": "İstinaf Başvurusundan Feragat Dilekçesi",
                        "desc": "HMK m. 349 uyarınca istinaf kanun yolundan feragat ve hükmün kesinleştirilmesi.",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAFTAN FERAGAT EDEN",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Mahkemenizin kararına karşı İSTİNAF KANUN YOLUNA BAŞVURU HAKKIMIZDAN FERAGAT ETTİĞİMİZİN bildirilmesidir.",
                                    "aciklama": "1- Karara karşı istinaf başvuru hakkımızdan gayrikabili rücu feragat ediyoruz.\\n2- Kararın kesinleştirilmesini talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 349 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Vekaletname ve mahkeme ilamı.",
                                    "sonuc": "İstinaftan feragat talebimizin KABULÜ ile kararın KESİNLEŞTİRİLMESİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "istinafa_cevap",
                        "category": "asliye_hukuk",
                        "main_cat": "hukuk",
                        "icon": "💬",
                        "title": "İstinaf Dilekçesine Cevap Dilekçesi",
                        "desc": "HMK m. 347 uyarınca karşı tarafın istinaf başvurusuna esastan ret cevabı.",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAFA CEVAP VEREN",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "İSTİNAF EDEN (KARŞI TARAF)",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Karşı tarafın usul ve yasaya aykırı istinaf başvurusuna karşı cevaplarımızın sunulmasıdır.",
                                    "aciklama": "1- Yerel mahkeme kararı hukuka uygundur.\\n2- Karşı tarafın istinaf başvurusunun esastan reddi gerekmektedir.",
                                    "hukuki_sebepler": "HMK m. 347, 353/1-b-1 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yerel mahkeme dava dosyası.",
                                    "sonuc": "Karşı tarafın İSTİNAF BAŞVURUSUNUN ESASTAN REDDİNE, yerel mahkeme kararının ONANMASINA karar verilmesini talep ederiz."
                        }
            }
];

        // Varsayılan Sık Kullanılanlar
        const DEFAULT_FAVORITES = ["asliye_hukuk_dava", "asliye_ceza_savunma", "ozel_alacak_dava", "savcilik_savunma"];
        
        function getFavorites() {
            try {
                const favs = localStorage.getItem("dilekce_favorites");
                return favs ? JSON.parse(favs) : DEFAULT_FAVORITES;
            } catch (e) {
                return DEFAULT_FAVORITES;
            }
        }

        function saveFavorites(favs) {
            try {
                localStorage.setItem("dilekce_favorites", JSON.stringify(favs));
            } catch (e) {}
        }

        function toggleFavorite(tplId, event) {
            if (event) event.stopPropagation();
            let favs = getFavorites();
            if (favs.includes(tplId)) {
                favs = favs.filter(id => id !== tplId);
            } else {
                favs.push(tplId);
            }
            saveFavorites(favs);
            renderFavorites();
            renderTemplates();
            
        }

        function renderFavorites() {
            const favGrid = document.getElementById("favoritesGrid");
            const favs = getFavorites();
            favGrid.innerHTML = "";

            const favTemplates = favs.map(id => TEMPLATES.find(t => t.id === id)).filter(Boolean);

            if (favTemplates.length === 0) {
                favGrid.innerHTML = `
                    <div class="col-span-full py-4 text-center text-slate-400 text-xs font-medium">
                        Henüz sık kullanılan şablon eklenmedi. Kartların sağ üstündeki ⭐ ikonuna tıklayarak ekleyebilirsiniz.
                    </div>
                `;
                return;
            }

            favTemplates.forEach(t => {
                const card = document.createElement("div");
                card.className = "bg-white rounded-xl border border-blue-200/80 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between relative group";
                card.innerHTML = `
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                            <div class="flex items-center gap-2">
                                <span class="text-xl">${t.icon}</span>
                                <h3 class="font-bold text-slate-900 text-xs leading-snug line-clamp-1">${t.title}</h3>
                            </div>
                            <button onclick="toggleFavorite('${t.id}', event)" class="text-amber-400 hover:text-amber-500 text-sm" title="Favorilerden Çıkar">★</button>
                        </div>
                        <p class="text-[11px] text-slate-500 line-clamp-2 leading-relaxed mb-3">${t.desc}</p>
                    </div>
                    <div class="pt-2 border-t border-slate-100 flex items-center gap-2">
                        <button onclick="openDirect('${t.id}')" class="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm transition flex items-center justify-center gap-1" title="Şablonu doğrudan UYAP Editörde açar">
                            ⚡️ Aç
                        </button>
                        <button onclick="openFormEditor('${t.id}')" class="py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition" title="Formla Düzenle">
                            ✏️ Düzenle
                        </button>
                    </div>
                `;
                favGrid.appendChild(card);
            });
        }

        let currentMainCategory = "all";
        let currentCategory = "all";

        function setMainCategory(mcat) {
            currentMainCategory = mcat;
            currentCategory = "all";
            document.querySelectorAll(".mcat-btn").forEach(btn => {
                btn.classList.remove("bg-blue-600", "text-white", "shadow-sm");
                btn.classList.add("bg-slate-100", "text-slate-700");
            });
            const activeBtn = document.getElementById("mcat_" + mcat);
            if (activeBtn) {
                activeBtn.classList.remove("bg-slate-100", "text-slate-700");
                activeBtn.classList.add("bg-blue-600", "text-white", "shadow-sm");
            }
            // Update subcategory buttons
            updateCategoryButtons();
            renderTemplates();
        }

        function setCategory(cat) {
            currentCategory = cat;
            updateCategoryButtons();
            renderTemplates();
        }

        function updateCategoryButtons() {
            document.querySelectorAll(".cat-btn").forEach(btn => {
                btn.classList.remove("bg-slate-800", "text-white");
                btn.classList.add("bg-slate-100", "text-slate-600");
            });
            const activeBtn = document.getElementById("cat_" + currentCategory);
            if (activeBtn) {
                activeBtn.classList.remove("bg-slate-100", "text-slate-600");
                activeBtn.classList.add("bg-slate-800", "text-white");
            }
        }

        function renderTemplates() {
            const grid = document.getElementById("templateGrid");
            const query = document.getElementById("searchInput").value.toLowerCase().trim();
            const favs = getFavorites();
            grid.innerHTML = "";

            const filtered = TEMPLATES.filter(t => {
                // If search query is active, search across ALL categories (global search)
                let matchCat = true;
                if (!query) {
                    if (currentCategory !== "all") {
                        matchCat = (t.category === currentCategory);
                    } else if (currentMainCategory !== "all") {
                        matchCat = (t.main_cat === currentMainCategory || t.category === currentMainCategory);
                    }
                }
                const matchQuery = (!query || t.title.toLowerCase().includes(query) || t.desc.toLowerCase().includes(query));
                return matchCat && matchQuery;
            });

            if (filtered.length === 0) {
                grid.innerHTML = `
                    <div class="col-span-full py-12 text-center text-slate-400">
                        <span class="text-4xl block mb-2">🔍</span>
                        <p class="text-sm font-semibold">Aradığınız kriterlere uygun şablon bulunamadı.</p>
                    </div>
                `;
                return;
            }

            filtered.forEach(t => {
                const isFav = favs.includes(t.id);
                const card = document.createElement("div");
                card.className = "bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between relative";
                card.innerHTML = `
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                            <div class="flex items-center gap-3">
                                <span class="text-2xl">${t.icon}</span>
                                <h3 class="font-bold text-slate-900 text-sm leading-snug">${t.title}</h3>
                            </div>
                            <button onclick="toggleFavorite('${t.id}', event)" class="${isFav ? 'text-amber-400' : 'text-slate-300 hover:text-amber-400'} text-lg transition" title="${isFav ? 'Favorilerden Çıkar' : 'Sık Kullanılanlara Ekle'}">
                                ${isFav ? '★' : '☆'}
                            </button>
                        </div>
                        <p class="text-xs text-slate-500 leading-relaxed mb-4">${t.desc}</p>
                    </div>
                    <div class="pt-3 border-t border-slate-100 flex items-center gap-2">
                        <button onclick="openDirect('${t.id}')" class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center justify-center gap-1.5" title="Şablonu doğrudan UYAP Editörde açar">
                            ⚡️ Doğrudan Aç
                        </button>
                        <button onclick="openFormEditor('${t.id}')" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition flex items-center justify-center gap-1" title="Bilgileri form ile doldurup oluştur">
                            ✏️ Formla Düzenle
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function setCategory(cat) {
            currentCategory = cat;
            document.querySelectorAll(".cat-btn").forEach(btn => {
                btn.classList.remove("bg-blue-600", "text-white", "shadow-sm");
                btn.classList.add("bg-slate-100", "text-slate-600");
            });
            const activeBtn = document.getElementById("cat_" + cat);
            if (activeBtn) {
                activeBtn.classList.remove("bg-slate-100", "text-slate-600");
                activeBtn.classList.add("bg-blue-600", "text-white", "shadow-sm");
            }
            renderTemplates();
            
        }

        function filterTemplates() {
            renderTemplates();
            
        }

        async function openDirect(tplId) {
            const t = TEMPLATES.find(x => x.id === tplId);
            if (!t) return;

            showToast(`⏳ ${t.title} UYAP'ta açılıyor...`, "info");
            
            const formattedData = formatDataForCity(t.data);
            const payload = {
                ...formattedData,
                vekil: getLawyerFullText(),
                avukat_imza: getLawyerSignatureName(),
                open_after: true
            };

            try {
                const res = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const r = await res.json();
                if (r.success) {
                    showToast(`✅ ${t.title} UYAP Doküman Editörü'nde açıldı!`, "success");
                } else {
                    showToast(`❌ Hata: ${r.message}`, "error");
                }
            } catch (err) {
                showToast(`❌ Bağlantı hatası: ${err}`, "error");
            }
        }

        function openFormEditor(tplId) {
            const t = TEMPLATES.find(x => x.id === tplId);
            if (!t) return;

            const fd = formatDataForCity(t.data);
            document.getElementById("formTitleBadge").textContent = `${t.icon} ${t.title}`;
            document.getElementById("mahkeme").value = fd.mahkeme || "";
            document.getElementById("talep").value = fd.talep || "";
            document.getElementById("dosya").value = fd.dosya || "";
            document.getElementById("m_sifat").value = fd.m_sifat || "";
            document.getElementById("m_ad").value = fd.m_ad || "";
            document.getElementById("m_adres").value = fd.m_adres || "";
            document.getElementById("vekil").value = getLawyerFullText();
            document.getElementById("k_sifat").value = fd.k_sifat || "";
            document.getElementById("k_ad").value = fd.k_ad || "";
            document.getElementById("k_vekil").value = fd.k_vekil || "";
            document.getElementById("hed").value = fd.hed || "";
            document.getElementById("konu").value = fd.konu || "";
            document.getElementById("aciklama").value = fd.aciklama || "";
            document.getElementById("hukuki_sebepler").value = fd.hukuki_sebepler || SEBEPLER_DEFAULT;
            document.getElementById("hukuki_deliller").value = fd.hukuki_deliller || DELILLER_DEFAULT;

            document.getElementById("galleryView").classList.add("hidden");
            document.getElementById("formView").classList.remove("hidden");
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function showGalleryView() {
            document.getElementById("formView").classList.add("hidden");
            document.getElementById("galleryView").classList.remove("hidden");
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        async function generateFromForm(openAfter) {
            const vekilText = document.getElementById("vekil").value.trim() || getLawyerFullText();
            const payload = {
                mahkeme: document.getElementById("mahkeme").value.trim(),
                talep: document.getElementById("talep").value.trim(),
                dosya: document.getElementById("dosya").value.trim(),
                m_sifat: document.getElementById("m_sifat").value.trim(),
                m_ad: document.getElementById("m_ad").value.trim(),
                m_adres: document.getElementById("m_adres").value.trim(),
                vekil: vekilText,
                avukat_imza: getLawyerSignatureName(),
                k_sifat: document.getElementById("k_sifat").value.trim(),
                k_ad: document.getElementById("k_ad").value.trim(),
                k_vekil: document.getElementById("k_vekil").value.trim(),
                hed: document.getElementById("hed").value.trim(),
                konu: document.getElementById("konu").value.trim(),
                aciklama: document.getElementById("aciklama").value.trim(),
                hukuki_sebepler: document.getElementById("hukuki_sebepler").value.trim(),
                hukuki_deliller: document.getElementById("hukuki_deliller").value.trim(),
                open_after: openAfter
            };

            if (!payload.mahkeme) {
                showToast("Lütfen Mahkeme Başlığını giriniz!", "error");
                return;
            }

            try {
                const res = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const r = await res.json();
                if (r.success) {
                    showToast(r.message, "success");
                } else {
                    showToast(r.message || "Hata oluştu", "error");
                }
            } catch (err) {
                showToast(`Bağlantı hatası: ${err}`, "error");
            }
        }

        function showToast(msg, type) {
            const toast = document.getElementById("toast");
            toast.classList.remove("hidden", "bg-slate-900", "bg-emerald-600", "bg-rose-600", "text-white");
            if (type === "success") {
                toast.classList.add("bg-emerald-600", "text-white");
            } else if (type === "error") {
                toast.classList.add("bg-rose-600", "text-white");
            } else {
                toast.classList.add("bg-slate-900", "text-white");
            }
            toast.textContent = msg;
            toast.classList.remove("hidden");
            setTimeout(() => {
                toast.classList.add("hidden");
            }, 4000);
        }

        window.onload = function() {
            updateLawyerDisplay();
            renderFavorites();
            renderTemplates();
            
        };
    </script>
</body>
</html>
"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        if self.path == "/generate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            mahkeme = data.get("mahkeme", "")
            talep = data.get("talep", "")
            dosya = data.get("dosya", "")
            m_sifat = data.get("m_sifat", "")
            m_ad = data.get("m_ad", "")
            m_adres = data.get("m_adres", "")
            vekil = data.get("vekil", "Av. Lütfi Serkan SAYOĞLU - UETS [16153-51280-36854]")
            avukat_imza = data.get("avukat_imza", "Av. Lütfi Serkan SAYOĞLU")
            k_sifat = data.get("k_sifat", "")
            k_ad = data.get("k_ad", "")
            k_vekil = data.get("k_vekil", "")
            hed = data.get("hed", "")
            konu = data.get("konu", "")
            aciklama = data.get("aciklama", "")
            hukuki_sebepler = data.get("hukuki_sebepler", "")
            hukuki_deliller = data.get("hukuki_deliller", "")
            sonuc = data.get("sonuc", "Yukarıda arz ve izah olunan nedenlerle; taleplerimizin kabulü ile yargılama giderleri ve vekâlet ücretinin karşı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz.")
            open_after = data.get("open_after", True)
            
            is_yetki_belgesi = data.get("is_yetki_belgesi", False) or (mahkeme.strip() == "YETKİ BELGESİ")
            
            if is_yetki_belgesi:
                tab_setting = "220:0:0,235:0:0"
                paragraphs = []
                
                # Başlık (Ortalı, Kalın)
                paragraphs.append((1, 0, "20.0", None, None, [("YETKİ BELGESİ\n", True, False, False)]))
                
                # 1. YETKİ BELGESİ VEREN AVUKAT/AVUKATLIK ORTAKLIĞI
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("YETKİ BELGESİ VEREN AVUKAT/\nAVUKATLIK ORTAKLIĞI", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{m_ad}\n" if m_ad else "\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("Baro ve Sicil No", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('m_baro', 'Mersin Barosu - [Sicil No]')}\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("Vergi Dairesi ve Sicil No", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('m_vergi', '[Vergi Dairesi ve Sicil No]')}\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "14.17", None, tab_setting, [
                    ("Adres", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{m_adres if m_adres else '[Adres]'}\n", False, False, False)
                ]))
                
                # 2. YETKİLİ KILINAN AVUKAT
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("YETKİLİ KILINAN AVUKAT", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{k_ad}\n" if k_ad else "\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("Baro ve Sicil No", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('k_baro', 'Mersin Barosu - [Sicil No]')}\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("Vergi Dairesi ve Sicil No", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('k_vergi', '[Vergi Dairesi ve Sicil No]')}\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "14.17", None, tab_setting, [
                    ("Adres", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('k_adres', '[Adres]')}\n", False, False, False)
                ]))
                
                # 3. VEKİL EDEN
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("VEKİL EDEN", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    ("\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("Ad ve Soyadı", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('asil_ad', '[Asil Ad ve Soyadı]')}\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("Adres", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('asil_adres', '[Adres]')}\n", False, False, False)
                ]))
                paragraphs.append((0, "0.0", "14.17", None, tab_setting, [
                    ("Dayanak Vekaletname/Vekaletnameler\nNoter Tarih ve Yevmiye No", False, False, False),
                    ("\t:\t", False, False, False),
                    (f"{data.get('dayanak_noter', '[Noterlik, Tarih ve Yevmiye No]')}\n", False, False, False)
                ]))
                
                # 4. YETKİ BELGESİNİN KAPSAMI
                paragraphs.append((0, "0.0", "14.17", None, tab_setting, [
                    ("YETKİ BELGESİNİN KAPSAMI", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    ("\n", False, False, False)
                ]))
                
                kapsam_text = aciklama if aciklama else "Bu yetki belgesi, 1136 sayılı Avukatlık Kanunu’nu değiştiren 4667 sayılı Kanun’un 36. maddesi ile 56. maddesine eklenen hüküm uyarınca, vekaletname yerine geçmek üzere, tarafımdan düzenlenmiştir."
                paragraphs.append((3, 0, "40.0", None, None, [(f"{kapsam_text}\n", False, False, False)]))
                
                # Tarih ve İmza Bloğu (Görseldeki gibi sağa yaslı noktalı tarih ve sola yaslı alt imza)
                paragraphs.append((2, 0, "20.0", None, None, [("...... / ...... / ......\n", False, False, False)]))
                paragraphs.append((0, 0, "0.0", None, None, [("Avukat/Avukat Ortaklığı\n", False, False, False)]))
                
                desktop_dir = os.path.expanduser("~/Desktop")
                out_path = os.path.join(desktop_dir, "Yetki Belgesi.udf")
                
                try:
                    build_udf(paragraphs, out_path)
                    if open_after:
                        subprocess.Popen(["open", "-a", "Uyap Doküman Editörü", out_path])
                        msg = "Yetki Belgesi UDF oluşturuldu ve UYAP'ta açıldı: Yetki Belgesi.udf"
                    else:
                        msg = "Yetki Belgesi Masaüstüne kaydedildi: Yetki Belgesi.udf"
                    response = {"success": True, "message": msg, "path": out_path}
                except Exception as e:
                    response = {"success": False, "message": f"Hata: {str(e)}"}
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return
            
            tab_setting = "140:0:0,155:0:0"
            paragraphs = []
            
            # Mahkeme Başlığı (Ortalı, Kalın)
            for line in mahkeme.split("\n"):
                if line.strip():
                    paragraphs.append((1, 0, "8.5", None, None, [(f"{line.strip()}\n", True, False, False)]))
            paragraphs[-1] = (1, 0, "14.17", None, None, paragraphs[-1][5])
            
            # Özel Talep (Sağa Yaslı, Kalın)
            if talep:
                paragraphs.append((2, 0, "14.17", None, None, [(f"{talep}\n", True, False, False)]))
                
            # Dosya No
            if dosya:
                dosya_etiket = "İCRA DOSYA NO" if ("İcra" in dosya or "İcra" in mahkeme) else "DOSYA NO"
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    (dosya_etiket, True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{dosya}\n", False, False, False)
                ]))
                
            # Müvekkil
            if m_sifat and m_ad:
                paragraphs.append((0, "0.0", "0.0" if m_adres else "5.0", None, tab_setting, [
                    (m_sifat, True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{m_ad}\n", True, False, False)
                ]))
                if m_adres:
                    paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                        ("", False, False, False),
                        ("\t\t", False, False, False),
                        (f"{m_adres}\n", False, True, False)
                    ]))
                    
            # Vekili
            if vekil:
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("VEKİLİ", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{vekil}\n", False, False, False)
                ]))
                
            # Karşı Taraf
            if k_sifat and k_ad:
                paragraphs.append((0, "0.0", "0.0" if k_vekil else "5.0", None, tab_setting, [
                    (k_sifat, True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{k_ad}\n", False, False, False)
                ]))
                if k_vekil:
                    paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                        ("VEKİLİ", True, False, True),
                        ("\t", False, False, True),
                        (":\t", False, False, False),
                        (f"{k_vekil}\n", False, False, False)
                    ]))
                    
            # Harca Esas Değer (H.E.D.)
            if hed:
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("DAVA DEĞERİ (H.E.D.)", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{hed}\n", False, False, False)
                ]))

            # Konu (Satır Aralığı 1.0)
            if konu:
                paragraphs.append((0, "0.0", "14.17", None, tab_setting, [
                    ("KONU", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{konu}\n", False, False, False)
                ]))
                
            # Açıklamalar Başlığı
            paragraphs.append((0, 0, "8.5", None, None, [
                ("AÇIKLAMALAR:", True, False, True),
                ("\n", False, False, False)
            ]))
            
            # Açıklama Maddeleri
            if aciklama:
                for line in aciklama.split("\n"):
                    if line.strip():
                        paragraphs.append((3, 0, "8.5", "35.43", None, [(f"{line.strip()}\n", False, False, False)]))
            else:
                paragraphs.append((3, 0, "8.5", "35.43", None, [("1- [Açıklamalarınızı buraya yazabilirsiniz.]\n", False, False, False)]))
                
            # Hukuki Sebepler (Varsa)
            if hukuki_sebepler:
                paragraphs.append((0, "0.0", "5.0", None, tab_setting, [
                    ("HUKUKİ SEBEPLER", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{hukuki_sebepler}\n", False, False, False)
                ]))

            # Hukuki Deliller (Varsa)
            if hukuki_deliller:
                paragraphs.append((0, "0.0", "14.17", None, tab_setting, [
                    ("HUKUKİ DELİLLER", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{hukuki_deliller}\n", False, False, False)
                ]))

            # Sonuç Başlığı
            paragraphs.append((0, 0, "8.5", None, None, [
                ("SONUÇ VE İSTEM:", True, False, True),
                ("\n", False, False, False)
            ]))
            
            # Sonuç Metni
            date_str = datetime.now().strftime("%d.%m.%Y")
            paragraphs.append((3, 0, "14.17", "35.43", None, [
                (f"{sonuc} {date_str}\n", False, False, False)
            ]))
            
            # İmza Bloğu
            imza_unvan = f"{m_sifat.title()} Vekili" if m_sifat else "Vekil"
            paragraphs.append((2, 0, "0.0", None, None, [(f"{imza_unvan}\n", True, False, False)]))
            paragraphs.append((2, 0, "0.0", None, None, [(f"{avukat_imza}\n", True, False, False)]))
            paragraphs.append((2, 0, "0.0", None, None, [("(e-imzalıdır)\n", False, True, False)]))
            
            desktop_dir = os.path.expanduser("~/Desktop")
            clean_title = mahkeme.split("MAHKEMESİ")[0].replace("\n", " ").strip() if "MAHKEMESİ" in mahkeme else "Dilekce"
            safe_filename = f"{clean_title} - {m_sifat}.udf"
            safe_filename = "".join(c for c in safe_filename if c not in r'\/:*?"<>|')
            
            out_path = os.path.join(desktop_dir, safe_filename)
            
            try:
                build_udf(paragraphs, out_path)
                if open_after:
                    subprocess.Popen(["open", "-a", "Uyap Doküman Editörü", out_path])
                    msg = f"Dilekçe UDF oluşturuldu ve UYAP'ta açıldı: {safe_filename}"
                else:
                    msg = f"Dilekçe Masaüstüne kaydedildi: {safe_filename}"
                response = {"success": True, "message": msg, "path": out_path}
            except Exception as e:
                response = {"success": False, "message": f"Hata: {str(e)}"}
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

def run():
    import threading
    threading.Thread(target=check_for_updates_silently, daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    no_browser = "--no-browser" in sys.argv
    try:
        server = socketserver.TCPServer(("127.0.0.1", PORT), RequestHandler)
    except OSError:
        if not no_browser:
            webbrowser.open(f"http://127.0.0.1:{PORT}")
        return
        
    if not no_browser:
        webbrowser.open(f"http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == "__main__":
    run()
