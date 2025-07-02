#!/bin/bash

# Script to run check validator with Docker secrets
# Usage: ./run-check-validator-secrets.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting Check Validator with Docker Secrets...${NC}"

# Create secrets (if they don't exist)
echo -e "${YELLOW}Creating Docker secrets...${NC}"

# Create MongoDB password secret
echo "your_mongodb_password" | docker secret create mongo_password -

# Create API keys secrets
echo "your_openai_api_key" | docker secret create openai_api_key -
echo "your_google_credentials_json" | docker secret create google_credentials -

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t check-validator .

# Run the container with secrets
echo -e "${GREEN}Running check validator container with secrets...${NC}"
docker run -d \
    --name check-validator \
    --network docusense \
    -v docusense:/repository \
    -v $(pwd)/logs:/app/logs \
    --secret mongo_password \
    --secret openai_api_key \
    --secret google_credentials \
    -e MONGO_URI=mongodb://mongo:27017/ \
    -e MONGO_DB_NAME=pan-ocr \
    -e MONGO_PASSWORD_FILE=/run/secrets/mongo_password \
    -e OPENAI_API_KEY_FILE=/run/secrets/openai_api_key \
    -e GOOGLE_CREDENTIALS_FILE=/run/secrets/google_credentials \
    -e POLL_INTERVAL=30 \
    -e LOG_LEVEL=INFO \
    --restart unless-stopped \
    check-validator

echo -e "${GREEN}Container started with secrets!${NC}" 