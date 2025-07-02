#!/bin/bash

# Script to run check validator with environment file
# Usage: ./run-check-validator-env.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting Check Validator with Environment File...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create a .env file with your configuration:${NC}"
    echo "cp env.example .env"
    echo "nano .env"
    exit 1
fi

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t check-validator .

# Run the container with env file
echo -e "${GREEN}Running check validator container with env file...${NC}"
docker run -d \
    --name check-validator \
    --network docusense \
    -v docusense:/repository \
    -v $(pwd)/logs:/app/logs \
    --env-file .env \
    --restart unless-stopped \
    check-validator

echo -e "${GREEN}Container started with environment file!${NC}" 