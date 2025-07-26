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