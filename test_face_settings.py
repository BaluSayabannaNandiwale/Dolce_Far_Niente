#!/usr/bin/env python
"""
Test face verification settings
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizapp.settings')
import django
django.setup()

from django.conf import settings

def test_face_verification_settings():
    """Test that face verification is properly configured"""
    print("Face Verification Settings Test")
    print("=" * 40)

    face_enabled = getattr(settings, 'FACE_VERIFICATION_ENABLED', True)
    print(f"FACE_VERIFICATION_ENABLED setting: {face_enabled}")

    if not face_enabled:
        print("✓ Face verification is disabled - login should work without face verification")
        return True
    else:
        print("⚠ Face verification is enabled - may cause login issues")
        return False

if __name__ == "__main__":
    success = test_face_verification_settings()
    sys.exit(0 if success else 1)