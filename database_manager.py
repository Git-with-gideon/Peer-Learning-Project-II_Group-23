import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class OptiGradeDatabase:
    """Database manager for OptiGrade application"""
    
    def __init__(self, db_path: str = 'data/optigrade.db'):
        self.db_path = db_path
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        if not os.path.exists(self.db_path):
            from database_setup import create_database
            create_database()
