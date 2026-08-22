import re

with open("/Users/serkan/Documents/DilekceOlusturucu/server.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace the generation logic in server.py
# Old pattern:
# (label, True, False, True),
# ("\t:\t", False, False, False),

old_chunk = """            # Dosya No
            if dosya:
                dosya_etiket = "İCRA DOSYA NO" if ("İcra" in dosya or "İcra" in mahkeme) else "DOSYA NO"
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    (dosya_etiket, True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{dosya}\\n", False, False, False)
                ]))
                
            # Müvekkil
            if m_sifat and m_ad:
                paragraphs.append((0, "0.5", "0.0" if m_adres else "5.0", None, tab_setting, [
                    (m_sifat, True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{m_ad}\\n", True, False, False)
                ]))
                if m_adres:
                    paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                        ("", False, False, False),
                        ("\t\t", False, False, False),
                        (f"{m_adres}\\n", False, True, False)
                    ]))
                    
            # Vekili
            if vekil:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("VEKİLİ", True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{vekil}\\n", False, False, False)
                ]))
                
            # Karşı Taraf
            if k_sifat and k_ad:
                paragraphs.append((0, "0.5", "0.0" if k_vekil else "5.0", None, tab_setting, [
                    (k_sifat, True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{k_ad}\\n", False, False, False)
                ]))
                if k_vekil:
                    paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                        ("VEKİLİ", True, False, True),
                        ("\t:\t", False, False, False),
                        (f"{k_vekil}\\n", False, False, False)
                    ]))
                    
            # Harca Esas Değer (H.E.D.)
            if hed:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("DAVA DEĞERİ (H.E.D.)", True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{hed}\\n", False, False, False)
                ]))

            # Konu (Satır Aralığı 1.0)
            if konu:
                paragraphs.append((0, "1.0", "14.17", None, tab_setting, [
                    ("KONU", True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{konu}\\n", False, False, False)
                ]))"""

new_chunk = """            # Dosya No
            if dosya:
                dosya_etiket = "İCRA DOSYA NO" if ("İcra" in dosya or "İcra" in mahkeme) else "DOSYA NO"
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    (dosya_etiket, True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{dosya}\\n", False, False, False)
                ]))
                
            # Müvekkil
            if m_sifat and m_ad:
                paragraphs.append((0, "0.5", "0.0" if m_adres else "5.0", None, tab_setting, [
                    (m_sifat, True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{m_ad}\\n", True, False, False)
                ]))
                if m_adres:
                    paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                        ("", False, False, False),
                        ("\t\t", False, False, False),
                        (f"{m_adres}\\n", False, True, False)
                    ]))
                    
            # Vekili
            if vekil:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("VEKİLİ", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{vekil}\\n", False, False, False)
                ]))
                
            # Karşı Taraf
            if k_sifat and k_ad:
                paragraphs.append((0, "0.5", "0.0" if k_vekil else "5.0", None, tab_setting, [
                    (k_sifat, True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{k_ad}\\n", False, False, False)
                ]))
                if k_vekil:
                    paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                        ("VEKİLİ", True, False, True),
                        ("\t", False, False, True),
                        (":\t", False, False, False),
                        (f"{k_vekil}\\n", False, False, False)
                    ]))
                    
            # Harca Esas Değer (H.E.D.)
            if hed:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("DAVA DEĞERİ (H.E.D.)", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{hed}\\n", False, False, False)
                ]))

            # Konu (Satır Aralığı 1.0)
            if konu:
                paragraphs.append((0, "1.0", "14.17", None, tab_setting, [
                    ("KONU", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{konu}\\n", False, False, False)
                ]))"""

old_sebepler = """            # Hukuki Sebepler (Varsa)
            if hukuki_sebepler:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("HUKUKİ SEBEPLER", True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{hukuki_sebepler}\\n", False, False, False)
                ]))

            # Hukuki Deliller (Varsa)
            if hukuki_deliller:
                paragraphs.append((0, "0.5", "14.17", None, tab_setting, [
                    ("HUKUKİ DELİLLER", True, False, True),
                    ("\t:\t", False, False, False),
                    (f"{hukuki_deliller}\\n", False, False, False)
                ]))"""

new_sebepler = """            # Hukuki Sebepler (Varsa)
            if hukuki_sebepler:
                paragraphs.append((0, "0.5", "5.0", None, tab_setting, [
                    ("HUKUKİ SEBEPLER", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{hukuki_sebepler}\\n", False, False, False)
                ]))

            # Hukuki Deliller (Varsa)
            if hukuki_deliller:
                paragraphs.append((0, "0.5", "14.17", None, tab_setting, [
                    ("HUKUKİ DELİLLER", True, False, True),
                    ("\t", False, False, True),
                    (":\t", False, False, False),
                    (f"{hukuki_deliller}\\n", False, False, False)
                ]))"""

code = code.replace(old_chunk, new_chunk)
code = code.replace(old_sebepler, new_sebepler)

with open("/Users/serkan/Documents/DilekceOlusturucu/server.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updated server.py with full-length underlines to colon.")
