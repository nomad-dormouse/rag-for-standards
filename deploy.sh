#!/bin/bash

# Local RAG system deployment script
# Usage options:
#   ./deploy.sh                 - Deploy with existing parsed pages (if available)
#   ./deploy.sh parse           - Force re-parsing of all documents
#   ./deploy.sh remotely        - Deploy to remote host with existing parsed pages (if available)
#   ./deploy.sh parse remotely  - Deploy to remote host with forced re-parsing of all documents

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

# Check for parse argument to force re-parsing
if [[ "$1" == "parse" ]] || [[ "$2" == "parse" ]]; then
    echo -e "${BLUE}Parse flag detected - forcing re-parsing by removing existing parsing files...${NC}"
    PARSING_RESULTS_FILE_PATH="${STORAGE_DIR_NAME}/${PARSING_RESULTS_FILE_NAME}"
    PARSING_STATISTICS_FILE_PATH="${STORAGE_DIR_NAME}/${PARSING_RESULTS_STATISTICS_FILE_NAME}"
    
    # Remove pickle file with parsed pages
    if [[ -f "${PARSING_RESULTS_FILE_PATH}" ]]; then
        rm "${PARSING_RESULTS_FILE_PATH}"
        echo -e "${GREEN}Removed existing pickle file with parsed pages: ${PARSING_RESULTS_FILE_PATH}${NC}"
    else
        echo -e "${YELLOW}No existing pickle file with parsed pages found at: ${PARSING_RESULTS_FILE_PATH}${NC}"
    fi
    
    # Remove JSON file with parsing statistics
    if [[ -f "${PARSING_STATISTICS_FILE_PATH}" ]]; then
        rm "${PARSING_STATISTICS_FILE_PATH}"
        echo -e "${GREEN}Removed existing JSON file with parsing statistics: ${PARSING_STATISTICS_FILE_PATH}${NC}"
    else
        echo -e "${YELLOW}No existing JSON file with parsing statistics found at: ${PARSING_STATISTICS_FILE_PATH}${NC}"
    fi
fi

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

# Comprehensive Docker cleanup
echo -e "${BLUE}Cleaning up existing project containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
docker image rm ${STORAGE_IMAGE_NAME}:latest 2>/dev/null || true
docker image rm ${WEBAPP_IMAGE_NAME}:latest 2>/dev/null || true
echo -e "${BLUE}Performing Docker system cleanup...${NC}"
docker image prune -f 2>/dev/null || true
docker builder prune -f 2>/dev/null || true

# Run one-time standards ingestion service
echo -e "${BLUE}Building and running standards ingestion service (one-time job)...${NC}"
docker-compose build ${STORAGE_SERVICE_NAME}
docker-compose run --rm ${STORAGE_SERVICE_NAME} python ${INGESTION_FILE_NAME}
INGESTION_EXIT_CODE=$?

if [ $INGESTION_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Standards ingestion failed with exit code: $INGESTION_EXIT_CODE${NC}"
    echo -e "${YELLOW}System information:${NC}"
    echo "Available memory: $(free -h | grep '^Mem:' | awk '{print $7}')"
    echo "Available disk space: $(df -h . | tail -1 | awk '{print $4}')"
    echo -e "${YELLOW}Check the error messages above for more details.${NC}"
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
if [[ "$1" == "remotely" ]] || [[ "$2" == "remotely" ]]; then
    HOST=${REMOTE_HOST:-localhost}
fi

echo -e "${YELLOW}The web application is available at: http://${HOST}:${WEBAPP_PORT}${NC}"