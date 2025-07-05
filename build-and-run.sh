#!/bin/bash

# Exit on any error
set -e

# Check for Google credentials
if [ ! -f "credentials/google-vision-credentials.json" ]; then
    echo "Error: Google Vision credentials file not found at credentials/google-vision-credentials.json"
    exit 1
fi

# Build base image
echo "Building base image..."
docker build -t vision-flow-base:latest -f Dockerfile.base .

# Build validator image
echo "Building validator image..."
docker build -t vision-flow-validator:latest -f Dockerfile.validator .

docker buildx build --platform linux/amd64 -t madhavpandey33/vision-flow-validator:07-04-25_amd -f Dockerfile.validator .

# Build processor image
echo "Building processor image..."
docker build -t vision-flow-processor:latest -f Dockerfile.processor .

docker buildx build --platform linux/amd64 -t madhavpandey33/vision-flow-processor:07-04-25_amd -f Dockerfile.processor .

# Create Docker network if it doesn't exist
docker network inspect document-net >/dev/null 2>&1 || \
    docker network create document-net

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="/app/credentials/google-vision-credentials.json"

# Run validator
echo "Starting validator container..."
docker run -d \
    --name vision-flow-validator \
    --network document-net \
    -v "docusense:/app/repository" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/credentials:/app/credentials:ro" \
    -e GOOGLE_APPLICATION_CREDENTIALS="/app/credentials/google-vision-credentials.json" \
    --env-file .env \
    vision-flow-validator:latest

# Run processor
echo "Starting processor container..."
docker run -d \
    --name vision-flow-processor \
    --network document-net \
    -v "docusense:/app/repository" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/credentials:/app/credentials:ro" \
    -e GOOGLE_APPLICATION_CREDENTIALS="/app/credentials/google-vision-credentials.json" \
    --env-file .env \
    vision-flow-processor:latest

echo "Services started! Check logs with:"
echo "docker logs vision-flow-validator"
echo "docker logs vision-flow-processor" 