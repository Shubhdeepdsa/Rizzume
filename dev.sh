#!/bin/bash

# ============================================
# Rizzume - Development Run Script
# ============================================
# This script starts the Rizzume application in development mode
# with hot-reload enabled for both frontend and backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              🎯 RIZZUME - Development Mode                 ║"
echo "║            AI-Powered Resume Scoring                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
USE_DOCKER=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --docker) USE_DOCKER=true ;;
        --backend) BACKEND_ONLY=true ;;
        --frontend) FRONTEND_ONLY=true ;;
        -h|--help)
            echo "Usage: ./dev.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --docker     Use Docker Compose for development"
            echo "  --backend    Start only the backend"
            echo "  --frontend   Start only the frontend"
            echo "  -h, --help   Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Check if Ollama is running
echo -e "${YELLOW}📋 Checking Ollama status...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is not running on localhost:11434${NC}"
    echo -e "${YELLOW}   Start Ollama with: ollama serve${NC}"
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    echo -e "${BLUE}📦 Loading environment variables from .env${NC}"
    set -a
    source .env
    set +a
fi

if [ "$USE_DOCKER" = true ]; then
    # Docker-based development
    echo -e "${BLUE}🐳 Starting development containers with Docker...${NC}"
    docker-compose --profile dev up --build
else
    # Local development without Docker
    
    cleanup() {
        echo ""
        echo -e "${YELLOW}🛑 Stopping services...${NC}"
        kill $(jobs -p) 2>/dev/null
        exit 0
    }
    
    trap cleanup SIGINT SIGTERM
    
    if [ "$FRONTEND_ONLY" = false ]; then
        # Start backend
        echo -e "${BLUE}🔧 Starting Backend...${NC}"
        
        # Check for virtual environment
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d "vevn" ]; then
            source vevn/bin/activate
        else
            echo -e "${YELLOW}⚠️  No virtual environment found. Creating one...${NC}"
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
        fi
        
        # Start uvicorn with reload
        uvicorn app.main:app --reload --port 8000 &
        BACKEND_PID=$!
        echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    fi
    
    if [ "$BACKEND_ONLY" = false ]; then
        # Start frontend
        echo -e "${BLUE}🌐 Starting Frontend...${NC}"
        cd rizzume-web-app
        
        # Install dependencies if needed
        if [ ! -d "node_modules" ]; then
            echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
            npm install
        fi
        
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    fi
    
    # Print access information
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 Development servers are running!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    if [ "$FRONTEND_ONLY" = false ]; then
        echo -e "${BLUE}🔧 Backend:${NC}   http://localhost:8000"
    fi
    if [ "$BACKEND_ONLY" = false ]; then
        echo -e "${BLUE}🌐 Frontend:${NC}  http://localhost:3000"
    fi
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
    # Wait for processes
    wait
fi
