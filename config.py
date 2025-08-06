import os
from typing import Optional

class Settings:
    # Database configuration
    # For local development, use default PostgreSQL connection
    # For cloud deployment, set DATABASE_URL environment variable
    
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:123123@localhost:5432/postgres")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres_id3q_user:WuL9RFOo5qjK1Hnmau9moYUf0JA1CgTi@dpg-d1vvjdemcj7s73fpgo2g-a:5432/postgres_id3q")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # XML Feed URLs
    XML_FEEDS = {
        "ekos": "https://ekos.gr/xml_feed/skroutz_ekos.xml",
        "beq": "https://beq.gr/xml_feed/skroutz_beq.xml",
        "zoro": "https://zoro.gr/xml_feed/skroutz_zoro.xml",
        "1-3gr": "https://1-3.gr/xml_feed/skroutz1-3.xml"
    }
    
    # Search configuration
    SEARCH_RESULTS_PER_PAGE: int = 50
    MAX_SEARCH_RESULTS: int = 1000
    
    # Feed processing
    FEED_REFRESH_INTERVAL_HOURS: int = 24
    FEED_TIMEOUT_SECONDS: int = 300
    MAX_RETRIES: int = 3
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Optional AI features
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "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")
    
    # Elasticsearch configuration
    ELASTICSEARCH_ENABLED: bool = os.getenv("ELASTICSEARCH_ENABLED", "true").lower() == "true"
    ELASTICSEARCH_HOST: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    ELASTICSEARCH_USERNAME: Optional[str] = os.getenv("ELASTICSEARCH_USERNAME")
    ELASTICSEARCH_PASSWORD: Optional[str] = os.getenv("ELASTICSEARCH_PASSWORD")
    ELASTICSEARCH_USE_SSL: bool = os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true"

settings = Settings()
