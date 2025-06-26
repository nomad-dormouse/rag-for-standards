#!/bin/bash

# Change to script directory which is project root
cd "$(dirname "${BASH_SOURCE[0]}")"

# Load environment variables
if [[ -f ".env" ]]; then
    source ".env"
else
    echo "ERROR: .env file not found"
    exit 1
fi

# Check required environment variables
required_vars=("REMOTE_USER" "REMOTE_HOST" "SSH_KEY" "REMOTE_DIR" "REPO_URL" "WEBAPP_PORT")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "ERROR: Required environment variable $var is not set"
        exit 1
    fi
done

echo -e "\n${BLUE}Starting remote deployment for RAG system for Ukrainian technical standards...${NC}"

echo -e "\n${BLUE}Copying .env file to remote server...${NC}"
scp -i "${SSH_KEY}" ".env" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/.env"

echo -e "\n${BLUE}Connecting to remote server and executing deployment...${NC}"
ssh -t -i "${SSH_KEY}" "${REMOTE_USER}@${REMOTE_HOST}" << EOF
    set -e
    trap 'echo "Command failed on remote server"; exit 1' ERR

    echo -e "${GREEN}Connected to remote server ${REMOTE_HOST}${NC}"
    
    echo -e "\n${BLUE}Updating system packages and installing Git LFS...${NC}"
    sudo apt-get update && \
    sudo apt-get upgrade -y && \
    sudo apt-get install -y git-lfs && \
    sudo apt-get autoremove -y && \
    sudo apt-get autoclean
    
    echo -e "\n${BLUE}Updating repository from ${REPO_URL}...${NC}"
    if [[ -d "${REMOTE_DIR}" ]]; then
        echo -e "${YELLOW}Repository found, updating...${NC}"
        cd "${REMOTE_DIR}"
        export GIT_LFS_SKIP_SMUDGE=1
        if git fetch origin && git reset --hard origin/main; then
            echo -e "${GREEN}Repository updated successfully${NC}"
            unset GIT_LFS_SKIP_SMUDGE
        else
            unset GIT_LFS_SKIP_SMUDGE
            echo -e "${YELLOW}Git update failed, removing corrupted repository and re-cloning...${NC}"
            cd ..
            rm -rf "${REMOTE_DIR}"
            GIT_LFS_SKIP_SMUDGE=1 git clone "${REPO_URL}" && \
            cd "${REMOTE_DIR}"
        fi
    else
        echo -e "${YELLOW}Repository not found, cloning (skipping LFS files)...${NC}"
        GIT_LFS_SKIP_SMUDGE=1 git clone "${REPO_URL}" && \
        cd "${REMOTE_DIR}"
    fi
    
    echo -e "\n${BLUE}Copying .env file to project directory...${NC}"
    cp /tmp/.env .env
    chmod 600 .env
    
    echo -e "\n${BLUE}Running deployment script on remote server...${NC}"
    chmod +x deploy.sh
    ./deploy.sh remotely
    
EOF