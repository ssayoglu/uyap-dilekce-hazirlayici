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
import re
from datetime import datetime

PORT = 5678

CURRENT_VERSION = "1.4.0"
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
    
    for item in paragraphs:
        # Support both 6-tuple and 7-tuple (with extra XML attributes dict)
        if len(item) == 7:
            align, lspacing, sbelow, findent, tabset, extra_attrs, runs = item
        else:
            align, lspacing, sbelow, findent, tabset, runs = item
            extra_attrs = None
            
        p_attr = []
        if align is not None: p_attr.append(f'Alignment="{align}"')
        if lspacing is not None: p_attr.append(f'LineSpacing="{lspacing}"')
        if sbelow is not None: p_attr.append(f'SpaceBelow="{sbelow}"')
        if findent is not None: p_attr.append(f'FirstLineIndent="{findent}"')
        if tabset is not None: p_attr.append(f'TabSet="{tabset}"')
        
        if extra_attrs and isinstance(extra_attrs, dict):
            for k, v in extra_attrs.items():
                p_attr.append(f'{k}="{v}"')
        
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

MAZERET_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ Hızlı Mazeret Gönder</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; user-select: none; }
        input, textarea, select { user-select: text; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 p-4 min-h-screen flex flex-col justify-between">

    <div class="space-y-3">
        <!-- Başlık -->
        <div class="flex items-center justify-between border-b border-slate-800 pb-2">
            <div class="flex items-center gap-2">
                <span class="text-lg p-1 bg-amber-500/20 rounded-lg border border-amber-500/30">⚡️</span>
                <div>
                    <h2 class="text-xs font-bold text-white tracking-tight">Hızlı Mazeret Modülü</h2>
                    <p class="text-[10px] text-slate-400">3 Saniyede UYAP Mazeret UDF'i</p>
                </div>
            </div>
            <span class="text-[10px] bg-blue-500/20 text-blue-300 font-bold px-2 py-0.5 rounded-md" id="lawyerBadge">Avukat</span>
        </div>

        <!-- Form Alanları -->
        <div class="space-y-2 text-xs">
            <!-- Mahkeme ve İl -->
            <div class="grid grid-cols-2 gap-2">
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-0.5">İl & Mahkeme Türü:</label>
                    <select id="maz_court_type" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs text-white font-semibold focus:ring-1 focus:ring-amber-500">
                        <option value="ASLİYE HUKUK">Asliye Hukuk</option>
                        <option value="SULH HUKUK">Sulh Hukuk</option>
                        <option value="İŞ">İş Mahkemesi</option>
                        <option value="AİLE">Aile Mahkemesi</option>
                        <option value="ASLİYE TİCARET">Asliye Ticaret</option>
                        <option value="TÜKETİCİ">Tüketici Mahkemesi</option>
                        <option value="İCRA HUKUK">İcra Hukuk</option>
                        <option value="ASLİYE CEZA">Asliye Ceza</option>
                        <option value="AĞIR CEZA">Ağır Ceza</option>
                    </select>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-0.5">Mahkeme No (Örn: 2.):</label>
                    <input type="text" id="maz_court_no" placeholder="Örn: 2." value="[..]." class="w-full bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs text-white font-semibold focus:ring-1 focus:ring-amber-500">
                </div>
            </div>

            <!-- Dosya No & Duruşma Saati -->
            <div class="grid grid-cols-2 gap-2">
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-0.5">Dosya No:</label>
                    <input type="text" id="maz_dosya" placeholder="2026/.. E." class="w-full bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs text-white font-mono focus:ring-1 focus:ring-amber-500">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-0.5">Duruşma Günü / Saati:</label>
                    <input type="text" id="maz_saat" placeholder="Bugün saat 10:30" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:ring-1 focus:ring-amber-500">
                </div>
            </div>

            <!-- Müvekkil Sıfatı & Adı -->
            <div class="grid grid-cols-2 gap-2">
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-0.5">Müvekkil Sıfatı:</label>
                    <select id="maz_sifat" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:ring-1 focus:ring-amber-500">
                        <option value="DAVACI">Davacı Vekili</option>
                        <option value="DAVALI">Davalı Vekili</option>
                        <option value="SANIK">Sanık Müdafii</option>
                        <option value="KATILAN">Katılan Vekili</option>
                        <option value="MÜŞTEKİ">Müşteki Vekili</option>
                        <option value="ŞİKAYET EDEN">Şikayet Eden Vekili</option>
                    </select>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-0.5">Müvekkil Adı:</label>
                    <input type="text" id="maz_m_ad" placeholder="Müvekkil Adı" class="w-full bg-slate-800 border border-slate-700 rounded-lg p-1.5 text-xs text-white focus:ring-1 focus:ring-amber-500">
                </div>
            </div>

            <!-- Hazır Mazeret Sebebi Çipleri -->
            <div>
                <label class="block text-[10px] font-bold text-slate-400 mb-1">Mazeret Nedeni Seçin:</label>
                <div class="grid grid-cols-1 gap-1 text-[11px]">
                    <button type="button" onclick="selectReason(1)" id="btnR1" class="reason-btn text-left p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:border-amber-500 text-slate-200 transition">
                        ⚖️ Başka Mahkemedeki Duruşma Çakışması
                    </button>
                    <button type="button" onclick="selectReason(2)" id="btnR2" class="reason-btn text-left p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:border-amber-500 text-slate-200 transition">
                        🏥 Mesleki Mazeret / Sağlık Raporu
                    </button>
                    <button type="button" onclick="selectReason(3)" id="btnR3" class="reason-btn text-left p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:border-amber-500 text-slate-200 transition">
                        🚗 Şehir Dışı Görev / Keşif İcrası
                    </button>
                </div>
            </div>

            <!-- Mazeret Metni -->
            <div>
                <textarea id="maz_aciklama" rows="2" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-[11px] text-slate-300 leading-relaxed focus:ring-1 focus:ring-amber-500"></textarea>
            </div>
        </div>

        <!-- Butonlar -->
        <div class="pt-1 flex gap-2">
            <button type="button" onclick="generateMazeret()" class="flex-1 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold rounded-xl text-xs shadow-lg transition flex items-center justify-center gap-1.5">
                <span>⚡️ UYAP'ta Mazereti Aç</span>
            </button>
        </div>
    </div>

    <script>
        const REASONS = {
            1: "Aynı gün ve saatte [..] Mahkemesi'nde önceden belirlenmiş duruşmamız bulunması nedeniyle Sayın Mahkemenizin belirtilen celsesine iştirak edememekteyiz. Mazeretimizin kabulü ile duruşma gününün UYAP üzerinden öğrenilmesine karar verilmesini vekâleten arz ve talep ederiz.",
            2: "Geçirmiş olduğumuz ani sağlık rahatsızlığı / mesleki mazeretimiz nedeniyle Sayın Mahkemenizin belirtilen celsesine katılamıyoruz. Mazeretimizin kabulü ile yeni duruşma gününün UYAP'tan öğrenilmesine karar verilmesini talep ederiz.",
            3: "Şehir dışında icra edilecek keşif ve haciz işlemleri nedeniyle Sayın Mahkemenizin duruşmasına bizzat iştirak etmemiz mümkün olamamıştır. Mazeretimizin kabulünü vekâleten arz ve talep ederiz."
        };

        function selectReason(id) {
            document.querySelectorAll('.reason-btn').forEach(b => {
                b.classList.remove('bg-amber-500/20', 'border-amber-500', 'text-amber-300');
                b.classList.add('bg-slate-800', 'border-slate-700', 'text-slate-200');
            });
            const btn = document.getElementById(`btnR${id}`);
            if (btn) {
                btn.classList.remove('bg-slate-800', 'border-slate-700', 'text-slate-200');
                btn.classList.add('bg-amber-500/20', 'border-amber-500', 'text-amber-300');
            }
            document.getElementById("maz_aciklama").value = REASONS[id];
        }

        function initProfile() {
            try {
                const lp = JSON.parse(localStorage.getItem("dilekce_lawyer_profile") || "{}");
                const name = lp.name || "Av. Lütfi Serkan SAYOĞLU";
                document.getElementById("lawyerBadge").textContent = name.split(" ")[0] + " " + (name.split(" ")[1] || "");
            } catch(e) {}
            selectReason(1);
        }

        async function generateMazeret() {
            const courtType = document.getElementById("maz_court_type").value;
            let courtNo = document.getElementById("maz_court_no").value.trim();
            if (courtNo && !courtNo.endsWith(".")) courtNo += ".";
            
            let lp = {};
            try { lp = JSON.parse(localStorage.getItem("dilekce_lawyer_profile") || "{}"); } catch(e) {}
            const city = (lp.city || "MERSİN").toUpperCase();
            
            const mahkeme = `${city} ${courtNo ? courtNo + ' ' : ''}${courtType} MAHKEMESİNE`;
            const dosya = document.getElementById("maz_dosya").value.trim();
            const saat = document.getElementById("maz_saat").value.trim();
            const sifat = document.getElementById("maz_sifat").value;
            const m_ad = document.getElementById("maz_m_ad").value.trim();
            const aciklama = document.getElementById("maz_aciklama").value.trim();
            
            const konu = `Mazeret Beyanımız ve Yeni Duruşma Gününün Bildirilmesi Talebimiz Hakkında.${saat ? ' (' + saat + ')' : ''}`;
            const sonuc = "Yukarıda arz olunan nedenlerle; mesleki mazeretimizin KABULÜNE, duruşmanın başka bir güne talikine ve yeni duruşma gününün UYAP sistemi üzerinden tarafımıza bildirilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz.";

            const payload = {
                mahkeme,
                talep: "",
                dosya,
                m_sifat: sifat,
                m_ad,
                m_adres: "",
                vekil: lp.name ? `${lp.name} ${lp.extra ? '- ' + lp.extra : ''}` : "Av. Lütfi Serkan SAYOĞLU - UETS [16153-51280-36854]",
                avukat_imza: lp.name || "Av. Lütfi Serkan SAYOĞLU",
                k_sifat: "KARŞI TARAF",
                k_ad: "",
                hed: "",
                konu,
                aciklama: `1- ${aciklama}`,
                hukuki_sebepler: "",
                hukuki_deliller: "",
                sonuc,
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
                    alert("✅ Mazeret dilekçesi UYAP'ta açıldı!");
                } else {
                    alert("Hata: " + r.message);
                }
            } catch(e) {
                alert("Bağlantı hatası: " + e);
            }
        }

        window.onload = initProfile;
    </script>
