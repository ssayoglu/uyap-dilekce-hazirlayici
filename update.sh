#!/usr/bin/env bash
set -e

# Renkler
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IN_APP=0
if [ "$1" == "--in-app" ]; then
    IN_APP=1
fi

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}🔄  UYAP Dilekçe & Şablon Yöneticisi Güncelleme    ${NC}"
echo -e "${BLUE}====================================================${NC}"

TARGET_DIR="$HOME/.dilekce-hazirlayici"
ZIP_URL="https://github.com/ssayoglu/uyap-dilekce-hazirlayici/archive/refs/heads/main.zip"
APP_NAME="Dilekçe Hazırlayıcı.app"
APPLICATIONS_DIR="/Applications"
DESKTOP_DIR="$HOME/Desktop"

# 1. Eski işlemleri durdur
echo -e "${YELLOW}🛑 Arka plan işlemleri kontrol ediliyor...${NC}"
pkill -f "server.py" 2>/dev/null || true
if [ "$IN_APP" -eq 0 ]; then
    pkill -f "DilekceApp" 2>/dev/null || true
fi

# 2. Dosyaları GitHub ZIP olarak indir
echo -e "${YELLOW}📥 En son sürüm indiriliyor...${NC}"
mkdir -p "$TARGET_DIR"

TMP_ZIP="/tmp/dilekce_update_main.zip"
TMP_UNZIP="/tmp/dilekce_update_extracted"
rm -rf "$TMP_ZIP" "$TMP_UNZIP"

curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
mkdir -p "$TMP_UNZIP"
unzip -q -o "$TMP_ZIP" -d "$TMP_UNZIP"
cp -R "$TMP_UNZIP/uyap-dilekce-hazirlayici-main/"* "$TARGET_DIR/"
rm -rf "$TMP_ZIP" "$TMP_UNZIP"
cd "$TARGET_DIR"

# 3. İzinleri ayarla
chmod +x "$TARGET_DIR/server.py" "$TARGET_DIR/DilekceApp" "$TARGET_DIR/build_app.sh" "$TARGET_DIR/update.sh" "$TARGET_DIR/install.sh" 2>/dev/null || true

# 4. .app Paketini güncelle
echo -e "${YELLOW}🔨 macOS Uygulama Paketi güncelleniyor...${NC}"
mkdir -p "$TARGET_DIR/$APP_NAME/Contents/MacOS"
mkdir -p "$TARGET_DIR/$APP_NAME/Contents/Resources"
cp -f "$TARGET_DIR/DilekceApp" "$TARGET_DIR/$APP_NAME/Contents/MacOS/DilekceApp"
cp -f "$TARGET_DIR/server.py" "$TARGET_DIR/$APP_NAME/Contents/Resources/server.py"
cp -f "$TARGET_DIR/version.json" "$TARGET_DIR/$APP_NAME/Contents/Resources/version.json" 2>/dev/null || true
if [ -f "$TARGET_DIR/AppIcon.icns" ]; then
    cp -f "$TARGET_DIR/AppIcon.icns" "$TARGET_DIR/$APP_NAME/Contents/Resources/AppIcon.icns" 2>/dev/null || true
fi
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
    <string>1.5.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# 5. /Applications ve Masaüstü kopyalarını yenile
echo -e "${YELLOW}📁 Uygulama konumları güncelleniyor...${NC}"
if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
    rm -rf "$APPLICATIONS_DIR/$APP_NAME"
    cp -R "$TARGET_DIR/$APP_NAME" "$APPLICATIONS_DIR/"
fi

if [ -d "$DESKTOP_DIR/$APP_NAME" ]; then
    rm -rf "$DESKTOP_DIR/$APP_NAME"
    cp -R "$TARGET_DIR/$APP_NAME" "$DESKTOP_DIR/"
fi

if [ ! -d "$APPLICATIONS_DIR/$APP_NAME" ] && [ ! -d "$DESKTOP_DIR/$APP_NAME" ]; then
    cp -R "$TARGET_DIR/$APP_NAME" "$APPLICATIONS_DIR/"
    cp -R "$TARGET_DIR/$APP_NAME" "$DESKTOP_DIR/"
fi

touch "$APPLICATIONS_DIR/$APP_NAME" "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true
killall Finder Dock 2>/dev/null || true

VER=$(grep -o '"version": "[^"]*"' "$TARGET_DIR/version.json" 2>/dev/null | cut -d'"' -f4 || echo "1.5.0")

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}✅  Güncelleme başarıyla tamamlandı! (Sürüm: v$VER)${NC}"
echo -e "${GREEN}====================================================${NC}"
if [ "$IN_APP" -eq 0 ]; then
    echo -e "🚀 Uygulama başlatılıyor..."
    open -a "$APPLICATIONS_DIR/$APP_NAME" 2>/dev/null || open -a "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true
fi
echo ""

