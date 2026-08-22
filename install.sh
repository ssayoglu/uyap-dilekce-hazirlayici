#!/usr/bin/env bash
set -e

# Renkler
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}⚖️  UYAP Dilekçe & Şablon Yöneticisi Kurulumu      ${NC}"
echo -e "${BLUE}====================================================${NC}"

TARGET_DIR="$HOME/.dilekce-hazirlayici"
REPO_URL="https://github.com/ssayoglu/uyap-dilekce-hazirlayici.git"
ZIP_URL="https://github.com/ssayoglu/uyap-dilekce-hazirlayici/archive/refs/heads/main.zip"
APP_NAME="Dilekçe Hazırlayıcı.app"
APPLICATIONS_DIR="/Applications"
DESKTOP_DIR="$HOME/Desktop"

# 1. Gerekli araçları kontrol et
echo -e "${YELLOW}🔍 Sistem gereksinimleri kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 bulunamadı. Lütfen Python 3 yükleyiniz.${NC}"
    exit 1
fi

# 2. Dosyaları İndir (Git varsa git ile, yoksa ZIP indirerek Xcode ihtiyacını sıfıra indirir)
echo -e "${YELLOW}📥 Dosyalar hazırlanıyor ($TARGET_DIR)...${NC}"
mkdir -p "$TARGET_DIR"

if command -v git &> /dev/null && git --version &> /dev/null 2>&1; then
    if [ -d "$TARGET_DIR/.git" ]; then
        echo -e "${YELLOW}🔄 Mevcut kurulum güncelleniyor...${NC}"
        cd "$TARGET_DIR"
        git pull --quiet || true
    else
        rm -rf "$TARGET_DIR"
        git clone --quiet "$REPO_URL" "$TARGET_DIR" || true
        if [ ! -f "$TARGET_DIR/server.py" ]; then
            # fallback to zip if git clone failed
            echo -e "${YELLOW}📦 Git clone tamamlanamadı, ZIP arşivi indiriliyor...${NC}"
            TMP_ZIP="/tmp/dilekce_app_main.zip"
            TMP_UNZIP="/tmp/dilekce_extracted"
            rm -rf "$TMP_ZIP" "$TMP_UNZIP"
            curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
            mkdir -p "$TMP_UNZIP"
            unzip -q -o "$TMP_ZIP" -d "$TMP_UNZIP"
            cp -R "$TMP_UNZIP/uyap-dilekce-hazirlayici-main/"* "$TARGET_DIR/"
            rm -rf "$TMP_ZIP" "$TMP_UNZIP"
        fi
        cd "$TARGET_DIR"
    fi
else
    echo -e "${YELLOW}📦 Git / Xcode bulunamadı, arşiv doğrudan indiriliyor...${NC}"
    TMP_ZIP="/tmp/dilekce_app_main.zip"
    TMP_UNZIP="/tmp/dilekce_extracted"
    rm -rf "$TMP_ZIP" "$TMP_UNZIP"
    curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
    mkdir -p "$TMP_UNZIP"
    unzip -q -o "$TMP_ZIP" -d "$TMP_UNZIP"
    cp -R "$TMP_UNZIP/uyap-dilekce-hazirlayici-main/"* "$TARGET_DIR/"
    rm -rf "$TMP_ZIP" "$TMP_UNZIP"
    cd "$TARGET_DIR"
fi

# 3. İzinleri ayarla
chmod +x "$TARGET_DIR/server.py" "$TARGET_DIR/build_app.sh" 2>/dev/null || true

# 4. Native App'i derle veya repo içerisindeki hazır ikiliyi kullan
echo -e "${YELLOW}🔨 Native macOS Uygulaması hazırlanıyor...${NC}"
if command -v swiftc &> /dev/null && swiftc --version &> /dev/null 2>&1; then
    swiftc "$TARGET_DIR/main.swift" -o "$TARGET_DIR/DilekceApp" -framework Cocoa -framework WebKit 2>/dev/null || true
fi

if [ ! -f "$TARGET_DIR/DilekceApp" ]; then
    echo -e "${RED}❌ DilekceApp ikili dosyası oluşturulamadı.${NC}"
    exit 1
fi
chmod +x "$TARGET_DIR/DilekceApp"

# 5. .app Paketini oluştur
mkdir -p "$TARGET_DIR/$APP_NAME/Contents/MacOS"
mkdir -p "$TARGET_DIR/$APP_NAME/Contents/Resources"
cp -f "$TARGET_DIR/DilekceApp" "$TARGET_DIR/$APP_NAME/Contents/MacOS/DilekceApp"
cp -f "$TARGET_DIR/server.py" "$TARGET_DIR/$APP_NAME/Contents/Resources/server.py"
cp -f "$TARGET_DIR/version.json" "$TARGET_DIR/$APP_NAME/Contents/Resources/version.json" 2>/dev/null || true
cp -f "$TARGET_DIR/AppIcon.icns" "$TARGET_DIR/$APP_NAME/Contents/Resources/AppIcon.icns" 2>/dev/null || true
chmod +x "$TARGET_DIR/$APP_NAME/Contents/MacOS/DilekceApp"
chmod +x "$TARGET_DIR/$APP_NAME/Contents/Resources/server.py"

cat << 'PLIST' > "$TARGET_DIR/$APP_NAME/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>DilekceApp</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.avukat.dilekcehazirlayici</string>
    <key>CFBundleName</key>
    <string>Dilekçe Hazırlayıcı</string>
    <key>CFBundleDisplayName</key>
    <string>Dilekçe Hazırlayıcı</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# 6. Uygulamalar ve Masaüstüne yerleştir
echo -e "${YELLOW}📁 Uygulama kısayolları oluşturuluyor...${NC}"
rm -rf "$APPLICATIONS_DIR/$APP_NAME" "$DESKTOP_DIR/$APP_NAME"
cp -R "$TARGET_DIR/$APP_NAME" "$APPLICATIONS_DIR/"
cp -R "$TARGET_DIR/$APP_NAME" "$DESKTOP_DIR/"
touch "/Applications/$APP_NAME" "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true

# macOS simge önbelleğini yenile
killall Finder Dock 2>/dev/null || true

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}✅  Kurulum başarıyla tamamlandı!                   ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "🚀 Uygulamayı Masaüstünüzdeki veya Uygulamalar'daki"
echo -e "   ${BLUE}'Dilekçe Hazırlayıcı.app'${NC} simgesine tıklayarak açabilirsiniz."
echo ""
