#!/bin/bash

# Set error handling
set -e
trap 'echo -e "${RED}Deployment script terminated with error${NC}"; exit 1' ERR

# Change to script directory which is project root
cd "$(dirname "${BASH_SOURCE[0]}")"

# Load environment variables
if [[ -f ".env" ]]; then
    source ".env"
else
    echo "ERROR: .env file not found"
    exit 1
fi

echo -e "${BLUE}Starting deployment for RAG system for Ukrainian technical standards...${NC}"

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${BLUE}Docker is not running. Attempting to start Docker...${NC}"
    # Different commands based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a Docker || { echo -e "${RED}Failed to launch Docker Desktop${NC}"; exit 1; }
    elif command -v systemctl > /dev/null; then
        sudo systemctl start docker || { echo -e "${RED}Failed to start Docker service${NC}"; exit 1; }
    else
        echo -e "${RED}Unsupported OS. Please start Docker manually.${NC}"
        exit 1
    fi
    echo -e "${BLUE}Waiting for Docker to start...${NC}"
    for i in {1..30}; do
        if docker info > /dev/null 2>&1; then
            echo -e "${GREEN}Docker started successfully${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Docker failed to start. Please start it manually${NC}"
        exit 1
    fi
fi

# Clean up Docker space and project-specific containers/images
echo -e "${BLUE}Cleaning up Docker space and existing project containers...${NC}"
docker builder prune -f 2>/dev/null || true
docker image prune -f 2>/dev/null || true
docker-compose down --remove-orphans 2>/dev/null || true
docker image rm ${STORAGE_IMAGE_NAME}:latest 2>/dev/null || true
docker image rm ${WEBAPP_IMAGE_NAME}:latest 2>/dev/null || true

# First, build, run and remove the standards ingestion service
echo -e "${BLUE}Building and running standards ingestion service...${NC}"
docker-compose build ${STORAGE_SERVICE_NAME}
docker-compose run --rm ${STORAGE_SERVICE_NAME}
if [ $? -ne 0 ]; then
    echo -e "${RED}Standards ingestion failed${NC}"
    exit 1
fi
echo -e "${GREEN}Standards ingestion completed successfully${NC}"

# Now build and start the web application service
echo -e "${BLUE}Building and starting web application service...${NC}"
docker-compose up -d --build ${WEBAPP_SERVICE_NAME}
echo -e "${BLUE}Waiting for web application service to be responsive...${NC}"
for attempt in {1..30}; do
    if curl -s --max-time 5 "http://localhost:${WEBAPP_PORT}/_stcore/health" > /dev/null 2>&1; then
        echo -e "\n${GREEN}Web application service is responsive on port ${WEBAPP_PORT}${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [[ $attempt -eq 30 ]]; then
        echo -e "\n${RED}Web application service did not respond in time${NC}"
        echo -e "${YELLOW}Checking container logs:${NC}"
        docker-compose logs ${WEBAPP_SERVICE_NAME}
        exit 1
    fi
done

# Set the host to localhost if running locally, or the remote host if running remotely
HOST="localhost"
if [[ "$1" == "remotely" ]]; then
    HOST=${REMOTE_HOST:-localhost}
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}The web application is available at: http://${HOST}:${WEBAPP_PORT}${NC}"