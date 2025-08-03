# E-commerce Search API

A scalable product search system with XML feed processing, built with FastAPI, PostgreSQL, and optional Elasticsearch integration.

## Features

- **Product Search**: Advanced search with filters, sorting, and pagination
- **Product Comparison**: Compare products across different shops
- **XML Feed Processing**: Automatic processing of product feeds from multiple sources
- **Elasticsearch Integration**: Optional enhanced search capabilities
- **Admin Dashboard**: Manage feeds, view statistics, and monitor system health
- **RESTful API**: Clean, documented API endpoints
- **Real-time Suggestions**: Search suggestions with fuzzy matching

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd Eshops
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL**
   ```bash
   # Create database and user
   sudo -u postgres psql -c "CREATE DATABASE postgres;"
   sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD '123123';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;"
   ```

5. **Run the application**
   ```bash
   ./start.sh
   # Or manually:
   # uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the application**
   - Main interface: http://localhost:8000
   - Admin panel: http://localhost:8000/admin
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## Cloud Deployment

### Option 1: Automated Deployment (Recommended)

1. **Upload files to your server**
   ```bash
   scp -r . user@your-server:/home/user/eshops
   ```

2. **Run the deployment script**
   ```bash
   ssh user@your-server
   cd /home/user/eshops
   chmod +x deploy.sh
   ./deploy.sh
   ```

The script will automatically:
- Install all required packages
- Set up PostgreSQL
- Configure Nginx
- Create systemd service
- Set up firewall
- Test the application

### Option 2: Manual Deployment

Follow the detailed instructions in [DEPLOYMENT.md](DEPLOYMENT.md)

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://postgres:123123@localhost:5432/postgres

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Optional: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Elasticsearch (optional)
ELASTICSEARCH_ENABLED=false
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_USE_SSL=false
```

### Elasticsearch Setup (Optional)

If you want enhanced search capabilities:

1. **Install Elasticsearch**
   ```bash
   # Ubuntu/Debian
   wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
   sudo apt update
   sudo apt install elasticsearch
   ```

2. **Configure Elasticsearch**
   ```bash
   sudo nano /etc/elasticsearch/elasticsearch.yml
   ```
   Add:
   ```yaml
   network.host: localhost
   http.port: 9200
   discovery.type: single-node
   xpack.security.enabled: false
   ```

3. **Start Elasticsearch**
   ```bash
   sudo systemctl enable elasticsearch
   sudo systemctl start elasticsearch
   ```

4. **Enable in configuration**
   ```env
   ELASTICSEARCH_ENABLED=true
   ```

## API Endpoints

### Core Endpoints

- `GET /` - Main search interface
- `GET /admin` - Admin dashboard
- `GET /health` - Health check
- `GET /docs` - API documentation

### Search Endpoints

- `GET /search` - Unified search with filters
- `GET /suggestions` - Search suggestions
- `GET /facets` - Search facets/aggregations
- `GET /categories/search` - Category search

### Product Endpoints

- `GET /product/{id}` - Get product by ID
- `GET /product/{id}/comparison` - Product comparison
- `GET /product/ean/{ean}` - Get product by EAN
- `GET /all-products` - List all products

### Admin Endpoints

- `POST /admin/process-feeds` - Process XML feeds
- `GET /admin/stats` - System statistics

## Database Schema

The application uses PostgreSQL with the following main tables:

- `products` - Product information
- `shops` - Shop information
- `brands` - Brand information
- `categories` - Category hierarchy

## Monitoring and Maintenance

### View Logs
```bash
# Application logs
sudo journalctl -u eshops -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Service Management
```bash
# Check status
sudo systemctl status eshops

# Restart service
sudo systemctl restart eshops

# Stop service
sudo systemctl stop eshops
```

### Database Backup
```bash
# Manual backup
pg_dump -h localhost -U postgres postgres > backup.sql

# Automated backup (cron job)
0 2 * * * /opt/eshops/backup.sh
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify connection string in `.env`
   - Check firewall settings

2. **Application Won't Start**
   - Check logs: `sudo journalctl -u eshops -f`
   - Verify virtual environment and dependencies
   - Check file permissions

3. **Elasticsearch Issues**
   - Check if Elasticsearch is running: `sudo systemctl status elasticsearch`
   - Verify configuration in `/etc/elasticsearch/elasticsearch.yml`
   - Check logs: `sudo journalctl -u elasticsearch -f`

4. **Nginx Issues**
   - Test configuration: `sudo nginx -t`
   - Check logs: `sudo tail -f /var/log/nginx/error.log`
   - Verify site configuration

### Health Check

The `/health` endpoint provides detailed system status:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-03T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "elasticsearch": "disabled"
  },
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 23.1
  }
}
```

## Performance Optimization

### Database Indexes
```sql
CREATE INDEX CONCURRENTLY idx_products_title ON products USING gin(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY idx_products_price ON products (price);
CREATE INDEX CONCURRENTLY idx_products_availability ON products (availability);
```

### Nginx Optimization
```nginx
client_max_body_size 10M;
client_body_timeout 60s;
client_header_timeout 60s;
keepalive_timeout 65s;
```

## Security Considerations

1. **Change default passwords** for PostgreSQL
2. **Use strong passwords** for all services
3. **Keep system updated** regularly
4. **Monitor logs** for suspicious activity
5. **Use SSL certificates** for HTTPS
6. **Configure firewall** properly
7. **Regular backups** of database and files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u eshops -f`
2. Verify configuration files
3. Test individual components
4. Check system resources: `htop`, `df -h`, `free -h` 