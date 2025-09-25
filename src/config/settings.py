"""
Configuration management for M-Pesa STK Push application.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class MpesaConfig:
    """M-Pesa API configuration."""
    consumer_key: str
    consumer_secret: str
    business_shortcode: int
    passkey: str
    callback_url: str
    environment: str = "sandbox"  # sandbox or production
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.consumer_key:
            raise ValueError("MPESA_CONSUMER_KEY is required")
        if not self.consumer_secret:
            raise ValueError("MPESA_CONSUMER_SECRET is required")
        if not self.passkey:
            raise ValueError("MPESA_PASSKEY is required")
        if self.business_shortcode <= 0:
            raise ValueError("MPESA_BUSINESS_SHORTCODE must be a valid number")
    
    @property
    def base_url(self) -> str:
        """Get the base URL based on environment."""
        if self.environment == "production":
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"
    
    @property
    def oauth_url(self) -> str:
        """Get OAuth token URL."""
        return f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
    
    @property
    def stk_push_url(self) -> str:
        """Get STK push URL."""
        return f"{self.base_url}/mpesa/stkpush/v1/processrequest"


@dataclass
class FlaskConfig:
    """Flask application configuration."""
    secret_key: str
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    threaded: bool = True
    json_sort_keys: bool = False
    jsonify_prettyprint_regular: bool = False
    
    def __post_init__(self):
        """Validate Flask configuration."""
        if not self.secret_key:
            raise ValueError("FLASK_SECRET_KEY is required")


class ConfigManager:
    """Centralized configuration manager."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager."""
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self._mpesa_config = None
        self._flask_config = None
    
    @property
    def mpesa(self) -> MpesaConfig:
        """Get M-Pesa configuration."""
        if self._mpesa_config is None:
            self._mpesa_config = MpesaConfig(
                consumer_key=os.getenv("MPESA_CONSUMER_KEY", ""),
                consumer_secret=os.getenv("MPESA_CONSUMER_SECRET", ""),
                business_shortcode=int(os.getenv("MPESA_BUSINESS_SHORTCODE", "0")),
                passkey=os.getenv("MPESA_PASSKEY", ""),
                callback_url=os.getenv("MPESA_CALLBACK_URL", "https://httpbin.org/post"),
                environment=os.getenv("MPESA_ENVIRONMENT", "sandbox")
            )
        return self._mpesa_config
    
    @property
    def flask(self) -> FlaskConfig:
        """Get Flask configuration."""
        if self._flask_config is None:
            self._flask_config = FlaskConfig(
                secret_key=os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-change-in-production"),
                debug=os.getenv("FLASK_DEBUG", "False").lower() == "true",
                host=os.getenv("FLASK_HOST", "127.0.0.1"),
                port=int(os.getenv("FLASK_PORT", "8000")),
                threaded=os.getenv("FLASK_THREADED", "True").lower() == "true"
            )
        return self._flask_config
    
    def validate(self) -> bool:
        """Validate all configurations."""
        try:
            # This will trigger validation in __post_init__
            _ = self.mpesa
            _ = self.flask
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")