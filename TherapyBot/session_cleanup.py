#!/usr/bin/env python
"""
Django Session Cleanup Script

This script helps diagnose and fix session-related issues in your Django application.
Run it as a standalone script or incorporate the functions into your management commands.

Usage:
python session_cleanup.py

Make sure to run this script in your Django project environment.
"""

import os
import sys
import django
from datetime import datetime

# Set up Django environment - adjust the path to your settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.core.management import call_command

def clean_expired_sessions():
    """Clean up expired sessions from the database."""
    print("Cleaning expired sessions...")
    
    # Get count before cleanup
    total_before = Session.objects.count()
    expired_count = Session.objects.filter(expire_date__lt=datetime.now()).count()
    
    # Run Django's built-in clearsessions command
    call_command('clearsessions', verbosity=1)
    
    # Get count after cleanup
    total_after = Session.objects.count()
    
    print(f"Found {expired_count} expired sessions out of {total_before} total sessions")
    print(f"Removed {total_before - total_after} sessions")
    print(f"{total_after} sessions remain in the database")

def check_session_configuration():
    """Check Django session configuration."""
    from django.conf import settings
    
    print("\nChecking session configuration...")
    
    # Check session engine
    engine = getattr(settings, 'SESSION_ENGINE', 'Not configured')
    print(f"Session engine: {engine}")
    
    # Check session cookie age
    cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)  # Default is 2 weeks
    print(f"Session cookie age: {cookie_age} seconds ({cookie_age // 86400} days)")
    
    # Check if sessions are saved on every request
    save_every_request = getattr(settings, 'SESSION_SAVE_EVERY_REQUEST', False)
    print(f"Save on every request: {save_every_request}")
    
    # Check session cookie name
    cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
    print(f"Session cookie name: {cookie_name}")
    
    # Recommendations
    print("\nRecommendations:")
    if not save_every_request:
        print("- Consider setting SESSION_SAVE_EVERY_REQUEST = True to keep sessions active")
    
    if cookie_age < 604800:  # Less than a week
        print("- Consider increasing SESSION_COOKIE_AGE for longer sessions")
    
    if 'db' in engine:
        print("- Run 'python manage.py clearsessions' regularly to clean expired sessions")

def main():
    """Main function to run all checks and cleanups."""
    print("Django Session Cleanup and Diagnostic Tool")
    print("=========================================")
    
    check_session_configuration()
    clean_expired_sessions()
    
    print("\nSession cleanup and diagnostics completed.")
    print("If you're still experiencing issues, check your application logs and consider:")
    print("1. Increasing session timeout values")
    print("2. Adding more robust error handling around session operations")
    print("3. Implementing a session recovery mechanism")

if __name__ == "__main__":
    main()