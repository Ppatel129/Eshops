#!/bin/bash

# E-commerce Search API Startup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting E-commerce Search API...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cat > .env << EOF
# Database
DATABASE_URL=postgresql://postgres:123123@0.0.0.0:5432/postgres

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Optional: OpenAI API Key
OPENAI_API_KEY=

# Elasticsearch (optional - set to false if not using)
ELASTICSEARCH_ENABLED=false
ELASTICSEARCH_HOST=0.0.0.0
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_USE_SSL=false
EOF
    echo -e "${YELLOW}Please edit .env file with your actual configuration${NC}"
fi

# Test database connection
echo -e "${GREEN}Testing database connection...${NC}"
python -c "
from sqlalchemy import create_engine
from config import settings
try:
    engine = create_engine(settings.DATABASE_URL)
    result = engine.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Database connection failed. Please check your DATABASE_URL in .env${NC}"
    exit 1
fi

# Create database tables if they don't exist
echo -e "${GREEN}Setting up database tables...${NC}"
python -c "
from sqlalchemy import create_engine
from config import settings
from models import Base

try:
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    print('Database tables created/verified successfully')
except Exception as e:
    print(f'Database setup failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Database setup failed. Please check your database configuration${NC}"
    exit 1
fi

# Start the application
echo -e "${GREEN}Starting FastAPI application...${NC}"
echo -e "${GREEN}API will be available at: http://0.0.0.0:8000${NC}"
echo -e "${GREEN}Press Ctrl+C to stop${NC}"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload 