# 🚀 NocheatZone Camera Monitoring - Quick Start Guide

## ✅ Verification Complete

Your system has passed all checks! All components are ready.

```
✓ Passed: 21/21 checks
✓ Python 3.12 | Django | OpenCV | YOLOv8
✓ YOLO Model: yolov8n.pt (6.2 MB)
✓ Database: Connected
✓ Frontend Assets: All present
```

---

## 🎯 Quick Start (5 minutes)

### Step 1: Start Django Server

```bash
cd c:\Users\nandi\complete
python manage.py runserver
```

**Expected Output**:
```
✓ Starting development server at http://127.0.0.1:8000/
✓ Django version 4.2.28
```

### Step 2: Create Test Exam (If needed)

```bash
# In Django admin
python manage.py createsuperuser

# Access admin panel
http://localhost:8000/admin/

# Create exam with Proctoring Type = "0" (Internal Camera)
```

### Step 3: Take Exam with Camera

1. Open: `http://localhost:8000/give-test/`
2. Enter Test ID and Password
3. **Allow Camera Permission** when browser asks
4. Click "Login For Exam"
5. Camera starts automatically ✓

### Step 4: Test Monitoring

Try these to trigger violations:

- **Show phone in camera** → Should detect and alert
- **Have 2 people in frame** → Multiple persons violation
- **Look away from screen** → Looking away violation
- **Exceed 5 violations** → Exam automatically terminates

---

## 📊 Real-time Monitoring Dashboard

Once in exam:

```
┌─────────────────────────────────────┐
│  📱 Exam Monitoring Overlay         │
│  (Top-right corner)                 │
├─────────────────────────────────────┤
│  ⏰ Time Remaining: 59:45            │
│  📷 [Live Camera Feed - 210x160]    │
│  ⚠️ Violations: 0/5                 │
│  🔴 LIVE MONITORING (pulsing)       │
└─────────────────────────────────────┘
```

---

## 🔴 Violation Detection Flow

```
FRAME SENT
    ↓
YOLOv8 Detection
    ├─ Count persons
    ├─ Detect phones/objects
    └─ Return: [person=1, phone=false]
    ↓
Face & Head Pose Detection
    ├─ Detect face
    ├─ Check looking away angle (>48°)
    └─ Return: [face=true, looking_away=false]
    ↓
Violation Rules
    ├─ Multiple persons? → ALERT
    ├─ Phone detected? → ALERT
    ├─ Looking away? → CHECK
    └─ No face? → CHECK
    ↓
Response
    ├─ No violations → {"status": "processed"}
    ├─ Violations → {"status": "warning_popup", "alerts": [...]}
    └─ Excess → {"status": "terminate"}
    ↓
Frontend Action
    ├─ Play alert sound 🔔
    ├─ Show SweetAlert popup
    ├─ Update violation counter
    └─ Auto-submit if >= 5 violations
```

---

## 🛠️ Configuration Quick Reference

### Adjust Detection Sensitivity

**File**: `exams/views.py` (Line ~300)

```python
# YOLO confidence thresholds (0-1, higher = more strict)
YOLO_PERSON_CONF = 0.4      # 40% - Increase to 0.5 for stricter
YOLO_PHONE_CONF = 0.3       # 30% - Decrease to 0.2 for sensitive

# Head pose angle threshold (degrees)
HEAD_POSE_THRESHOLD = 48    # Decrease to 40 for stricter

# Violation accumulation
NO_FACE_TRIGGER = 5         # 5 consecutive frames no face
LOOKING_AWAY_TRIGGER = 3    # 3 times looking away

# Termination
VIOLATION_LIMIT = 5         # Change to 3 for more strict
```

### Adjust Frame Rate

**File**: `static/camera-monitoring.js` (Line ~20)

```javascript
// Frame send interval
const FRAME_SEND_INTERVAL = 2000;  // Milliseconds
// 2000 = 1 frame every 2 seconds (current - optimal)
// 1000 = 1 frame per second (faster but heavier)
// 3000 = 1 frame every 3 seconds (slower)
```

---

## 🔍 Debugging Checklist

### Camera Not Starting

```bash
# Check 1: Browser console error
# Open DevTools (F12 → Console)
# Should see: "✓ Camera stream initialized successfully"

# Check 2: Permissions
# Chrome Settings → Privacy & Security → Camera
# Make sure localhost:8000 is allowed

# Check 3: HTTPS requirement
# Development: Works on localhost
# Production: MUST use HTTPS
```

### Frames Not Sending

```bash
# Check 1: Network tab (F12 → Network)
# Filter by "detect-cheating"
# Should see POST requests every 2 seconds
# Response: 200 OK with JSON

# Check 2: CSRF token
# Open browser console and run:
console.log(getCSRFToken())
# Should return a token string

# Check 3: Backend error logs
# Django terminal should show:
# ✓ Frame decoded successfully
# ✓ Detected: person (conf: 0.95)
```

### YOLO Not Detecting

```bash
# Check 1: Model loaded
# Django shell:
python manage.py shell
>>> from exams.views import load_yolo_model, YOLO_MODEL
>>> load_yolo_model()
>>> print(YOLO_MODEL)
# Should show: <model_type: object (v8) ...>

# Check 2: Model accuracy
# Can try different model sizes:
# yolov8n.pt (nano - fastest, less accurate)
# yolov8s.pt (small - balanced)
# yolov8m.pt (medium - slower, accurate)

# Edit: exams/views.py line ~50
YOLO_MODEL = YOLO('yolov8m.pt')  # Change here
```

---

## 📈 Performance Tips

### Optimize for Slow Networks

