#!/bin/bash

# ============================================
# Rizzume - Production Run Script
# ============================================
# This script starts the Rizzume application in production mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    🎯 RIZZUME                              ║"
echo "║            AI-Powered Resume Scoring                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if Ollama is running
echo -e "${YELLOW}📋 Checking Ollama status...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is not running on localhost:11434${NC}"
    echo -e "${YELLOW}   The backend will still start but LLM features won't work.${NC}"
    echo -e "${YELLOW}   Start Ollama with: ollama serve${NC}"
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    echo -e "${BLUE}📦 Loading environment variables from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Build and start containers
echo -e "${BLUE}🐳 Building and starting containers...${NC}"
docker-compose up --build -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check backend health
echo -e "${BLUE}🔍 Checking backend health...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo -e "${YELLOW}   Waiting for backend... (attempt $attempt/$max_attempts)${NC}"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Backend failed to start. Check logs with: docker-compose logs backend${NC}"
    exit 1
fi

# Print access information
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Rizzume is now running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}🌐 Frontend:${NC}  http://localhost:3000"
echo -e "${BLUE}🔧 Backend:${NC}   http://localhost:8000"
echo -e "${BLUE}❤️  Health:${NC}    http://localhost:8000/health"
echo -e "${BLUE}📊 Metrics:${NC}   http://localhost:8000/metrics"
echo ""
echo -e "${YELLOW}📝 Useful commands:${NC}"
echo -e "   View logs:     docker-compose logs -f"
echo -e "   Stop:          docker-compose down"
echo -e "   Restart:       docker-compose restart"
echo ""
