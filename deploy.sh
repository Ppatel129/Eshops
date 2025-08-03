#!/bin/bash

# E-commerce Search API Deployment Script
# This script automates the deployment process on a fresh Ubuntu server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  E-commerce Search API Deployer${NC}"
echo -e "${BLUE}================================${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please don't run this script as root${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl wget

# Start and enable PostgreSQL
print_status "Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
print_status "Setting up database..."
sudo -u postgres psql -c "CREATE DATABASE postgres;" || print_warning "Database might already exist"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD '123123';" || print_warning "User might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;"
sudo -u postgres psql -c "ALTER USER postgres CREATEDB;"

# Create application directory
print_status "Setting up application directory..."
sudo mkdir -p /opt/eshops
sudo chown $USER:$USER /opt/eshops

# Copy application files (assuming script is run from project directory)
print_status "Copying application files..."
cp -r . /opt/eshops/
cd /opt/eshops

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
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
fi

# Test database connection
print_status "Testing database connection..."
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

# Create database tables
print_status "Setting up database tables..."
python -c "
from sqlalchemy import create_engine
from config import settings
from models import Base

try:
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    print('Database tables created successfully')
except Exception as e:
    print(f'Database setup failed: {e}')
    exit(1)
"

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/eshops.service > /dev/null << EOF
[Unit]
Description=E-commerce Search API
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/eshops
Environment=PATH=/opt/eshops/venv/bin
ExecStart=/opt/eshops/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
print_status "Setting permissions..."
sudo chown -R www-data:www-data /opt/eshops
sudo chmod +x /opt/eshops/start.sh

# Enable and start service
print_status "Starting application service..."
sudo systemctl daemon-reload
sudo systemctl enable eshops
sudo systemctl start eshops

# Create Nginx configuration
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/eshops > /dev/null << EOF
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Static files
    location /static/ {
        alias /opt/eshops/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/eshops /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Configure firewall
print_status "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Wait for service to start
print_status "Waiting for service to start..."
sleep 5

# Test the application
print_status "Testing application..."
if curl -f http://0.0.0.0:8000/health > /dev/null 2>&1; then
    print_status "Application is running successfully!"
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  Deployment Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo -e "${BLUE}Application URL:${NC} http://$(curl -s ifconfig.me)"
    echo -e "${BLUE}Health Check:${NC} http://$(curl -s ifconfig.me)/health"
    echo -e "${BLUE}Admin Panel:${NC} http://$(curl -s ifconfig.me)/admin"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo -e "  View logs: ${BLUE}sudo journalctl -u eshops -f${NC}"
    echo -e "  Restart app: ${BLUE}sudo systemctl restart eshops${NC}"
    echo -e "  Check status: ${BLUE}sudo systemctl status eshops${NC}"
    echo -e "  View Nginx logs: ${BLUE}sudo tail -f /var/log/nginx/access.log${NC}"
else
    print_error "Application failed to start. Check logs with: sudo journalctl -u eshops -f"
    exit 1
fi 