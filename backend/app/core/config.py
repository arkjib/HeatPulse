from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26083 Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sih26083.db"  # Use SQLite for now
    
    # External API Keys (to be overridden by .env in production)
    WEATHER_API_KEY: str = ""
    
    # Risk Engine (Heuristic defaults)
    RISK_WEIGHT_HAZARD: float = 0.50
    RISK_WEIGHT_VULNERABILITY: float = 0.30
    RISK_WEIGHT_EXPOSURE: float = 0.20
    DEMO_DATA_ENABLED: bool = False
    
    # Alert & Notification Engine
    NOTIFICATION_ENABLED: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
