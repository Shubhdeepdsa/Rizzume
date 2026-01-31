#!/bin/bash

# ============================================
# Rizzume - Universal Start Script
# ============================================
# One command to rule them all.
# Handles:
# 1. Prerequisite checks (Docker, Git, Curl)
# 2. Environment setup (.env creation)
# 3. Ollama setup (Model pulling)
# 4. Starting the application
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_MODEL="qwen3:1.7b"  # Default model used in docker-compose.yml
REQUIRED_DOCKER_VERSION="24.0.0" # Approx recent version

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                   🚀 Starting Rizzume                     ║"
echo "║          Your AI-Powered Resume Scoring Assistant         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# --------------------------------------------
# 1. Prerequisite Checks
# --------------------------------------------
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed.${NC}"
    echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check Docker Daemon
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running.${NC}"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi
echo -e "${GREEN}✅ Docker is ready${NC}"

# Check Curl
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is not installed.${NC} Please install curl."
    exit 1
fi

# --------------------------------------------
# 2. Environment Setup
# --------------------------------------------
echo -e "\n${BLUE}⚙️  Configuring environment...${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found.${NC}"
    if [ -f .env.example ]; then
        echo -e "${GREEN}✨ Creating .env from defaults...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}ℹ️  Created .env. You can edit it later to add API keys if needed.${NC}"
    else
        echo -e "${RED}❌ .env.example not found. Cannot create config automatically.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# --------------------------------------------
# 3. Ollama Setup
# --------------------------------------------
echo -e "\n${BLUE}🦙 Checking AI Provider (Ollama)...${NC}"

# Check if Ollama is accessible
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is running${NC}"

    # Check for the model
    echo -e "${BLUE}   Checking for model '${OLLAMA_MODEL}'...${NC}"
    if curl -s http://localhost:11434/api/tags | grep -q "${OLLAMA_MODEL}"; then
        echo -e "${GREEN}✅ Model '${OLLAMA_MODEL}' is already pulled${NC}"
    else
        echo -e "${YELLOW}⬇️  Model '${OLLAMA_MODEL}' not found. Pulling now... (This may take a while)${NC}"
        # Trigger pull via curl to local ollama instance
        curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"${OLLAMA_MODEL}\"}"
        echo -e "\n${GREEN}✅ Model pulled successfully${NC}"
    fi

else
    echo -e "${YELLOW}⚠️  Ollama is not running on localhost:11434${NC}"
    echo -e "${YELLOW}   The application relies on Ollama for local AI processing.${NC}"
    
    # Try to start Ollama if on Mac
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -d "/Applications/Ollama.app" ]; then
            echo -e "${BLUE}   Attempting to start Ollama...${NC}"
            open -a Ollama
            echo -e "${YELLOW}   Waiting for Ollama to initialize...${NC}"
            sleep 5
            # Recheck
            if curl -s http://localhost:11434/api/tags &> /dev/null; then
                 echo -e "${GREEN}✅ Ollama started successfully${NC}"
            else
                 echo -e "${RED}❌ Failed to start Ollama automatically.${NC}"
                 echo "   Please start Ollama manually and re-run this script."
                 read -p "   Press Enter once Ollama is running..."
            fi
        else
            echo -e "${RED}❌ Ollama application not found in /Applications.${NC}"
            echo "   Please install it from https://ollama.ai"
        fi
    else
        echo "   Please ensure Ollama is running: 'ollama serve'"
        echo "   Or continue without local AI (some features may fail)."
        read -p "   Press Enter to continue anyway (or Ctrl+C to abort)..."
    fi
fi

# --------------------------------------------
# 4. Start Application
# --------------------------------------------
echo -e "\n${BLUE}🚀 Launching Rizzume...${NC}"

# Stop existing containers if any (to ensure clean slate or restart)
# docker-compose down --remove-orphans 2>/dev/null

echo -e "${CYAN}Stopping any previous instances...${NC}"
docker-compose down 2>/dev/null

echo -e "${CYAN}Building and starting containers...${NC}"
docker-compose up --build -d

# --------------------------------------------
# 5. Health Check & Info
# --------------------------------------------
echo -e "\n${YELLOW}⏳ Waiting for services to come online...${NC}"
sleep 5

# Simple wait loop for backend
max_attempts=30
attempt=0
echo -e "${BLUE}   Checking backend connectivity...${NC}"
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}⚠️  Backend seems slow to start. Check logs: docker-compose logs -f backend${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Setup Complete! Rizzume is running.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}👉 Access the App:${NC}  http://localhost:3000"
echo -e "${BLUE}👉 Backend API:${NC}     http://localhost:8000"
echo ""
echo -e "${YELLOW}💡 To stop the app, run:${NC} docker-compose down"
echo -e "${YELLOW}💡 To view logs, run:${NC}    docker-compose logs -f"
echo ""
