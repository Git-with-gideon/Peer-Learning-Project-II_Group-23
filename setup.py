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
     # Check dependencies
    print("\nChecking dependencies...")
    required_packages = ['cv2', 'numpy', 'imutils']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT FOUND")
            missing_packages.append(package)
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install missing packages using:")
        print("pip install -r requirements.txt")
        return False
    
    print("\nSetup completed successfully!")
    print("\nYou can now run the application using:")
    print("python OptiGrade_Enhanced.py")
    print("\nOr view the database using:")
    print("python database_viewer.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 