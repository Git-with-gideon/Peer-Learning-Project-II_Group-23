#!/usr/bin/env python3
"""
Setup script for OptiGrade
Initializes database and creates necessary directories
"""

import os
import sys
from database_setup import create_database

def main():
    """Main setup function"""
    print("OptiGrade Setup")
    print("=" * 50)
    
    # Create necessary directories
    directories = ['data', 'images']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    # Initialize database
    print("\nInitializing database...")
    try:
        create_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False