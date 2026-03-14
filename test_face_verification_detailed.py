#!/usr/bin/env python
"""
Test face verification functionality
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

from django.conf import settings

def test_face_verification_components():
    """Test all face verification components"""
    print("Face Verification Component Test")
    print("=" * 50)

    # Test settings
    face_enabled = getattr(settings, 'FACE_VERIFICATION_ENABLED', True)
    print(f"✓ FACE_VERIFICATION_ENABLED: {face_enabled}")

    if not face_enabled:
        print("⚠ Face verification is disabled in settings")
        return False

    # Test imports
    try:
        from deepface import DeepFace
        deepface_available = True
        print("✓ DeepFace imported successfully")
    except ImportError as e:
        deepface_available = False
        print(f"⚠ DeepFace import failed: {e}")
        print("  System will use basic image comparison fallback")

    try:
        import cv2
        import numpy as np
        cv2_available = True
        print("✓ OpenCV and NumPy imported successfully")
    except ImportError as e:
        cv2_available = False
        print(f"✗ OpenCV/NumPy import failed: {e}")
        return False

    if not deepface_available and not cv2_available:
        print("✗ Neither DeepFace nor OpenCV available")
        return False

    # Test basic image processing
    try:
        # Create test images
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[:, :] = [255, 0, 0]  # Red square

        # Encode to base64
        _, buffer = cv2.imencode('.jpg', test_img)
        img_b64 = base64.b64encode(buffer).decode('utf-8')

        # Decode back
        nparr = np.frombuffer(base64.b64decode(img_b64), np.uint8)
        decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if decoded_img is not None and decoded_img.shape[0] > 0:
            print("✓ Image encoding/decoding works")
        else:
            print("✗ Image encoding/decoding failed")
            return False

    except Exception as e:
        print(f"✗ Image processing test failed: {e}")
        return False

    # Test DeepFace if available
    if deepface_available:
        try:
            # Test with same image (should match)
            result = DeepFace.verify(decoded_img, decoded_img, enforce_detection=False)
            verified = bool(result.get("verified", False))
            distance = result.get("distance", "N/A")

            print(f"✓ DeepFace basic test: verified={verified}, distance={distance}")

            if not verified:
                print("⚠ DeepFace self-verification failed - this may cause issues")
            else:
                print("✓ DeepFace self-verification passed")

        except Exception as e:
            print(f"⚠ DeepFace test failed: {e}")
            print("  System will use fallback verification")
    else:
        print("✓ Will use basic image comparison (DeepFace not available)")

    print("\n✓ Face verification system components are working")
    return True

def test_database_user_images():
    """Test that user images exist in database"""
    from accounts.models import User

    print("\nUser Image Database Test")
    print("=" * 30)

    users_with_images = User.objects.exclude(user_image__isnull=True).exclude(user_image='').count()
    total_users = User.objects.count()

    print(f"Users with images: {users_with_images}/{total_users}")

    if users_with_images == 0:
        print("⚠ No users have stored face images")
        print("  Face verification will be skipped for all users")
    else:
        print("✓ Some users have stored face images")

    return users_with_images > 0

if __name__ == "__main__":
    print("Testing Face Verification System")
    print("=" * 50)

    components_ok = test_face_verification_components()
    images_ok = test_database_user_images()

    print("\n" + "=" * 50)
    if components_ok:
        print("✓ Face verification system is ready")
        if images_ok:
            print("✓ Users have stored face images")
        else:
            print("⚠ No stored face images - verification will be skipped")
    else:
        print("✗ Face verification system has issues")

    sys.exit(0 if components_ok else 1)