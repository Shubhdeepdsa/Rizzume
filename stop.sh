#!/bin/bash

# ============================================
# Rizzume - Stop Script
# ============================================
# This script stops all Rizzume containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Rizzume containers...${NC}"

# Stop docker compose
docker-compose down

echo -e "${GREEN}✅ All containers stopped!${NC}"
