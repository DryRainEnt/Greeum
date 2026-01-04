#!/bin/bash
# Greeum Server Control Script
# Usage: ./greeum-server.sh [start|stop|status|restart]

GREEUM_DIR="$(cd "$(dirname "$0")" && pwd)"
GREEUM_PORT=8400
GREEUM_API_KEY="nGnd6d2Dy4EIUONCOBx3XKCUq0pANczX2QVKVn61dwk"
PID_FILE="$GREEUM_DIR/.greeum-server.pid"
LOG_FILE="$GREEUM_DIR/greeum-server.log"

# 색상
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

get_local_ip() {
    # Linux
    hostname -I 2>/dev/null | awk '{print $1}' || \
    # macOS fallback
    ipconfig getifaddr en0 2>/dev/null || \
    echo "localhost"
}

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo -e "${YELLOW}Server already running (PID: $(cat "$PID_FILE"))${NC}"
        return 1
    fi

    echo -e "${GREEN}Starting Greeum Server...${NC}"

    cd "$GREEUM_DIR"
    source .venv_test/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true

    GREEUM_API_KEY="$GREEUM_API_KEY" nohup python -m greeum.server --port "$GREEUM_PORT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        LOCAL_IP=$(get_local_ip)
        echo -e "${GREEN}Server started successfully!${NC}"
        echo ""
        echo "============================================"
        echo -e "  Local:   http://localhost:$GREEUM_PORT"
        echo -e "  Network: http://$LOCAL_IP:$GREEUM_PORT"
        echo -e "  API Key: $GREEUM_API_KEY"
        echo "============================================"
        echo ""
        echo "To connect from another machine, run:"
        echo -e "  ${YELLOW}greeum setup --remote http://$LOCAL_IP:$GREEUM_PORT --api-key $GREEUM_API_KEY${NC}"
        echo ""
        echo "Log file: $LOG_FILE"
    else
        echo -e "${RED}Failed to start server. Check $LOG_FILE${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_server() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}Server not running (no PID file)${NC}"
        return 0
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping Greeum Server (PID: $PID)...${NC}"
        kill "$PID"
        sleep 2

        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing..."
            kill -9 "$PID"
        fi

        echo -e "${GREEN}Server stopped.${NC}"
    else
        echo -e "${YELLOW}Server not running.${NC}"
    fi

    rm -f "$PID_FILE"
}

status_server() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        LOCAL_IP=$(get_local_ip)
        echo -e "${GREEN}Server is running${NC} (PID: $PID)"
        echo "  URL: http://$LOCAL_IP:$GREEUM_PORT"

        # Health check
        HEALTH=$(curl -s "http://localhost:$GREEUM_PORT/health" 2>/dev/null)
        if [ -n "$HEALTH" ]; then
            VERSION=$(echo "$HEALTH" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
            echo "  Version: $VERSION"
            echo "  Status: healthy"
        fi
    else
        echo -e "${RED}Server is not running${NC}"
        rm -f "$PID_FILE" 2>/dev/null
    fi
}

case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
