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
    SECRET_KEY: str = Field(default="")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Computer Vision Directories
    MODEL_DIR: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../lstm/saved_models")))
    MOCK_FEED_DIR: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/mock_feeds")))
    # Default pose model path (relative to backend folder). Override via env if needed.
    POSE_MODEL_PATH: str = Field(default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../yolov8n-pose.pt")))
    # Device used for pose model inference. Use 'cpu' or 'cuda:0', etc.
    POSE_DEVICE: str = Field(default="cpu")
    
    # Dynamic Agent Behavior Evaluation Thresholds
    # Used by Reasoning Agent to classify incident urgency
    LOW_RISK_THRESHOLD: int = 40
    MEDIUM_RISK_THRESHOLD: int = 70
    HIGH_RISK_THRESHOLD: int = 90
    CRITICAL_RISK_THRESHOLD: int = 100
    
    # Platform Warning Metrics
    PLATFORM_EDGE_SAFETY_LIMIT_METERS: float = 1.5
    PIXELS_PER_METER: float = 100.0
    WEBSOCKET_DETECTION_BROADCAST_INTERVAL_SECONDS: float = 0.25
    PLATFORM_CONTEXT_MULTIPLIERS: dict[str, float] = Field(
        default_factory=lambda: {"Platform 1": 1.25}
    )

    # LSTM configuration
    LSTM_SEQUENCE_LENGTH: int = 30
    LSTM_FEATURE_NAMES: List[str] = Field(
        default_factory=lambda: [
            "edge_proximity_seconds",
            "loitering_time",
            "pacing_count",
            "movement_speed",
            "direction_changes",
            "following_distance",
            "crowd_interactions",
        ]
    )
    LSTM_FEATURE_COUNT: int = 7

    # LSTM behavior label thresholds
    BEHAVIOR_HIGH_SCORE_THRESHOLD: float = 0.65
    BEHAVIOR_ERRATIC_SCORE_THRESHOLD: float = 0.4
    BEHAVIOR_FOLLOWING_DISTANCE_METERS: float = 1.2

    # Risk scoring weights
    RISK_SCORE_WEIGHTS: dict[str, float] = Field(
        default_factory=lambda: {
            "lstm": 0.4,
            "edge": 0.2,
            "duration": 0.1,
            "loitering": 0.1,
            "following": 0.1,
            "pose": 0.1,
        }
    )
    RISK_CONTEXT_MULTIPLIER_WEIGHT: float = 0.1

    # Twilio Escalation Configuration
    TWILIO_ACCOUNT_SID: str = Field(default="")
    TWILIO_AUTH_TOKEN: str = Field(default="")
    TWILIO_FROM_NUMBER: str = Field(default="")
    TWILIO_TO_NUMBERS: List[str] = Field(default=[], validation_alias="TWILIO_TO_NUMBERS")

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def _validate_secret_key(cls, value):
        import secrets
        if not value or value == "your-secret-key-here":
            # Auto-generate a secure random key if not set or using default
            return secrets.token_hex(32)
        return value

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
