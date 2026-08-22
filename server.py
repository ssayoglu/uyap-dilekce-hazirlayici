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

CURRENT_VERSION = "1.0.0"
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
                <button onclick="openLawyerModal()" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-900/60 hover:bg-blue-800 text-blue-300 border border-blue-700 transition shadow-sm" title="Avukat bilgilerini değiştirmek için tıklayın">
                    <span id="activeLawyerHeader">Av. Lütfi Serkan SAYOĞLU</span>
                    <span class="text-[10px] bg-blue-700/50 px-1.5 py-0.5 rounded text-blue-200">⚙️ Değiştir</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Avukat Profili Modal -->
    <div id="lawyerModal" class="fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 class="font-bold text-slate-900 text-base flex items-center gap-2">
                    <span>👤</span> Avukat & Vekil Bilgileri
                </h3>
                <button onclick="closeLawyerModal()" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
            </div>
            <p class="text-xs text-slate-500 leading-relaxed">
                Buraya gireceğiniz bilgiler tüm dilekçelerde <strong>VEKİLİ</strong> alanında ve imza bloğunda otomatik olarak kullanılacaktır.
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
            <div class="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
                <button onclick="setCategory('all')" id="cat_all" class="cat-btn px-3.5 py-1.5 rounded-xl text-xs font-bold bg-blue-600 text-white shadow-sm transition">Tümü</button>
                <button onclick="setCategory('hukuk_dava')" id="cat_hukuk_dava" class="cat-btn px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Dava Dilekçeleri</button>
                <button onclick="setCategory('hukuk_talep')" id="cat_hukuk_talep" class="cat-btn px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Cevap / Delil / İstinaf</button>
                <button onclick="setCategory('icra')" id="cat_icra" class="cat-btn px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">İcra & İflas</button>
                <button onclick="setCategory('ceza')" id="cat_ceza" class="cat-btn px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">Ceza & Savcılık</button>
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

        // Avukat Profili Yönetimi
        const DEFAULT_LAWYER = {
            name: "Av. Lütfi Serkan SAYOĞLU",
            extra: "UETS [16153-51280-36854]"
        };

        function getLawyerProfile() {
            try {
                const lp = localStorage.getItem("dilekce_lawyer_profile");
                return lp ? JSON.parse(lp) : DEFAULT_LAWYER;
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

        function updateLawyerDisplay() {
            const lp = getLawyerProfile();
            document.getElementById("activeLawyerHeader").textContent = lp.name;
            document.getElementById("footerLawyer").textContent = lp.name;
            const vekilInput = document.getElementById("vekil");
            if (vekilInput) {
                vekilInput.value = getLawyerFullText();
            }
        }

        function openLawyerModal() {
            const lp = getLawyerProfile();
            document.getElementById("modalLawyerName").value = lp.name;
            document.getElementById("modalLawyerExtra").value = lp.extra || "";
            document.getElementById("lawyerModal").classList.remove("hidden");
        }

        function closeLawyerModal() {
            document.getElementById("lawyerModal").classList.add("hidden");
        }

        function saveLawyerProfile() {
            const name = document.getElementById("modalLawyerName").value.trim() || DEFAULT_LAWYER.name;
            const extra = document.getElementById("modalLawyerExtra").value.trim();
            const lp = { name, extra };
            localStorage.setItem("dilekce_lawyer_profile", JSON.stringify(lp));
            updateLawyerDisplay();
            closeLawyerModal();
            showToast(`✅ Avukat bilgileri '${name}' olarak güncellendi!`, "success");
        }

        const TEMPLATES = [
            // --- HUKUK DAVA DİLEKÇELERİ ---
            {
                id: "alacak_dava",
                category: "hukuk_dava",
                icon: "📄",
                title: "Dava Dilekçesi (Alacak & Tazminat)",
                desc: "H.E.D., tanık, bilirkişi, yemin delilleri ve ihtiyati tedbir talepli genel dava dilekçesi.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                    talep: "İHTİYATİ TEDBİR TALEPLİDİR",
                    dosya: "",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Müvekkil Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı - T.C. / Vergi No]",
                    k_vekil: "[Varsa Davalı Vekili]",
                    hed: "10.000,00 TL (Fazlaya ilişkin haklarımız saklı kalmak kaydıyla)",
                    konu: "Müvekkilin ödenmeyen alacağının ve ticari/maddi tazminatın faiziyle birlikte tahsili talebidir.",
                    aciklama: "1- Müvekkil ile davalı taraf arasındaki ticari/hukuki ilişkiden doğan alacak vadesinde ödenmemiştir.\\n2- Davalıya gönderilen ihtarlara rağmen borç ifa edilmemiş olup dava açma zorunluluğu hasıl olmuştur.\\n3- Alacağın tahsilinin temini için davalının malvarlığı üzerine ihtiyati tedbir konulmasını talep ederiz.",
                    hukuki_sebepler: "TBK, HMK, TTK ve ilgili mevzuat.",
                    hukuki_deliller: "Sözleşme, faturalar, banka kayıtları, yazışmalar, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Yukarıda arz ve izah edilen nedenlerle; fazlaya ilişkin haklarımız saklı kalmak kaydıyla DAVAMIZIN KABULÜNE, alacağımızın temerrüt tarihinden itibaren işleyecek faiziyle birlikte tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini saygıyla vekâleten arz ve talep ederiz."
                }
            },
            {
                id: "itirazin_iptali",
                category: "hukuk_dava",
                icon: "⚖️",
                title: "İtirazın İptali Dava Dilekçesi",
                desc: "İcra inkar tazminatı talepli, takibe itirazın iptali ve takibin devamı davası.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "Mersin ... İcra Dairesi - 2026/... E.",
                    m_sifat: "DAVACI (ALACAKLI)",
                    m_ad: "[Davacı Alacaklı Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI (BORÇLU)",
                    k_ad: "[Davalı Borçlu Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Davalı Vekili]",
                    hed: "[... TL (İtiraz Edilen Takip Tutarı)]",
                    konu: "Mersin ... İcra Dairesi'nin 2026/... E. sayılı takibine yapılan haksız itirazın iptali ile takibin devamı ve %20 icra inkâr tazminatı talebidir.",
                    aciklama: "1- Davalı aleyhine başlatılan icra takibine davalı borçlu kötü niyetli ve haksız olarak itiraz etmiştir.\\n2- Borç likit ve muayyen olup davalının itirazı yalnızca takibi sürüncemede bırakma amaçlıdır.\\n3- İİK m. 67 uyarınca itirazın iptali ile takibin devamına karar verilmelidir.",
                    hukuki_sebepler: "İİK m. 67, HMK, TBK, TTK ve ilgili mevzuat.",
                    hukuki_deliller: "İcra takip dosyası, faturalar, hesap özetleri, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Davalının haksız itirazının İPTALİNE, takibin DEVAMINA, alacağın %20'sinden aşağı olmamak üzere İCRA İNKÂR TAZMİNATININ davalıdan tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "kira_tahliye",
                category: "hukuk_dava",
                icon: "🏠",
                title: "Kira Tahliye ve Alacak Dava Dilekçesi",
                desc: "Kiralananın tahliyesi (tahliye taahhüdü / temerrüt) ve kira alacağı davası.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ SULH HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "",
                    m_sifat: "DAVACI (KİRAYA VEREN)",
                    m_ad: "[Kiraya Veren Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "DAVALI (KİRACI)",
                    k_ad: "[Kiracı Adı Soyadı - T.C. No]",
                    k_vekil: "[Varsa Kiracı Vekili]",
                    hed: "[... TL (Bir Yıllık Kira Bedeli)]",
                    konu: "Taşınmazın tahliyesi ile ödenmeyen kira bedellerinin yasal faiziyle tahsili talebidir.",
                    aciklama: "1- Davalı, müvekkile ait taşınmazda ... tarihli kira sözleşmesi uyarınca kiracı olarak oturmaktadır.\\n2- Davalı taraf vadesi gelen kira bedellerini ödememiş / tahliye taahhüdüne uymamıştır.\\n3- TBK hükümleri uyarınca taşınmazın tahliyesini talep etme zorunluluğu doğmuştur.",
                    hukuki_sebepler: "TBK m. 315, 352 vd., HMK, İİK ve ilgili mevzuat.",
                    hukuki_deliller: "Kira sözleşmesi, tahliye taahhütnamesi, banka dekontları, ihtarname, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Davalının kiralanan taşınmazdan TAHLİYESİNE, ödenmeyen kira bedellerinin faiziyle tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "kira_tespit",
                category: "hukuk_dava",
                icon: "📈",
                title: "Kira Bedelinin Tespiti (Artırım) Dava Dilekçesi",
                desc: "5 yılı aşan kira ilişkilerinde emsal rayiçlere göre kira bedelinin tespiti davası.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ SULH HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "",
                    m_sifat: "DAVACI (KİRAYA VEREN)",
                    m_ad: "[Kiraya Veren Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "DAVALI (KİRACI)",
                    k_ad: "[Kiracı Adı Soyadı - T.C. No]",
                    k_vekil: "[Varsa Kiracı Vekili]",
                    hed: "[... TL (Aylık Artırım Farkının Yıllık Tutarı)]",
                    konu: "Kira bedelinin emsal rayiç ve hakkaniyete uygun olarak aylık ... TL olarak tespit edilmesi talebidir.",
                    aciklama: "1- Davalı ile müvekkil arasındaki kira ilişkisi 5 yıldan uzun süredir devam etmektedir.\\n2- Mevcut kira bedeli ekonomik koşullar ve çevre emsal rayiçlerin çok altında kalmıştır.\\n3- TBK m. 344/3 uyarınca yeni dönem kira bedelinin tespiti gerekmektedir.",
                    hukuki_sebepler: "TBK m. 344 vd., HMK ve ilgili mevzuat.",
                    hukuki_deliller: "Kira sözleşmesi, emsal kira sözleşmeleri, keşif, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Yeni kira döneminden itibaren geçerli olmak üzere kira bedelinin AYLIK ... TL OLARAK TESPİTİNE, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "bosanma_dava",
                category: "hukuk_dava",
                icon: "💔",
                title: "Boşanma Dava Dilekçesi (Çekişmeli)",
                desc: "Evlilik birliğinin temelinden sarsılması, nafaka, velayet ve maddi/manevi tazminat talepli.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ AİLE MAHKEMESİNE",
                    talep: "TEDBİR NAFAKASI VE İHTİYATİ TEDBİR TALEPLİDİR",
                    dosya: "",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Müvekkil Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Eş Adı Soyadı - T.C. No]",
                    k_vekil: "[Varsa Davalı Vekili]",
                    hed: "[... TL Maddi - ... TL Manevi Tazminat]",
                    konu: "Evlilik birliğinin temelinden sarsılması nedeniyle BOŞANMA, velayet, nafaka ve tazminat talebimizdir.",
                    aciklama: "1- Taraflar ... tarihinde evlenmiş olup müşterek ... çocukları bulunmaktadır.\\n2- Davalı eşin kusurlu tutum ve davranışları sebebiyle evlilik birliği onarılamaz şekilde temelinden sarsılmıştır.\\n3- TMK m. 166 uyarınca boşanma ve ferilerine hükmedilmesini talep ederiz.",
                    hukuki_sebepler: "TMK m. 166, 169, 174, 175, 182 vd., HMK ve ilgili mevzuat.",
                    hukuki_deliller: "Aile nüfus kaydı, mali ve sosyal durum araştırması, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Tarafların BOŞANMALARINA, müşterek çocuğun velayetinin müvekkile verilmesine, aylık ... TL tedbir/iştirak nafakasına, müvekkil lehine ... TL maddi ve ... TL manevi tazminata hükmedilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "iscilik_alacak",
                category: "hukuk_dava",
                icon: "👷",
                title: "İşçilik Alacakları ve Kıdem Tazminatı Dava Dilekçesi",
                desc: "Kıdem, ihbar tazminatı, fazla mesai, UBGT ve yıllık izin alacakları davası.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ İŞ MAHKEMESİNE",
                    talep: "",
                    dosya: "Arabuluculuk Büro No: 2026/...",
                    m_sifat: "DAVACI (İŞÇİ)",
                    m_ad: "[Davacı İşçi Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI (İŞVEREN)",
                    k_ad: "[İşveren Şirket / Şahıs Unvanı]",
                    k_vekil: "[Varsa İşveren Vekili]",
                    hed: "5.000,00 TL (Kısmi Dava - Fazlaya ilişkin haklarımız saklıdır)",
                    konu: "Haksız fesih nedeniyle kıdem ve ihbar tazminatları ile ödenmeyen işçilik alacaklarının tahsili talebidir.",
                    aciklama: "1- Müvekkil, davalı işyerinde ... ile ... tarihleri arasında çalışmıştır.\\n2- İş akdi davalı işveren tarafından haksız ve bildirimsiz olarak feshedilmiştir.\\n3- Arabuluculuk sürecinde anlaşma sağlanamamış olup dava açma zorunluluğu doğmuştur.",
                    hukuki_sebepler: "4857 sayılı İş Kanunu, 7036 sayılı İş Mahkemeleri Kanunu, HMK ve ilgili mevzuat.",
                    hukuki_deliller: "SGK hizmet dökümü, işyeri şahsi sicil dosyası, arabuluculuk tutanağı, emsal ücret araştırması, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Fazlaya ilişkin haklarımız saklı kalmak kaydıyla DAVAMIZIN KABULÜNE, kıdem, ihbar, fazla mesai ve yıllık izin alacaklarımızın en yüksek mevduat faiziyle davalıdan tahsiline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "tuketici_dava",
                category: "hukuk_dava",
                icon: "🛒",
                title: "Tüketici Mahkemesi Dava Dilekçesi",
                desc: "Ayıplı mal/hizmet, sözleşmeden dönme ve bedel iadesi talepli tüketici davası.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ TÜKETİCİ MAHKEMESİNE",
                    talep: "",
                    dosya: "",
                    m_sifat: "DAVACI (TÜKETİCİ)",
                    m_ad: "[Tüketici Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "DAVALI (SATICI / SAĞLAYICI)",
                    k_ad: "[Davalı Şirket Unvanı]",
                    k_vekil: "[Varsa Davalı Vekili]",
                    hed: "[... TL (Satış Bedeli İadesi)]",
                    konu: "Ayıplı mal nedeniyle sözleşmeden dönülerek ödenen bedelin yasal faiziyle iadesi talebidir.",
                    aciklama: "1- Müvekkil, davalı firmadan ... tarihinde satın aldığı üründe gizli/açık ayıp ortaya çıkmıştır.\\n2- Yasal süre içinde ayıp ihbarında bulunulmuş ancak davalı firma sorumluluk almamıştır.\\n3- 6502 sayılı Kanun uyarınca bedel iadesini talep zorunluluğu doğmuştur.",
                    hukuki_sebepler: "6502 sayılı TKHK, TBK, HMK ve ilgili mevzuat.",
                    hukuki_deliller: "Fatura, servis kayıtları, ayıp ihbar yazışmaları, arabuluculuk tutanağı, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Ayıplı mal nedeniyle sözleşmeden dönülerek ÖDENEN BEDELİN FAİZİYLE İADESİNE, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "tapu_iptal",
                category: "hukuk_dava",
                icon: "📜",
                title: "Tapu İptali ve Tescil Dava Dilekçesi",
                desc: "Muris muvazaası / vekalet görevinin kötüye kullanılması nedeniyle tapu iptal ve tescil.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                    talep: "TAPU KAYDINA İHTİYATİ TEDBİR TALEPLİDİR",
                    dosya: "",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Müvekkil Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Davalı Vekili]",
                    hed: "[... TL (Taşınmazın Harca Esas Değeri)]",
                    konu: "Taşınmaz tapu kaydının iptali ile müvekkil adına tescili talebimizdir.",
                    aciklama: "1- Dava konusu Mersin İli ... Parsel sayılı taşınmaz hukuka aykırı ve muvazaalı devredilmiştir.\\n2- Taşınmazın üçüncü kişilere devrinin önlenmesi için tapu kaydına tedbir konulması elzemdir.\\n3- Tapu kaydının iptali ile tesciline karar verilmesini talep ederiz.",
                    hukuki_sebepler: "TMK, TBK, HMK ve ilgili mevzuat.",
                    hukuki_deliller: "Tapu kayıtları, resmi senetler, mirasçılık belgesi, tanık, bilirkişi, keşif, yemin ve sair hukuki deliller.",
                    sonuc: "Taşınmaz üzerine İHTİYATİ TEDBİR KONULMASINA, tapu kaydının İPTALİ ile müvekkil adına TESCİLİNE karar verilmesini saygıyla vekâleten arz ve talep ederiz."
                }
            },

            // --- HUKUK CEVAP / TALEP / DELİL DİLEKÇELERİ ---
            {
                id: "cevap",
                category: "hukuk_talep",
                icon: "💬",
                title: "Cevap Dilekçesi (Davalı)",
                desc: "Usul ve esas itirazları, zamanaşımı ve davanın reddi talepli cevap dilekçesi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVALI",
                    m_ad: "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davalı Müvekkil Adresi]",
                    k_sifat: "DAVACI",
                    k_ad: "[Davacı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davacı Vekili]",
                    hed: "",
                    konu: "Dava dilekçesine karşı yasal süresi içinde usule ve esasa ilişkin cevaplarımızın sunulmasıdır.",
                    aciklama: "USULE İLİŞKİN İTİRAZLARIMIZ:\\n1- [Yetki, görev, zamanaşımı ve dava şartı yokluğu itirazları]\\n\\nESASA İLİŞKİN CEVAPLARIMIZ:\\n2- Davacının iddiaları gerçeği yansıtmamakta olup, hukuki dayanaktan yoksundur.\\n3- [Olayın gerçek mahiyeti ve davacının haksızlığını gösteren açıklamalar]",
                    hukuki_sebepler: "HMK, TBK, TTK ve ilgili mevzuat.",
                    hukuki_deliller: "Karşı deliller, yazışmalar, kayıtlar, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Öncelikle USULDEN REDDİNE, aksi kanaatte ise HAKSIZ VE MESNETSİZ DAVANIN ESASTAN REDDİNE, yargılama giderleri ile vekâlet ücretinin davacı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "delil_bildirme",
                category: "hukuk_talep",
                icon: "📁",
                title: "Delil Bildirme Dilekçesi",
                desc: "Müzekkere celp talepleri, ekli belgeler ve delil hasrı sunumu.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemeniz ara kararı uyarınca delil listemizin ve delillerimizin sunulmasıdır.",
                    aciklama: "Sayın Mahkemenizin ara kararı doğrultusunda delil listemiz aşağıdadır:\\n\\nDELİL LİSTEMİZ:\\n1- [Delil 1: Sözleşme / Yazışmalar / Fatura vb.] (Ek-1)\\n2- [Delil 2: Banka Dekontları / Kamera Kaydı vb.] (Ek-2)\\n3- İlgili kurumlardan celbi talep edilen müzekkere cevapları\\n4- Tanık, Bilirkişi incelemesi, Keşif, Yemin ve her türlü yasal delil.",
                    hukuki_sebepler: "HMK m. 199 vd. ve ilgili mevzuat.",
                    hukuki_deliller: "Yazılı belgeler, müzekkere kayıtları, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Ekli delillerimizin dosya arasına alınmasına, celbi gereken kayıtlar için müzekkere yazılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "genel_talep",
                category: "hukuk_talep",
                icon: "📌",
                title: "Genel Talep ve Beyan Dilekçesi",
                desc: "Ara karar gereği beyan, müzekkere tekidi, duruşma günü veya dosya fotokopisi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemeniz ara kararı doğrultusunda beyanlarımızın ve taleplerimizin sunulmasıdır.",
                    aciklama: "1- Mahkemenizin ... tarihli duruşmasında kurulan ara karar uyarınca beyanda bulunmaktayız.\\n2- İlgili kurumlara yazılan müzekkere cevaplarının tekidini ve dosyadaki eksikliklerin ikmalini talep ederiz.\\n3- [Konuya ilişkin somut açıklamalar ve talepler]",
                    hukuki_sebepler: "HMK ve ilgili mevzuat.",
                    hukuki_deliller: "Dosya kapsamı.",
                    sonuc: "Yukarıda arz edilen hususlar doğrultusunda işlem tesis edilmesini ve taleplerimizin kabulünü vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "talep_artirim",
                category: "hukuk_talep",
                icon: "📊",
                title: "Talep Artırım Dilekçesi (HMK m. 109/4)",
                desc: "Kısmi davada bilirkişi raporu sonrası ıslah hakkı tüketilmeden HMK 109/4 uyarınca talep artırımı ve tamamlama harcı.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davalı Vekili]",
                    hed: "[... TL Artırılan Tutar / Toplam: ... TL]",
                    konu: "Bilirkişi raporu doğrultusunda belirlenen alacak miktarımız uyarınca HMK m. 109/4 gereğince TALEP ARTIRIM DİLEKÇEMİZİN ve tamamlama harcımızın sunulmasıdır.",
                    aciklama: "1- Mahkemeniz dosyasına sunulan ... tarihli bilirkişi raporu ile dava konusu alacağımızın tam ve kesin miktarı tespit edilmiştir.\\n2- Dava dilekçemizde fazlaya ilişkin haklarımız saklı tutularak açılan kısmi davada talep sonucumuz, HMK m. 109/4 hükmü uyarınca (ISLAH HAKKIMIZ SAKLI KALMAK KAYDIYLA) artırılmaktadır.\\n3- Bu kapsamda dava değerimiz ... TL artırılarak toplam ... TL'ye yükseltilmiş olup, tamamlama harcı mahkeme veznesine yatırılmıştır.\\n4- İşbu dilekçemiz HMK m. 109/4 kapsamında talep artırım dilekçesi mahiyetinde olup, ıslah niteliğinde değildir.",
                    hukuki_sebepler: "HMK m. 109/4, Harçlar Kanunu, TBK ve ilgili mevzuat.",
                    hukuki_deliller: "Bilirkişi raporu, harç tamamlama makbuzu, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "HMK m. 109/4 uyarınca TALEP ARTIRIM DİLEKÇEMİZİN KABULÜ ile toplam ... TL alacağımızın dava/temerrüt tarihinden itibaren işleyecek faiziyle birlikte davalıdan tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "replik",
                category: "hukuk_talep",
                icon: "📝",
                title: "Cevaba Cevap Dilekçesi (Replik)",
                desc: "Davalının cevap dilekçesine karşı süresi içinde cevaba cevap sunumu.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davalı Vekili]",
                    hed: "",
                    konu: "Davalının cevap dilekçesine karşı süresi içinde cevaba cevaplarımızın sunulmasıdır.",
                    aciklama: "1- Davalının cevap dilekçesinde ileri sürdüğü itirazların tamamı yersiz olup reddi gerekmektedir.\\n2- Davalı taraf borcun ifa edildiğini yasal delillerle ispatlayamamıştır.\\n3- Dava dilekçemizdeki haklı iddialarımızı yineliyor, davanın kabulünü talep ediyoruz.",
                    hukuki_sebepler: "HMK, TBK ve ilgili mevzuat.",
                    hukuki_deliller: "Dava dilekçesinde sunulan deliller, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Davalının haksız cevap ve itirazlarının reddi ile DAVAMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "duplik",
                category: "hukuk_talep",
                icon: "📑",
                title: "İkinci Cevap Dilekçesi (Düplik)",
                desc: "Davacının cevaba cevap dilekçesine karşı ikinci cevapların sunulması.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVALI",
                    m_ad: "[Davalı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davalı Adresi]",
                    k_sifat: "DAVACI",
                    k_ad: "[Davacı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davacı Vekili]",
                    hed: "",
                    konu: "Davacının cevaba cevap dilekçesine karşı ikinci cevaplarımızın (düplik) sunulmasıdır.",
                    aciklama: "1- Davacının cevaba cevap dilekçesindeki iddiaları soyut ve hukuki dayanaktan yoksundur.\\n2- Müvekkilimizin sorumluluğu bulunmadığı tarafımızca sunulan delillerle sabittir.",
                    hukuki_sebepler: "HMK, TBK ve ilgili mevzuat.",
                    hukuki_deliller: "Cevap dilekçemizde bildirilen deliller, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Haksız ve hukuki dayanaktan yoksun DAVANIN REDDİNE karar verilmesini vekâleten arz ve talep ederiz."
                }
            },
            {
                id: "tanik_bildirme",
                category: "hukuk_talep",
                icon: "👥",
                title: "Tanık Bildirme Dilekçesi",
                desc: "İsim, TC ve adresli tanık listesi ile dinlenecekleri konuların sunumu.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemenizin ara kararı uyarınca tanık listemizin sunulmasıdır.",
                    aciklama: "Mahkemenizin ara kararı uyarınca tanıklarımızın isim ve adres bilgileri aşağıda sunulmuştur:\\n\\nTANIKLARIMIZ:\\n1- [Tanık 1 Adı Soyadı - T.C. No] - [Adres Bilgisi] (Hangi konuda dinleneceği: ...)\\n2- [Tanık 2 Adı Soyadı - T.C. No] - [Adres Bilgisi] (Hangi konuda dinleneceği: ...)",
                    hukuki_sebepler: "HMK m. 240 vd. ve ilgili mevzuat.",
                    hukuki_deliller: "Tanık beyanları ve dosyadaki sair deliller.",
                    sonuc: "Yukarıda bildirilen tanıklarımızın duruşma günü davetiye tebliği suretiyle dinlenilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "mehil",
                category: "hukuk_talep",
                icon: "⏱️",
                title: "Süre Uzatım (Mehil) Talep Dilekçesi",
                desc: "HMK 127 uyarınca cevap süresinin bir ay süreyle uzatılması talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVALI / DAVACI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Dava dilekçesine / ara karara cevap süremizin HMK m. 127 uyarınca uzatılması talebidir.",
                    aciklama: "1- Mahkemenizin yukarıda esas numarası yazılı dosyasında dava dilekçesi tarafımıza ... tarihinde tebliğ edilmiştir.\\n2- Toplanması gereken belge ve kayıtların çokluğu nedeniyle yasal 2 haftalık sürede cevap hazırlamak imkânsızdır.\\n3- HMK m. 127 gereğince cevap süremizin uzatılmasını talep ediyoruz.",
                    hukuki_sebepler: "HMK m. 127 ve ilgili mevzuat.",
                    hukuki_deliller: "Tebligat mazbatası ve dosya kapsamı.",
                    sonuc: "Cevap süremizin HMK 127. maddesi uyarınca ilk sürenin bitiminden itibaren BİR AY SÜREYLE UZATILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "istinaf_hukuk",
                category: "hukuk_talep",
                icon: "⚖️",
                title: "İstinaf Başvuru Dilekçesi (Tehiri İcra)",
                desc: "Yerel mahkeme kararının kaldırılması ve tehir-i icra talepli istinaf başvurusu.",
                data: {
                    mahkeme: "MERSİN BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "TEHİR-İ İCRA (İCRANIN GERİ BIRAKILMASI) TALEPLİDİR",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "İSTİNAF EDEN (DAVALI)",
                    m_ad: "[İstinaf Eden Müvekkil - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF (DAVACI)",
                    k_ad: "[Davacı Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Davacı Vekili]",
                    hed: "[... TL (İstinafa Konu Karar Tutarı)]",
                    konu: "Mersin .. Asliye Hukuk Mahkemesi'nin ... tarih ve ... E., ... K. sayılı haksız kararının istinafen incelenerek KALDIRILMASI talebimizdir.",
                    aciklama: "1- Yerel mahkemece eksik inceleme ve hatalı delil değerlendirmesi sonucunda usul ve yasaya aykırı karar verilmiştir.\\n2- [Yerel mahkeme kararındaki somut maddi ve hukuki hata gerekçeleri]\\n3- Karar usul ve esas yönünden hukuka aykırı olup kaldırılması gerekmektedir.",
                    hukuki_sebepler: "HMK m. 341 vd., İİK m. 36 ve ilgili mevzuat.",
                    hukuki_deliller: "Yerel mahkeme dava dosyası, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "İstinaf başvurumuzun KABULÜ ile yerel mahkeme kararının KALDIRILMASINA ve tehiri icra talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "bilirkisi_itiraz",
                category: "hukuk_talep",
                icon: "📑",
                title: "Bilirkişi Raporuna İtiraz Dilekçesi",
                desc: "Hatalı ve eksik bilirkişi raporuna itiraz ile ek rapor / yeni heyet incelemesi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Dosyaya sunulan ... tarihli bilirkişi raporuna karşı itirazlarımızın sunulmasıdır.",
                    aciklama: "1- Sayın Mahkemeniz dosyasına sunulan bilirkişi raporu eksik incelemeye ve hatalı kabullere dayanmaktadır.\\n2- [Rapordaki teknik, maddi ve hukuki hata kalemleri]\\n3- Hatalı rapor hükme esas alınamaz; ek rapor veya yeni bir heyetten rapor alınmalıdır.",
                    hukuki_sebepler: "HMK m. 281 ve ilgili mevzuat.",
                    hukuki_deliller: "Dosya kapsamı, emsal raporlar, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Hatalı bilirkişi raporuna itirazlarımızın KABULÜ ile dosyanın EK RAPOR veya YENİ BİLİRKİŞİ HEYETİNE tevdine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "bilirkisi_beyan",
                category: "hukuk_talep",
                icon: "📋",
                title: "Bilirkişi Raporuna Karşı Beyan Dilekçesi",
                desc: "HMK m. 281 uyarınca lehe olan bilirkişi raporuna muvafakat ve rapor doğrultusunda karar verilmesi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Dosyaya sunulan ... tarihli Bilirkişi Raporuna karşı süresi içerisinde beyanlarımızın sunulmasıdır.",
                    aciklama: "1- Mahkemenizce aldırılan ... tarihli bilirkişi raporu tarafımıza tebliğ edilmiştir.\\n2- Bilirkişi heyeti/uzmanı dosya kapsamındaki tüm delilleri, defter ve kayıtları bilimsel ve mevzuata uygun şekilde incelemiş; iddia ve savunmalarımızı doğrulamıştır.\\n3- Rapor gerekçeli, denetime elverişli ve hüküm kurmaya yeterli olup rapor doğrultusunda davamızın/taleplerimizin kabulüne karar verilmesini talep ederiz.",
                    hukuki_sebepler: "HMK m. 281 ve ilgili mevzuat.",
                    hukuki_deliller: "Tarihli bilirkişi raporu ve dosya kapsamı.",
                    sonuc: "Hukuka ve dosya kapsamına uygun Bilirkişi Raporu doğrultusunda haklı DAVAMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "bilirkisi_rapora_itiraz",
                category: "hukuk_talep",
                icon: "📊",
                title: "Bilirkişi Raporuna Karşı İtiraz Dilekçesi",
                desc: "HMK m. 281 uyarınca eksik, çelişkili veya hatalı bilirkişi raporuna itiraz ve ek/yeni bilirkişi incelemesi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Dosyaya sunulan ... tarihli usul ve yasaya aykırı Bilirkişi Raporuna karşı İTİRAZLARIMIZIN sunulması ile EK RAPOR / YENİ HEYET RAPORU aldırılması talebimizdir.",
                    aciklama: "1- Mahkemeniz dosyasına ibraz olunan ... havale tarihli bilirkişi raporu tarafımıza tebliğ edilmiş olup yasal süresi içinde itirazlarımızı sunuyoruz.\\n2- [İtiraz Maddesi 1: Bilirkişinin somut verileri veya belgeleri değerlendirmemesi].\\n3- [İtiraz Maddesi 2: Hatalı hesaplama yöntemi veya mevzuata aykırı değerlendirme].\\n4- Rapor denetime elverişsiz ve hüküm kurmaya yetersiz olduğundan itirazlarımız doğrultusunda ek rapor veya yeni bir bilirkişi heyetinden rapor aldırılmalıdır.",
                    hukuki_sebepler: "HMK m. 266, 281, 282 ve ilgili mevzuat.",
                    hukuki_deliller: "Tarihli bilirkişi raporu, ticari defterler, banka kayıtları, emsal Yargıtay kararları.",
                    sonuc: "Hatalı ve eksik Bilirkişi Raporuna vaki İTİRAZLARIMIZIN KABULÜ ile itirazlarımız doğrultusunda EK RAPOR ALDIRILMASINA (veya yeni bir uzman heyetten YENİ RAPOR teminine) karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "bilirkisiye_itiraz_reddi",
                category: "hukuk_talep",
                icon: "🚫",
                title: "Bilirkişinin Şahsına İtiraz / Reddi Dilekçesi",
                desc: "HMK m. 272 uyarınca hâkimin reddi sebeplerine dayalı olarak tarafsızlığı şüpheli bilirkişinin reddi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemenizce bilirkişi olarak görevlendirilen [Bilirkişinin Adı Soyadı - Uzmanlık Alanı]'nın HMK m. 272 ve m. 36 uyarınca REDDİ ve yeni bir tarafsız bilirkişi görevlendirilmesi talebimizdir.",
                    aciklama: "1- Mahkemeniz tensip/ara kararı ile dosya incelemesi için [Bilirkişi Adı Soyadı] bilirkişi olarak tayin edilmiştir.\\n2- Bilirkişi ile karşı taraf/şirket arasında [Husumet / İş ilişkisi / Menfaat birliği / Tarafsızlığı şüpheye düşürecek somut bağ] bulunmaktadır.\\n3- HMK m. 272/1 gereğince bilirkişiler hakkında hâkimin reddine ilişkin sebepler uygulanır. Tarafsızlığını yitirmiş bilirkişinin dosyada görev yapması hukuka aykırıdır.",
                    hukuki_sebepler: "HMK m. 36, 272 ve ilgili mevzuat.",
                    hukuki_deliller: "Bilirkişi atama ara kararı, bilirkişi ile taraf arasındaki ilişkiyi gösterir belgeler.",
                    sonuc: "Bilirkişinin REDDİ TALEBİMİZİN KABULÜNE, görevlendirmenin iptali ile dosyanın tarafsız ve bağımsız yeni bir bilirkişiye tevdiine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "adli_yardim_ret_itiraz",
                category: "hukuk_talep",
                icon: "⚖️",
                title: "Adli Yardım Talebinin Reddini İtiraz Dilekçesi",
                desc: "HMK m. 337/2 uyarınca mahkemenin adli yardım talebini reddine karşı itiraz ve kararın kaldırılması talebi.",
                data: {
                    mahkeme: "MERSİN [..+1]. ASLİYE HUKUK MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / TALEP EDEN",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davalı Vekili]",
                    hed: "",
                    konu: "Mersin [..]. Asliye Hukuk Mahkemesi'nin ... tarihli adli yardım talebimizin reddine dair ara kararına karşı HMK m. 337/2 uyarınca İTİRAZLARIMIZIN sunulmasıdır.",
                    aciklama: "1- Müvekkilin kendisi ve ailesinin geçimini önemli ölçüde zor duruma düşürmeksizin gereken yargılama ve harç giderlerini kısmen veya tamamen ödeme gücünden yoksun olduğu ekli belgelerle sabittir.\\n2- Müvekkil adına kayıtlı herhangi bir gayrimenkul veya gelir getirici malvarlığı bulunmamakta olup fakirlik belgesi, SGK dökümü ve banka kayıtları dosyada mevcuttur.\\n3- Mahkemenin ret gerekçesi Anayasa m. 36 ile teminat altına alınan hak arama hürriyetini ve mahkemeye erişim hakkını engellemektedir.",
                    hukuki_sebepler: "Anayasa m. 36, AİHS m. 6, HMK m. 334, 336, 337/2 ve ilgili mevzuat.",
                    hukuki_deliller: "Fakirlik ilmuhaberi, SGK hizmet dökümü, tapu ve araç sorgu kayıtları, mahkemenin ret ara kararı.",
                    sonuc: "Adli yardım talebimizin reddine ilişkin ara karara vaki İTİRAZIMIZIN KABULÜ ile ret kararının KALDIRILMASINA ve müvekkil hakkında ADLİ YARDIM TALEBİNİN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "dahili_davali",
                category: "hukuk_talep",
                icon: "👥",
                title: "Dahili Davalı Ekleme Dilekçesi",
                desc: "Mecburi dava arkadaşlığı veya husumet yöneltilmesi amacıyla davaya dahil etme talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davalı Vekili]",
                    hed: "",
                    konu: "Uyuşmazlığın mahiyeti gereği [Dahil Edilecek Kişi Adı Soyadı - T.C. / Unvanı - Adres] şahsın/şirketin davaya DAHİLİ DAVALI olarak eklenmesi ve dava dilekçesinin tebliği talebimizdir.",
                    aciklama: "1- Mahkemenizin yukarıda esas numarası yazılı dosyasında görülmekte olan davada, dava konusu hakkın/borcun niteliği gereği üçüncü kişinin davada yer alması zorunludur.\\n2- HMK hükümleri ve maddi hukuk gereğince husumetin işbu şahsa/şirkete de yöneltilmesi ve davaya dahil edilmesi gerekmektedir.\\n3- Dahili davalıya tensip zaptı ve dava dilekçesi ekli davetiye tebliğe çıkarılmalıdır.",
                    hukuki_sebepler: "HMK m. 124 ve ilgili mevzuat.",
                    hukuki_deliller: "Dava dosyası kapsamı ve resmi kayıtlar.",
                    sonuc: "Bildirilen şahsın/şirketin davaya DAHİLİ DAVALI olarak eklenmesine, duruşma günü ve dava dilekçesinin tebliğine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "tashih_dilekcesi",
                category: "hukuk_talep",
                icon: "✏️",
                title: "Tashih (Hükmün Tashihi) Dilekçesi",
                desc: "HMK m. 304 uyarınca karardaki yazı, hesap veya isim hatalarının tashihi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemenizin ... tarih ve ... E., ... K. sayılı gerekçeli kararında yer alan açık yazı/hesap/isim hatasının HMK m. 304 uyarınca TASHİHİ (düzeltilmesi) talebimizdir.",
                    aciklama: "1- Sayın Mahkemenizce yukarıda numarası belirtilen dosyada verilen gerekçeli kararın hüküm fıkrasında açık bir yazı/hesaplama/isim hatası yapılmıştır.\\n2- [Yapılan somut maddi hatanın açıklaması: Örn. vekalet ücreti hesaplaması, taraf ismi, TC no veya alacak miktarı rakam hatası] sehven yanlış yazılmıştır.\\n3- HMK m. 304 uyarınca kararın taraflara tebliğ edilmiş olup olmadığına bakılmaksızın tashih edilmesini talep ederiz.",
                    hukuki_sebepler: "HMK m. 304 ve ilgili mevzuat.",
                    hukuki_deliller: "Mahkeme ilamı ve dosya kapsamı.",
                    sonuc: "Gerekçeli kararda yer alan açık maddi hatanın HMK m. 304 uyarınca TASHİHİNE ve düzeltme şerhli kararın taraflara tebliğine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "tavzih_dilekcesi",
                category: "hukuk_talep",
                icon: "📖",
                title: "Tavzih (Hükmün Açıklanması) Dilekçesi",
                desc: "HMK m. 305 uyarınca açık olmayan veya çelişkili fıkralar içeren hükmün tavzihi talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemenizin ... tarih ve ... E., ... K. sayılı ilamının hüküm fıkrasındaki müphemliğin/çelişkinin HMK m. 305 uyarınca TAVZİHİ (açıklığa kavuşturulması) talebimizdir.",
                    aciklama: "1- Mahkemeniz ilamının hüküm kısmı icra/infaz aşamasında tereddüt ve belirsizlik yaratacak nitelikte müphem kalmıştır.\\n2- [Hüküm fıkrasındaki açıklığa kavuşturulması gereken kısım ve icra dairesinin infaz edememe gerekçesi].\\n3- HMK m. 305 uyarınca hükmün sınırları genişletilmeksizin fıkranın açık ve tereddütsüz hale getirilmesi için tavzih kararı verilmesini talep ederiz.",
                    hukuki_sebepler: "HMK m. 305, 306 ve ilgili mevzuat.",
                    hukuki_deliller: "Mahkeme gerekçeli kararı, icra müdürlüğü tensip/kararı ve dosya kapsamı.",
                    sonuc: "Hüküm fıkrasındaki belirsizliğin HMK m. 305 uyarınca TAVZİHEN AÇIKLIĞA KAVUŞTURULMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "tefrik_dilekcesi",
                category: "hukuk_talep",
                icon: "✂️",
                title: "Davanın Tefriki (Ayırma) Dilekçesi",
                desc: "HMK m. 167 uyarınca yargılamanın daha hızlı yürümesi için davanın tefriki talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Birlikte açılan veya birleştirilen talepler/davalılar yönünden davanın HMK m. 167 uyarınca TEFRİK EDİLEREK ayrı bir esasa kaydedilmesi talebimizdir.",
                    aciklama: "1- Mahkemeniz dosyasında birden fazla talep/davalı bir arada yer almakta olup, delillerin toplanması ve yargılama usulü birbirinden farklılaşmıştır.\\n2- Taleplerin bir arada görülmesi yargılamayı sürüncemede bırakmakta ve usul ekonomisine aykırılık teşkil etmektedir.\\n3- HMK m. 167 gereğince davanın tefriki ile ayrı bir esasa kaydı gerekmektedir.",
                    hukuki_sebepler: "HMK m. 30, 167 ve ilgili mevzuat.",
                    hukuki_deliller: "Dava dosyası kapsamı.",
                    sonuc: "Davanın [.. talebi / .. davalısı] yönünden TEFRİK EDİLEREK ayrı bir esasa kaydına ve yargılamanın ayrı dosya üzerinden yürütülmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "vekillikten_cekilme",
                category: "hukuk_talep",
                icon: "🚪",
                title: "Vekillikten Çekilme (İstifa) Dilekçesi",
                desc: "Avukatlık Kanunu m. 41 ve HMK m. 82 uyarınca vekillik görevinden istifa bildirimi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "VEKİLLİKTEN ÇEKİLEN VEKİL",
                    m_ad: "Av. Lütfi Serkan SAYOĞLU",
                    m_adres: "[Büro Adresi]",
                    k_sifat: "ASİL (MÜVEKKİL)",
                    k_ad: "[Vekillikten Çekilinen Müvekkil Adı Soyadı - T.C. No - Adres]",
                    k_vekil: "",
                    hed: "",
                    konu: "Görülen lüzum üzerine dosyadaki vekillik görevimizden İSTİFA ETTİĞİMİZİN (çekildiğimizin) bildirilmesidir.",
                    aciklama: "1- Mahkemenizin yukarıda esas numarası yazılı dosyasında müvekkil [Müvekkil Adı Soyadı] adına vekillik görevini yürütmekte idik.\\n2- Görülen lüzum üzerine vekillik görevinden istifa ediyoruz.\\n3- Avukatlık Kanunu m. 41 ve HMK m. 82 gereğince vekillikten çekilme dilekçemizin asil müvekkile tebliğe çıkarılmasını ve UYAP kaydımızın silinmesini talep ederiz.",
                    hukuki_sebepler: "1136 sayılı Avukatlık Kanunu m. 41, HMK m. 81, 82, 83 ve ilgili mevzuat.",
                    hukuki_deliller: "Vekaletname ve dosya kapsamı.",
                    sonuc: "Vekillikten çekilme talebimizin KABULÜ ile dosyadaki vekillik kaydımızın silinmesine ve durumun asile tebliğine karar verilmesini vekâleten saygıyla arz ve talep ederim."
                }
            },
            {
                id: "adres_bildirim",
                category: "hukuk_talep",
                icon: "📍",
                title: "Adres Bildirim Dilekçesi",
                desc: "Tebligata yarar yeni MERNİS / ikamet adresinin mahkemeye bildirilmesi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI / DAVALI",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Yeni ve Güncel Tebligat Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Müvekkilin / davalının tebligata elverişli güncel adresinin Mahkemenize bildirilmesidir.",
                    aciklama: "1- Mahkemeniz dosyasında müvekkilin / karşı tarafın adresi değişmiş olup eski adrese yapılan tebligatlar bila ikmal dönmüştür.\\n2- Tebligata yarar yeni ve güncel adres aşağıda sunulmuştur:\\n\\nYENİ TEBLİGAT ADRESİ:\\n[Açık Mahalle, Cadde, Sokak, No, İlçe, İl Bilgisi]\\n\\n3- Bundan sonraki tüm tebligatların bu adrese çıkartılmasını talep ederiz.",
                    hukuki_sebepler: "Tebligat Kanunu m. 35, HMK ve ilgili mevzuat.",
                    hukuki_deliller: "MERNİS yerleşim yeri kaydı ve dosya kapsamı.",
                    sonuc: "Bildirilen yeni adresin UYAP ve dosya sistemine kaydedilmesine, tebligatların bu adrese yapılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "yetki_belgesi_sunum",
                category: "hukuk_talep",
                icon: "📑",
                title: "Avukatlık Yetki Belgesi",
                desc: "1136 sayılı Avukatlık Kanunu m. 56 uyarınca vekaletname yerine geçen resmi Yetki Belgesi.",
                data: {
                    is_yetki_belgesi: true,
                    mahkeme: "YETKİ BELGESİ",
                    talep: "",
                    dosya: "",
                    m_sifat: "YETKİ BELGESİ VEREN AVUKAT/AVUKATLIK ORTAKLIĞI",
                    m_ad: "Av. [Yetki Veren Avukat Adı Soyadı]",
                    m_adres: "[Yetki Veren Avukat Bürosu Adresi]",
                    m_baro: "Mersin Barosu - [Sicil No]",
                    m_vergi: "[Vergi Dairesi ve Sicil No]",
                    k_sifat: "YETKİLİ KILINAN AVUKAT",
                    k_ad: "Av. Lütfi Serkan SAYOĞLU",
                    k_adres: "[Yetkili Kılınan Avukat Adresi]",
                    k_baro: "Mersin Barosu - [Sicil No]",
                    k_vergi: "[Vergi Dairesi ve Sicil No]",
                    asil_ad: "[Vekil Eden Asil / Müvekkil Adı Soyadı - T.C.]",
                    asil_adres: "[Vekil Eden Adresi]",
                    dayanak_noter: "[Noterlik Adı, Tarih ve Yevmiye No]",
                    konu: "",
                    aciklama: "Bu yetki belgesi, 1136 sayılı Avukatlık Kanunu’nu değiştiren 4667 sayılı Kanun’un 36. maddesi ile 56. maddesine eklenen hüküm uyarınca, vekaletname yerine geçmek üzere, tarafımdan düzenlenmiştir.",
                    hukuki_sebepler: "",
                    hukuki_deliller: "",
                    sonuc: ""
                }
            },
            {
                id: "davadan_feragat",
                category: "hukuk_talep",
                icon: "🛑",
                title: "Davadan Feragat Dilekçesi",
                desc: "HMK m. 307 vd. uyarınca vekaletteki özel yetkiye istinaden davadan feragat bildirimi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davalı Vekili]",
                    hed: "",
                    konu: "Sayın Mahkemenizde görülmekte olan davamızdan HMK m. 307 vd. uyarınca FERAGAT ETTİĞİMİZİN bildirilmesidir.",
                    aciklama: "1- Mahkemenizin yukarıda esas numarası yazılı dosyasında açmış olduğumuz davadan, vekaletnamemizdeki feragat yetkisine istinaden gayrikabili rücu FERAGAT EDİYORUZ.\\n2- Taraflar arasında sulh olunmuş olup, karşılıklı olarak yargılama gideri ve vekâlet ücreti talebimiz bulunmamaktadır.\\n3- Feragat doğrultusunda karar verilmesini talep ederiz.",
                    hukuki_sebepler: "HMK m. 307, 309, 310, 311, 312 ve ilgili mevzuat.",
                    hukuki_deliller: "Özel feragat yetkili vekaletname ve dosya kapsamı.",
                    sonuc: "Feragat beyanımız doğrultusunda DAVANIN FERAGAT NEDENİYLE REDDİNE, tarafların yargılama gideri ve vekâlet ücreti talebi olmadığından bu hususta hüküm kurulmasına yer olmadığına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "istinaftan_feragat",
                category: "hukuk_talep",
                icon: "🛑",
                title: "İstinaf Başvurusundan Feragat Dilekçesi",
                desc: "HMK m. 349 uyarınca istinaf kanun yolundan feragat ve hükmün kesinleştirilmesi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "İSTİNAFTAN FERAGAT EDEN",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Mahkemenizin ... tarih ve ... E., ... K. sayılı kararına karşı İSTİNAF KANUN YOLUNA BAŞVURU HAKKIMIZDAN FERAGAT ETTİĞİMİZİN bildirilmesidir.",
                    aciklama: "1- Mahkemenizce yukarıda numarası yazılı dosyada verilen karar tarafımıza tebliğ edilmiştir.\\n2- Vekaletnamemizdeki yetkiye dayanarak istinaf kanun yoluna başvuru hakkımızdan gayrikabili rücu feragat ediyoruz.\\n3- Kararın kesinleştirilerek kesinleşme şerhinin düzenlenmesini talep ederiz.",
                    hukuki_sebepler: "HMK m. 349 ve ilgili mevzuat.",
                    hukuki_deliller: "Özel yetkili vekaletname ve mahkeme ilamı.",
                    sonuc: "İstinaf kanun yolundan FERAGAT TALEBİMİZİN KABULÜ ile yerel mahkeme kararının KESİNLEŞTİRİLMESİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "istinafa_cevap",
                category: "hukuk_talep",
                icon: "💬",
                title: "İstinaf Dilekçesine Cevap Dilekçesi",
                desc: "HMK m. 347 uyarınca davalının/davacının istinaf başvurusuna karşı esastan ret cevabı.",
                data: {
                    mahkeme: "MERSİN BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "İSTİNAFA CEVAP VEREN",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "İSTİNAF EDEN (KARŞI TARAF)",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Karşı tarafın usul ve yasaya aykırı istinaf başvuru dilekçesine karşı süresi içinde cevaplarımızın sunulmasıdır.",
                    aciklama: "1- Yerel mahkemece yapılan kapsamlı tahkikat ve toplanan deliller doğrultusunda usul ve yasaya tam uygun olarak karar tesis edilmiştir.\\n2- Karşı tarafın istinaf dilekçesinde ileri sürdüğü itirazların tamamı hukuki dayanaktan yoksundur.\\n3- Yerel mahkeme kararı hukuka uygun olup istinaf başvurusunun esastan reddi gerekmektedir.",
                    hukuki_sebepler: "HMK m. 347, 353/1-b-1 ve ilgili mevzuat.",
                    hukuki_deliller: "Yerel mahkeme dava dosyası ve dosya kapsamı.",
                    sonuc: "Karşı tarafın haksız ve hukuki dayanaktan yoksun İSTİNAF BAŞVURUSUNUN ESASTAN REDDİNE, yerel mahkeme kararının ONANMASINA, yargılama giderleri ve vekâlet ücretinin karşı tarafa yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "istinaf_red_istinafi",
                category: "hukuk_talep",
                icon: "⚖️",
                title: "İstinaf Reddi Kararına İtiraz / İstinaf Dilekçesi",
                desc: "HMK m. 346/2 uyarınca yerel mahkemenin istinaf başvurusunu ret kararına karşı BAM'a başvuru.",
                data: {
                    mahkeme: "MERSİN BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "İSTİNAF EDEN (DAVACI / DAVALI)",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Yerel Mahkemenin ... tarihli usul ve yasaya aykırı 'İstinaf Talebinin Reddine' dair ek kararının HMK m. 346/2 uyarınca KALDIRILMASI ve asıl istinaf başvurumuzun incelenmesi talebidir.",
                    aciklama: "1- Yerel mahkemece süresi içinde yapılan ve harcı yatırılan istinaf başvurumuz hakkında hatalı değerlendirme ile 'süre / kesinlik' yönünden ret kararı verilmiştir.\\n2- İstinaf başvurumuz yasal süresi içindedir / karar kesinlik sınırının üzerindedir.\\n3- HMK m. 346/2 gereğince yerel mahkemenin ret kararının kaldırılarak asıl istinaf incelemesine geçilmesini talep ederiz.",
                    hukuki_sebepler: "HMK m. 346/2, 352 ve ilgili mevzuat.",
                    hukuki_deliller: "Tebligat mazbatası, istinaf harç makbuzları, dava dosyası.",
                    sonuc: "Yerel mahkemenin istinaf talebimizin reddine dair ... tarihli ek kararının KALDIRILMASINA, asıl istinaf başvurumuzun kabulü ile yerel mahkeme kararının KALDIRILARAK taleplerimiz doğrultusunda karar tesisine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "islah_dilekcesi",
                category: "hukuk_talep",
                icon: "📈",
                title: "Islah ve Değer Artırım Dilekçesi (HMK 176)",
                desc: "Bilirkişi raporu doğrultusunda dava değerinin ıslah edilmesi ve tamamlama harcı.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "DAVACI",
                    m_ad: "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Davacı Adresi]",
                    k_sifat: "DAVALI",
                    k_ad: "[Davalı Adı Soyadı / Unvanı]",
                    k_vekil: "[Davalı Vekili]",
                    hed: "[... TL (Islah Edilen Yeni Dava Değeri)]",
                    konu: "Bilirkişi raporu uyarınca dava değerinin ... TL artırılarak toplam ... TL olarak ıslah edilmesidir.",
                    aciklama: "1- Dosyaya sunulan bilirkişi raporu ile müvekkilin toplam alacağı ... TL olarak hesaplanmıştır.\\n2- HMK m. 176 vd. uyarınca dava değerimizi ıslah ediyor ve tamamlama harcını yatırıyoruz.",
                    hukuki_sebepler: "HMK m. 176 vd., Harçlar Kanunu ve ilgili mevzuat.",
                    hukuki_deliller: "Bilirkişi raporu, harç makbuzu ve dosya kapsamı.",
                    sonuc: "Islah talebimizin kabulü ile toplam ... TL alacağımızın temerrüt faiziyle davalıdan tahsiline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },

            // --- İCRA VE İFLAS HUKUKU ---
            {
                id: "icra_sikayet",
                category: "icra",
                icon: "📌",
                title: "İcra Mahkemesi Şikayet Dilekçesi",
                desc: "Usulsüz tebligat, takibin iptali ve tedbiren durdurulması talepli şikayet dilekçesi.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
                    talep: "İCRANIN DURDURULMASI TALEPLİDİR",
                    dosya: "Mersin ... İcra Dairesi - 2026/... E.",
                    m_sifat: "ŞİKAYET EDEN",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KARŞI TARAF",
                    k_ad: "[Karşı Taraf Adı Soyadı / Unvanı]",
                    k_vekil: "[Varsa Karşı Taraf Vekili]",
                    hed: "",
                    konu: "Yapılan usulsüz tebligatın şikayeti ile takibin iptali ve durdurulması talebimizi içerir.",
                    aciklama: "1- Mersin ... İcra Dairesi'nin 2026/... Esas sayılı dosyasında müvekkil aleyhine icra takibi başlatılmıştır.\\n2- Ödeme emri müvekkilin MERNİS adresine usulüne uygun şekilde tebliğ edilmemiştir.\\n3- Yasal süresi içinde usulsüz tebligatın iptalini ve takibin tedbiren durdurulmasını talep ederiz.",
                    hukuki_sebepler: "İİK m. 16, Tebligat Kanunu m. 10, 21, 32 ve ilgili mevzuat.",
                    hukuki_deliller: "İcra takip dosyası, tebligat mazbatası, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Öncelikle icra takibinin TEDBİREN DURDURULMASINA, tebligatın USULSÜZ OLMASI NEDENİYLE İPTALİNE, öğrenme tarihinin tebliğ tarihi olarak kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "icra_itiraz",
                category: "icra",
                icon: "🛑",
                title: "İcra Takibine İtiraz Dilekçesi",
                desc: "İlamsız icra takibinde ödeme emrine, borca, faize ve tüm fer'ilerine itiraz.",
                data: {
                    mahkeme: "MERSİN ... İCRA DAİRESİNE",
                    talep: "TAKİBİN DURDURULMASI TALEBİDİR",
                    dosya: "2026/... Esas",
                    m_sifat: "BORÇLU (İTİRAZ EDEN)",
                    m_ad: "[Müvekkil Borçlu Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "ALACAKLI",
                    k_ad: "[Alacaklı Adı Soyadı / Unvanı]",
                    k_vekil: "[Alacaklı Vekili]",
                    hed: "",
                    konu: "Ödeme emrine, borca, faize, vekalet ücretine ve tüm fer'ilerine itirazlarımızın sunulmasıdır.",
                    aciklama: "1- Alacaklı tarafından başlatılan ilamsız icra takibine ilişkin ödeme emri müvekkile ... tarihinde tebliğ edilmiştir.\\n2- Müvekkilin alacaklı tarafa herhangi bir borcu bulunmamaktadır. Borcun tamamına, asıl alacağa, faize ve tüm ferilerine açıkça itiraz ediyoruz.",
                    hukuki_sebepler: "İİK m. 62 vd. ve ilgili mevzuat.",
                    hukuki_deliller: "Ödeme belgeleri, banka dekontları ve dosya kapsamı.",
                    sonuc: "Yasal süresi içinde yaptığımız itirazlarımızın kabulü ile icra takibinin DURDURULMASINA karar verilmesini vekâleten saygıyla talep ederiz."
                }
            },
            {
                id: "kambiyo_itiraz",
                category: "icra",
                icon: "💳",
                title: "Kambiyo Senetlerine Özgü Takibe İtiraz / Şikayet",
                desc: "İcra Hukuk Mahkemesi'ne imza inkarı, borca itiraz ve takibin geçici durdurulması.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
                    talep: "TAKİBİN GEÇİCİ OLARAK DURDURULMASI TALEPLİDİR",
                    dosya: "Mersin ... İcra Dairesi - 2026/... E.",
                    m_sifat: "BORÇLU (İTİRAZ EDEN)",
                    m_ad: "[Müvekkil Borçlu - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "ALACAKLI",
                    k_ad: "[Alacaklı Adı Soyadı / Unvanı]",
                    k_vekil: "[Alacaklı Vekili]",
                    hed: "[... TL (Senet Bedeli)]",
                    konu: "Kambiyo takibine konu senetteki İMZAYA / BORCA AÇIKÇA İTİRAZIMIZDIR.",
                    aciklama: "1- Takibe konu senetteki imza müvekkilin eli ürünü değildir; imza müvekkile ait değildir.\\n2- Müvekkilin alacaklıya hiçbir borcu bulunmamaktadır.\\n3- İİK m. 168-170 uyarınca takibin durdurulması ve iptali gerekmektedir.",
                    hukuki_sebepler: "İİK m. 168, 169, 170, TTK ve ilgili mevzuat.",
                    hukuki_deliller: "İcra dosyası, müvekkilin imza örnekleri, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                    sonuc: "Takibin GEÇİCİ OLARAK DURDURULMASINA, imza incelemesi neticesinde TAKİBİN İPTALİNE ve alacaklının kötü niyet tazminatına mahkum edilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "haciz_talep",
                category: "icra",
                icon: "🔒",
                title: "İcra Dairesi Haciz ve Muhafaza Talep Dilekçesi",
                desc: "Kesinleşen icra takibinde borçlunun taşınır/taşınmaz mallarına haciz ve muhafaza talebi.",
                data: {
                    mahkeme: "MERSİN ... İCRA DAİRESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "ALACAKLI VEKİLİ",
                    m_ad: "[Avukat Adı Soyadı]",
                    m_adres: "[Büro Adresi]",
                    k_sifat: "BORÇLU",
                    k_ad: "[Borçlu Adı Soyadı / Unvanı - T.C. / Vergi No]",
                    k_vekil: "",
                    hed: "",
                    konu: "Borçlunun menkul, gayrimenkul ve banka hesaplarına haciz konulması talebidir.",
                    aciklama: "1- Takip kesinleşmiş olup borç ödenmemiştir.\\n2- Borçlunun UYAP / TAKBİS / POLNET / EGM / SGK sorgularının yapılarak taşınmazlarına, araçlarına ve banka hesaplarına haciz konulmasını talep ederiz.",
                    hukuki_sebepler: "İİK m. 78 vd. ve ilgili mevzuat.",
                    hukuki_deliller: "İcra takip dosyası.",
                    sonuc: "Gereği gibi haciz işlemlerinin tatbiki ile ilgili kurumlara haciz müzekkeresi yazılmasına karar verilmesini talep ederim."
                }
            },

            // --- CEZA MAHKEMELERİ VE SAVCILIK ---
            {
                id: "sikayet",
                category: "ceza",
                icon: "👮",
                title: "Müşteki Suç Duyurusu (Cumhuriyet Başsavcılığı)",
                desc: "Cumhuriyet Başsavcılığı'na kamu davası açılması istemli suç duyurusu.",
                data: {
                    mahkeme: "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
                    talep: "",
                    dosya: "",
                    m_sifat: "MÜŞTEKİ",
                    m_ad: "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müşteki Adresi]",
                    k_sifat: "ŞÜPHELİ / ŞÜPHELİLER",
                    k_ad: "[Şüpheli Adı Soyadı / Kimliği Belirlenecek Şahıslar]",
                    k_vekil: "",
                    hed: "",
                    konu: "Şüpheli/ler hakkında TCK m. ... (Suç Adı) uyarınca kamu davası açılması talepli suç duyurumuzdur.",
                    aciklama: "SUÇ : [Örn: Dolandırıcılık, Tehdit, Hakaret vb.]\\nSUÇ TARİHİ : .../.../2026\\n\\n1- Şüpheli şahıs ... tarihinde müvekkile karşı atılı suçu işlemiştir.\\n2- Olayın gerçekleşme şekli, tanık beyanları ve ekteki delillerle sabittir.\\n3- Şüphelinin cezalandırılması için hakkında kamu davası açılması zorunludur.",
                    hukuki_sebepler: "TCK, CMK ve ilgili mevzuat.",
                    hukuki_deliller: "Yazışma kayıtları, kamera görüntüleri, tanık beyanları ve her türlü yasal delil.",
                    sonuc: "Şüpheli hakkında gerekli soruşturmanın yapılarak KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "kyok",
                category: "ceza",
                icon: "🚫",
                title: "KYOK (Takipsizlik) Kararına İtiraz",
                desc: "Kovuşturmaya yer olmadığına dair kararın Sulh Ceza Hâkimliğince kaldırılması talebi.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ SULH CEZA HÂKİMLİĞİNE\\nGönderilmek Üzere\\nMERSİN CUMHURİYET BAŞSAVCILIĞINA",
                    talep: "",
                    dosya: "Soruşturma No: 2026/... - Karar No: 2026/...",
                    m_sifat: "İTİRAZ EDEN (MÜŞTEKİ)",
                    m_ad: "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müşteki Adresi]",
                    k_sifat: "ŞÜPHELİ",
                    k_ad: "[Şüpheli Adı Soyadı]",
                    k_vekil: "",
                    hed: "",
                    konu: "Mersin Cumhuriyet Başsavcılığı'nın ... tarihli Kovuşturmaya Yer Olmadığına Dair Kararına (KYOK) itirazlarımızın sunulmasıdır.",
                    aciklama: "1- Başsavcılıkça dosya kapsamındaki deliller toplanmadan eksik soruşturma ile takipsizlik kararı verilmiştir.\\n2- [Soruşturulmayan deliller ve somut delil durumu]\\n3- Kamu davası açılması için yeterli şüphe mevcuttur.",
                    hukuki_sebepler: "CMK m. 172, 173 ve ilgili mevzuat.",
                    hukuki_deliller: "Soruşturma dosyası, kamera kayıtları, tanık, bilirkişi ve sair deliller.",
                    sonuc: "KYOK kararının KALDIRILMASINA ve şüpheli hakkında KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "tutuklama",
                category: "ceza",
                icon: "⛓️",
                title: "Tutukluluğa İtiraz ve Tahliye Dilekçesi",
                desc: "Sulh Ceza / Ağır Ceza tutuklama kararına itiraz ve ivedi tahliye talebi.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
                    talep: "TAHLİYE TALEPLİDİR",
                    dosya: "Sorgu No: 2026/... Sorgu",
                    m_sifat: "ŞÜPHELİ / SANIK",
                    m_ad: "[Müvekkil Şüpheli/Sanık - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi / Cezaevi Bilgisi]",
                    k_sifat: "MÜŞTEKİ",
                    k_ad: "[Müşteki Adı Soyadı]",
                    k_vekil: "[Müşteki Vekili]",
                    hed: "",
                    konu: "Mersin .. Sulh Ceza Hâkimliği'nin ... tarihli tutuklama kararına itirazımız ve TAHLİYE talebimizdir.",
                    aciklama: "1- Müvekkil hakkında verilen tutuklama kararı CMK 100 ve devamı maddelerine aykırıdır.\\n2- Müvekkilin kaçma veya delil karartma şüphesi bulunmamaktadır.\\n3- Tutuklama ölçülülük ilkesine aykırıdır.",
                    hukuki_sebepler: "AİHM içtihatları, Anayasa, CMK m. 100, 101, 109 ve ilgili mevzuat.",
                    hukuki_deliller: "Soruşturma evrakı, ikametgah belgesi, tanık, bilirkişi ve sair deliller.",
                    sonuc: "TUTUKLAMA KARARININ KALDIRILARAK MÜVEKKİLİN TAHLİYESİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "adli_kontrol",
                category: "ceza",
                icon: "📋",
                title: "Adli Kontrol Kararına İtiraz Dilekçesi",
                desc: "İmza yükümlülüğü veya yurtdışı yasağı adli kontrol tedbirlerinin kaldırılması talebi.",
                data: {
                    mahkeme: "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
                    talep: "ADLİ KONTROLÜN KALDIRILMASI TALEPLİDİR",
                    dosya: "2026/... Sorgu (veya Esas)",
                    m_sifat: "ŞÜPHELİ / SANIK",
                    m_ad: "[Müvekkil Şüpheli/Sanık - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "MÜŞTEKİ",
                    k_ad: "[Müşteki Adı Soyadı]",
                    k_vekil: "",
                    hed: "",
                    konu: "Müvekkil hakkında uygulanan adli kontrol tedbirinin kaldırılması talebimizdir.",
                    aciklama: "1- Müvekkil hakkında tesis edilen adli kontrol kararı çalışma ve seyahat hürriyetini ölçüsüz biçimde kısıtlamaktadır.\\n2- Müvekkil tüm adli kontrol tedbirlerine eksiksiz uymuştur.\\n3- Tedbirin devamında hukuki yarar kalmamıştır.",
                    hukuki_sebepler: "CMK m. 109, 110, 111 ve ilgili mevzuat.",
                    hukuki_deliller: "Dosya kapsamı ve adli kontrol takip tutanakları.",
                    sonuc: "Müvekkil hakkındaki ADLİ KONTROL TEDBİRLERİNİN KALDIRILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "ceza_savunma",
                category: "ceza",
                icon: "🛡️",
                title: "Asliye Ceza Savunma ve Beraat Dilekçesi",
                desc: "Esas hakkındaki mütalaaya karşı son savunma ve beraat talebi.",
                data: {
                    mahkeme: "MERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "SANIK",
                    m_ad: "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Sanık Adresi]",
                    k_sifat: "KATILAN / MÜŞTEKİ",
                    k_ad: "[Katılan/Müşteki Adı Soyadı]",
                    k_vekil: "[Katılan Vekili]",
                    hed: "",
                    konu: "Esas hakkındaki mütalaaya karşı savunmalarımız ve BERAAT talebimizin sunulmasıdır.",
                    aciklama: "1- İddianamede isnat edilen fiillerin müvekkil tarafından işlendiğine dair somut delil bulunmamaktadır.\\n2- Suçun yasal unsurları oluşmamış olup 'şüpheden sanık yararlanır' ilkesi geçerlidir.",
                    hukuki_sebepler: "TCK, CMK m. 223/2 ve ilgili mevzuat.",
                    hukuki_deliller: "Duruşma tutanakları, tanık beyanları, bilirkişi raporu ve sair deliller.",
                    sonuc: "Müvekkil sanığın BERAATİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "ceza_istinaf",
                category: "ceza",
                icon: "⚖️",
                title: "Ceza İstinaf Başvuru Dilekçesi",
                desc: "Ceza mahkemesi mahkumiyet kararının kaldırılarak beraat kararı verilmesi talebi.",
                data: {
                    mahkeme: "MERSİN BÖLGE ADLİYE MAHKEMESİ İLGİLİ CEZA DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... E. - 2026/... K.",
                    m_sifat: "SANIK (İSTİNAF EDEN)",
                    m_ad: "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KATILAN",
                    k_ad: "[Katılan Adı Soyadı]",
                    k_vekil: "[Katılan Vekili]",
                    hed: "",
                    konu: "Mersin .. Asliye Ceza Mahkemesi'nin ... tarih ve ... E., ... K. sayılı mahkumiyet kararının istinafen incelenerek BOZULMASI ve BERAAT kararı verilmesi talebidir.",
                    aciklama: "1- Yerel mahkemece eksik kovuşturma ve delillerin hatalı takdiri ile usul ve yasaya aykırı mahkumiyet hükmü kurulmuştur.\\n2- [Karardaki somut maddi ve hukuki hata gerekçeleri]\\n3- Suç unsurları oluşmamıştır.",
                    hukuki_sebepler: "CMK m. 272 vd., TCK ve ilgili mevzuat.",
                    hukuki_deliller: "Ceza dava dosyası, tanık, bilirkişi ve sair deliller.",
                    sonuc: "İstinaf başvurumuzun KABULÜ ile yerel mahkeme kararının BOZULMASINA ve müvekkilin BERAATİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "dijital_materyal_iade",
                category: "ceza",
                icon: "💻",
                title: "Dijital Materyallerin İadesi Dilekçesi",
                desc: "CMK m. 134 uyarınca el konulan cep telefonu, bilgisayar ve dijital materyallerin imaj alma işlemi sonrası ivedi iadesi talebi.",
                data: {
                    mahkeme: "MERSİN CUMHURİYET BAŞSAVCILIĞINA\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                    talep: "",
                    dosya: "Soruşturma No: 2026/... (veya 2026/... Esas)",
                    m_sifat: "ŞÜPHELİ / SANIK",
                    m_ad: "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "MÜŞTEKİ",
                    k_ad: "[Varsa Müşteki Adı Soyadı]",
                    k_vekil: "",
                    hed: "",
                    konu: "Müvekkilden muhafaza altına alınan/el konulan dijital materyallerin imaj alma/adli bilişim incelemesi tamamlandığından CMK m. 134 ve CMK m. 131 uyarınca İVEDİ OLARAK İADESİ talebimizdir.",
                    aciklama: "1- Başsavcılığınızın/Mahkemenizin yukarıda numarası yazılı dosyasında gerçekleştirilen arama ve elkoyma işlemi neticesinde müvekkile ait dijital materyallere el konulmuştur.\\n2- CMK m. 134/4 hükmü gereğince dijital materyallerin kopyası/imajı alındıktan sonra gecikmeksizin ilgilisine iade edilmesi zorunludur.\\n3- Cihazlarda müvekkilin ticari, mesleki ve özel yaşamına ilişkin zorunlu veriler bulunmakta olup cihazların alıkonulması müvekkili mağdur etmektedir.\\n4- Adli bilişim incelemesi ve yedekleme işlemleri tamamlandığından cihazların el altında tutulmasında hukuki yarar kalmamıştır.",
                    hukuki_sebepler: "Anayasa m. 20, 22, 35, CMK m. 131, 134 ve ilgili mevzuat.",
                    hukuki_deliller: "Arama ve elkoyma tutanağı, teslim-tesellüm tutanağı ve dosya kapsamı.",
                    sonuc: "Yukarıda arz ve izah olunan nedenlerle; müvekkilden el konulan dijital materyallerin CMK m. 134/4 ve CMK m. 131 uyarınca MÜVEKKİLE / VEKİLİNE İVEDİLİKLE İADESİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            },
            {
                id: "sure_tutum",
                category: "ceza",
                icon: "⏱️",
                title: "Ceza Süre Tutum (Müddeti Muhafaza) Dilekçesi",
                desc: "Gerekçeli karar tebliğine kadar istinaf başvuru süresini koruma talebi.",
                data: {
                    mahkeme: "MERSİN BÖLGE ADLİYE MAHKEMESİ CEZA DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                    talep: "",
                    dosya: "2026/... Esas",
                    m_sifat: "SANIK",
                    m_ad: "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                    m_adres: "[Müvekkil Adresi]",
                    k_sifat: "KATILAN",
                    k_ad: "[Katılan Adı Soyadı]",
                    k_vekil: "",
                    hed: "",
                    konu: "Mahkemenizin ... tarihli tefhim olunan kararına karşı süresi içinde istinaf kanun yoluna başvurduğumuza dair süre tutum dilekçemizdir.",
                    aciklama: "1- Mahkemenizce ... tarihli duruşmada müvekkil aleyhine verilen karar usul ve yasaya aykırıdır.\\n2- Gerekçeli kararın tarafımıza tebliğinden sonra ayrıntılı istinaf gerekçelerimizi sunmak üzere istinaf süremizi muhafaza ediyoruz.",
                    hukuki_sebepler: "CMK m. 273 ve ilgili mevzuat.",
                    hukuki_deliller: "Duruşma tutanağı ve dosya kapsamı.",
                    sonuc: "İstinaf başvuru süremizin korunmasına, gerekçeli kararın tarafımıza tebliğine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                }
            }
        ];

        // Varsayılan Sık Kullanılanlar
        const DEFAULT_FAVORITES = ["alacak_dava", "cevap", "delil_bildirme", "genel_talep"];
        
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

        let currentCategory = "all";

        function renderTemplates() {
            const grid = document.getElementById("templateGrid");
            const query = document.getElementById("searchInput").value.toLowerCase().trim();
            const favs = getFavorites();
            grid.innerHTML = "";

            const filtered = TEMPLATES.filter(t => {
                const matchCat = (currentCategory === "all" || t.category === currentCategory);
                const matchQuery = (!query || t.title.toLowerCase().includes(query));
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
            
            const payload = {
                ...t.data,
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

            document.getElementById("formTitleBadge").textContent = `${t.icon} ${t.title}`;
            document.getElementById("mahkeme").value = t.data.mahkeme || "";
            document.getElementById("talep").value = t.data.talep || "";
            document.getElementById("dosya").value = t.data.dosya || "";
            document.getElementById("m_sifat").value = t.data.m_sifat || "";
            document.getElementById("m_ad").value = t.data.m_ad || "";
            document.getElementById("m_adres").value = t.data.m_adres || "";
            document.getElementById("vekil").value = getLawyerFullText();
            document.getElementById("k_sifat").value = t.data.k_sifat || "";
            document.getElementById("k_ad").value = t.data.k_ad || "";
            document.getElementById("k_vekil").value = t.data.k_vekil || "";
            document.getElementById("hed").value = t.data.hed || "";
            document.getElementById("konu").value = t.data.konu || "";
            document.getElementById("aciklama").value = t.data.aciklama || "";
            document.getElementById("hukuki_sebepler").value = t.data.hukuki_sebepler || SEBEPLER_DEFAULT;
            document.getElementById("hukuki_deliller").value = t.data.hukuki_deliller || DELILLER_DEFAULT;

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
