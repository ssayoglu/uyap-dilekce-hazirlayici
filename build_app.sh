#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Dilekçe Hazırlayıcı.app"
DEST_APP="$DIR/$APP_NAME"

echo "🔨 Derleniyor: Swift Native macOS Wrapper..."
swiftc "$DIR/main.swift" -o "$DIR/DilekceApp" -framework Cocoa -framework WebKit

echo "📦 Paket oluşturuluyor: $APP_NAME..."
rm -rf "$DEST_APP"
mkdir -p "$DEST_APP/Contents/MacOS"
mkdir -p "$DEST_APP/Contents/Resources"

cp "$DIR/DilekceApp" "$DEST_APP/Contents/MacOS/DilekceApp"
cp "$DIR/server.py" "$DEST_APP/Contents/Resources/server.py"
cp "$DIR/version.json" "$DEST_APP/Contents/Resources/version.json" 2>/dev/null || true
chmod +x "$DEST_APP/Contents/MacOS/DilekceApp"
chmod +x "$DEST_APP/Contents/Resources/server.py"

cat << 'PLIST' > "$DEST_APP/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>DilekceApp</string>
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

echo "✅ Başarıyla oluşturuldu: $DEST_APP"