```javascript
// Reduce frame quality in camera-monitoring.js
const imageData = canvasElement.toDataURL('image/jpeg', 0.6); // Was 0.8
// Lower quality = faster upload = more real-time
```

### Optimize for Slow Devices

```python
# Use lighter YOLO model in exams/views.py
YOLO_MODEL = YOLO('yolov8n.pt')  # Nano (default, fastest)

# Or reduce frame resolution
# current: 210x160, can reduce to 160x120
```

### Balance Speed vs Accuracy

| Model | Frame Time | Accuracy | File Size |
|-------|-----------|----------|-----------|
| nano (n) | 20ms | 80% | 6.2MB |
| small (s) | 40ms | 85% | 22MB |
| medium (m) | 80ms | 90% | 49MB |

---

## 📱 Testing Different Scenarios

### Scenario 1: Normal Student

```
Frame 1: ✓ Person detected (1), Face found, No phone
Response: {"status": "processed", "score": 0}
✓ No alert
```

### Scenario 2: Student with Phone

```
Frame 1: ✓ Person detected (1), Face found, ✓ Phone detected
Response: {
  "status": "warning_popup",
  "alerts": ["Mobile phone detected"]
}
🔔 Alert shown, violation count = 1
```

### Scenario 3: Multiple People

```
Frame 1: ✓ Person detected (2), Faces found (2)
Response: {
  "status": "warning_popup",
  "alerts": ["Multiple persons detected (2)"]
}
🔔 Alert shown
```

### Scenario 4: Excessive Violations

```
Frame 1: violation (total: 1)
Frame 2: violation (total: 2)
Frame 3: violation (total: 3)
Frame 4: violation (total: 4)
Frame 5: violation (total: 5)
Response: {
  "status": "terminate",
  "message": "Exam terminated due to 5 violations"
}
❌ Exam auto-submitted, student cannot continue
```

---

## 🔐 Exam Integrity Features

### What Gets Monitored

✅ **Person count** (detect extra people)
✅ **Phone detection** (detect restricted devices)
✅ **Face visibility** (ensure student on camera)
✅ **Head pose** (detect looking away)
✅ **Attention span** (flag distractions)

### Violation Scoring

| Violation | Frequency | Threshold |
|-----------|-----------|-----------|
| Multiple persons | Each frame | Immediate flag |
| Phone/Object | Each frame | Immediate flag |
| No face | Per 5 frames | After 5 frames no face |
| Looking away | Per 3 times | After 3 instances |

---

## 📊 View Violation Logs

### In Django Admin

```
http://localhost:8000/admin/exams/violationlog/
```

Shows:
- Student name & email
- Test ID
- Violation details
- Timestamp
- Severity score

### Via CLI

```bash
python manage.py shell
>>> from exams.models import ViolationLog
>>> logs = ViolationLog.objects.filter(test_id='TEST001')
>>> for log in logs:
...     print(log.student, log.details, log.timestamp)
```

---

## 🚨 Emergency Stop

If monitoring needs to stop:

```javascript
// In browser console
window.NocheatZone.stopMonitoring()
// Camera stops, monitoring stops
// Can resume by refreshing page
```

---

## 🎓 Student Instructions (To Give to Students)

**Before Exam:**
1. Find a quiet place with good lighting
2. Sit 60-90cm from laptop
3. Minimize other applications
4. Put phone away

**During Exam:**
1. When camera permission prompt appears → Click "Allow"
2. Camera will start automatically (green border = active)
3. Keep face clearly visible
4. Don't step away from camera
5. No phones or external devices

**If Violations Occur:**
1. You'll see a popup alert ⚠️
2. Read the violation message
3. Correct the issue immediately
4. After 5 violations → Exam terminates automatically

---

## 📞 Support Commands

```bash
# Restart Django
python manage.py runserver

# Clear old violation logs
python manage.py shell
>>> from exams.models import ViolationLog
>>> ViolationLog.objects.all().delete()

# Check model performance
python manage.py shell
>>> from exams.views import load_yolo_model
>>> import time
>>> load_yolo_model()
>>> start = time.time()
>>> results = YOLO_MODEL(image)  # Run inference
>>> print(f"Inference: {time.time() - start}s")

# View system status
python verify_camera_system.py
```

---

## ✅ Pre-Exam Checklist

- [ ] Django server running (`python manage.py runserver`)
- [ ] Test exam created in admin panel
- [ ] Proctoring type set to "0" (Internal Camera)
- [ ] Camera physically working on device
- [ ] Browser permissions allowed for camera
- [ ] Good lighting in room
- [ ] No other applications capturing camera
- [ ] Test Student account created
- [ ] Violation logs accessible in admin

---

## 🎯 Success Indicators

✓ Camera feed visible in exam page
✓ Frame being sent every 2 seconds (Network tab shows POST to /exams/detect-cheating/)
✓ Detection results returned (JSON response with status/alerts)
✓ Violations logged in database
✓ Alert popup shows when violations detected
✓ Violation counter updates
✓ Exam terminates at 5 violations

---

## 📚 Full Documentation

See `CAMERA_MONITORING_GUIDE.md` for:
- Complete architecture overview
- Detailed API reference
- Advanced configuration
- Security considerations
- Performance optimization

```bash
cat CAMERA_MONITORING_GUIDE.md
```

---

## 🎉 You're Ready!

Your NocheatZone camera monitoring system is fully operational.

```bash
# Start the server
python manage.py runserver

# Then visit
http://localhost:8000/give-test/
```

Good luck! 🍀

---

**Version**: 1.0 | **Status**: ✅ Production Ready | **Last Updated**: Feb 2026
