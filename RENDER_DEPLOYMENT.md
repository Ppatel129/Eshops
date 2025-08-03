# Render.com Deployment Guide

This guide will help you deploy the Eshops application to Render.com.

## Prerequisites

1. A Render.com account
2. A PostgreSQL database (you can create one on Render or use an external one)

## Step 1: Create a PostgreSQL Database

1. Go to your Render dashboard
2. Click "New" → "PostgreSQL"
3. Choose a name for your database
4. Select a plan (Free tier works for development)
5. Note down the connection details

## Step 2: Create a Web Service

1. In your Render dashboard, click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Step 3: Environment Variables (Optional)

The application will work with default settings, but you can customize it by adding these environment variables in your Render web service settings:

### Database Configuration
```
DATABASE_URL=postgresql://username:password@host:port/database_name
```
**Note**: If not set, the application will use a default local database configuration.

### Optional Customization
```
LOG_LEVEL=INFO
ELASTICSEARCH_ENABLED=false
OPENAI_API_KEY=your_openai_key_if_using_ai_features
```

## Step 4: Database Setup

After deployment, you'll need to initialize the database. You can do this by:

1. Going to your deployed service URL
2. Visiting `/admin` to access the admin panel
3. The database will be automatically initialized on first access

## Step 5: Verify Deployment

1. Check your service logs in Render dashboard
2. Visit your service URL (e.g., `https://your-app-name.onrender.com`)
3. Test the health endpoint: `https://your-app-name.onrender.com/health`

## Troubleshooting

### Common Issues

1. **Database Connection Error**: 
   - If using Render PostgreSQL, set the DATABASE_URL environment variable
   - If not set, the app will use default local database settings
2. **Port Issues**: Render automatically sets the PORT environment variable
3. **Build Failures**: Check that all dependencies are in requirements.txt

### Logs

Check the logs in your Render dashboard for detailed error messages. The application includes comprehensive logging for database connection issues.

## Example DATABASE_URL Format

For Render PostgreSQL, your DATABASE_URL will look like:
```
postgresql://username:password@host:port/database_name?sslmode=require
```

The application will automatically handle the SSL parameters and convert it to the asyncpg format.

## Default Configuration

If no environment variables are set, the application uses these defaults:
- **Database**: `postgresql://postgres:123123@localhost:5432/postgres`
- **Host**: `0.0.0.0`
- **Port**: `8000`
- **Log Level**: `INFO`
- **Elasticsearch**: Disabled

## Support

If you encounter issues:
1. Check the application logs in Render dashboard
2. Verify environment variables are set correctly (if using custom values)
3. Ensure your database is running and accessible 