#!/bin/bash

# Remote RAG system deployment script
# Usage options:
#   ./deploy_remotely.sh       - Deploy to remote host with existing parsed pages (if available)
#   ./deploy_remotely.sh parse - Deploy to remote host with forced re-parsing of all documents

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

# Check for parse argument to force re-parsing
DEPLOY_ARGS="remotely"
if [[ "$1" == "parse" ]]; then
    echo -e "${BLUE}Parse flag detected - will force re-parsing on remote server${NC}"
    DEPLOY_ARGS="parse remotely"
fi

echo -e "\n${BLUE}Starting remote deployment for RAG system for Ukrainian technical standards...${NC}"

echo -e "\n${BLUE}Copying .env file to remote server...${NC}"
scp -i "${SSH_KEY}" ".env" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/.env"

echo -e "\n${BLUE}Connecting to remote server and executing deployment...${NC}"
ssh -t -i "${SSH_KEY}" "${REMOTE_USER}@${REMOTE_HOST}" << EOF
    set -e
    trap 'echo "Command failed on remote server"; exit 1' ERR

    echo -e "\${GREEN}Connected to remote server ${REMOTE_HOST}\${NC}"
    
    echo -e "\n\${BLUE}Updating system packages and installing Git LFS...\${NC}"
    sudo apt-get update && \
    sudo apt-get upgrade -y && \
    sudo apt-get install -y git-lfs && \
    sudo apt-get autoremove -y && \
    sudo apt-get autoclean
    
    echo -e "\n\${BLUE}Configuring swap space for memory-intensive operations...\${NC}"
    if [[ \$(free -h | grep -i swap | awk '{print \$2}') == "0B" ]]; then
        echo -e "\${YELLOW}No swap space found, creating 2GB swap file...\${NC}"
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        if ! grep -q '/swapfile' /etc/fstab; then
            echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        fi
        echo -e "\${GREEN}Swap space created and activated\${NC}"
        free -h
    else
        echo -e "\${GREEN}Swap space already configured\${NC}"
        free -h
    fi
    
    echo -e "\n\${BLUE}Updating repository from ${REPO_URL}...\${NC}"
    if [[ -d "${REMOTE_DIR}" ]]; then
        echo -e "\${YELLOW}Repository found, updating...\${NC}"
        cd "${REMOTE_DIR}"
        if git fetch origin && git reset --hard origin/main; then
            echo -e "\${GREEN}Repository updated successfully\${NC}"
            echo -e "\${BLUE}Downloading Git LFS files (standards)...\${NC}"
            git lfs pull
            echo -e "\${GREEN}Standards updated successfully\${NC}"
        else
            echo -e "\${YELLOW}Git update failed, removing corrupted repository and re-cloning...\${NC}"
            cd ..
            rm -rf "${REMOTE_DIR}"
            git clone "${REPO_URL}" && \
            cd "${REMOTE_DIR}" && \
            git lfs pull
        fi
    else
        echo -e "\${YELLOW}Repository not found, cloning with LFS files...\${NC}"
        git clone "${REPO_URL}" && \
        cd "${REMOTE_DIR}" && \
        git lfs pull
    fi
    
    echo -e "\n\${BLUE}Copying .env file to project directory...\${NC}"
    cp /tmp/.env .env
    chmod 600 .env
    
    echo -e "\n\${BLUE}Running deployment script on remote server...\${NC}"
    chmod +x deploy.sh
    ./deploy.sh ${DEPLOY_ARGS}
    
EOF