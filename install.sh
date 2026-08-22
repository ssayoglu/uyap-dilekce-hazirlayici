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
APP_NAME="Dilekçe Hazırlayıcı.app"
APPLICATIONS_DIR="/Applications"
DESKTOP_DIR="$HOME/Desktop"

# 1. Gerekli araçları kontrol et
echo -e "${YELLOW}🔍 Sistem gereksinimleri kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 bulunamadı. Lütfen Python 3 yükleyiniz.${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ git bulunamadı. Lütfen Xcode Command Line Tools yükleyiniz (xcode-select --install).${NC}"
    exit 1
fi

# 2. Depoyu klonla veya güncelle
if [ -d "$TARGET_DIR/.git" ]; then
    echo -e "${YELLOW}🔄 Mevcut kurulum güncelleniyor...${NC}"
    cd "$TARGET_DIR"
    git pull --quiet || true
else
    echo -e "${YELLOW}📥 Dosyalar indiriliyor ($TARGET_DIR)...${NC}"
    rm -rf "$TARGET_DIR"
    git clone --quiet "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR"
fi

# 3. İzinleri ayarla
chmod +x "$TARGET_DIR/server.py" "$TARGET_DIR/build_app.sh" 2>/dev/null || true

# 4. Native App'i derle
echo -e "${YELLOW}🔨 Native macOS Uygulaması derleniyor...${NC}"
if command -v swiftc &> /dev/null; then
    swiftc "$TARGET_DIR/main.swift" -o "$TARGET_DIR/DilekceApp" -framework Cocoa -framework WebKit
else
    echo -e "${YELLOW}⚠️ swiftc bulunamadı, mevcut ikili dosya kullanılıyor.${NC}"
fi

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

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}✅  Kurulum başarıyla tamamlandı!                   ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "🚀 Uygulamayı Masaüstünüzdeki veya Uygulamalar'daki"
echo -e "   ${BLUE}'Dilekçe Hazırlayıcı.app'${NC} simgesine tıklayarak açabilirsiniz."
echo ""
