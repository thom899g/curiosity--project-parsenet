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