</body>
</html>
"""

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
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
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

            <!-- İlk Kurulum Hoş Geldiniz Bildirimi -->
            <div id="lawyerModalFirstTimeHint" class="hidden bg-blue-50 border border-blue-200 rounded-xl p-3.5 space-y-1">
                <div class="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                    <span>👋</span> Hoş Geldiniz! Lütfen Bilgilerinizi Tanımlayın
                </div>
                <p class="text-[11px] text-blue-800 leading-relaxed">
                    Dilekçelerinizin, vekâletnamelerinizin ve istinaf başlıklarınızın otomatik olarak adınıza düzenlenmesi için lütfen <strong>Avukat Adınızı</strong>, <strong>İletişim/UETS bilginizi</strong> ve <strong>Bulunduğunuz İli</strong> kaydediniz.
                </p>
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

        <!-- Mahkeme Seçim Modalı (Hızlı Açılış İçin) -->
        <!-- Mahkeme ve Taraf Sıfatı Seçim Modalı (2 Adımlı Hızlı Sihirbaz) -->
    <div id="courtPickerModal" class="fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            
            <!-- Başlık Alanı -->
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div class="flex items-center gap-2.5">
                    <span class="text-2xl" id="modalStepIcon">🏛️</span>
                    <div>
                        <h3 class="font-bold text-slate-900 text-sm" id="courtModalTitle">1. Adım: Mahkeme Seçimi</h3>
                        <p class="text-[11px] text-slate-500" id="courtModalSubtitle">Dilekçenin sunulacağı mahkemeyi seçin.</p>
                    </div>
                </div>
                <button onclick="closeCourtPickerModal()" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
            </div>

            <!-- 1. Adım: Mahkeme Seçenekleri -->
            <div id="step1CourtContainer">
                <div class="grid grid-cols-2 gap-2.5 max-h-72 overflow-y-auto pr-1" id="courtOptionsGrid">
                </div>
            </div>

            <!-- 2. Adım: Taraf Sıfatı Seçenekleri (Müvekkil Sıfatı) -->
            <div id="step2PartyContainer" class="hidden space-y-3">
                <p class="text-xs font-bold text-slate-700">Müvekkilinizin bu dosyadaki sıfatı nedir?</p>
                <div class="grid grid-cols-2 gap-2.5 max-h-64 overflow-y-auto pr-1" id="partyOptionsGrid">
                </div>

                <!-- Özel / Diğer Sıfat Girişi -->
                <div class="pt-2 border-t border-slate-100 flex items-center gap-2">
                    <input type="text" id="customPartyInput" placeholder="Örn: VASİ / KISITLI / MİRASÇI / ÜÇÜNCÜ KİŞİ..." class="flex-1 px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500">
                    <button onclick="applyCustomPartyRole()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition">
                        ✓ Uygula
                    </button>
                </div>
            </div>

            <!-- Alt Butonlar -->
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                <button id="btnBackToCourts" onclick="backToStep1()" class="hidden px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition">
                    ← Mahkeme Seçimine Dön
                </button>
                <div class="flex items-center gap-2 ml-auto">
                    <button onclick="closeCourtPickerModal()" class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition">Vazgeç</button>
                </div>
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

                        <!-- Arama ve Kategori Filtreleme -->
        <div class="flex flex-col lg:flex-row items-center justify-between gap-3.5 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm">
            <div class="relative w-full lg:w-72 flex-shrink-0">
                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">🔍</span>
                <input type="text" id="searchInput" oninput="filterTemplates()" placeholder="Tüm şablonlarda ara (Savunma, Delil...)" class="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition">
            </div>
            <div class="flex flex-wrap items-center justify-start lg:justify-end gap-2 w-full">
                <button onclick="setCategory('all')" id="cat_all" class="cat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-600 text-white shadow-sm transition">Tümü (47)</button>
                <button onclick="setCategory('hukuk_dava')" id="cat_hukuk_dava" class="cat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">🏛️ Dava Dilekçeleri</button>
                <button onclick="setCategory('hukuk_talep')" id="cat_hukuk_talep" class="cat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">📝 Cevap / Delil / İstinaf</button>
                <button onclick="setCategory('ceza')" id="cat_ceza" class="cat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">🛡️ Ceza & Savcılık</button>
                <button onclick="setCategory('icra')" id="cat_icra" class="cat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">⚖️ İcra & İflas</button>
                <button onclick="setCategory('ozel_dava')" id="cat_ozel_dava" class="cat-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 transition">💰 Özel Dava Türleri</button>
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

    <!-- 2. GÖRÜNÜM: FORM DÜZENLEYİCİ (GELİŞMİŞ EDİTÖR) -->
    <main id="formView" class="max-w-7xl mx-auto px-4 sm:px-6 py-6 hidden flex-1 w-full space-y-4">
        
        <!-- Üst Kontrol Barı -->
        <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div class="flex items-center gap-3">
                <button onclick="showGalleryView()" class="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition shadow-sm">
                    ← Şablonlara Dön
                </button>
                <span id="formTitleBadge" class="text-xs sm:text-sm font-bold text-blue-950 bg-blue-50 px-3 py-1.5 rounded-xl border border-blue-200"></span>
            </div>

            <div class="flex items-center gap-2">
                <button type="button" onclick="openClientDirectoryModal()" class="px-3.5 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    👥 Müvekkil Rehberi
                </button>
                <button type="button" onclick="saveCurrentClientToDirectory()" class="px-3.5 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl text-xs font-bold transition flex items-center gap-1" title="Formdaki müvekkil bilgilerini rehbere kaydet">
                    💾 Rehbere Ekle
                </button>
                <button type="button" onclick="toggleLivePreview()" id="btnTogglePreview" class="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    👁️ Canlı Önizleme
                </button>
            </div>
        </div>

        <!-- Ana Düzenleme Alanı: Form & Canlı Önizleme (Grid) -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <!-- SOL / ORTA PANEL: Form Alanları (lg:col-span-7 veya 12) -->
            <div id="formFieldsCol" class="lg:col-span-7 space-y-5">
                
                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 sm:p-6 space-y-6">
                    
                    <!-- Bölüm 1: Mahkeme & Dosya -->
                    <div>
                        <h2 class="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
                            <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">1</span>
                            Mahkeme ve Dosya Bilgileri
                        </h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                            <div class="md:col-span-2">
                                <label class="block text-xs font-bold text-slate-600 mb-1">Mahkeme Başlığı (Ortalı, Kalın):</label>
                                <textarea id="mahkeme" oninput="updateLivePreview()" rows="2" class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm font-bold text-slate-900 focus:ring-2 focus:ring-blue-500"></textarea>
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-600 mb-1">Özel Talep (Sağ Üst Başlık):</label>
                                <input type="text" id="talep" oninput="updateLivePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-bold text-red-600 focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-600 mb-1">Dosya / İcra / Soruşturma No:</label>
                                <input type="text" id="dosya" oninput="updateLivePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500">
                            </div>
                        </div>
                    </div>

                    <hr class="border-slate-200">

                    <!-- Bölüm 2: Taraflar -->
                    <div>
                        <div class="flex items-center justify-between mb-3">
                            <h2 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                                <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">2</span>
                                Taraf ve Vekil Bilgileri
                            </h2>
                            <button type="button" onclick="openClientDirectoryModal()" class="text-xs text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-1">
                                👥 Rehberden Seç
                            </button>
                        </div>
                        
                        <!-- Müvekkil Bloğu -->
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200 mb-3.5">
                            <div>
                                <label class="block text-xs font-bold text-slate-600 mb-1">Müvekkil Sıfatı:</label>
                                <input type="text" id="m_sifat" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-bold text-slate-800 bg-white">
                            </div>
                            <div class="md:col-span-2">
                                <label class="block text-xs font-bold text-slate-600 mb-1">Müvekkil İsim / T.C. / Vergi No:</label>
                                <input type="text" id="m_ad" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 bg-white">
                            </div>
                            <div class="md:col-span-3">
                                <label class="block text-xs font-bold text-slate-600 mb-1">Müvekkil Adresi (İtalik yerleşir):</label>
                                <input type="text" id="m_adres" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-slate-300 rounded-xl text-xs italic text-slate-700 bg-white">
                            </div>
                        </div>

                        <!-- Vekil Bloğu -->
                        <div class="mb-3.5">
                            <div class="flex items-center justify-between mb-1">
                                <label class="block text-xs font-bold text-slate-600">Vekili:</label>
                                <button type="button" onclick="openLawyerModal()" class="text-[11px] text-blue-600 hover:underline font-bold">⚙️ Avukat Ayarları</button>
                            </div>
                            <input type="text" id="vekil" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-blue-200 bg-blue-50/50 rounded-xl text-xs font-bold text-blue-950">
                        </div>

                        <!-- Karşı Taraf Bloğu -->
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                            <div>
                                <label class="block text-xs font-bold text-slate-600 mb-1">Karşı Taraf Sıfatı:</label>
                                <input type="text" id="k_sifat" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-bold text-slate-800 bg-white">
                            </div>
                            <div class="md:col-span-2">
                                <label class="block text-xs font-bold text-slate-600 mb-1">Karşı Taraf İsim / Unvan:</label>
                                <input type="text" id="k_ad" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-semibold text-slate-900 bg-white">
                            </div>
                            <div class="md:col-span-3">
                                <label class="block text-xs font-bold text-slate-600 mb-1">Karşı Taraf Vekili (Varsa):</label>
                                <input type="text" id="k_vekil" oninput="updateLivePreview()" class="w-full px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-medium text-slate-700 bg-white">
                            </div>
                        </div>
                    </div>

                    <hr class="border-slate-200">

                    <!-- Bölüm 3: Konu, Dava Değeri ve Harç Hesaplama -->
                    <div>
                        <h2 class="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
                            <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">3</span>
                            Dilekçe Konusu ve Dava Değeri
                        </h2>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                            <div class="md:col-span-2">
                                <label class="block text-xs font-bold text-slate-600 mb-1">Dilekçe Konusu:</label>
                                <input type="text" id="konu" oninput="updateLivePreview()" class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-600 mb-1">Dava Değeri (H.E.D.):</label>
                                <input type="text" id="hed" oninput="calculateCourtFees(); updateLivePreview();" placeholder="Örn: 100000" class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-bold text-slate-900 focus:ring-2 focus:ring-blue-500">
                            </div>
                        </div>

                        <!-- 💰 CANLI HARÇ & MASRAF HESAPLAMA KARTI -->
                        <div id="feeCalculatorCard" class="hidden bg-gradient-to-r from-emerald-50 via-teal-50 to-slate-50 border border-emerald-200 rounded-xl p-3.5 space-y-2">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                                    💰 Otomatik Harç & Masraf Hesabı
                                </span>
                                <span class="text-[11px] font-semibold text-emerald-700" id="calcBaseValueLabel"></span>
                            </div>
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                                <div class="bg-white p-2 rounded-lg border border-emerald-100">
                                    <span class="text-[10px] text-slate-500 block">Peşin Nispi Harç (1/4):</span>
                                    <span class="font-bold text-slate-900" id="calcPesinHarc">0,00 TL</span>
                                </div>
                                <div class="bg-white p-2 rounded-lg border border-emerald-100">
                                    <span class="text-[10px] text-slate-500 block">Başvuru Harcı:</span>
                                    <span class="font-bold text-slate-900">427,60 TL</span>
                                </div>
                                <div class="bg-white p-2 rounded-lg border border-emerald-100">
                                    <span class="text-[10px] text-slate-500 block">%20 İcra İnkâr Taz.:</span>
                                    <span class="font-bold text-slate-900" id="calcInkarTazminat">0,00 TL</span>
                                </div>
                                <div class="bg-white p-2 rounded-lg border border-emerald-100">
                                    <span class="text-[10px] text-slate-500 block">Vekâlet Ücreti (AAÜT):</span>
                                    <span class="font-bold text-slate-900" id="calcAaut">0,00 TL</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <hr class="border-slate-200">

                    <!-- Bölüm 4: Açıklamalar ve Hızlı Hukuki Çipler -->
                    <div>
                        <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
                            <h2 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                                <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">4</span>
                                Açıklamalar ve Hukuki Gerekçeler
                            </h2>
                            <span class="text-[11px] text-slate-500">Hızlı eklemek için aşağıdaki çiplere tıklayın:</span>
                        </div>

                        <!-- ⚡️ HIZLI HUKUKİ PARAGRAF ÇİPLERİ (KİŞİSELLEŞTİRİLEBİLİR & DÜZENLENEBİLİR) -->
                        <div class="space-y-2 mb-3">
                            <div class="flex items-center justify-between">
                                <span class="text-[11px] font-bold text-slate-500">Hızlı Paragraf Çipleri:</span>
                                <button type="button" onclick="openChipManagerModal()" class="text-[11px] text-blue-600 hover:text-blue-800 font-bold flex items-center gap-1 transition">
                                    ⚙️ Çipleri Yönet & Yeni Ekle
                                </button>
                            </div>

                            <!-- Hukuk Çipleri Grubu -->
                            <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                                <div class="text-[10px] font-bold uppercase tracking-wider text-blue-900 mb-1.5 flex items-center gap-1">
                                    <span>🏛️ Hukuk Mahkemeleri Çipleri:</span>
                                </div>
                                <div class="flex flex-wrap items-center gap-1.5" id="hukukChipsContainer">
                                    <!-- Dinamik Hukuk Çipleri -->
                                </div>
                            </div>

                            <!-- Ceza Çipleri Grubu -->
                            <div class="bg-amber-50/50 p-2.5 rounded-xl border border-amber-200/60">
                                <div class="text-[10px] font-bold uppercase tracking-wider text-amber-900 mb-1.5 flex items-center gap-1">
                                    <span>🛡️ Ceza & Soruşturma Çipleri:</span>
                                </div>
                                <div class="flex flex-wrap items-center gap-1.5" id="cezaChipsContainer">
                                    <!-- Dinamik Ceza Çipleri -->
                                </div>
                            </div>
                        </div>

                        <textarea id="aciklama" oninput="updateLivePreview()" rows="6" class="w-full px-3.5 py-2.5 border border-slate-300 rounded-xl text-xs sm:text-sm font-normal text-slate-900 focus:ring-2 focus:ring-blue-500 leading-relaxed"></textarea>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                        <div>
                            <label class="block text-xs font-bold text-slate-600 mb-1">Hukuki Sebepler:</label>
                            <input type="text" id="hukuki_sebepler" oninput="updateLivePreview()" value="HMK, TBK, TTK, TMK, İİK ve ilgili mevzuat." class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-600 mb-1">Hukuki Deliller:</label>
                            <input type="text" id="hukuki_deliller" oninput="updateLivePreview()" value="Sözleşmeler, banka kayıtları, yazışmalar, tanık, bilirkişi, yemin ve sair hukuki deliller." class="w-full px-3 py-2 border border-slate-300 rounded-xl text-xs font-medium text-slate-900 focus:ring-2 focus:ring-blue-500">
                        </div>
                    </div>

                    <hr class="border-slate-200">

                    <!-- Bölüm 5: Netice-i Talep (Sonuç ve İstem) -->
                    <div>
                        <h2 class="text-sm font-bold text-slate-900 flex items-center gap-2 mb-2">
                            <span class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">5</span>
                            Sonuç ve İstem (Netice-i Talep)
                        </h2>
                        <textarea id="sonuc" oninput="updateLivePreview()" rows="3" class="w-full px-3.5 py-2 border border-slate-300 rounded-xl text-xs sm:text-sm font-semibold text-slate-900 focus:ring-2 focus:ring-blue-500 leading-relaxed"></textarea>
                    </div>

                    <!-- Butonlar -->
                    <div class="pt-3 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-end gap-3">
                        <button type="button" onclick="generateFromForm(false)" class="w-full sm:w-auto px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs shadow-sm transition flex items-center justify-center gap-2">
                            💾 Masaüstüne Kaydet
                        </button>
                        <button type="button" onclick="generateFromForm(true)" class="w-full sm:w-auto px-7 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs shadow-md transition flex items-center justify-center gap-2">
                            ✨ UDF Oluştur ve UYAP'ta Aç
                        </button>
                    </div>

                </div>
            </div>

            <!-- SAĞ PANEL: CANLI UYAP ÖNİZLEME (DRAWER / PANEL) -->
            <div id="previewCol" class="lg:col-span-5 sticky top-20">
                <div class="bg-white rounded-2xl border border-slate-200 shadow-md p-5 space-y-4 max-h-[85vh] overflow-y-auto">
                    <div class="flex items-center justify-between border-b border-slate-100 pb-2.5">
                        <div class="flex items-center gap-2">
                            <span class="text-lg">👁️</span>
                            <h3 class="font-bold text-xs uppercase tracking-wide text-slate-800">Canlı UYAP Önizleme</h3>
                        </div>
                        <span class="text-[10px] bg-slate-100 px-2 py-0.5 rounded text-slate-500 font-semibold">1.0 Satır Aralığı</span>
                    </div>

                    <!-- UYAP Belge Kağıt Simülasyonu -->
                    <div class="bg-white border border-slate-200 p-5 rounded-lg text-slate-900 font-serif text-[11px] leading-relaxed space-y-3 shadow-inner bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:16px_16px]">
                        <div class="text-center font-bold whitespace-pre-line leading-snug" id="pv_mahkeme">MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE</div>
                        
                        <div class="text-right font-bold text-red-600 text-[10px]" id="pv_talep"></div>

                        <!-- Taraflar Tablosu Simülasyonu -->
                        <div class="space-y-1 font-sans text-[11px] border-b border-slate-200 pb-2">
                            <div class="grid grid-cols-12 gap-1" id="pv_row_dosya">
                                <div class="col-span-4 font-bold text-slate-700">DOSYA NO</div>
                                <div class="col-span-8 font-medium">: <span id="pv_dosya">-</span></div>
                            </div>
                            <div class="grid grid-cols-12 gap-1" id="pv_row_m">
                                <div class="col-span-4 font-bold text-slate-700" id="pv_m_sifat">DAVACI</div>
                                <div class="col-span-8 font-bold">: <span id="pv_m_ad">[Davacı Adı]</span></div>
                            </div>
                            <div class="grid grid-cols-12 gap-1" id="pv_row_m_adres">
                                <div class="col-span-4 font-bold text-slate-700"></div>
                                <div class="col-span-8 italic text-slate-600 text-[10px]">: <span id="pv_m_adres">[Müvekkil Adresi]</span></div>
                            </div>
                            <div class="grid grid-cols-12 gap-1">
                                <div class="col-span-4 font-bold text-slate-700">VEKİLİ</div>
                                <div class="col-span-8 font-semibold text-blue-900">: <span id="pv_vekil">Av. Lütfi Serkan SAYOĞLU</span></div>
                            </div>
                            <div class="grid grid-cols-12 gap-1" id="pv_row_k">
                                <div class="col-span-4 font-bold text-slate-700" id="pv_k_sifat">DAVALI</div>
                                <div class="col-span-8 font-medium">: <span id="pv_k_ad">[Davalı Adı]</span></div>
                            </div>
                            <div class="grid grid-cols-12 gap-1" id="pv_row_hed">
                                <div class="col-span-4 font-bold text-slate-700">DAVA DEĞERİ</div>
                                <div class="col-span-8 font-medium">: <span id="pv_hed">-</span></div>
                            </div>
                            <div class="grid grid-cols-12 gap-1">
                                <div class="col-span-4 font-bold text-slate-700">KONU</div>
                                <div class="col-span-8 font-medium">: <span id="pv_konu">[Konu]</span></div>
                            </div>
                        </div>

                        <!-- Açıklamalar -->
                        <div>
                            <div class="font-bold underline mb-1 font-sans text-[11px]">AÇIKLAMALAR:</div>
                            <div class="whitespace-pre-line text-slate-800 indent-4 text-[11px]" id="pv_aciklama">1- [Açıklamalar]</div>
                        </div>

                        <!-- Sebepler & Deliller -->
                        <div class="space-y-1 font-sans text-[10px]">
                            <div><strong class="text-slate-700">HUKUKİ SEBEPLER:</strong> <span id="pv_sebepler">HMK, TBK ve ilgili mevzuat.</span></div>
                            <div><strong class="text-slate-700">HUKUKİ DELİLLER:</strong> <span id="pv_deliller">Banka kayıtları, tanık, bilirkişi ve yasal deliller.</span></div>
                        </div>

                        <!-- Sonuç ve İstem -->
                        <div>
                            <div class="font-bold underline mb-1 font-sans text-[11px]">SONUÇ VE İSTEM:</div>
                            <div class="whitespace-pre-line text-slate-800 indent-4 text-[11px]" id="pv_sonuc">[Sonuç ve Talep]</div>
                        </div>

                        <!-- İmza -->
                        <div class="text-right font-sans text-[10px] space-y-0.5 pt-2">
                            <div class="font-bold" id="pv_imza_unvan">Davacı Vekili</div>
                            <div class="font-bold" id="pv_imza_ad">Av. Lütfi Serkan SAYOĞLU</div>
                            <div class="italic text-slate-400 text-[9px]">(e-imzalıdır)</div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </main>

        <!-- ÇİP YÖNETİCİSİ & YENİ ÇİP EKLEME MODALI -->
    <div id="chipManagerModal" class="fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-xl w-full p-5 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div class="flex items-center gap-2">
                    <span class="text-xl">⚙️</span>
                    <div>
                        <h3 class="font-bold text-slate-900 text-sm">Hukuki Çip Yöneticisi</h3>
                        <p class="text-[11px] text-slate-500">Mevcut çipleri düzenleyin veya büronuza özel yeni paragraflar ekleyin.</p>
                    </div>
                </div>
                <button onclick="closeChipManagerModal()" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
            </div>

            <!-- Yeni Çip Ekleme / Düzenleme Formu -->
            <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2.5">
                <div class="text-xs font-bold text-slate-800 flex items-center justify-between">
                    <span id="chipFormTitle">➕ Yeni Çip Ekle</span>
                    <button id="btnCancelEditChip" onclick="resetChipForm()" class="hidden text-[10px] text-slate-500 hover:text-slate-800 underline">Vazgeç</button>
                </div>
                <input type="hidden" id="editChipId" value="">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div class="sm:col-span-2">
                        <label class="block text-[10px] font-bold text-slate-600 mb-0.5">Çip Buton Başlığı:</label>
                        <input type="text" id="modalChipTitle" placeholder="Örn: 🚗 Araç Değer Kaybı Bendi" class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-[10px] font-bold text-slate-600 mb-0.5">Kategori:</label>
                        <select id="modalChipCategory" class="w-full px-2 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold focus:ring-2 focus:ring-blue-500">
                            <option value="hukuk">🏛️ Hukuk</option>
                            <option value="ceza">🛡️ Ceza</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-600 mb-0.5">Açıklamalara Eklenecek Hukuki Metin:</label>
                    <textarea id="modalChipContent" rows="3" placeholder="Açıklamalara eklenecek hukuki gerekçe ve talep metnini buraya yazınız..." class="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs leading-relaxed focus:ring-2 focus:ring-blue-500"></textarea>
                </div>
                <div class="flex justify-end">
                    <button type="button" onclick="saveCustomChip()" class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm transition">
                        💾 Çipi Kaydet
                    </button>
                </div>
            </div>

            <!-- Kayıtlı Çipler Listesi -->
            <div>
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-slate-700">Mevcut Çipleriniz</span>
                    <button onclick="restoreDefaultChips()" class="text-[10px] text-amber-600 hover:underline font-semibold">🔄 Varsayılanlara Sıfırla</button>
                </div>
                <div id="chipManagerList" class="max-h-52 overflow-y-auto space-y-1.5 pr-1">
                    <!-- Dinamik liste -->
                </div>
            </div>

            <div class="pt-2 border-t border-slate-100 flex justify-end">
                <button onclick="closeChipManagerModal()" class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold">Tamam</button>
            </div>
        </div>
    </div>

    <!-- MÜVEKKİL REHBERİ MODALI -->
    <div id="clientDirectoryModal" class="fixed inset-0 z-50 hidden bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-5 space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div class="flex items-center gap-2">
                    <span class="text-xl">👥</span>
                    <div>
                        <h3 class="font-bold text-slate-900 text-sm">Müvekkil & Taraf Rehberi</h3>
                        <p class="text-[11px] text-slate-500">Kayıtlı müvekkillerinizi tek tıkla forma aktarın.</p>
                    </div>
                </div>
                <button onclick="closeClientDirectoryModal()" class="text-slate-400 hover:text-slate-600 font-bold text-lg">✕</button>
            </div>

            <!-- Arama Kutusu -->
            <input type="text" id="clientSearchInput" oninput="renderClientDirectoryList()" placeholder="Müvekkil adı veya T.C. ile filtrele..." class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:ring-2 focus:ring-blue-500">

            <!-- Müvekkil Listesi Grid -->
            <div id="clientListContainer" class="max-h-64 overflow-y-auto space-y-2 pr-1">
                <!-- Dinamik doldurulur -->
            </div>

            <div class="pt-2 border-t border-slate-100 flex justify-end">
                <button onclick="closeClientDirectoryModal()" class="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold">Kapat</button>
            </div>
        </div>
    </div>
<!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        UYAP Doküman Editörü UDF Oluşturucu • <span id="footerLawyer">Av. Lütfi Serkan SAYOĞLU</span>
    </footer>

    <script>
        const DELILLER_DEFAULT = "Sözleşmeler, faturalar, banka kayıtları, ticari defterler, tanık, bilirkişi, yemin ve sair hukuki deliller.";
        const SEBEPLER_DEFAULT = "HMK, TBK, TTK, TMK, İİK ve ilgili mevzuat.";

        // Güncelleme Notları Yönetimi
        const APP_VERSION = "1.4.0";

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

                function checkFirstTimeLawyerSetup() {
            try {
                const profile = localStorage.getItem("dilekce_lawyer_profile");
                if (!profile) {
                    setTimeout(() => {
                        openLawyerModal(true);
                    }, 500);
                }
            } catch(e) {}
        }

        function openLawyerModal(isFirstTime = false) {
            const lp = getLawyerProfile();
            document.getElementById("modalLawyerName").value = lp.name;
            document.getElementById("modalLawyerExtra").value = lp.extra || "";
            document.getElementById("modalLawyerCity").value = lp.city || "MERSİN";
            document.getElementById("modalLawyerBamCity").value = lp.bamCity || "ADANA";

            const hintEl = document.getElementById("lawyerModalFirstTimeHint");
            if (hintEl) {
                if (isFirstTime) {
                    hintEl.classList.remove("hidden");
                } else {
                    hintEl.classList.add("hidden");
                }
            }

            document.getElementById("lawyerModal").classList.remove("hidden");
        }function closeLawyerModal() {
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
                        "id": "genel_dava_dilekcesi",
                        "category": "hukuk_dava",
                        "icon": "⚖️",
                        "title": "Genel Dava Dilekçesi (Hukuk)",
                        "desc": "Tüm Hukuk Mahkemeleri için genel dava açılış dilekçesi (H.E.D., deliller, ihtiyati tedbir).",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı - T.C. / Vergi No]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "10.000,00 TL (Fazlaya ilişkin haklarımız saklı kalmak kaydıyla)",
                                    "konu": "Müvekkilin ödenmeyen alacağının ve maddi tazminatının temerrüt faiziyle birlikte tahsili talebidir.",
                                    "aciklama": "1- Taraflar arasındaki hukuki ilişkiden doğan alacak davalı tarafça vadesinde ifa edilmemiştir.\\n2- Davalıya yapılan bildirim ve ihtarlara rağmen sonuç alınamamış olup dava açma zorunluluğu hasıl olmuştur.\\n3- Alacağın tahsilinin temini için davalının malvarlığı üzerine ihtiyati tedbir konulmasını talep ederiz.",
                                    "hukuki_sebepler": "TBK, HMK, TTK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Sözleşme, faturalar, banka kayıtları, yazışmalar, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                                    "sonuc": "Yukarıda arz ve izah edilen nedenlerle; fazlaya ilişkin haklarımız saklı kalmak kaydıyla DAVAMIZIN KABULÜNE, alacağımızın temerrüt faiziyle birlikte tahsiline, tedbir talebimizin kabulüne, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini saygıyla vekâleten arz ve talep ederiz."
                        }
            },
            {
                        "id": "itirazin_iptali",
                        "category": "hukuk_dava",
                        "icon": "⚖️",
                        "title": "İtirazın İptali Dava Dilekçesi",
                        "desc": "İcra takibine haksız itirazın iptali, takibin devamı ve %20 icra inkar tazminatı davası.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
                                    "m_sifat": "DAVACI ALACAKLI",
                                    "m_ad": "[Davacı Alacaklı Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAVALI BORÇLU",
                                    "k_ad": "[Davalı Borçlu Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[... TL (İtiraz Edilen Takip Tutarı)]",
                                    "konu": "Mersin ... İcra Dairesi'nin 2026/... E. sayılı takibine yapılan haksız itirazın iptali ile takibin devamı ve %20 icra inkâr tazminatı talebidir.",
                                    "aciklama": "1- Davalı aleyhine başlatılan icra takibine davalı borçlu kötü niyetli ve haksız olarak itiraz etmiştir.\\n2- Borç likit ve muayyen olup davalının itirazı yalnızca takibi sürüncemede bırakma amaçlıdır.\\n3- İİK m. 67 uyarınca itirazın iptali ile takibin devamına karar verilmelidir.",
                                    "hukuki_sebepler": "İİK m. 67, HMK, TBK, TTK ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra takip dosyası, faturalar, hesap özetleri, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                                    "sonuc": "Davalının haksız itirazının İPTALİNE, takibin DEVAMINA, alacağın %20'sinden aşağı olmamak üzere İCRA İNKÂR TAZMİNATININ davalıdan tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "cevap",
                        "category": "hukuk_talep",
                        "icon": "📝",
                        "title": "Cevap Dilekçesi",
                        "desc": "Dava dilekçesine karşı ilk itirazlar, zamanaşımı ve esasa ilişkin cevapların sunulması.",
                        "court_type": "hukuk",
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
                                    "konu": "Davacının haksız ve mesnetsiz dava dilekçesine karşı süresi içinde esasa ilişkin cevaplarımızın sunulmasıdır.",
                                    "aciklama": "1- Davacının iddiaları gerçeğe aykırı olup müvekkilin herhangi bir borcu veya kusuru bulunmamaktadır.\\n2- Davacı taraf iddialarını somut delillerle ispatlayamamıştır.\\n3- Haksız ve hukuki dayanaktan yoksun davanın reddi gerekmektedir.",
                                    "hukuki_sebepler": "HMK, TBK, TTK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Banka kayıtları, ticari defterler, tanık, bilirkişi, yemin ve her türlü yasal delil.",
                                    "sonuc": "Haksız ve hukuki dayanaktan yoksun DAVANIN REDDİNE, yargılama giderleri ve vekâlet ücretinin davacıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "replik",
                        "category": "hukuk_talep",
                        "icon": "📨",
                        "title": "Cevaba Cevap Dilekçesi (Replik)",
                        "desc": "Davalının cevap dilekçesindeki savunmalara karşı cevaba cevap (replik) sunulması.",
                        "court_type": "hukuk",
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
                                    "konu": "Davalının haksız ve yasal dayanaktan yoksun cevap dilekçesine karşı CEVABA CEVAPLARIMIZIN (Replik) sunulmasıdır.",
                                    "aciklama": "1- Davalı tarafın cevap dilekçesinde ileri sürdüğü iddia ve savunmalar gerçeği yansıtmamaktadır.\\n2- Davalının soyut beyanları tarafımızca sunulan somut deliller karşısında hükümsüzdür.\\n3- Davamızın kabulü gerekmektedir.",
                                    "hukuki_sebepler": "HMK m. 136 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Dava dilekçemiz ekindeki deliller ve dosya kapsamı.",
                                    "sonuc": "Davalının mesnetsiz itirazlarının reddi ile DAVAMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "duplik",
                        "category": "hukuk_talep",
                        "icon": "📩",
                        "title": "İkinci Cevap Dilekçesi (Düplik)",
                        "desc": "Davacının cevaba cevap dilekçesine karşı ikinci cevap (düplik) layihasının sunulması.",
                        "court_type": "hukuk",
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
                                    "konu": "Davacının cevaba cevap dilekçesine karşı İKİNCİ CEVAPLARIMIZIN (Düplik) sunulmasıdır.",
                                    "aciklama": "1- Davacının replik dilekçesindeki iddiaları davanın haksızlığını örtbas etmeye yöneliktir.\\n2- Dilekçeler aşaması tamamlanmış olup haksız davanın reddine karar verilmelidir.",
                                    "hukuki_sebepler": "HMK m. 136 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Cevap dilekçemiz ekindeki deliller ve yasal deliller.",
                                    "sonuc": "Haksız ve mesnetsiz DAVANIN REDDİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "delil_bildirme",
                        "category": "hukuk_talep",
                        "icon": "🗂️",
                        "title": "Delil Bildirme Dilekçesi",
                        "desc": "Mahkeme tensip/ara kararı uyarınca kesin süre içinde delil listesi ve belgelerin sunulması.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Mahkemenizin ara kararı uyarınca yasal delil listemizin ve dayanak belgelerimizin sunulmasıdır.",
                                    "aciklama": "1- Mahkemenizce verilen kesin süre içinde delil listemiz ve ekleri sunulmuştur:\\n\\nDELİLLERİMİZ:\\n1- Ekli sözleşme, fatura ve banka dekontları,\\n2- İlgili banka ve kurumlara yazılacak müzekkere kayıtları,\\n3- Tanık, bilirkişi incelemesi, yemin ve ikamesi caiz her türlü yasal delil.",
                                    "hukuki_sebepler": "HMK m. 119, 121, 194 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Delil listesinde belirtilen tüm deliller.",
                                    "sonuc": "Delillerimizin kabulü ile müzekkere yazılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "tanik_bildirme",
                        "category": "hukuk_talep",
                        "icon": "👥",
                        "title": "Tanık Bildirme Dilekçesi",
                        "desc": "Tanıkların isim, T.C., adres ve hangi vakıa hakkında dinleneceklerinin listesi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Mahkemenizin ara kararı uyarınca tanık listemizin sunulması ve tanıkların duruşmaya davet edilmesi talebidir.",
                                    "aciklama": "1- Mahkemenizce verilen süre içinde tanık listemiz aşağıda sunulmuştur:\\n\\nTANIKLARIMIZ:\\n1- [Tanık-1 Adı Soyadı - T.C. 12345678901 - Adres] (Olay ve uyuşmazlık vakıalarına ilişkin),\\n2- [Tanık-2 Adı Soyadı - T.C. 12345678901 - Adres] (Ödeme ve ifa süreçlerine ilişkin).",
                                    "hukuki_sebepler": "HMK m. 240 vd. ve ilgili mevzuat.",
                                    "hukuki_deliller": "Tanık beyanları ve dosya kapsamı.",
                                    "sonuc": "Tanık listemizin kabulü ile belirtilen tanıkların duruşma gününde dinlenilmek üzere davetiye çıkarılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "mehil",
                        "category": "hukuk_talep",
                        "icon": "⏱️",
                        "title": "Süre Uzatım (Mehil) Talep Dilekçesi",
                        "desc": "Cevap veya beyan süresinin uzatılması talebi (HMK m. 127).",
                        "court_type": "hukuk",
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
                                    "konu": "Dava dilekçesine karşı cevaplarımızı sunabilmemiz için HMK m. 127 uyarınca tarafımıza EK SÜRE (Mehil) verilmesi talebidir.",
                                    "aciklama": "1- Dava dilekçesi ve tensip zaptı tarafımıza ... tarihinde tebliğ edilmiştir.\\n2- Dava konusu iddialara ilişkin bilgi ve belgelerin toplanması zaman almaktadır.\\n3- HMK m. 127 uyarınca cevap süresinin 1 ay süreyle uzatılmasını talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 127 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Tebligat parçası ve dosya kapsamı.",
                                    "sonuc": "HMK m. 127 gereğince cevap süremizin YASAL OLARAK UZATILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "talep_artirim",
                        "category": "hukuk_talep",
                        "icon": "📊",
                        "title": "Talep Artırım Dilekçesi (HMK m. 109/4)",
                        "desc": "Kısmi davada bilirkişi raporu sonrası HMK 109/4 gereği müddeabihin artırılması (Islah değildir).",
                        "court_type": "hukuk",
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
                                    "hed": "[... TL (Artırılan Net Tutar)]",
                                    "konu": "HMK m. 109/4 gereğince bilirkişi raporu doğrultusunda dava değerinin artırılması ve tamamlama harcının yatırılmasıdır. (Islah değildir).",
                                    "aciklama": "1- Sayın Mahkemeniz nezdinde açılan kısmi davada alınan bilirkişi raporu ile müvekkilin toplam alacağı netleşmiştir.\\n2- HMK m. 109/4 uyarınca talep artırımı yapıyoruz; harcı yatırılmıştır.",
                                    "hukuki_sebepler": "HMK m. 109/4 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Bilirkişi raporu, harç makbuzu ve dosya kapsamı.",
                                    "sonuc": "HMK m. 109/4 gereğince TALEP ARTIRIMIMIZIN KABULÜ ile artırılan toplam tutarın faiziyle tahsiline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "islah_dilekcesi",
                        "category": "hukuk_talep",
                        "icon": "✏️",
                        "title": "Islah ve Değer Artırım Dilekçesi (HMK 176)",
                        "desc": "Dava konusunun veya miktarının HMK m. 176 uyarınca tamamen/kısmen ıslah edilmesi.",
                        "court_type": "hukuk",
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
                                    "hed": "[... TL (Islah ile Artırılan Miktar)]",
                                    "konu": "HMK m. 176 vd. uyarınca dava değerinin ISLAH EDİLMESİ ve ıslah harcının ikmali talebidir.",
                                    "aciklama": "1- Dosyada alınan bilirkişi raporu ile müvekkilin talep edebileceği alacak miktarı tespit edilmiştir.\\n2- HMK m. 176 uyarınca ıslah hakkımızı kullanıyoruz; bakiye ıslah harcı yatırılmıştır.",
                                    "hukuki_sebepler": "HMK m. 176 vd. ve ilgili mevzuat.",
                                    "hukuki_deliller": "Bilirkişi raporu, ıslah harç makbuzu.",
                                    "sonuc": "ISLAH TALEBİMİZİN KABULÜ ile toplam alacağımızın faiziyle tahsiline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "istinaf_hukuk",
                        "category": "hukuk_talep",
                        "icon": "⚖️",
                        "title": "İstinaf Başvuru Dilekçesi (Tehiri İcra)",
                        "desc": "Yerel Hukuk Mahkemesi gerekçeli kararına karşı BAM İlgili Hukuk Dairesi'ne istinaf başvurusu.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "TEHİR-İ İCRA (İCRANIN GERİ BIRAKILMASI) TALEPLİDİR",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAF EDEN DAVALI",
                                    "m_ad": "[İstinaf Eden Müvekkil - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVACI",
                                    "k_ad": "[Davacı Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Davacı Vekili]",
                                    "hed": "[... TL (İstinafa Konu Tutar)]",
                                    "konu": "Mersin [..]. Asliye Hukuk Mahkemesi'nin ... tarih ve ... E., ... K. sayılı haksız kararının istinafen incelenerek KALDIRILMASI ve davanın reddi talebimizdir.",
                                    "aciklama": "1- Yerel mahkemece eksik inceleme ve delillerin hatalı takdiri ile usul ve yasaya aykırı karar verilmiştir.\\n2- [Karardaki somut maddi ve hukuki hata gerekçeleri].\\n3- Karar kaldırılmalıdır.",
                                    "hukuki_sebepler": "HMK m. 341 vd., İİK m. 36 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yerel mahkeme dava dosyası, tanık, bilirkişi ve sair deliller.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile yerel mahkeme kararının KALDIRILMASINA ve tehiri icra talebimizin kabulüne karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "istinafa_cevap",
                        "category": "hukuk_talep",
                        "icon": "💬",
                        "title": "İstinaf Dilekçesine Cevap Dilekçesi",
                        "desc": "HMK m. 347 uyarınca karşı tarafın istinaf başvurusuna esastan ret cevabı.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAFA CEVAP VEREN",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "İSTİNAF EDEN",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Karşı tarafın haksız istinaf başvurusuna karşı cevaplarımızın sunulmasıdır.",
                                    "aciklama": "1- Yerel mahkeme kararı usul ve yasaya tam uygundur.\\n2- Karşı tarafın istinaf başvurusunun esastan reddi gerekmektedir.",
                                    "hukuki_sebepler": "HMK m. 347, 353/1-b-1 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yerel mahkeme dava dosyası.",
                                    "sonuc": "Karşı tarafın İSTİNAF BAŞVURUSUNUN ESASTAN REDDİNE, yerel mahkeme kararının ONANMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "istinaftan_feragat",
                        "category": "hukuk_talep",
                        "icon": "🛑",
                        "title": "İstinaf Başvurusundan Feragat Dilekçesi",
                        "desc": "HMK m. 349 uyarınca istinaf kanun yolundan feragat ve hükmün kesinleştirilmesi.",
                        "court_type": "hukuk",
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
                                    "aciklama": "1- Karara karşı istinaf başvuru hakkımızdan feragat ediyoruz.\\n2- Kararın kesinleştirilerek kesinleşme şerhli suretinin verilmesini talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 349 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Vekaletname ve mahkeme ilamı.",
                                    "sonuc": "İstinaftan feragat talebimizin KABULÜ ile kararın KESİNLEŞTİRİLMESİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "davadan_feragat",
                        "category": "hukuk_talep",
                        "icon": "🛑",
                        "title": "Davadan Feragat Dilekçesi",
                        "desc": "HMK m. 307 vd. uyarınca davadan feragat bildirimi.",
                        "court_type": "hukuk",
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
                        "id": "genel_talep",
                        "category": "hukuk_talep",
                        "icon": "💬",
                        "title": "Genel Talep ve Beyan Dilekçesi",
                        "desc": "Dosyaya beyan, mazeret, müzekkere tekidi veya genel usuli taleplerin sunulması.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Dosyaya ilişkin beyan ve taleplerimizin sunulmasıdır.",
                                    "aciklama": "1- Mahkemenizin yukarıda numarası belirtilen dosyasında [Beyan ve taleplerinizin ayrıntıları].\\n2- Talebimiz doğrultusunda işlem ifasını saygıyla arz ve talep ederiz.",
                                    "hukuki_sebepler": "HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Dava dosyası kapsamı.",
                                    "sonuc": "Talebimiz doğrultusunda gerekli işlemlerin yapılmasına karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "bilirkisi_itiraz",
                        "category": "hukuk_talep",
                        "icon": "📊",
                        "title": "Bilirkişi Raporuna İtiraz Dilekçesi",
                        "desc": "Eksik veya hatalı bilirkişi raporuna karşı itiraz ve ek/yeni bilirkişi raporu talebi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Dosyaya sunulan ... tarihli Bilirkişi Raporuna karşı İTİRAZLARIMIZIN sunulması ile EK RAPOR aldırılması talebimizdir.",
                                    "aciklama": "1- Bilirkişi raporunda müvekkilce sunulan belgeler ve kayıtlar eksik incelenmiştir.\\n2- Rapordaki hesaplama yöntemi yerleşik Yargıtay içtihatlarına aykırıdır.\\n3- HMK m. 281 uyarınca itirazlarımız doğrultusunda ek rapor tanzimi gerekmektedir.",
                                    "hukuki_sebepler": "HMK m. 281 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Bilirkişi raporu ve dosya kapsamı.",
                                    "sonuc": "Bilirkişi raporuna itirazlarımızın KABULÜ ile EK RAPOR ALDIRILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "bilirkisi_beyan",
                        "category": "hukuk_talep",
                        "icon": "📋",
                        "title": "Bilirkişi Raporuna Karşı Beyan Dilekçesi",
                        "desc": "Lehe olan bilirkişi raporuna muvafakat ve rapor doğrultusunda karar verilmesi talebi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Dosyaya tebliğ edilen ... tarihli Bilirkişi Raporuna karşı BEYANLARIMIZIN sunulmasıdır.",
                                    "aciklama": "1- Bilirkişi raporu dosya kapsamına, hukuka ve hakkaniyete uygun tanzim edilmiştir.\\n2- Raporda tespit edilen hususlar iddialarımızı tam olarak doğrulamaktadır.\\n3- Rapor doğrultusunda hüküm kurulmasını talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 281 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Tarihli bilirkişi raporu ve dosya.",
                                    "sonuc": "Bilirkişi raporu doğrultusunda DAVAMIZIN KABULÜNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "bilirkisiye_itiraz_reddi",
                        "category": "hukuk_talep",
                        "icon": "🚫",
                        "title": "Bilirkişinin Şahsına İtiraz / Reddi Dilekçesi",
                        "desc": "HMK m. 272 uyarınca tarafsızlığını yitiren bilirkişinin reddi talebi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "HMK m. 272 uyarınca görevlendirilen Bilirkişi [Bilirkişi Adı Soyadı]'nın REDDİ talebimizdir.",
                                    "aciklama": "1- Görevlendirilen bilirkişi ile karşı taraf arasında tarafsızlığı şüpheye düşürecek ilişki mevcuttur.\\n2- HMK m. 272 ve m. 36 uyarınca bilirkişinin reddi talep olunur.",
                                    "hukuki_sebepler": "HMK m. 36, 272 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Görevlendirme tensibi ve deliller.",
                                    "sonuc": "Bilirkişinin REDDİNE ve yeni bir bilirkişi heyeti tayinine karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "adli_yardim_ret_itiraz",
                        "category": "hukuk_talep",
                        "icon": "⚖️",
                        "title": "Adli Yardım Talebinin Reddini İtiraz Dilekçesi",
                        "desc": "HMK m. 337/2 uyarınca adli yardım talebinin reddi kararına itiraz.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..+1]. ASLİYE HUKUK MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Mahkemenin adli yardım talebimizin reddine ilişkin ara kararına İTİRAZLARIMIZIN sunulmasıdır.",
                                    "aciklama": "1- Müvekkilin yargılama giderlerini karşılama gücü bulunmamaktadır.\\n2- Fakirlik belgesi ve SGK kayıtları ekonomik durumu ispatlamaktadır.\\n3- HMK m. 337/2 uyarınca itirazımızın kabulü gerekmektedir.",
                                    "hukuki_sebepler": "HMK m. 334, 337/2 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Fakirlik belgesi, SGK kayıtları.",
                                    "sonuc": "İtirazımızın KABULÜ ile adli yardım talebimizin kabulüne karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "dahili_davali",
                        "category": "hukuk_talep",
                        "icon": "👥",
                        "title": "Dahili Davalı Ekleme Dilekçesi",
                        "desc": "HMK m. 124 uyarınca iradi veya mecburi dava arkadaşlığı nedeniyle dahili davalı ekleme.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Adresi]",
                                    "k_sifat": "DAHİLİ DAVALI",
                                    "k_ad": "[Dahili Davalı Adı Soyadı / Unvanı - T.C. / Vergi No]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "HMK m. 124 uyarınca üçüncü kişinin DAHİLİ DAVALI olarak davaya dahil edilmesi talebidir.",
                                    "aciklama": "1- Uyuşmazlık konusu hak ve borç ilişkisi yönünden dahili davalı tarafın davada yer alması zorunludur.\\n2- Dava dilekçesinin ve tensip zaptının dahili davalıya tebliğe çıkarılmasını talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 124 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Dava dosyası.",
                                    "sonuc": "Dahili davalının davaya DAHİL EDİLMESİNE ve dava dilekçesinin tebliğine karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "tashih_dilekcesi",
                        "category": "hukuk_talep",
                        "icon": "✏️",
                        "title": "Tashih (Hükmün Tashihi) Dilekçesi",
                        "desc": "HMK m. 304 uyarınca karardaki açık hesap, isim veya yazı hatalarının düzeltilmesi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Gerekçeli kararda yer alan açık maddi hatanın HMK m. 304 uyarınca TASHİHİ (düzeltilmesi) talebimizdir.",
                                    "aciklama": "1- Mahkemenizin kararında [Maddi hatanın detayı: isim/rakam/hesap hatası] yer almaktadır.\\n2- HMK m. 304 uyarınca tashih şerhi verilmesini talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 304 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Gerekçeli karar ve dosya.",
                                    "sonuc": "Maddi hatanın TASHİH EDİLEREK kararın düzeltilmesine karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "tavzih_dilekcesi",
                        "category": "hukuk_talep",
                        "icon": "📖",
                        "title": "Tavzih (Hükmün Açıklanması) Dilekçesi",
                        "desc": "HMK m. 305 uyarınca hüküm fıkrasındaki belirsizlik ve çelişkilerin açıklanması.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "HMK m. 305 uyarınca hüküm fıkrasındaki belirsizliğin TAVZİHİ (açıklanması) talebimizdir.",
                                    "aciklama": "1- Mahkemeniz hüküm fıkrası icra kabiliyeti yönünden açık ve net değildir.\\n2- HMK m. 305 uyarınca hükmün tavzih edilmesini talep ederiz.",
                                    "hukuki_sebepler": "HMK m. 305 vd. ve ilgili mevzuat.",
                                    "hukuki_deliller": "Gerekçeli karar.",
                                    "sonuc": "Hüküm fıkrasının TAVZİH EDİLMESİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "tefrik_dilekcesi",
                        "category": "hukuk_talep",
                        "icon": "✂️",
                        "title": "Davanın Tefriki (Ayırma) Dilekçesi",
                        "desc": "HMK m. 167 uyarınca birlikte açılan davaların ayrı esasa kaydedilerek tefriki.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "HMK m. 167 uyarınca davanın TEFRİK EDİLEREK ayrı bir esasa kaydedilmesi talebidir.",
                                    "aciklama": "1- Davaların birlikte görülmesi yargılamayı sürüncemede bırakmaktadır.\\n2- HMK m. 167 uyarınca davanın tefriki gerekmektedir.",
                                    "hukuki_sebepler": "HMK m. 167 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Dava dosyası.",
                                    "sonuc": "Davanın TEFRİKİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "vekillikten_cekilme",
                        "category": "hukuk_talep",
                        "icon": "🚪",
                        "title": "Vekillikten Çekilme (İstifa) Dilekçesi",
                        "desc": "Avukatlık Kanunu m. 41 ve HMK m. 82 uyarınca vekillikten istifa bildirimi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "VEKİLLİKTEN ÇEKİLEN VEKİL",
                                    "m_ad": "Av. Lütfi Serkan SAYOĞLU",
                                    "m_adres": "[Büro Adresi]",
                                    "k_sifat": "MÜVEKKİL",
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
                        "id": "adres_bildirim",
                        "category": "hukuk_talep",
                        "icon": "📍",
                        "title": "Adres Bildirim Dilekçesi",
                        "desc": "Tebligat Kanunu m. 35 ve HMK uyarınca yeni tebligat adresinin mahkemeye bildirimi.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "DAVACI / DAVALI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Yeni Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Müvekkilin güncel tebligat adresinin mahkemenize bildirilmesidir.",
                                    "aciklama": "1- Müvekkilin güncel adresi: [Yeni Adres Bilgisi].\\n2- Bundan sonraki tüm tebligatların bu adrese yapılması talep olunur.",
                                    "hukuki_sebepler": "Tebligat Kanunu, HMK.",
                                    "hukuki_deliller": "Nüfus / ikametgah kayıtları.",
                                    "sonuc": "Yeni adresimizin kayıtlara işlenmesini talep ederiz."
                        }
            },
            {
                        "id": "yetki_belgesi_sunum",
                        "category": "hukuk_talep",
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
                        "id": "istinaf_red_istinafi",
                        "category": "hukuk_talep",
                        "icon": "⚖️",
                        "title": "İstinaf Reddi Kararına İtiraz / İstinaf Dilekçesi",
                        "desc": "HMK m. 346/2 uyarınca yerel mahkemenin istinaf talebini ret kararına karşı itiraz.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... E. - 2026/... K.",
                                    "m_sifat": "İSTİNAF EDEN",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KARŞI TARAF",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "HMK m. 346/2 uyarınca yerel mahkemenin istinaf talebimizi ret kararının KALDIRILMASI ve istinaf incelemesinin yapılması talebimizdir.",
                                    "aciklama": "1- Yerel mahkeme istinaf başvurumuzu haksız yere reddetmiştir.\\n2- HMK m. 346/2 gereğince ret kararının kaldırılarak esas hakkında istinaf incelemesi yapılması zorunludur.",
                                    "hukuki_sebepler": "HMK m. 346/2 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yerel mahkeme ret kararı ve istinaf dilekçemiz.",
                                    "sonuc": "İstinaf talebimizin reddi kararının KALDIRILMASINA ve istinaf incelemesine geçilmesine karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "ceza_savunma",
                        "category": "ceza",
                        "icon": "🛡️",
                        "title": "Ceza Mahkemesi Savunma ve Beraat Dilekçesi",
                        "desc": "Esas hakkındaki mütalaaya karşı son savunma, tahliye ve beraat talebi.",
                        "court_type": "ceza",
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
                                    "konu": "İddianameye ve esas hakkındaki mütalaaya karşı savunmalarımızın sunulması ile BERAAT talebimizdir.",
                                    "aciklama": "1- Müvekkil üzerine atılı suçun maddi ve manevi unsurları kesinlikle oluşmamıştır.\\n2- Mahkumiyete yeter kesin delil bulunmamakta olup şüpheden sanık yararlanır ilkesi gereğince beraat verilmelidir.",
                                    "hukuki_sebepler": "TCK, CMK m. 223/2 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Duruşma tutanakları, tanık beyanları, kamera kayıtları ve dosya kapsamı.",
                                    "sonuc": "Müvekkilin üzerine atılı suçtan BERAATİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "ceza_istinaf",
                        "category": "ceza",
                        "icon": "⚖️",
                        "title": "Ceza İstinaf Başvuru Dilekçesi",
                        "desc": "Yerel Ceza Mahkemesi mahkumiyet kararına karşı BAM İlgili Ceza Dairesi'ne istinaf.",
                        "court_type": "ceza",
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
                                    "aciklama": "1- Yerel mahkemece eksik inceleme ile hukuka aykırı karar kurulmuştur.\\n2- Suçun unsurları oluşmamıştır.",
                                    "hukuki_sebepler": "CMK m. 272 vd., TCK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Ceza dava dosyası.",
                                    "sonuc": "İstinaf başvurumuzun KABULÜ ile mahkûmiyet kararının BOZULMASINA ve müvekkilin BERAATİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "sure_tutum",
                        "category": "ceza",
                        "icon": "⏱️",
                        "title": "Ceza Süre Tutum (Müddeti Muhafaza) Dilekçesi",
                        "desc": "Gerekçeli karar tebliğine kadar istinaf başvuru süresini koruma talebi.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "ADANA BÖLGE ADLİYE MAHKEMESİ İLGİLİ CEZA DAİRESİNE\\nGönderilmek Üzere\\nMERSİN [..]. ASLİYE CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "SANIK",
                                    "m_ad": "[Sanık Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "KATILAN",
                                    "k_ad": "[Katılan Adı Soyadı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Mahkemenizin tefhim olunan kararına karşı süresi içinde istinaf kanun yoluna başvurduğumuza dair süre tutum dilekçemizdir.",
                                    "aciklama": "1- Mahkemenizce verilen karar usul ve yasaya aykırıdır.\\n2- Gerekçeli kararın tebliğinden sonra ayrıntılı istinaf gerekçelerimiz sunulacaktır.",
                                    "hukuki_sebepler": "CMK m. 273 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Duruşma tutanağı.",
                                    "sonuc": "İstinaf süremizin korunmasına ve gerekçeli kararın tarafımıza tebliğine karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "tutuklama",
                        "category": "ceza",
                        "icon": "⛓️",
                        "title": "Tutukluluğa İtiraz ve Tahliye Dilekçesi",
                        "desc": "Tutuklama veya tutukluluğun devamı kararına itiraz ve ivedi tahliye talebi.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
                                    "talep": "TAHLİYE TALEPLİDİR",
                                    "dosya": "Sorgu No: 2026/... Sorgu",
                                    "m_sifat": "ŞÜPHELİ / SANIK",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Cezaevi / Adres Bilgisi]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Müşteki Adı Soyadı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Tutuklama kararına itirazlarımız ile müvekkilin TAHLİYESİ talebimizdir.",
                                    "aciklama": "1- Tutuklama kararı CMK 100 vd. maddelerine aykırıdır.\\n2- Kaçma, delil karartma şüphesi yoktur; adli kontrol hükümleri yeterlidir.",
                                    "hukuki_sebepler": "AİHM, Anayasa, CMK m. 100, 101, 109, 267 vd.",
                                    "hukuki_deliller": "Soruşturma evrakı, ikametgah belgeleri.",
                                    "sonuc": "Tutuklama kararının kaldırılarak müvekkilin TAHLİYESİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "adli_kontrol",
                        "category": "ceza",
                        "icon": "📋",
                        "title": "Adli Kontrol Kararına İtiraz Dilekçesi",
                        "desc": "İmza yükümlülüğü veya yurtdışı çıkış yasağının kaldırılması talebi.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE CEZA MAHKEMESİNE\\nGönderilmek Üzere\\nMERSİN [..]. SULH CEZA HÂKİMLİĞİNE",
                                    "talep": "ADLİ KONTROLÜN KALDIRILMASI TALEPLİDİR",
                                    "dosya": "2026/... Sorgu (veya Esas)",
                                    "m_sifat": "ŞÜPHELİ / SANIK",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Müşteki Adı Soyadı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Müvekkil hakkında verilen adli kontrol tedbirlerinin KALDIRILMASI talebimizdir.",
                                    "aciklama": "1- Adli kontrol tedbiri müvekkilin çalışma ve seyahat hürriyetini ölçüsüz kısıtlamaktadır.\\n2- CMK m. 111 uyarınca adli kontrolün kaldırılmasını talep ederiz.",
                                    "hukuki_sebepler": "CMK m. 109, 110, 111 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Soruşturma dosyası ve mazeret belgeleri.",
                                    "sonuc": "Adli kontrol kararının KALDIRILMASINA karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "sikayet",
                        "category": "ceza",
                        "icon": "⚖️",
                        "title": "Suç Duyurusu (Cumhuriyet Başsavcılığı)",
                        "desc": "Cumhuriyet Başsavcılığı'na şikayet ve kamu davası açılması talebi.",
                        "court_type": "savcilik",
                        "data": {
                                    "mahkeme": "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "MÜŞTEKİ",
                                    "m_ad": "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "ŞÜPHELİ / ŞÜPHELİLER",
                                    "k_ad": "[Şüpheli Adı Soyadı - T.C. / Adres]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Şüpheli hakkında gerekli soruşturmanın yürütülerek KAMU DAVASI AÇILMASI talebimizdir.",
                                    "aciklama": "1- Şüpheli şahıs müvekkile karşı suç teşkil eden eylemlerde bulunmuştur.\\n2- Şüphelinin cezalandırılması için kamu davası açılması zorunludur.",
                                    "hukuki_sebepler": "TCK, CMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yazışmalar, dekontlar, kamera görüntüleri, tanık.",
                                    "sonuc": "Şüpheli hakkında KAMU DAVASI AÇILMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "savcilik_savunma",
                        "category": "ceza",
                        "icon": "🛡️",
                        "title": "Savcılık Savunma Dilekçesi",
                        "desc": "Soruşturma dosyasında şüpheli müdafi olarak savunma sunumu ve KYOK talebi.",
                        "court_type": "savcilik",
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
                                    "konu": "Müştekinin haksız ve soyut şikayetine karşı savunmalarımızın sunulması ve KOVUŞTURMAYA YER OLMADIĞINA DAİR KARAR (KYOK) verilmesi talebimizdir.",
                                    "aciklama": "1- Müştekinin şikayeti somut delilden yoksundur.\\n2- Suçun yasal unsurları oluşmamıştır.\\n3- CMK m. 172 uyarınca KYOK kararı verilmelidir.",
                                    "hukuki_sebepler": "TCK, CMK m. 170, 172 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Yazılı belgeler, kamera kayıtları, tanık beyanları.",
                                    "sonuc": "Müvekkil hakkında KOVUŞTURMAYA YER OLMADIĞINA DAİR KARAR (KYOK) verilmesini talep ederiz."
                        }
            },
            {
                        "id": "kyok",
                        "category": "ceza",
                        "icon": "📑",
                        "title": "KYOK (Takipsizlik) Kararına İtiraz",
                        "desc": "Cumhuriyet Başsavcılığı takipsizlik kararına karşı Sulh Ceza Hakimliği'ne itiraz.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ SULH CEZA HÂKİMLİĞİNE\\nGönderilmek Üzere\\nMERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "Soruşturma No: 2026/... - Karar No: 2026/...",
                                    "m_sifat": "MÜŞTEKİ İTİRAZ EDEN",
                                    "m_ad": "[Müşteki Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "ŞÜPHELİ",
                                    "k_ad": "[Şüpheli Adı Soyadı]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Cumhuriyet Başsavcılığı'nın ... tarihli Kovuşturmaya Yer Olmadığına Dair Kararına (KYOK) İTİRAZLARIMIZIN sunulmasıdır.",
                                    "aciklama": "1- Eksik soruşturma ile takipsizlik kararı verilmiştir.\\n2- Kamu davası açılması için yeterli şüphe mevcuttur.",
                                    "hukuki_sebepler": "CMK m. 172, 173 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Soruşturma dosyası.",
                                    "sonuc": "KYOK kararının KALDIRILMASINA ve kamu davası açılmasına karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "dijital_materyal_iade",
                        "category": "ceza",
                        "icon": "💻",
                        "title": "Dijital Materyallerin İadesi Dilekçesi",
                        "desc": "CMK m. 134 uyarınca el konulan dijital materyallerin ivedi iadesi talebi.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "MERSİN CUMHURİYET BAŞSAVCILIĞINA",
                                    "talep": "",
                                    "dosya": "Soruşturma No: 2026/...",
                                    "m_sifat": "ŞÜPHELİ / SANIK",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ",
                                    "k_ad": "[Varsa Müşteki]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Müvekkilden muhafaza altına alınan dijital materyallerin CMK m. 134 uyarınca İVEDİ OLARAK İADESİ talebimizdir.",
                                    "aciklama": "1- Dijital cihazların imaj alma/adli bilişim incelemesi tamamlanmıştır.\\n2- CMK m. 134/4 gereğince materyallerin gecikmeksizin iadesi zorunludur.",
                                    "hukuki_sebepler": "CMK m. 131, 134 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Elkoyma tutanağı ve dosya kapsamı.",
                                    "sonuc": "Dijital materyallerin MÜVEKKİLE / VEKİLİNE İVEDİLİKLE İADESİNE karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "icra_sikayet",
                        "category": "icra",
                        "icon": "⚖️",
                        "title": "İcra Mahkemesi Şikayet Dilekçesi",
                        "desc": "İcra müdürlüğü işleminin kanuna aykırılığı nedeniyle şikayet ve iptal talebi.",
                        "court_type": "icra",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
                                    "talep": "TAKİBİN DURDURULMASI TALEBİDİR",
                                    "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Karşı Taraf Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Karşı Taraf Vekili]",
                                    "hed": "",
                                    "konu": "Mersin ... İcra Dairesi'nin usul ve yasaya aykırı işleminin İPTALİ talebimizdir.",
                                    "aciklama": "1- İcra müdürlüğü işlemi İİK amir hükümlerine açıkça aykırıdır.\\n2- İİK m. 16 uyarınca işlemin iptali gerekmektedir.",
                                    "hukuki_sebepler": "İİK m. 16, 17, 18 ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra takip dosyası.",
                                    "sonuc": "İcra müdürlüğü işleminin İPTALİNE, takibin tedbiren durdurulmasına karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "icra_itiraz",
                        "category": "icra",
                        "icon": "🛑",
                        "title": "İcra Takibine İtiraz Dilekçesi",
                        "desc": "İlamsız icra takibine (Örnek No: 7) süresi içinde borca, faize ve yetkiye itiraz.",
                        "court_type": "icra",
                        "data": {
                                    "mahkeme": "MERSİN ... İCRA DAİRESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "BORÇLU",
                                    "m_ad": "[Borçlu Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "ALACAKLI",
                                    "k_ad": "[Alacaklı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Alacaklı Vekili]",
                                    "hed": "",
                                    "konu": "Müdürlüğünüzün yukarıda esas numarası yazılı takibine, ödeme emrine, borca, faize ve tüm fer'ilerine süresi içinde İTİRAZLARIMIZIN sunulmasıdır.",
                                    "aciklama": "1- Müvekkilin alacaklı tarafa herhangi bir borcu bulunmamaktadır.\\n2- Takibe, borcun tamamına, faiz oranına ve fer'ilerine açıkça itiraz ediyoruz.\\n3- İİK m. 62 uyarınca takibin durdurulması gerekmektedir.",
                                    "hukuki_sebepler": "İİK m. 62 ve ilgili mevzuat.",
                                    "hukuki_deliller": "Ödeme belgeleri, banka kayıtları ve her türlü delil.",
                                    "sonuc": "İtirazımızın kabulü ile müvekkil aleyhine başlatılan icra takibinin DURDURULMASINA karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "kambiyo_itiraz",
                        "category": "icra",
                        "icon": "✍️",
                        "title": "Kambiyo Senetlerine Özgü Takibe İtiraz / Şikayet",
                        "desc": "Örnek No: 10 kambiyo takibinde imzaya, borca itiraz ve takibin geçici durdurulması.",
                        "court_type": "icra",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İCRA HUKUK MAHKEMESİNE",
                                    "talep": "TAKİBİN GEÇİCİ OLARAK DURDURULMASI TALEPLİDİR",
                                    "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
                                    "m_sifat": "DAVACI BORÇLU",
                                    "m_ad": "[Borçlu Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI ALACAKLI",
                                    "k_ad": "[Alacaklı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Alacaklı Vekili]",
                                    "hed": "[... TL (Takip Tutarı)]",
                                    "konu": "Takibe dayanak bonodaki imzaya/borca itirazlarımız ile takibin geçici durdurulması ve iptali talebimizdir.",
                                    "aciklama": "1- Takibe konu senetteki imza müvekkile ait değildir.\\n2- İİK m. 170 uyarınca imza incelemesi yapılmalıdır.",
                                    "hukuki_sebepler": "İİK m. 168, 169, 170 ve ilgili mevzuat.",
                                    "hukuki_deliller": "İcra dosyası, imza örnekleri, grafoloji bilirkişi incelemesi.",
                                    "sonuc": "İmzaya itirazımızın KABULÜ ile takibin İPTALİNE, alacaklı aleyhine tazminata hükmedilmesine karar verilmesini talep ederiz."
                        }
            },
            {
                        "id": "haciz_talep",
                        "category": "icra",
                        "icon": "🚛",
                        "title": "İcra Dairesi Haciz ve Muhafaza Talep Dilekçesi",
                        "desc": "Kesinleşen icra takibinde borçlunun araç, taşınmaz, banka ve menkul mallarına haciz talebi.",
                        "court_type": "icra",
                        "data": {
                                    "mahkeme": "MERSİN ... İCRA DAİRESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "ALACAKLI VEKİLİ",
                                    "m_ad": "Av. Lütfi Serkan SAYOĞLU",
                                    "m_adres": "[Büro Adresi]",
                                    "k_sifat": "BORÇLU",
                                    "k_ad": "[Borçlu Adı Soyadı - T.C. No]",
                                    "k_vekil": "",
                                    "hed": "",
                                    "konu": "Kesinleşen takipte borçlunun malvarlığı üzerine UYAP üzerinden HACİZ KONULMASI talebimizdir.",
                                    "aciklama": "1- Borçluya gönderilen ödeme emri kesinleşmiştir.\\n2- Borçlu adına kayıtlı taşınmazlara (TAKBİS), araçlara (EGM), banka hesaplarına (89/1) ve SGK kayıtlarına haciz konulmasını talep ederiz.",
                                    "hukuki_sebepler": "İİK m. 78, 85 vd.",
                                    "hukuki_deliller": "İcra takip dosyası.",
                                    "sonuc": "Talebimiz doğrultusunda gerekli haciz işlemlerinin derhal yapılmasına karar verilmesini talep ederim."
                        }
            },
            {
                        "id": "icra_ceza_savunma",
                        "category": "icra",
                        "icon": "🛡️",
                        "title": "İcra Ceza Savunma Dilekçesi",
                        "desc": "Taahhüdü ihlal veya nafaka ödememe şikayetine karşı savunma ve beraat.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "MERSİN [..]. İCRA CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "2026/... Esas",
                                    "m_sifat": "SANIK BORÇLU",
                                    "m_ad": "[Sanık Borçlu Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "MÜŞTEKİ ALACAKLI",
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
                        "category": "icra",
                        "icon": "⚖️",
                        "title": "İcra Ceza Şikayet Dilekçesi (Taahhüdü İhlal / Nafaka)",
                        "desc": "İİK m. 340 taahhüdü ihlal veya m. 344 nafaka borcunu ödememe şikayeti.",
                        "court_type": "ceza",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İCRA CEZA MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "Mersin ... İcra Dairesi - 2026/... E.",
                                    "m_sifat": "MÜŞTEKİ ALACAKLI",
                                    "m_ad": "[Müşteki Alacaklı Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "SANIK BORÇLU",
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
                        "id": "alacak_dava",
                        "category": "ozel_dava",
                        "icon": "💰",
                        "title": "Alacak ve Maddi Tazminat Dava Dilekçesi",
                        "desc": "Sözleşmeden, haksız fiilden veya ticari ilişkiden doğan alacak ve maddi tazminat davası.",
                        "court_type": "hukuk",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı - T.C. / Vergi No]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "10.000,00 TL (Fazlaya ilişkin haklarımız saklı kalmak kaydıyla)",
                                    "konu": "Müvekkilin ödenmeyen alacağının ve ticari/maddi tazminatın faiziyle birlikte tahsili talebidir.",
                                    "aciklama": "1- Müvekkil ile davalı taraf arasındaki ticari/hukuki ilişkiden doğan alacak vadesinde ödenmemiştir.\\n2- Davalıya gönderilen ihtarlara rağmen borç ifa edilmemiş olup dava açma zorunluluğu hasıl olmuştur.\\n3- Alacağın tahsilinin temini için davalının malvarlığı üzerine ihtiyati tedbir konulmasını talep ederiz.",
                                    "hukuki_sebepler": "TBK, HMK, TTK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Sözleşme, faturalar, banka kayıtları, yazışmalar, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                                    "sonuc": "Yukarıda arz ve izah edilen nedenlerle; fazlaya ilişkin haklarımız saklı kalmak kaydıyla DAVAMIZIN KABULÜNE, alacağımızın temerrüt tarihinden itibaren işleyecek faiziyle birlikte tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini saygıyla vekâleten arz ve talep ederiz."
                        }
            },
            {
                        "id": "iscilik_alacak",
                        "category": "ozel_dava",
                        "icon": "👷",
                        "title": "İşçilik Alacakları ve Kıdem Tazminatı Dava Dilekçesi",
                        "desc": "Kıdem, ihbar tazminatı, fazla mesai, UBGT ve yıllık izin ücreti alacakları davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ İŞ MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI İŞÇİ",
                                    "m_ad": "[Davacı İşçi Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI İŞVEREN",
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
                        "id": "bosanma_dava",
                        "category": "ozel_dava",
                        "icon": "💍",
                        "title": "Boşanma Dava Dilekçesi (Çekişmeli)",
                        "desc": "Evlilik birliğinin temelinden sarsılması, nafaka, velayet ve maddi/manevi tazminat talepli.",
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
                        "id": "kira_tahliye",
                        "category": "ozel_dava",
                        "icon": "🏠",
                        "title": "Kira Tahliye ve Alacak Dava Dilekçesi",
                        "desc": "Kiralananın tahliyesi (tahliye taahhüdü / temerrüt) ve kira alacağı davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ SULH HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI KİRAYA VEREN",
                                    "m_ad": "[Kiraya Veren Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI KİRACI",
                                    "k_ad": "[Kiracı Adı Soyadı - T.C. No]",
                                    "k_vekil": "[Varsa Kiracı Vekili]",
                                    "hed": "[... TL (Bir Yıllık Kira Bedeli)]",
                                    "konu": "Taşınmazın tahliyesi ile ödenmeyen kira bedellerinin yasal faiziyle tahsili talebidir.",
                                    "aciklama": "1- Davalı, müvekkile ait taşınmazda ... tarihli kira sözleşmesi uyarınca kiracı olarak oturmaktadır.\\n2- Davalı taraf vadesi gelen kira bedellerini ödememiş / tahliye taahhüdüne uymamıştır.\\n3- TBK hükümleri uyarınca taşınmazın tahliyesini talep etme zorunluluğu doğmuştur.",
                                    "hukuki_sebepler": "TBK m. 315, 352 vd., HMK, İİK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Kira sözleşmesi, tahliye taahhütnamesi, banka dekontları, ihtarname, tanık, bilirkişi, yemin ve sair hukuki deliller.",
                                    "sonuc": "Davalının kiralanan taşınmazdan TAHLİYESİNE, ödenmeyen kira bedellerinin faiziyle tahsiline, yargılama giderleri ve vekâlet ücretinin davalıya yükletilmesine karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "kira_tespit",
                        "category": "ozel_dava",
                        "icon": "📈",
                        "title": "Kira Bedelinin Tespiti (Artırım) Dava Dilekçesi",
                        "desc": "5 yılı aşan kira ilişkilerinde emsal rayiçlere göre kira bedelinin tespiti davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ SULH HUKUK MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI KİRAYA VEREN",
                                    "m_ad": "[Kiraya Veren Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI KİRACI",
                                    "k_ad": "[Kiracı Adı Soyadı - T.C. No]",
                                    "k_vekil": "[Varsa Kiracı Vekili]",
                                    "hed": "[... TL (Aylık Artış Farkının Yıllık Değeri)]",
                                    "konu": "Kira bedelinin yeni dönem için aylık ... TL olarak TESPİTİ talebidir.",
                                    "aciklama": "1- Taraflar arasındaki kira ilişkisi 5 yılı doldurmuştur.\\n2- Taşınmazın bulunduğu bölgedeki emsal rayiçler ve TÜFE oranları gözetildiğinde ödenen bedel çok düşük kalmıştır.\\n3- TBK m. 344 uyarınca kira bedelinin hak ve nesafete uygun tespitini talep ederiz.",
                                    "hukuki_sebepler": "TBK m. 344 vd., HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Kira sözleşmesi, emsal kira sözleşmeleri, keşif, bilirkişi incelemesi ve sair deliller.",
                                    "sonuc": "Kira bedelinin yeni kira döneminden itibaren geçerli olmak üzere AYLIK ... TL OLARAK TESPİTİNE karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "tuketici_dava",
                        "category": "ozel_dava",
                        "icon": "🛒",
                        "title": "Tüketici Mahkemesi Dava Dilekçesi",
                        "desc": "Ayıplı mal/hizmet, sözleşmeden dönme ve bedel iadesi talepli tüketici davası.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ TÜKETİCİ MAHKEMESİNE",
                                    "talep": "",
                                    "dosya": "",
                                    "m_sifat": "DAVACI TÜKETİCİ",
                                    "m_ad": "[Tüketici Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Müvekkil Adresi]",
                                    "k_sifat": "DAVALI SATICI",
                                    "k_ad": "[Davalı Şirket Unvanı - Vergi No]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[... TL (Satış Bedeli İadesi)]",
                                    "konu": "Ayıplı mal nedeniyle sözleşmeden dönülerek ödenen bedelin yasal faiziyle iadesi talebidir.",
                                    "aciklama": "1- Müvekkil davalıdan ... tarihinde faturalı ürün satın almıştır.\\n2- Üründe kullanım amacına aykırı gizli/açık ayıp ortaya çıkmış, yasal sürede ayıp ihbarında bulunulmuştur.\\n3- Davalı tarafça sorun giderilmemiş olup 6502 sayılı Kanun uyarınca bedel iadesi talep zorunluluğu doğmuştur.",
                                    "hukuki_sebepler": "6502 sayılı TKHK, TBK, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Fatura, servis fişleri, arabuluculuk tutanağı, bilirkişi incelemesi ve sair deliller.",
                                    "sonuc": "Davamızın KABULÜ ile ayıplı ürünün iadesi karşılığında ödenen satış bedelinin faiziyle tahsiline karar verilmesini vekâleten saygıyla arz ve talep ederiz."
                        }
            },
            {
                        "id": "tapu_iptal",
                        "category": "ozel_dava",
                        "icon": "📜",
                        "title": "Tapu İptali ve Tescil Dava Dilekçesi",
                        "desc": "Muris muvazaası / inançlı işlem / vekalet görevinin kötüye kullanılması nedeniyle tapu iptal ve tescil.",
                        "data": {
                                    "mahkeme": "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE",
                                    "talep": "TAPU KAYDINA İHTİYATİ TEDBİR TALEPLİDİR",
                                    "dosya": "",
                                    "m_sifat": "DAVACI",
                                    "m_ad": "[Davacı Müvekkil Adı Soyadı - T.C. 12345678901]",
                                    "m_adres": "[Davacı Müvekkil Adresi]",
                                    "k_sifat": "DAVALI",
                                    "k_ad": "[Davalı Adı Soyadı / Unvanı]",
                                    "k_vekil": "[Varsa Davalı Vekili]",
                                    "hed": "[... TL (Taşınmazın Harca Esas Değeri)]",
                                    "konu": "Dava konusu taşınmazın tapu kaydının iptali ile müvekkil adına payı oranında tescili talebimizdir.",
                                    "aciklama": "1- Dava konusu taşınmaz, mirasbırakan tarafından diğer mirasçılardan mal kaçırmak kastıyla muvazaalı devredilmiştir.\\n2- Taşınmazın üçüncü kişilere devrinin önlenmesi için tapu kaydına ihtiyati tedbir konulması zorunludur.\\n3- Tapu kaydının iptali ile müvekkil adına tescili talep olunur.",
                                    "hukuki_sebepler": "TMK, TBK, HMK ve ilgili mevzuat.",
                                    "hukuki_deliller": "Tapu kayıtları, resmi senetler, mirasçılık belgesi, tanık, bilirkişi, keşif ve sair deliller.",
                                    "sonuc": "Taşınmaz üzerine İHTİYATİ TEDBİR KONULMASINA, tapu kaydının İPTALİ ile tesciline karar verilmesini saygıyla vekâleten arz ve talep ederiz."
                        }
            }
];

        // Varsayılan Sık Kullanılanlar
        const DEFAULT_FAVORITES = ["genel_dava_dilekcesi", "cevap", "delil_bildirme", "istinaf_hukuk", "ceza_savunma"];
        
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

        function renderTemplates() {
            const grid = document.getElementById("templateGrid");
            const query = document.getElementById("searchInput").value.toLowerCase().trim();
            const favs = getFavorites();
            grid.innerHTML = "";

            const filtered = TEMPLATES.filter(t => {
                // If user types search query, search globally across all 46 templates!
                const matchCat = (!query) ? (currentCategory === "all" || t.category === currentCategory) : true;
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

                        let pendingTemplateId = null;
        let selectedCourtType = null;

        const HUKUK_COURT_OPTIONS = [
            { type: "ASLİYE HUKUK", icon: "🏛️", title: "Asliye Hukuk", desc: "Genel Hukuk Davaları" },
            { type: "SULH HUKUK", icon: "🏠", title: "Sulh Hukuk", desc: "Kira / Tahliye / İzale-i Şuyu" },
            { type: "İŞ", icon: "👷", title: "İş Mahkemesi", desc: "İşçilik & Kıdem Alacakları" },
            { type: "AİLE", icon: "💍", title: "Aile Mahkemesi", desc: "Boşanma, Velayet & Nafaka" },
            { type: "TÜKETİCİ", icon: "🛒", title: "Tüketici Mahkemesi", desc: "Ayıplı Mal & İade" },
            { type: "ASLİYE TİCARET", icon: "📈", title: "Asliye Ticaret", desc: "Ticari Uyuşmazlıklar" },
            { type: "İCRA HUKUK", icon: "⚖️", title: "İcra Hukuk", desc: "Takibe İtiraz & Şikayet" }
        ];

        const CEZA_COURT_OPTIONS = [
            { type: "ASLİYE CEZA", icon: "🛡️", title: "Asliye Ceza", desc: "Asliye Ceza Mahkemesi" },
            { type: "AĞIR CEZA", icon: "🏛️", title: "Ağır Ceza", desc: "Ağır Ceza Mahkemesi" },
            { type: "SULH CEZA", icon: "⚖️", title: "Sulh Ceza Hâkimliği", desc: "Sorgu / Tutuklama / İtiraz" },
            { type: "İCRA CEZA", icon: "📋", title: "İcra Ceza", desc: "Taahhüdü İhlal / Tazyik Hapsi" }
        ];

        // Temel Taraf Sıfatları (İstinaf / İtiraz / Şikayet durumunda sihirbaz otomatik önek ekler!)
        const HUKUK_PARTY_ROLES = [
            { m_sifat: "DAVACI", k_sifat: "DAVALI", icon: "⚖️", title: "Davacı", desc: "Karşı Taraf: DAVALI" },
            { m_sifat: "DAVALI", k_sifat: "DAVACI", icon: "🛡️", title: "Davalı", desc: "Karşı Taraf: DAVACI" },
            { m_sifat: "TALEP EDEN", k_sifat: "KARŞI TARAF", icon: "📝", title: "Talep Eden", desc: "Değişik İş / Genel Talep" },
            { m_sifat: "VASİ", k_sifat: "KISITLI", icon: "🤝", title: "Vasi", desc: "Vesayet Dosyaları" },
            { m_sifat: "KISITLI", k_sifat: "TALEP EDEN", icon: "👤", title: "Kısıtlı / Kısıtlı Adayı", desc: "Vesayet / Kısıtlama İtirazı" },
            { m_sifat: "İHTİYATİ TEDBİR TALEP EDEN", k_sifat: "ALEYHİNE TEDBİR TALEP EDİLEN", icon: "🔒", title: "Tedbir Talep Eden", desc: "İhtiyati Tedbir Talebi" },
            { m_sifat: "ALEYHİNE TEDBİR TALEP EDİLEN", k_sifat: "İHTİYATİ TEDBİR TALEP EDEN", icon: "🔓", title: "Aleyhine Tedbir Talep Edilen", desc: "Tedbire İtiraz" },
            { m_sifat: "ŞİKAYET EDEN", k_sifat: "ŞİKAYET OLUNAN", icon: "⚠️", title: "Şikayet Eden", desc: "İcra Memur Muamelesi Şikayeti" },
            { m_sifat: "ŞİKAYET OLUNAN", k_sifat: "ŞİKAYET EDEN", icon: "🛡️", title: "Şikayet Olunan", desc: "İcra Şikayetine Cevap" },
            { m_sifat: "İHBAR OLUNAN", k_sifat: "DAVACI / DAVALI", icon: "📢", title: "İhbar Olunan", desc: "Davanın İhbarı / Yan Müdahale" },
            { m_sifat: "MİRASÇI", k_sifat: "DAVALI / DİĞER MİRASÇILAR", icon: "📜", title: "Mirasçı", desc: "Mirasçılık ve Tereke Dosyaları" },
            { m_sifat: "ÜÇÜNCÜ KİŞİ", k_sifat: "ALACAKLI / BORÇLU", icon: "🏢", title: "Üçüncü Kişi", desc: "İstihkak / 89 Haciz İtirazı" }
        ];

        const CEZA_PARTY_ROLES = [
            { m_sifat: "SANIK", k_sifat: "KATILAN / MÜŞTEKİ", icon: "⚖️", title: "Sanık", desc: "Kovuşturma / Ceza Mahkemesi" },
            { m_sifat: "ŞÜPHELİ", k_sifat: "MÜŞTEKİ", icon: "🛡️", title: "Şüpheli", desc: "Soruşturma / Sulh Ceza Sorgu" },
            { m_sifat: "KATILAN", k_sifat: "SANIK", icon: "🏛️", title: "Katılan (Müdahil)", desc: "Kamu Davasına Katılan" },
            { m_sifat: "MÜŞTEKİ", k_sifat: "ŞÜPHELİ / SANIK", icon: "📋", title: "Müşteki (Şikayetçi)", desc: "Suçtan Zarar Gören / Şikayet Eden" },
            { m_sifat: "MALEN SORUMLU", k_sifat: "KATILAN", icon: "💼", title: "Malen Sorumlu", desc: "Tazminat / Müsadere Sorumlusu" }
        ];

        function openDirect(tplId) {
            const t = TEMPLATES.find(x => x.id === tplId);
            if (!t) return;

            // If template has court_type specified, open Court & Party Picker Wizard!
            if (t.court_type === "hukuk" || t.court_type === "ceza") {
                pendingTemplateId = tplId;
                selectedCourtType = null;

                // Step 1: Render Courts
                document.getElementById("modalStepIcon").textContent = (t.court_type === "ceza") ? "🛡️" : "🏛️";
                document.getElementById("courtModalTitle").textContent = "1. Adım: Mahkeme Türünü Seçin";
                document.getElementById("courtModalSubtitle").textContent = `${t.title} için mahkeme seçin.`;
                
                document.getElementById("step1CourtContainer").classList.remove("hidden");
                document.getElementById("step2PartyContainer").classList.add("hidden");
                document.getElementById("btnBackToCourts").classList.add("hidden");

                const grid = document.getElementById("courtOptionsGrid");
                grid.innerHTML = "";

                const options = (t.court_type === "ceza") ? CEZA_COURT_OPTIONS : HUKUK_COURT_OPTIONS;
                options.forEach(opt => {
                    const btn = document.createElement("button");
                    btn.className = "p-3 text-left rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/70 transition flex flex-col justify-between";
                    btn.onclick = () => onCourtSelected(opt.type);
                    btn.innerHTML = `
                        <div class="font-bold text-xs text-slate-900 flex items-center gap-1.5">
                            <span>${opt.icon}</span> <span>${opt.title}</span>
                        </div>
                        <div class="text-[10px] text-slate-500 mt-1">${opt.desc}</div>
                    `;
                    grid.appendChild(btn);
                });

                document.getElementById("courtPickerModal").classList.remove("hidden");
                return;
            }

            executeDirectGenerate(t.data, t.title);
        }

        function onCourtSelected(courtType) {
            selectedCourtType = courtType;
            const t = TEMPLATES.find(x => x.id === pendingTemplateId);

            // Step 2: Show Party Roles
            document.getElementById("step1CourtContainer").classList.add("hidden");
            document.getElementById("step2PartyContainer").classList.remove("hidden");
            document.getElementById("btnBackToCourts").classList.remove("hidden");

            document.getElementById("modalStepIcon").textContent = "👤";
            document.getElementById("courtModalTitle").textContent = `2. Adım: Müvekkil Sıfatı (${courtType})`;
            document.getElementById("courtModalSubtitle").textContent = "Dilekçedeki taraf sıfatını tek tıkla belirleyin:";

            const partyGrid = document.getElementById("partyOptionsGrid");
            partyGrid.innerHTML = "";

            const isCeza = (t.court_type === "ceza" || courtType.includes("CEZA") || courtType.includes("AĞIR"));
            const roles = isCeza ? CEZA_PARTY_ROLES : HUKUK_PARTY_ROLES;

            roles.forEach(role => {
                const btn = document.createElement("button");
                btn.className = "p-3 text-left rounded-xl border border-slate-200 hover:border-blue-500 hover:bg-blue-50/70 transition flex flex-col justify-between";
                btn.onclick = () => finishWizardAndGenerate(role.m_sifat, role.k_sifat);
                btn.innerHTML = `
                    <div class="font-bold text-xs text-slate-900 flex items-center gap-1.5">
                        <span>${role.icon}</span> <span>${role.title}</span>
                    </div>
                    <div class="text-[10px] text-slate-500 mt-1">${role.desc}</div>
                `;
                partyGrid.appendChild(btn);
            });
        }

        function backToStep1() {
            document.getElementById("step1CourtContainer").classList.remove("hidden");
            document.getElementById("step2PartyContainer").classList.add("hidden");
            document.getElementById("btnBackToCourts").classList.add("hidden");

            const t = TEMPLATES.find(x => x.id === pendingTemplateId);
            document.getElementById("modalStepIcon").textContent = (t && t.court_type === "ceza") ? "🛡️" : "🏛️";
            document.getElementById("courtModalTitle").textContent = "1. Adım: Mahkeme Türünü Seçin";
            document.getElementById("courtModalSubtitle").textContent = "Dilekçenin sunulacağı mahkemeyi seçin.";
        }

        function closeCourtPickerModal() {
            document.getElementById("courtPickerModal").classList.add("hidden");
            pendingTemplateId = null;
            selectedCourtType = null;
        }

                function applyCustomPartyRole() {
            const input = document.getElementById("customPartyInput");
            const val = input.value.trim().toUpperCase();
            if (!val) {
                showToast("Lütfen bir sıfat yazın", "error");
                return;
            }
            finishWizardAndGenerate(val, "KARŞI TARAF");
        }

        function finishWizardAndGenerate(m_sifat, k_sifat) {
            if (!pendingTemplateId || !selectedCourtType) return;
            const t = TEMPLATES.find(x => x.id === pendingTemplateId);
            if (!t) return;

            const lp = getLawyerProfile();
            const city = lp.city || "MERSİN";
            const bamCity = lp.bamCity || "ADANA";
            const courtType = selectedCourtType;

            let copyData = { ...t.data };
            
            // 1. Adapt Mahkeme Heading
            if (t.id.includes("istinaf")) {
                if (courtType.includes("CEZA") || courtType.includes("AĞIR")) {
                    copyData.mahkeme = `${bamCity} BÖLGE ADLİYE MAHKEMESİ İLGİLİ CEZA DAİRESİNE\nGönderilmek Üzere\n${city} [..]. ${courtType} MAHKEMESİNE`;
                } else {
                    copyData.mahkeme = `${bamCity} BÖLGE ADLİYE MAHKEMESİ İLGİLİ HUKUK DAİRESİNE\nGönderilmek Üzere\n${city} [..]. ${courtType} MAHKEMESİNE`;
                }
            } else if (t.id.includes("dava") || t.id.includes("iptali")) {
                if (courtType === "SULH CEZA") {
                    copyData.mahkeme = `${city} NÖBETÇİ SULH CEZA HÂKİMLİĞİNE`;
                } else {
                    copyData.mahkeme = `${city} NÖBETÇİ ${courtType} MAHKEMESİNE`;
                }
            } else {
                if (courtType === "SULH CEZA") {
                    copyData.mahkeme = `${city} [..]. SULH CEZA HÂKİMLİĞİNE`;
                } else {
                    copyData.mahkeme = `${city} [..]. ${courtType} MAHKEMESİNE`;
                }
            }

            // 2. Apply Smart Contextual Prefixes (İstinaf, İtiraz, Şikayet Uyarlaması)
            let finalMSifat = m_sifat;
            let finalKSifat = k_sifat;

            if (t.id === "istinaf_hukuk" || t.id === "ceza_istinaf") {
                // İstinaf Başvuru Dilekçesi: "İSTİNAF EDEN DAVALI" veya "İSTİNAF EDEN SANIK"
                if (!finalMSifat.startsWith("İSTİNAF EDEN")) {
                    finalMSifat = `İSTİNAF EDEN ${finalMSifat}`;
                }
                if (!finalKSifat.startsWith("İSTİNAFA CEVAP VEREN") && !finalKSifat.startsWith("KARŞI TARAF")) {
                    finalKSifat = `İSTİNAFA CEVAP VEREN ${finalKSifat}`;
                }
            } else if (t.id === "istinafa_cevap") {
                // İstinafa Cevap Dilekçesi: "İSTİNAFA CEVAP VEREN DAVACI" / "İSTİNAF EDEN DAVALI"
                if (!finalMSifat.startsWith("İSTİNAFA CEVAP VEREN")) {
                    finalMSifat = `İSTİNAFA CEVAP VEREN ${finalMSifat}`;
                }
                if (!finalKSifat.startsWith("İSTİNAF EDEN")) {
                    finalKSifat = `İSTİNAF EDEN ${finalKSifat}`;
                }
            } else if (t.id === "istinaftan_feragat") {
                if (!finalMSifat.startsWith("İSTİNAFTAN FERAGAT EDEN")) {
                    finalMSifat = `İSTİNAFTAN FERAGAT EDEN ${finalMSifat}`;
                }
            } else if (t.id === "tutuklama" || t.id === "adli_kontrol" || t.id === "kyok") {
                if (!finalMSifat.startsWith("İTİRAZ EDEN")) {
                    finalMSifat = `İTİRAZ EDEN ${finalMSifat}`;
                }
            }

            copyData.m_sifat = finalMSifat;
            copyData.k_sifat = finalKSifat;

            closeCourtPickerModal();
            executeDirectGenerate(copyData, `${t.title} (${courtType} - ${finalMSifat})`);
        }

        async function executeDirectGenerate(dataObj, title) {
            showToast(`⏳ ${title} UYAP'ta açılıyor...`, "info");
            const formattedData = formatDataForCity(dataObj);
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
                    showToast(`✅ ${title} UYAP Doküman Editörü'nde açıldı!`, "success");
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
            document.getElementById("sonuc").value = fd.sonuc || "Yukarıda arz ve izah edilen nedenlerle; DAVAMIZIN KABULÜNE, yargılama giderleri ve vekâlet ücretinin karşı tarafa yükletilmesine karar verilmesini saygıyla vekâleten arz ve talep ederiz.";

            calculateCourtFees();
            renderChipsOnForm();
            updateLivePreview();

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
                sonuc: document.getElementById("sonuc").value.trim(),
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
            checkFirstTimeLawyerSetup();
        };
    
        // ==========================================
        // 1. MÜVEKKİL & TARAF REHBERİ (LOCAL CRM)
        // ==========================================
        const CLIENTS_STORAGE_KEY = "dilekce_saved_clients";

        function getSavedClients() {
            try {
                const data = localStorage.getItem(CLIENTS_STORAGE_KEY);
                return data ? JSON.parse(data) : [
                    { name: "Ahmet YILMAZ", tc: "12345678901", adres: "Atatürk Cad. No:10 D:5 Yenişehir / MERSİN", sifat: "DAVACI" },
                    { name: "Mehmet KAYA", tc: "98765432109", adres: "İnönü Mah. Barboros Bulvarı No:45 Mezitli / MERSİN", sifat: "DAVACI" },
                    { name: "Ayşe DEMİR", tc: "55544433322", adres: "Akdeniz Mah. Liman Cad. No:8 Akdeniz / MERSİN", sifat: "DAVALI" }
                ];
            } catch(e) {
                return [];
            }
        }

        function saveClientToStorage(client) {
            const list = getSavedClients();
            const existsIndex = list.findIndex(c => c.name.toLowerCase() === client.name.toLowerCase() || (client.tc && c.tc === client.tc));
            if (existsIndex >= 0) {
                list[existsIndex] = client;
            } else {
                list.unshift(client);
            }
            localStorage.setItem(CLIENTS_STORAGE_KEY, JSON.stringify(list));
        }

        function deleteClient(name, e) {
            if (e) e.stopPropagation();
            const list = getSavedClients().filter(c => c.name !== name);
            localStorage.setItem(CLIENTS_STORAGE_KEY, JSON.stringify(list));
            renderClientDirectoryList();
            showToast(`🗑️ ${name} rehberden silindi`, "info");
        }

        function openClientDirectoryModal() {
            renderClientDirectoryList();
            document.getElementById("clientDirectoryModal").classList.remove("hidden");
        }

        function closeClientDirectoryModal() {
            document.getElementById("clientDirectoryModal").classList.add("hidden");
        }

        function renderClientDirectoryList() {
            const container = document.getElementById("clientListContainer");
            const query = (document.getElementById("clientSearchInput")?.value || "").toLowerCase().trim();
            const clients = getSavedClients().filter(c => !query || c.name.toLowerCase().includes(query) || (c.tc && c.tc.includes(query)));

            container.innerHTML = "";
            if (clients.length === 0) {
                container.innerHTML = `
                    <div class="py-8 text-center text-slate-400 text-xs font-medium">
                        Kayıtlı müvekkil bulunamadı. Formdaki bilgileri "💾 Rehbere Ekle" ile kaydedebilirsiniz.
                    </div>
                `;
                return;
            }

            clients.forEach(c => {
                const item = document.createElement("div");
                item.className = "p-3 rounded-xl border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 transition cursor-pointer flex items-center justify-between group";
                item.onclick = () => selectClientAndFillForm(c);
                item.innerHTML = `
                    <div>
                        <div class="font-bold text-xs text-slate-900 flex items-center gap-2">
                            <span>👤 ${c.name}</span>
                            ${c.tc ? `<span class="text-[10px] font-normal text-slate-500">T.C: ${c.tc}</span>` : ''}
                        </div>
                        <div class="text-[11px] text-slate-500 mt-0.5 truncate max-w-xs">${c.adres || 'Adres belirtilmemiş'}</div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] bg-indigo-100 text-indigo-800 font-bold px-2 py-0.5 rounded-lg">${c.sifat || 'MÜVEKKİL'}</span>
                        <button onclick="deleteClient('${c.name}', event)" class="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 text-sm transition" title="Sil">🗑️</button>
                    </div>
                `;
                container.appendChild(item);
            });
        }

        function selectClientAndFillForm(c) {
            if (c.sifat) document.getElementById("m_sifat").value = c.sifat;
            document.getElementById("m_ad").value = c.tc ? `${c.name} - T.C. ${c.tc}` : c.name;
            if (c.adres) document.getElementById("m_adres").value = c.adres;
            closeClientDirectoryModal();
            updateLivePreview();
            showToast(`✅ ${c.name} bilgileri forma aktarıldı`, "success");
        }

        function saveCurrentClientToDirectory() {
            const m_ad_raw = document.getElementById("m_ad").value.trim();
            const m_adres = document.getElementById("m_adres").value.trim();
            const m_sifat = document.getElementById("m_sifat").value.trim() || "DAVACI";

            if (!m_ad_raw) {
                showToast("Kaydetmek için en azından Müvekkil İsmini giriniz", "error");
                return;
            }

            let name = m_ad_raw;
            let tc = "";
            if (m_ad_raw.includes("- T.C.")) {
                const parts = m_ad_raw.split("- T.C.");
                name = parts[0].trim();
                tc = parts[1].trim();
            }

            saveClientToStorage({ name, tc, adres: m_adres, sifat: m_sifat });
            showToast(`💾 ${name} Müvekkil Rehberine kaydedildi!`, "success");
        }


        // ==========================================
        // 2. CANLI HARÇ & VEKÂLET ÜCRETİ HESAPLAYICI
        // ==========================================
        function calculateCourtFees() {
            const hedInput = document.getElementById("hed").value;
            const card = document.getElementById("feeCalculatorCard");
            
            // Extract numeric value from string (e.g. "100.000,00 TL" -> 100000)
            const cleaned = hedInput.replace(/[^0-9,.-]/g, "").replace(/\./g, "").replace(",", ".");
            const val = parseFloat(cleaned);

            if (isNaN(val) || val <= 0) {
                card.classList.add("hidden");
                return;
            }

            card.classList.remove("hidden");
            document.getElementById("calcBaseValueLabel").textContent = `Dava Değeri: ${val.toLocaleString('tr-TR', { minimumFractionDigits: 2 })} TL`;

            // 1. Peşin Nispi Harç (%68.31 / 4)
            const pesinHarc = val * 0.06831 / 4;
            document.getElementById("calcPesinHarc").textContent = `${pesinHarc.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TL`;

            // 2. İcra İnkar Tazminatı (%20)
            const inkarTaz = val * 0.20;
            document.getElementById("calcInkarTazminat").textContent = `${inkarTaz.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TL`;

            // 3. Tahmini Nispi AAÜT Kademeli Hesabı
            let aaut = 0;
            if (val <= 40000) aaut = val * 0.16;
            else if (val <= 80000) aaut = 40000 * 0.16 + (val - 40000) * 0.15;
            else if (val <= 180000) aaut = 40000 * 0.16 + 40000 * 0.15 + (val - 80000) * 0.14;
            else if (val <= 500000) aaut = 40000 * 0.16 + 40000 * 0.15 + 100000 * 0.14 + (val - 180000) * 0.11;
            else aaut = 40000 * 0.16 + 40000 * 0.15 + 100000 * 0.14 + 320000 * 0.11 + (val - 500000) * 0.08;
            
            // Asgari maktu sınır gözetimi
            if (aaut < 17900) aaut = 17900;

            document.getElementById("calcAaut").textContent = `${aaut.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} TL`;
        }


        
        // ==========================================
        // 3. KİŞİSELLEŞTİRİLEBİLİR HUKUKİ ÇİP SİSTEMİ
        // ==========================================
        const CHIPS_STORAGE_KEY = "dilekce_custom_chips";

        const DEFAULT_CHIPS = [
            { id: "tanik", category: "hukuk", title: "+ 👥 Tanık Dinletme", content: "TANIK DİNLETME TALEBİMİZ:\\nİddia ve vakıalarımızın sübutu amacıyla bildirdiğimiz tanıkların HMK m. 240 vd. uyarınca duruşmada dinlenilmesini ve tanıklarımıza davetiye çıkarılmasını talep ederiz." },
            { id: "banka", category: "hukuk", title: "+ 🏦 Banka Müzekkeresi", content: "MÜZEKKERE TALEBİMİZ:\\nTaraflar arasındaki ticari ve parasal akışın tespiti için ilgili banka şubelerine müzekkere yazılarak geçmişe dönük tüm hesap hareketleri ve dekontların celbini talep ederiz." },
            { id: "tedbir", category: "hukuk", title: "+ 🔒 İhtiyati Tedbir", content: "İHTİYATİ TEDBİR TALEBİMİZ:\\nDavalının dava konusu taşınmazı/araçları/malvarlığını üçüncü kişilere devretme ve kaçırma ihtimali kuvvetle muhtemel olduğundan HMK m. 389 vd. uyarınca teminatsız olarak İHTİYATİ TEDBİR konulmasını talep ederiz." },
            { id: "bilirkisi_itiraz", category: "hukuk", title: "+ 📊 Bilirkişi Rapor İtirazı", content: "BİLİRKİŞİ RAPORUNA İTİRAZLARIMIZ:\\nDosyaya sunulan bilirkişi raporu eksik incelemeye ve hatalı hesaplama yöntemine dayanmaktadır. HMK m. 281 uyarınca itirazlarımızın kabulü ile ek/yeni bilirkişi raporu aldırılmasını talep ederiz." },
            { id: "zamanasimi", category: "hukuk", title: "+ ⏳ Zamanaşımı Def'i", content: "ZAMANAŞIMI DEF'İ:\\nDavacının talepleri yasal zamanaşımı süresine uğramıştır. Süresi içinde zamanaşımı ilk itirazımızı ileri sürüyor ve davanın zamanaşımı nedeniyle esasa girilmeden REDDİNİ talep ediyoruz." },
            { id: "yemin", category: "hukuk", title: "+ 📜 Yemin Teklifi", content: "YEMİN DELİLİ:\\nİddiamızın sübutu yönünden HMK m. 225 vd. uyarınca karşı tarafa yemin teklif etme hakkımızı saklı tutuyor ve bu doğrultuda yemin teklif ediyoruz." },
            { id: "yargitay", category: "hukuk", title: "+ ⚖️ Yargıtay İçtihadı", content: "YARGITAY YERLEŞİK İÇTİHADI:\\nYargıtay Hukuk Genel Kurulu'nun ve ilgili dairelerin yerleşik içtihatlarında da açıkça vurgulandığı üzere, ispat yükü ve delillerin takdiri hususunda davanın kabulü yasal bir zorunluluktur." },
            { id: "supheden_sanik", category: "ceza", title: "+ ⚖️ Şüpheden Sanık Yararlanır", content: "ŞÜPHEDEN SANIK YARARLANIR İLKESİ (IN DUBIO PRO REO):\\nEvrensel ceza hukuku prensibi olan 'Şüpheden sanık yararlanır' ilkesi gereğince, mahkûmiyet hükmü hiçbir şüpheye yer bırakmayacak kesinlikte delillere dayanmalıdır. Dosyada müvekkilin cezalandırılmasına yeter kesin ve inandırıcı delil bulunmadığından BERAATİNE karar verilmelidir." },
            { id: "kast_yoklugu", category: "ceza", title: "+ 🎯 Suç Kastının Yokluğu", content: "SUÇ KASTININ BULUNMADIĞI VE UNSURLARIN OLUŞMADIĞI:\\nMüvekkilin üzerine atılı suçun maddi ve manevi unsurları kesinlikle oluşmamıştır. Müvekkilin herhangi bir suç işleme kastı veya iradesi bulunmamakta olup eylemin haksız fiil dahi oluşturmadığı açıktır." },
            { id: "hukuka_aykiri_delil", category: "ceza", title: "+ 🚫 Hukuka Aykırı Delil İtirazı", content: "HUKUKA AYKIRI DELİLLERİN HÜKME ESAS ALINAMAYACAĞI (CMK m. 206/2-a ve m. 217/2):\\nAnayasa m. 38/6 ve CMK amir hükümleri uyarınca, hukuka aykırı yöntemlerle elde edilmiş deliller yargılamada kullanılamaz ve hükme esas alınamaz. Dosyadaki hukuka aykırı delillerin dosyadan çıkarılmasını talep ederiz." },
            { id: "haksiz_tahrik", category: "ceza", title: "+ ⚡ Haksız Tahrik İndirimi", content: "HAKSIZ TAHRİK İNDİRİMİ (TCK m. 29):\\nKabul anlamına gelmemek kaydıyla, müvekkilin eylemi karşı tarafın haksız ve ağır tahrik oluşturan söz/fiilleri neticesinde gerçekleşmiştir. TCK m. 29 uyarınca azami oranda haksız tahrik indirimi uygulanmalıdır." },
            { id: "tahliye_talebi", category: "ceza", title: "+ ⛓️ Tahliye Talebi", content: "TUTUKLAMA TEDBİRİNİN ÖLÇÜSÜZLÜĞÜ VE TAHLİYE TALEBİMİZ:\\nTutuklama en son başvurulacak istisnai bir koruma tedbiridir. Müvekkilin sabit ikametgâh sahibi olması, kaçma veya delilleri karartma şüphesinin bulunmaması ve tutuklulukta geçen süre gözetilerek İVEDİLİKLE TAHLİYESİNE karar verilmesini talep ederiz." },
            { id: "adli_kontrol_kifayet", category: "ceza", title: "+ 📋 Adli Kontrolün Yeterliliği", content: "ADLİ KONTROL HÜKÜMLERİNİN YETERLİLİĞİ (CMK m. 109):\\nCMK m. 109 uyarınca adli kontrol tedbirleri amaca ulaşmak için fazlasıyla yeterlidir. Ölçülülük ilkesi gereğince tutuklama kararının kaldırılarak müvekkil hakkında adli kontrol uygulanmasını talep ederiz." },
            { id: "hagb_erteleme", category: "ceza", title: "+ 📝 Lehe Hükümler (HAGB/Erteleme)", content: "LEHE OLAN HÜKÜMLERİN UYGULANMASI (HAGB / ERTELEME):\\nMahkemeniz aksi kanaatte ise; müvekkilin sabıkasız geçmişi, yargılama sürecindeki saygılı tutumu ve pişmanlığı gözetilerek TCK m. 62 (Takdiri İndirim), CMK m. 231 (HAGB) ve TCK m. 51 (Hapis Cezasını Erteleme) hükümlerinin uygulanmasını talep ederiz." }
        ];

        function getAllChips() {
            try {
                const stored = localStorage.getItem(CHIPS_STORAGE_KEY);
                return stored ? JSON.parse(stored) : DEFAULT_CHIPS;
            } catch(e) {
                return DEFAULT_CHIPS;
            }
        }

        function saveAllChips(chips) {
            localStorage.setItem(CHIPS_STORAGE_KEY, JSON.stringify(chips));
            renderChipsOnForm();
            renderChipsManagerList();
        }

        function restoreDefaultChips() {
            if (confirm("Tüm çipleri varsayılan ayarlara döndürmek istediğinize emin misiniz?")) {
                localStorage.removeItem(CHIPS_STORAGE_KEY);
                renderChipsOnForm();
                renderChipsManagerList();
                showToast("🔄 Çipler varsayılana sıfırlandı", "info");
            }
        }

        function renderChipsOnForm() {
            const chips = getAllChips();
            const hukukContainer = document.getElementById("hukukChipsContainer");
            const cezaContainer = document.getElementById("cezaChipsContainer");
            if (!hukukContainer || !cezaContainer) return;

            hukukContainer.innerHTML = "";
            cezaContainer.innerHTML = "";

            chips.forEach(c => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = (c.category === "ceza")
                    ? "px-2 py-1 bg-white hover:bg-amber-100 hover:text-amber-900 border border-amber-200 rounded-lg text-[11px] font-semibold text-amber-950 transition shadow-2xs"
                    : "px-2 py-1 bg-white hover:bg-blue-50 hover:text-blue-700 border border-slate-200 rounded-lg text-[11px] font-semibold text-slate-700 transition shadow-2xs";
                btn.textContent = c.title;
                btn.onclick = () => insertCustomChipContent(c.content);

                if (c.category === "ceza") {
                    cezaContainer.appendChild(btn);
                } else {
                    hukukContainer.appendChild(btn);
                }
            });
        }

        function insertCustomChipContent(rawContent) {
            const aciklamaEl = document.getElementById("aciklama");
            let current = aciklamaEl.value.trim();
            const textToAdd = (typeof rawContent === 'string') ? rawContent.trim() : '';
            aciklamaEl.value = current ? (current + "\\n\\n" + textToAdd) : textToAdd;
            updateLivePreview();
            showToast("✨ Paragraf açıklamalar alanına eklendi!", "info");
        }

        function openChipManagerModal() {
            resetChipForm();
            renderChipsManagerList();
            document.getElementById("chipManagerModal").classList.remove("hidden");
        }

        function closeChipManagerModal() {
            document.getElementById("chipManagerModal").classList.add("hidden");
        }

        function renderChipsManagerList() {
            const container = document.getElementById("chipManagerList");
            if (!container) return;
            const chips = getAllChips();
            container.innerHTML = "";

            chips.forEach(c => {
                const row = document.createElement("div");
                row.className = "p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition flex items-center justify-between gap-2 text-xs";
                const previewSnippet = (c.content || "").split("\\n").join(" ");
                row.innerHTML = `
                    <div class="truncate flex-1">
                        <div class="font-bold text-slate-900 flex items-center gap-1.5">
                            <span>${c.title}</span>
                            <span class="text-[9px] px-1.5 py-0.2 rounded font-semibold ${c.category === 'ceza' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'}">${c.category === 'ceza' ? 'CEZA' : 'HUKUK'}</span>
                        </div>
                        <div class="text-[10px] text-slate-500 truncate mt-0.5">${previewSnippet}</div>
                    </div>
                    <div class="flex items-center gap-1">
                        <button onclick="editChip('${c.id}')" class="p-1 text-slate-400 hover:text-blue-600 transition" title="Düzenle">✏️</button>
                        <button onclick="deleteChip('${c.id}')" class="p-1 text-slate-400 hover:text-red-600 transition" title="Sil">🗑️</button>
                    </div>
                `;
                container.appendChild(row);
            });
        }

        function editChip(id) {
            const chips = getAllChips();
            const c = chips.find(x => x.id === id);
            if (!c) return;

            document.getElementById("editChipId").value = c.id;
            document.getElementById("modalChipTitle").value = c.title;
            document.getElementById("modalChipCategory").value = c.category;
            document.getElementById("modalChipContent").value = c.content || "";

            document.getElementById("chipFormTitle").textContent = `✏️ Çipi Düzenle: ${c.title}`;
            document.getElementById("btnCancelEditChip").classList.remove("hidden");
        }

        function resetChipForm() {
            document.getElementById("editChipId").value = "";
            document.getElementById("modalChipTitle").value = "";
            document.getElementById("modalChipCategory").value = "hukuk";
            document.getElementById("modalChipContent").value = "";
            document.getElementById("chipFormTitle").textContent = "➕ Yeni Çip Ekle";
            document.getElementById("btnCancelEditChip").classList.add("hidden");
        }

        function saveCustomChip() {
            const id = document.getElementById("editChipId").value.trim() || `chip_${Date.now()}`;
            let title = document.getElementById("modalChipTitle").value.trim();
            const category = document.getElementById("modalChipCategory").value;
            let content = document.getElementById("modalChipContent").value.trim();

            if (!title || !content) {
                showToast("Lütfen başlık ve metin alanlarını doldurunuz", "error");
                return;
            }

            if (!title.startsWith("+")) {
                title = "+ " + title;
            }

            const chips = getAllChips();
            const existingIdx = chips.findIndex(x => x.id === id);

            if (existingIdx >= 0) {
                chips[existingIdx] = { id, category, title, content };
                showToast(`✅ "${title}" çipi güncellendi!`, "success");
            } else {
                chips.push({ id, category, title, content });
                showToast(`✨ Yeni çip başarıyla eklendi!`, "success");
            }

            saveAllChips(chips);
            resetChipForm();
        }

        function deleteChip(id) {
            const chips = getAllChips().filter(x => x.id !== id);
            saveAllChips(chips);
            showToast("🗑️ Çip silindi", "info");
        }


        // ==========================================
        // 4. CANLI UYAP ÖNİZLEME MOTORU
        // ==========================================
        let isPreviewVisible = true;

        function toggleLivePreview() {
            isPreviewVisible = !isPreviewVisible;
            const previewCol = document.getElementById("previewCol");
            const formCol = document.getElementById("formFieldsCol");
            const btn = document.getElementById("btnTogglePreview");

            if (isPreviewVisible) {
                previewCol.classList.remove("hidden");
                formCol.className = "lg:col-span-7 space-y-5";
                btn.classList.add("bg-blue-50", "text-blue-700");
                btn.classList.remove("bg-slate-100", "text-slate-700");
                updateLivePreview();
            } else {
                previewCol.classList.add("hidden");
                formCol.className = "lg:col-span-12 space-y-5";
                btn.classList.remove("bg-blue-50", "text-blue-700");
                btn.classList.add("bg-slate-100", "text-slate-700");
            }
        }

        function updateLivePreview() {
            if (!isPreviewVisible) return;

            const mahkeme = document.getElementById("mahkeme")?.value || "MERSİN NÖBETÇİ ASLİYE HUKUK MAHKEMESİNE";
            const talep = document.getElementById("talep")?.value || "";
            const dosya = document.getElementById("dosya")?.value || "";
            const m_sifat = document.getElementById("m_sifat")?.value || "DAVACI";
            const m_ad = document.getElementById("m_ad")?.value || "[Davacı Adı Soyadı]";
            const m_adres = document.getElementById("m_adres")?.value || "";
            const vekil = document.getElementById("vekil")?.value || getLawyerFullText();
            const k_sifat = document.getElementById("k_sifat")?.value || "DAVALI";
            const k_ad = document.getElementById("k_ad")?.value || "[Karşı Taraf Adı]";
            const hed = document.getElementById("hed")?.value || "";
            const konu = document.getElementById("konu")?.value || "[Dilekçe Konusu]";
            const aciklama = document.getElementById("aciklama")?.value || "1- [Açıklamalar]";
            const sebepler = document.getElementById("hukuki_sebepler")?.value || "HMK, TBK ve ilgili mevzuat.";
            const deliller = document.getElementById("hukuki_deliller")?.value || "Banka kayıtları, tanık, bilirkişi ve yasal deliller.";
            const sonuc = document.getElementById("sonuc")?.value || "Davamızın kabulüne karar verilmesini arz ve talep ederiz.";

            document.getElementById("pv_mahkeme").textContent = mahkeme;
            document.getElementById("pv_talep").textContent = talep;
            document.getElementById("pv_dosya").textContent = dosya || "-";
            document.getElementById("pv_m_sifat").textContent = m_sifat;
            document.getElementById("pv_m_ad").textContent = m_ad;
            document.getElementById("pv_m_adres").textContent = m_adres;
            document.getElementById("pv_vekil").textContent = vekil;
            document.getElementById("pv_k_sifat").textContent = k_sifat;
            document.getElementById("pv_k_ad").textContent = k_ad;
            document.getElementById("pv_hed").textContent = hed || "-";
            document.getElementById("pv_konu").textContent = konu;
            document.getElementById("pv_aciklama").textContent = aciklama;
            document.getElementById("pv_sebepler").textContent = sebepler;
            document.getElementById("pv_deliller").textContent = deliller;
            document.getElementById("pv_sonuc").textContent = sonuc;
            document.getElementById("pv_imza_unvan").textContent = `${m_sifat.toLowerCase().includes('davalı') ? 'Davalı' : 'Davacı'} Vekili`;
            document.getElementById("pv_imza_ad").textContent = getLawyerSignatureName();

            // Toggle rows visibility if empty
            document.getElementById("pv_row_dosya").style.display = dosya ? "grid" : "none";
            document.getElementById("pv_row_m_adres").style.display = m_adres ? "grid" : "none";
            document.getElementById("pv_row_hed").style.display = hed ? "grid" : "none";
        }

    </script>
</body>
</html>
"""

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/mazeret":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MAZERET_HTML.encode("utf-8"))
        elif self.path == "/" or self.path.startswith("/?"):
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
            
            # Açıklama Maddeleri (UYAP Yerel Otomatik 1,2,3... Sıralı Liste Özelliği)
            list_attrs = {
                "Numbered": "true",
                "ListLevel": "1",
                "ListId": "1",
                "LeftIndent": "25.0",
                "NumberType": "NUMBER_TYPE_NUMBER_DOT",
                "SecListTypeLevel1": "NUMBER_TYPE_NUMBER_DOT"
            }
            
            if aciklama:
                lines = [l.strip() for l in aciklama.split("\n") if l.strip()]
                for line in lines:
                    # Strip any manual hardcoded 1-, 1., 2), 3 - prefix so UYAP generates the dynamic active list number
                    cleaned_line = re.sub(r"^\s*\d+\s*[\.\-\)]\s*", "", line)
                    if not cleaned_line:
                        cleaned_line = line
                    paragraphs.append((3, 0, "8.5", None, None, list_attrs, [(f"{cleaned_line}\n", False, False, False)]))
            else:
                paragraphs.append((3, 0, "8.5", None, None, list_attrs, [("[Açıklamalarınızı buraya yazabilirsiniz.]\n", False, False, False)]))
                
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
