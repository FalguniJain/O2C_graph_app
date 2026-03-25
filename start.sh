#!/bin/bash

echo "============================================="
echo "  O2C Graph - Order to Cash Analytics"
echo "============================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found. Install from python.org"
    exit 1
fi

# Check Node
if ! command -v node &>/dev/null; then
    echo "ERROR: Node.js not found. Install from nodejs.org"
    exit 1
fi

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "IMPORTANT: You need an Anthropic API key."
    read -p "Enter your Anthropic API key (sk-ant-...): " ANTHROPIC_API_KEY
    export ANTHROPIC_API_KEY
    echo "export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'" >> ~/.bashrc
    echo "export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'" >> ~/.zshrc 2>/dev/null || true
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/backend/requirements.txt" -q

echo "[2/3] Installing frontend dependencies..."
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    cd "$SCRIPT_DIR/frontend" && npm install -q
fi

echo "[3/3] Starting servers..."
echo ""
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Start backend
cd "$SCRIPT_DIR/backend" && python3 app.py &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start frontend
cd "$SCRIPT_DIR/frontend" && npm run dev &
FRONTEND_PID=$!

# Open browser (works on mac and linux)
sleep 4
if command -v open &>/dev/null; then
    open http://localhost:5173
elif command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5173
fi

echo "Both servers running. Ctrl+C to quit."
wait $BACKEND_PID $FRONTEND_PID
