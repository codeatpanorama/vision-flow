#!/bin/bash

# Exit on any error
set -e

# Build base image
echo "Building base image..."
docker build -t vision-flow-base:latest -f Dockerfile.base .

# Build validator image
echo "Building validator image..."
docker build -t vision-flow-validator:latest -f Dockerfile.validator .

# Build processor image
echo "Building processor image..."
docker build -t vision-flow-processor:latest -f Dockerfile.processor .

# Create Docker network if it doesn't exist
docker network inspect vision-flow >/dev/null 2>&1 || \
    docker network create vision-flow

# Run validator
echo "Starting validator container..."
docker run -d \
    --name vision-flow-validator \
    --network vision-flow \
    -v "$(pwd)/repository:/app/repository" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    --env-file .env \
    vision-flow-validator:latest

# Run processor
echo "Starting processor container..."
docker run -d \
    --name vision-flow-processor \
    --network vision-flow \
    -v "$(pwd)/repository:/app/repository" \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    --env-file .env \
    vision-flow-processor:latest

echo "Services started! Check logs with:"
echo "docker logs vision-flow-validator"
echo "docker logs vision-flow-processor" 