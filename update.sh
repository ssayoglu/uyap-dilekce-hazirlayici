#!/usr/bin/env bash
set -e

DIR="$HOME/.dilekce-hazirlayici"

if [ -d "$DIR/.git" ]; then
    echo "🔄 Güncellemeler alınıyor..."
    cd "$DIR"
    git pull --quiet
    bash "$DIR/build_app.sh"
    rm -rf "/Applications/Dilekçe Hazırlayıcı.app" "$HOME/Desktop/Dilekçe Hazırlayıcı.app"
    cp -R "$DIR/Dilekçe Hazırlayıcı.app" "/Applications/"
    cp -R "$DIR/Dilekçe Hazırlayıcı.app" "$HOME/Desktop/"
    echo "✅ Başarıyla güncellendi!"
else
    echo "📥 Yeni kurulum çalıştırılıyor..."
    curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/install.sh | bash
fi
