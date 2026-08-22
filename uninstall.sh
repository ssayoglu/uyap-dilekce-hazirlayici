#!/usr/bin/env bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}🗑️  UYAP Dilekçe Hazırlayıcı Kaldırma Aracı         ${NC}"
echo -e "${BLUE}====================================================${NC}"

echo -e "${YELLOW}🛑 Çalışan işlemler kapatılıyor...${NC}"
pkill -f "DilekceApp" 2>/dev/null || true
pkill -f "server.py" 2>/dev/null || true

echo -e "${YELLOW}🧹 Uygulama dosyaları ve kısayolları temizleniyor...${NC}"
rm -rf "/Applications/Dilekçe Hazırlayıcı.app"
rm -rf "$HOME/Desktop/Dilekçe Hazırlayıcı.app"
rm -rf "$HOME/.dilekce-hazirlayici"

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}✅ UYAP Dilekçe Hazırlayıcı sistemden kaldırıldı.   ${NC}"
echo -e "${GREEN}====================================================${NC}"
