import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    # API App Metadata
    PROJECT_NAME: str = "RailMind AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # CORS Security Policies
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
        validation_alias="CORS_ORIGINS"
    )

    # Email Notification Configuration
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    ALERT_EMAIL_RECIPIENTS: List[str] = Field(default=["admin@railmind.ai"], validation_alias="ALERT_EMAIL_RECIPIENTS")

    # Database Architecture 
    DATABASE_URL: str = Field(default="sqlite:///./data/railmind.db", validation_alias="DATABASE_URL")
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="your-secret-key-here")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Computer Vision Directories
    MODEL_DIR: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lstm/saved_models")))
    MOCK_FEED_DIR: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/mock_feeds")))
    
    # Dynamic Agent Behavior Evaluation Thresholds
    # Used by Reasoning Agent to classify incident urgency
    LOW_RISK_THRESHOLD: float = 0.30
    MEDIUM_RISK_THRESHOLD: float = 0.50
    HIGH_RISK_THRESHOLD: float = 0.70
    CRITICAL_RISK_THRESHOLD: float = 0.90
    
    # Platform Warning Metrics
    PLATFORM_EDGE_SAFETY_LIMIT_METERS: float = 1.5
    PIXELS_PER_METER: float = 100.0

    # Twilio Escalation Configuration
    TWILIO_ACCOUNT_SID: str = Field(default="")
    TWILIO_AUTH_TOKEN: str = Field(default="")
    TWILIO_FROM_NUMBER: str = Field(default="")
    TWILIO_TO_NUMBERS: List[str] = Field(default=[], validation_alias="TWILIO_TO_NUMBERS")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _validate_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ALERT_EMAIL_RECIPIENTS", mode="before")
    @classmethod
    def _validate_alert_email_recipients(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("TWILIO_TO_NUMBERS", mode="before")
    @classmethod
    def _validate_twilio_to_numbers(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()