#!/bin/bash

# CTI GenAI Platform Setup Script
# This script helps you set up the platform quickly

set -e

echo "========================================="
echo "CTI GenAI Platform Setup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating data directories..."
mkdir -p data/vector_store
mkdir -p cache
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Check for Ollama
echo ""
echo "Checking for Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}Ollama is installed${NC}"
    
    # Check if llama3.2 model is available
    if ollama list | grep -q "llama3.2"; then
        echo -e "${GREEN}llama3.2 model is available${NC}"
    else
        echo -e "${YELLOW}llama3.2 model not found${NC}"
        read -p "Do you want to pull llama3.2 model? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Pulling llama3.2 model (this may take a while)..."
            ollama pull llama3.2
        fi
    fi
else
    echo -e "${YELLOW}Ollama is not installed${NC}"
    echo "You can install Ollama from: https://ollama.ai"
    echo "Or use LM Studio or cloud providers (OpenAI, Anthropic)"
fi

# Optional: Docker setup
echo ""
read -p "Do you want to set up Docker services (Neo4j, etc.)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v docker-compose &> /dev/null; then
        echo "Starting Docker services..."
        docker-compose up -d neo4j ollama
        echo -e "${GREEN}Docker services started${NC}"
        echo "Neo4j: http://localhost:7474 (neo4j/password)"
    else
        echo -e "${RED}docker-compose is not installed${NC}"
        echo "Please install Docker and docker-compose"
    fi
fi

# Summary
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. If using Ollama, ensure it's running: ollama serve"
echo "3. Run the application: streamlit run app.py"
echo ""
echo "For more information, see README.md"
echo ""

# Deactivate virtual environment
deactivate
