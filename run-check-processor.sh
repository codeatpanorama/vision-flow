#!/bin/bash

# Script to run check processor as Docker container
# Usage: ./run-check-processor.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Check Processor Docker Container...${NC}"

# Check if docusense network exists
if ! docker network ls | grep -q "docusense"; then
    echo -e "${YELLOW}Creating docusense network...${NC}"
    docker network create docusense
fi

# Check if docusense volume exists
if ! docker volume ls | grep -q "docusense"; then
    echo -e "${YELLOW}Creating docusense volume...${NC}"
    docker volume create docusense
fi

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t check-processor .

# Run the container
echo -e "${GREEN}Running check processor container...${NC}"
docker run -d \
    --name check-processor \
    --network docusense \
    -v docusense:/repository \
    -v $(pwd)/logs:/app/logs \
    -e MONGO_URI=mongodb://mongo:27017/ \
    -e MONGO_DB_NAME=pan-ocr \
    -e POLL_INTERVAL=30 \
    -e LOG_LEVEL=INFO \
    --restart unless-stopped \
    check-processor

echo -e "${GREEN}Check processor container started successfully!${NC}"
echo -e "${YELLOW}Container name: check-processor${NC}"
echo -e "${YELLOW}Network: docusense${NC}"
echo -e "${YELLOW}Volume: docusense:/repository${NC}"
echo -e "${YELLOW}Logs: ./logs/check_processor.log${NC}"

# Show container status
echo -e "${GREEN}Container status:${NC}"
docker ps --filter name=check-processor

echo -e "${GREEN}To view logs:${NC}"
echo "docker logs -f check-processor"
echo "or"
echo "tail -f logs/check_processor.log" 