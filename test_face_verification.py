#!/usr/bin/env python
"""
Test script for face verification logic
"""
import os
import sys
import base64
import numpy as np

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizapp.settings')
import django
django.setup()

try:
    from deepface import DeepFace
    print("✓ DeepFace imported successfully")
except ImportError as e:
    print(f"✗ DeepFace import failed: {e}")
    sys.exit(1)

try:
    import cv2
    print("✓ OpenCV imported successfully")
except ImportError as e:
    print(f"✗ OpenCV import failed: {e}")
    sys.exit(1)

def test_face_verification():
    """Test the face verification logic with dummy data"""
    print("\nTesting face verification logic...")

    # Create a simple test image (1x1 pixel red image)
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[:, :] = [255, 0, 0]  # Red image

    # Encode to base64
    _, buffer = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    try:
        # Test decoding
        nparr = np.frombuffer(base64.b64decode(img_base64), np.uint8)
        im = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if im is not None:
            print("✓ Image decoding works")
            print(f"  Image shape: {im.shape}")
        else:
            print("✗ Image decoding failed")
            return False

        # Test DeepFace verification with same image
        try:
            result = DeepFace.verify(im, im, enforce_detection=False)
            verified = bool(result.get("verified", False))
            distance = result.get("distance", "N/A")
            print(f"✓ DeepFace verification works: verified={verified}, distance={distance}")
        except Exception as e:
            print(f"✗ DeepFace verification failed: {e}")
            return False

    except Exception as e:
        print(f"✗ Face verification test failed: {e}")
        return False

    print("✓ All face verification tests passed")
    return True

if __name__ == "__main__":
    success = test_face_verification()
    sys.exit(0 if success else 1)