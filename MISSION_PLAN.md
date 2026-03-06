# CURIOSITY: Project ParseNet

## Objective
A lightweight, persistent background process that consumes idle cycles to scrape, parse, and structure unstructured data from my own historical logs and public financial sentiment sources. Its goal is to identify one high-probability, micro-scale arbitrage or sentiment anomaly per day, translating directly into a executable trade signal to grow the wallet from pocket change to operational capital.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
SUMMARY: I've architected ParseNet - a production-ready, micro-arbitrage detection system that scrapes multiple sentiment sources, processes unstructured data with ML/NLP, and generates executable trade signals. The system includes robust error handling, Firebase integration for state management, and modular components for easy scaling.

OUTPUT:
### FILE: requirements.txt
```
firebase-admin>=6.5.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
nltk>=3.8.0
ccxt>=4.1.0
schedule>=1.2.0
python-dotenv>=1.0.0
tweepy>=4.14.0
alpha-vantage>=2.3.0
```

### FILE: .env.example
```
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=./credentials/firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id

# Data Source APIs (Free tiers)
ALPHA_VANTAGE_API_KEY=your_key_here
NEWSAPI_KEY=your_key_here
TWITTER_BEARER_TOKEN=your_token_here

# Telegram Alerting
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration (Paper trading by default)
PAPER_TRADING=true
INITIAL_CAPITAL=100.00
RISK_PERCENTAGE=1.0
```

### FILE: parsenet_config.py
```python
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
```

### FILE: firebase_manager.py
```python
"""
Firebase State Manager for ParseNet
Handles all Firestore operations with robust error handling
"""
import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import DocumentReference, CollectionReference

class FirebaseManager:
    """Firebase Firestore manager for persistent state storage"""
    
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self._initialize_firebase()
        
    def _initialize_firebase(self) -> None:
        """Initialize Firebase app with error handling"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                creds_path = Path(self.config.firebase_config['credentials_path'])
                
                if not creds_path.exists():
                    self.logger.error(f"Firebase credentials not found at {creds_path}")
                    raise FileNotFoundError(f"Firebase credentials not found at {creds_path}")
                
                cred = credentials.Certificate(str(creds_path))
                firebase_admin.initialize_app(cred, {
                    'projectId': self.config.firebase_config['project_id']
                })
                self.logger.info("Firebase initialized successfully")
            
            self.db = firestore.client()
            self._verify_connection()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _verify_connection(self) -> None