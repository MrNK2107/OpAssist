#!/bin/bash
# OpAssist startup script

set -e

echo "=== OpAssist startup ==="

# Check for .env files
if [ ! -f backend/.env ]; then
    echo "ERROR: backend/.env is missing. Copy backend/.env.example and fill in your values."
    exit 1
fi

if [ ! -f frontend/.env.local ]; then
    echo "ERROR: frontend/.env.local is missing. Copy frontend/.env.local.example and fill in your values."
    exit 1
fi

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
if ! command -v playwright &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install chromium
fi
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "=== Setup complete ==="
echo ""
echo "To start the application:"
echo "  Terminal 1: cd backend && uvicorn main:app --reload"
echo "  Terminal 2: cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:3000"
