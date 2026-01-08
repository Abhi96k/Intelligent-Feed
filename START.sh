#!/bin/bash

# Tellius Intelligent Feed - One-Click Startup Script
# This script starts both backend and frontend servers

set -e

echo "=================================="
echo "Tellius Intelligent Feed System"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm found${NC}"

echo ""

# Backend Setup
echo -e "${BLUE}Setting up backend...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q -r requirements.txt
    touch venv/.installed
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠ Please edit backend/.env and add your ANTHROPIC_API_KEY${NC}"
    echo -e "${RED}Then run this script again.${NC}"
    exit 1
fi

# Check if database exists
if [ ! -f "tellius_feed.db" ]; then
    echo -e "${YELLOW}Initializing database...${NC}"
    python scripts/init_database.py
fi

echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

# Frontend Setup
echo -e "${BLUE}Setting up frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

# Start servers
echo -e "${BLUE}Starting servers...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo -e "${BLUE}Starting backend on http://localhost:8000${NC}"
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python -m app.main > /tmp/tellius_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        echo -e "${RED}Check logs: tail -f /tmp/tellius_backend.log${NC}"
        kill $BACKEND_PID
        exit 1
    fi
    sleep 1
done

# Start frontend in background
echo -e "${BLUE}Starting frontend on http://localhost:3000${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev > /tmp/tellius_frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo -e "${YELLOW}Waiting for frontend to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Frontend failed to start${NC}"
        echo -e "${RED}Check logs: tail -f /tmp/tellius_frontend.log${NC}"
        kill $BACKEND_PID $FRONTEND_PID
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}=================================="
echo "✓ System is running!"
echo "==================================${NC}"
echo ""
echo -e "Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Try these example questions:${NC}"
echo "  1. Why did revenue in APAC drop in the last 8 weeks vs previous period?"
echo "  2. Show me anomalies in revenue for Q4 2024"
echo "  3. What caused the revenue spike in Enterprise segment last month?"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Backend:  tail -f /tmp/tellius_backend.log"
echo "  Frontend: tail -f /tmp/tellius_frontend.log"
echo ""
echo -e "${RED}Press Ctrl+C to stop all servers${NC}"
echo ""

# Keep script running
wait
