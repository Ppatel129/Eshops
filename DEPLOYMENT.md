# E-commerce Search API - Cloud Deployment Guide

This guide will help you deploy the E-commerce Search API to a cloud server without Docker.

## Prerequisites

- Ubuntu 20.04+ or CentOS 8+ server
- Python 3.10+
- PostgreSQL 13+
- Nginx (for reverse proxy)
- Git

## 1. Server Setup

### Update system packages
```bash
sudo apt update && sudo apt upgrade -y
```

### Install required packages
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl wget
```

## 2. PostgreSQL Setup

### Install and configure PostgreSQL
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE postgres;"
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;"
sudo -u postgres psql -c "ALTER USER postgres CREATEDB;"
```

### Configure PostgreSQL for remote connections (optional)
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/*/main/postgresql.conf
# Uncomment and modify: listen_addresses = '*'

# Edit pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## 3. Application Deployment

### Create application directory
```bash
sudo mkdir -p /opt/eshops
sudo chown $USER:$USER /opt/eshops
cd /opt/eshops
```

### Clone the repository
```bash
git clone <your-repository-url> .
```

### Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Create environment file
```bash
nano .env
```

Add the following content:
```env
# Database
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/postgres

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Optional: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Elasticsearch (optional - set to false if not using)
ELASTICSEARCH_ENABLED=false
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_USE_SSL=false
```

## 4. Database Setup

### Run database migrations
```bash
# Activate virtual environment
source venv/bin/activate

# Create database tables
python -c "
from sqlalchemy import create_engine, text
from config import settings
import asyncio
from models import Base

engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(engine)
print('Database tables created successfully')
"
```

## 5. Systemd Service Setup

### Create systemd service file
```bash
sudo nano /etc/systemd/system/eshops.service
```

Add the following content:
```ini
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
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Set permissions and enable service
```bash
# Set ownership
sudo chown -R www-data:www-data /opt/eshops

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable eshops
sudo systemctl start eshops
sudo systemctl status eshops
```

## 6. Nginx Configuration

### Create Nginx configuration
```bash
sudo nano /etc/nginx/sites-available/eshops
```

Add the following content:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

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
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
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
```

### Enable the site
```bash
sudo ln -s /etc/nginx/sites-available/eshops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. SSL Certificate (Optional but Recommended)

### Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain SSL certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 8. Firewall Configuration

### Configure UFW firewall
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 9. Monitoring and Logs

### View application logs
```bash
sudo journalctl -u eshops -f
```

### View Nginx logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 10. Elasticsearch Setup (Optional)

If you want to use Elasticsearch for enhanced search capabilities:

### Install Elasticsearch
```bash
# Add Elasticsearch repository
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# Install Elasticsearch
sudo apt update
sudo apt install -y elasticsearch

# Configure Elasticsearch
sudo nano /etc/elasticsearch/elasticsearch.yml
```

Add/modify these settings:
```yaml
network.host: localhost
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false
```

### Start Elasticsearch
```bash
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
sudo systemctl status elasticsearch
```

### Update environment file
```bash
nano .env
```

Set Elasticsearch to enabled:
```env
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

### Restart the application
```bash
sudo systemctl restart eshops
```

## 11. Maintenance

### Update application
```bash
cd /opt/eshops
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart eshops
```

### Backup database
```bash
# Create backup script
sudo nano /opt/eshops/backup.sh
```

Add content:
```bash
#!/bin/bash
BACKUP_DIR="/opt/eshops/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

mkdir -p $BACKUP_DIR
pg_dump -h localhost -U postgres postgres > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Make executable:
```bash
chmod +x /opt/eshops/backup.sh
```

### Set up automatic backups
```bash
sudo crontab -e
```

Add line for daily backup at 2 AM:
```
0 2 * * * /opt/eshops/backup.sh
```

## 12. Troubleshooting

### Check service status
```bash
sudo systemctl status eshops
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Check logs
```bash
sudo journalctl -u eshops -n 50
sudo tail -f /var/log/nginx/error.log
```

### Test database connection
```bash
source venv/bin/activate
python -c "
from sqlalchemy import create_engine
from config import settings
engine = create_engine(settings.DATABASE_URL)
result = engine.execute('SELECT 1')
print('Database connection successful')
"
```

### Test API endpoints
```bash
curl http://localhost:8000/health
curl http://your-domain.com/health
```

## 13. Performance Optimization

### Database optimization
```sql
-- Connect to PostgreSQL and run:
CREATE INDEX CONCURRENTLY idx_products_title ON products USING gin(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY idx_products_price ON products (price);
CREATE INDEX CONCURRENTLY idx_products_availability ON products (availability);
```

### Nginx optimization
```bash
sudo nano /etc/nginx/nginx.conf
```

Add to http block:
```nginx
client_max_body_size 10M;
client_body_timeout 60s;
client_header_timeout 60s;
keepalive_timeout 65s;
```

## 14. Security Considerations

1. **Change default passwords** for PostgreSQL and any other services
2. **Use strong passwords** for all database users
3. **Keep system updated** regularly
4. **Monitor logs** for suspicious activity
5. **Use SSL certificates** for HTTPS
6. **Configure firewall** properly
7. **Regular backups** of database and application files

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u eshops -f`
2. Verify configuration files
3. Test individual components (database, API, etc.)
4. Check system resources: `htop`, `df -h`, `free -h` 