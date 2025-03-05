#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p logs

echo -e "${YELLOW}Setting up PP-Datamining application...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install requirements
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    touch .env
    exit 1
fi

# Check if drug_indications.db file exists
if [ -f "drug_indications.db" ]; then
    echo -e "${YELLOW}Deleting drug_indications.db file...${NC}"
    rm drug_indications.db
fi


# Setup the application
echo -e "${YELLOW}Setting up the application...${NC}"
python scripts/setup.py

# Run the application with proper error handling
echo -e "${GREEN}Starting the application...${NC}"
if python main.py; then
    echo -e "${GREEN}Application started successfully${NC}"
else
    echo -e "${RED}Application failed to start. Check logs/app.log for details.${NC}"
    exit 1
fi

# Deactivate virtual environment on exit
deactivate 