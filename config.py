import os
from typing import Optional

class Settings:
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres_id3q_user:WuL9RFOo5qjK1Hnmau9moYUf0JA1CgTi@dpg-d1vvjdemcj7s73fpgo2g-a:5432/postgres_id3q")
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
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
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Elasticsearch configuration
    ELASTICSEARCH_ENABLED: bool = os.getenv("ELASTICSEARCH_ENABLED", "false").lower() == "true"

settings = Settings()
