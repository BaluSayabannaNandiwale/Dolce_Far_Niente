#!/usr/bin/env python
"""
Face verification troubleshooting script
"""
import os
import sys

def check_face_verification_setup():
    """Check if face verification components are properly set up"""
    print("Face Verification Setup Check")
    print("=" * 40)

    # Check environment variable
    face_enabled = os.getenv('FACE_VERIFICATION_ENABLED', 'True').lower() == 'true'
    print(f"FACE_VERIFICATION_ENABLED: {face_enabled}")

    if not face_enabled:
        print("✓ Face verification is disabled via environment variable")
        return True

    # Check imports
    try:
        from deepface import DeepFace
        print("✓ DeepFace imported successfully")
    except ImportError as e:
        print(f"✗ DeepFace import failed: {e}")
        return False

    try:
        import cv2
        import numpy as np
        print("✓ OpenCV and NumPy imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV/NumPy import failed: {e}")
        return False

    print("✓ All face verification dependencies are available")
    return True

def diagnose_common_issues():
    """Diagnose common face verification issues"""
    print("\nCommon Issues and Solutions:")
    print("-" * 30)
    print("1. 'Face verification failed' error:")
    print("   - Check camera permissions")
    print("   - Ensure good lighting")
    print("   - Face the camera directly")
    print("   - Try again with a clearer image")
    print()
    print("2. To disable face verification temporarily:")
    print("   - Set environment variable: FACE_VERIFICATION_ENABLED=False")
    print("   - Or modify quizapp/settings.py: FACE_VERIFICATION_ENABLED = False")
    print()
    print("3. If DeepFace fails to load:")
    print("   - Check TensorFlow installation")
    print("   - Try reinstalling deepface: pip install --upgrade deepface")
    print()
    print("4. For testing without face verification:")
    print("   - The system will now allow login even with face verification errors")
    print("   - Check Django logs for detailed error messages")

if __name__ == "__main__":
    success = check_face_verification_setup()
    diagnose_common_issues()

    if success:
        print("\n✓ Face verification setup looks good")
    else:
        print("\n✗ Face verification setup has issues")

    sys.exit(0 if success else 1)