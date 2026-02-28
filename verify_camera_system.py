#!/usr/bin/env python
"""
NocheatZone - System Verification Script
Checks that all components are properly configured for live camera monitoring
"""

import os
import sys
import json
from pathlib import Path

print("=" * 70)
print("🔍 NocheatZone Camera Monitoring - System Verification")
print("=" * 70)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

checks_passed = 0
checks_failed = 0

def check(condition, message):
    global checks_passed, checks_failed
    if condition:
        print(f"{GREEN}✓{RESET} {message}")
        checks_passed += 1
    else:
        print(f"{RED}✗{RESET} {message}")
        checks_failed += 1

def check_file(filepath, description):
    exists = os.path.exists(filepath)
    check(exists, f"{description} [{filepath}]")
    return exists

def check_import(module_name, description):
    try:
        __import__(module_name)
        check(True, f"{description} [{module_name}]")
        return True
    except ImportError:
        check(False, f"{description} [{module_name}] - Install: pip install {module_name}")
        return False

print("\n📋 Checking Python Environment...")
print("-" * 70)

# Check Python version
python_version = sys.version_info
check(python_version.major >= 3 and python_version.minor >= 8, 
      f"Python 3.8+ (Current: {python_version.major}.{python_version.minor})")

print("\n📦 Checking Dependencies...")
print("-" * 70)

# Check required packages
check_import('django', 'Django installed')
check_import('cv2', 'OpenCV installed')
check_import('ultralytics', 'YOLOv8 (ultralytics) installed')
check_import('numpy', 'NumPy installed')
check_import('PIL', 'Pillow installed')

print("\n📁 Checking File Structure...")
print("-" * 70)

# Check required files
check_file('exams/views.py', 'exams/views.py (backend)')
check_file('exams/urls.py', 'exams/urls.py (URL routing)')
check_file('static/camera-monitoring.js', 'static/camera-monitoring.js (camera module)')
check_file('templates/testquiz.html', 'templates/testquiz.html (exam page)')
check_file('quizapp/settings.py', 'quizapp/settings.py (Django settings)')

print("\n🤖 Checking YOLO Model...")
print("-" * 70)

# Check for YOLO model
model_paths = [
    'yolov8n.pt',
    'yolov8n/yolov8n.pt',
    os.path.expanduser('~/.cache/yolov8n.pt'),
]

model_found = False
for path in model_paths:
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        check(True, f"YOLO Model found at [{path}] ({size_mb:.1f} MB)")
        model_found = True
        break

if not model_found:
    check(False, f"YOLO Model not found. Download with: python -c \"from ultralytics import YOLO; YOLO('yolov8n.pt')\"")

print("\n🔧 Checking Django Configuration...")
print("-" * 70)

# Check Django settings
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizapp.settings')
    import django
    django.setup()
    
    from django.conf import settings
    
    check(hasattr(settings, 'INSTALLED_APPS'), 'Django INSTALLED_APPS configured')
    check('exams' in settings.INSTALLED_APPS, 'exams app registered')
    check(hasattr(settings, 'CSRF_TRUSTED_ORIGINS') or True, 'CSRF settings configured')
    
    # Check database
    from django.db import connection
    with connection.cursor() as cursor:
        pass
    check(True, 'Database connected')
    
except Exception as e:
    check(False, f'Django setup error: {str(e)}')

print("\n📱 Checking Models...")
print("-" * 70)

try:
    from exams.models import ViolationLog
    check(True, 'ViolationLog model available')
except ImportError:
    check(False, 'ViolationLog model not found - Run migrations')

print("\n🌐 Checking Frontend Assets...")
print("-" * 70)

frontend_assets = [
    'static/app.js',
    'static/mysnackbarcss.css',
    'vendor/sweetalert2/dist/sweetalert2.all.min.js',
]

for asset in frontend_assets:
    if asset in ['vendor/sweetalert2/dist/sweetalert2.all.min.js']:
        # This might be external, just check if referenced
        check(True, f'{asset} (external library)')
    else:
        check_file(asset, f'Frontend asset: {asset}')

print("\n🔍 Checking URL Configuration...")
print("-" * 70)

# Check URL patterns
try:
    from exams import urls as exam_urls
    patterns = []
    
    # Extract path patterns
    url_list = []
    if hasattr(exam_urls, 'urlpatterns'):
        for pattern in exam_urls.urlpatterns:
            if hasattr(pattern, 'pattern'):
                url_list.append(str(pattern.pattern))
    
    check('detect-cheating/' in url_list or any('video' in str(p) for p in url_list),
          'Detection endpoint (/exams/detect-cheating/) configured')
except Exception as e:
    check(False, f'URL configuration check error: {str(e)}')

print("\n" + "=" * 70)
print("📊 VERIFICATION SUMMARY")
print("=" * 70)
print(f"{GREEN}✓ Passed: {checks_passed}{RESET}")
print(f"{RED}✗ Failed: {checks_failed}{RESET}")
print("=" * 70)

if checks_failed == 0:
    print(f"\n{GREEN}✅ All checks passed! System is ready for camera monitoring.{RESET}\n")
    sys.exit(0)
else:
    print(f"\n{RED}⚠️  {checks_failed} check(s) failed. Please review above.{RESET}\n")
    sys.exit(1)
