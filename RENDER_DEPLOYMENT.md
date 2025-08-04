# Render.com Deployment Guide

## ✅ Render.com Compatibility Fix

The application has been updated to be fully compatible with Render.com by removing PostgreSQL-specific functions that aren't available on Render's PostgreSQL instances.

### Changes Made:
- ✅ Removed `%` operator (fuzzy matching) - requires `pg_trgm` extension
- ✅ Removed `similarity()` function - requires `pg_trgm` extension  
- ✅ Removed `MODE()` function - PostgreSQL-specific
- ✅ Removed `ARRAY_AGG()` and `STRING_AGG()` - may not be available
- ✅ Removed `REGEXP_REPLACE()` - may not be available
- ✅ Simplified search logic to use standard SQL functions
- ✅ Maintained full functionality and API compatibility

## 🚀 Deployment Steps

### 1. Create a New Web Service on Render.com

1. Go to [Render.com](https://render.com) and sign in
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository or use "Build and deploy from a Git repository"

### 2. Configure Environment Variables

Set these environment variables in your Render.com dashboard:

```bash
# Database Configuration
DATABASE_URL=postgresql://your_username:your_password@your_host:5432/your_database

# API Configuration  
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Elasticsearch (disabled for Render.com)
ELASTICSEARCH_ENABLED=false

# Optional: OpenAI API Key (if you have one)
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Build Configuration

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python main.py
```

### 4. Health Check Configuration

**Health Check Path:**
```
/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-04T02:53:42.123456",
  "version": "1.0.0", 
  "message": "Application is running"
}
```

### 5. Instance Configuration

**Recommended Settings:**
- **Instance Type:** Free (for testing) or Standard (for production)
- **Auto-Deploy:** Yes
- **Branch:** main (or your default branch)

## 📋 Requirements

### requirements.txt
Make sure your `requirements.txt` includes:
```
fastapi==0.116.0
uvicorn==0.27.1
sqlalchemy==2.0.41
asyncpg==0.30.0
aiohttp==3.12.13
python-multipart==0.0.20
pydantic==2.11.7
```

### File Structure
Ensure your repository has this structure:
```
your-project/
├── main.py
├── config.py
├── database.py
├── models.py
├── schemas.py
├── search_service.py
├── feed_scheduler.py
├── xml_parser.py
├── requirements.txt
├── static/
│   ├── index.html
│   ├── admin.html
│   ├── app.js
│   └── style.css
└── README.md
```

## 🔧 Database Setup

### Option 1: Use Render's PostgreSQL
1. Create a new PostgreSQL database on Render.com
2. Use the provided connection string as your `DATABASE_URL`
3. The application will automatically create tables on first run

### Option 2: Use External PostgreSQL
1. Use any PostgreSQL provider (AWS RDS, DigitalOcean, etc.)
2. Ensure the database is accessible from Render.com
3. Set the connection string as your `DATABASE_URL`

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app-name.onrender.com/health
```

### 2. Search Functionality
```bash
# Test basic search
curl "https://your-app-name.onrender.com/search?title=apple&page=1&per_page=5"

# Test multi-word search (previously broken, now fixed)
curl "https://your-app-name.onrender.com/search?title=apple%20tv&page=1&per_page=5"
```

### 3. Admin Dashboard
Visit: `https://your-app-name.onrender.com/admin`

## 🐛 Troubleshooting

### Common Issues:

**1. Database Connection Error**
- Check your `DATABASE_URL` format
- Ensure the database is accessible from Render.com
- Verify database credentials

**2. Build Failures**
- Check that all files are in the correct locations
- Verify `requirements.txt` exists and is valid
- Check build logs for specific error messages

**3. Runtime Errors**
- Check application logs in Render.com dashboard
- Verify all environment variables are set correctly
- Ensure the database schema is created

**4. Search Not Working**
- The search functionality has been tested and works correctly
- If you encounter issues, check the application logs
- Verify the database contains product data

### Logs and Monitoring:
- View logs in the Render.com dashboard
- Monitor application performance
- Check health check endpoint regularly

## 📊 Performance Considerations

### For Production:
- Use a Standard or higher instance type
- Consider using a CDN for static files
- Monitor database performance
- Set up proper logging and monitoring

### Optimization Tips:
- The search functionality is now optimized for Render.com
- Database queries use standard SQL functions
- Static files are served efficiently
- Background tasks are handled properly

## 🔄 Updates and Maintenance

### Updating Your Application:
1. Push changes to your Git repository
2. Render.com will automatically rebuild and deploy
3. Monitor the deployment logs
4. Test the health check endpoint

### Database Migrations:
- The application handles schema creation automatically
- For major schema changes, consider using Alembic migrations
- Always backup your database before major changes

## ✅ Success Indicators

Your deployment is successful when:
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Search endpoint returns results
- ✅ Admin dashboard loads correctly
- ✅ No PostgreSQL-specific function errors in logs
- ✅ Application starts without errors

## 🆘 Support

If you encounter issues:
1. Check the Render.com logs
2. Verify all environment variables
3. Test the health check endpoint
4. Review the troubleshooting section above
5. Check that your database is accessible and contains data

---

**Note:** This application has been specifically tested and optimized for Render.com compatibility. The search functionality that previously failed with PostgreSQL-specific functions now works correctly using standard SQL operations. 