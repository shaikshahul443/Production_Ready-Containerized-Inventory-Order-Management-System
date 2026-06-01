#!/bin/bash
set -e

# Color codes for clean CLI outputs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}      StockFlow Local Setup & Run Wizard      ${NC}"
echo -e "${BLUE}==============================================${NC}"
echo -e "Preparing to download standalone Node.js and Python binaries for"
echo -e "Apple Silicon (ARM64) to run the full FastAPI & React web stack."
echo

# 1. Create local binaries folder
mkdir -p binaries
cd binaries

# 2. Download and Extract Node.js if not present
if [ ! -d "node-v20.11.0-darwin-arm64" ]; then
    echo -e "${YELLOW}[1/4] Downloading Node.js binary (v20.11.0)...${NC}"
    curl -L https://nodejs.org/dist/v20.11.0/node-v20.11.0-darwin-arm64.tar.gz -o node.tar.gz
    echo -e "${GREEN}Extracting Node.js...${NC}"
    tar -xzf node.tar.gz
    rm node.tar.gz
else
    echo -e "${GREEN}Node.js binary already present.${NC}"
fi

# 3. Download and Extract Python if not present
if [ ! -d "python" ]; then
    echo -e "${YELLOW}[2/4] Downloading Python standalone binary...${NC}"
    curl -L https://github.com/indygreg/python-build-standalone/releases/download/20240107/cpython-3.11.7+20240107-aarch64-apple-darwin-install_only.tar.gz -o python.tar.gz
    echo -e "${GREEN}Extracting Python...${NC}"
    mkdir -p python
    tar -xzf python.tar.gz -C python --strip-components=1
    rm python.tar.gz
else
    echo -e "${GREEN}Python binary already present.${NC}"
fi

cd ..

# 4. Set Environment PATH for the session
export PATH="$(pwd)/binaries/node-v20.11.0-darwin-arm64/bin:$(pwd)/binaries/python/bin:$PATH"

echo
echo -e "${GREEN}Configured local bin paths:${NC}"
echo -n "  Node.js: " && node -v
echo -n "  NPM:     " && npm -v
echo -n "  Python:  " && python3 --version
echo

# 5. Install Python dependencies
echo -e "${YELLOW}[3/4] Installing Python requirements...${NC}"
python3 -m pip install fastapi uvicorn sqlalchemy pydantic python-dotenv email-validator

# 6. Install React frontend dependencies
echo -e "${YELLOW}[4/4] Installing React/Vite node modules...${NC}"
cd frontend
npm install
cd ..

# 7. Start Services
echo
echo -e "${BLUE}=== Starting App Servers ===${NC}"

# Clean up ports 8000 and 3000 if occupied
echo -e "Checking if ports 8000 or 3000 are occupied and cleaning up..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true

# Start FastAPI backend server in background
echo -e "${GREEN}Starting backend (FastAPI) at http://127.0.0.1:8000...${NC}"
cd backend
DATABASE_URL=sqlite:///./inventory.db python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Grace period for DB and backend to launch
sleep 2

# Start React/Vite development server in background
echo -e "${GREEN}Starting frontend (React) at http://localhost:3000...${NC}"
cd frontend
VITE_BACKEND_URL=http://localhost:8000 npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo
echo -e "${GREEN}Servers are running successfully!${NC}"
echo -e "  - Backend API PID: ${YELLOW}$BACKEND_PID${NC}"
echo -e "  - Frontend App PID: ${YELLOW}$FRONTEND_PID${NC}"
echo

# 8. Open default browser
echo -e "${BLUE}Opening http://localhost:3000 in your browser...${NC}"
open http://localhost:3000

echo
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}         Setup Completed Successfully!         ${NC}"
echo -e "${GREEN}==============================================${NC}"
echo -e "To stop both servers later, run:"
echo -e "  kill $BACKEND_PID $FRONTEND_PID"
echo
