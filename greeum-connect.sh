#!/bin/bash
# Greeum Remote Connection Script
# Download and run this on any machine to connect to your Greeum server
#
# Quick install & connect:
#   curl -sSL https://your-server/greeum-connect.sh | bash -s -- SERVER_IP API_KEY
#
# Or download and run:
#   ./greeum-connect.sh 192.168.1.100 your-api-key

set -e

# 색상
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════╗"
echo "║     Greeum Remote Connection Setup     ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Arguments
SERVER_IP="${1:-}"
API_KEY="${2:-}"
SERVER_PORT="${3:-8400}"

# Interactive mode if no arguments
if [ -z "$SERVER_IP" ]; then
    read -p "Server IP or hostname: " SERVER_IP
fi

if [ -z "$API_KEY" ]; then
    read -sp "API Key: " API_KEY
    echo ""
fi

SERVER_URL="http://$SERVER_IP:$SERVER_PORT"

echo ""
echo -e "${YELLOW}Checking connection to $SERVER_URL...${NC}"

# Test connection
HEALTH=$(curl -s --connect-timeout 5 "$SERVER_URL/health" 2>/dev/null || echo "")

if [ -z "$HEALTH" ]; then
    echo -e "${RED}Cannot connect to server at $SERVER_URL${NC}"
    echo "Please check:"
    echo "  - Server is running"
    echo "  - Firewall allows port $SERVER_PORT"
    echo "  - IP address is correct"
    exit 1
fi

VERSION=$(echo "$HEALTH" | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
echo -e "${GREEN}Connected! Server version: $VERSION${NC}"

# Test authentication
AUTH_TEST=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/stats" 2>/dev/null || echo "")

if echo "$AUTH_TEST" | grep -q "invalid_api_key\|authentication_required"; then
    echo -e "${RED}Authentication failed. Check your API key.${NC}"
    exit 1
fi

echo -e "${GREEN}Authentication successful!${NC}"

# Check if greeum is installed
if ! command -v greeum &> /dev/null; then
    echo ""
    echo -e "${YELLOW}Greeum CLI not found. Installing...${NC}"

    # Try pip install
    if command -v pip3 &> /dev/null; then
        pip3 install greeum --quiet
    elif command -v pip &> /dev/null; then
        pip install greeum --quiet
    else
        echo -e "${RED}pip not found. Please install greeum manually:${NC}"
        echo "  pip install greeum"
        exit 1
    fi

    if command -v greeum &> /dev/null; then
        echo -e "${GREEN}Greeum installed successfully!${NC}"
    else
        echo -e "${RED}Installation failed. Please install manually.${NC}"
        exit 1
    fi
fi

# Configure greeum
echo ""
echo -e "${YELLOW}Configuring Greeum...${NC}"

greeum setup --remote "$SERVER_URL" --api-key "$API_KEY"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Setup Complete!               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "You can now use Greeum with the remote server:"
echo ""
echo -e "  ${CYAN}greeum config show${NC}      # View configuration"
echo -e "  ${CYAN}greeum config test${NC}      # Test connection"
echo -e "  ${CYAN}greeum memory add \"...\"${NC} # Add a memory"
echo -e "  ${CYAN}greeum memory search \"...\"${NC} # Search memories"
echo ""
echo "MCP servers will automatically use this configuration."
