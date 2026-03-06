"""
ParseNet Configuration Manager
Centralized configuration with validation and environment variable handling
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ParseNetConfig:
    """Central configuration manager for ParseNet"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._validate_environment()
        
    def _validate_environment(self) -> None:
        """Validate required environment variables"""
        required_vars = [
            'FIREBASE_PROJECT_ID',
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            self.logger.error(f"Missing required environment variables: {missing}")
            raise EnvironmentError(f"Missing environment variables: {missing}")
    
    @property
    def firebase_config(self) -> Dict[str, str]:
        """Firebase configuration"""
        return {
            'project_id': os.getenv('FIREBASE_PROJECT_ID'),
            'credentials_path': os.getenv('FIREBASE_CREDENTIALS_PATH', './credentials/firebase-service-account.json')
        }
    
    @property
    def data_sources(self) -> Dict[str, Optional[str]]:
        """Data source API keys"""
        return {
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'newsapi': os.getenv('NEWSAPI_KEY'),
            'twitter': os.getenv('TWITTER_BEARER_TOKEN')
        }
    
    @property
    def trading_config(self) -> Dict[str, Any]:
        """Trading configuration"""
        return {
            'paper_trading': os.getenv('PAPER_TRADING', 'true').lower() == 'true',
            'initial_capital': float(os.getenv('INITIAL_CAPITAL', '100.0')),
            'risk_percentage': float(os.getenv('RISK_PERCENTAGE', '1.0')),
            'min_signal_confidence': 0.75,
            'max_daily_signals': 1
        }
    
    @property
    def scraping_config(self) -> Dict[str, Any]:
        """Web scraping configuration"""
        return {
            'user_agent': 'ParseNet/1.0 (Research Bot; contact@example.com)',
            'request_timeout': 30,
            'max_retries': 3,
            'rate_limit_delay': 1.0,
            'cache_ttl_hours': 24
        }
    
    @property
    def telegram_config(self) -> Dict[str, Optional[str]]:
        """Telegram alerting configuration"""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Validate if both are provided or both are None
        if (token and not chat_id) or (chat_id and not token):
            self.logger.warning("Telegram bot token and chat ID must both be set or both be None")
            
        return {
            'bot_token': token,
            'chat_id': chat_id,
            'enabled': bool(token and chat_id)
        }
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate which API keys are available"""
        validation = {}
        for source, key in self.data_sources.items():
            validation[source] = bool(key and key != 'your_key_here')
        return validation

config = ParseNetConfig()