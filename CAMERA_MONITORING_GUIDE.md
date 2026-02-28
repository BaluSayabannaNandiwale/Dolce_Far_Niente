# NocheatZone - AI Proctoring System
## Complete Live Camera Monitoring Implementation Guide

---

## 📋 System Overview

NocheatZone is a comprehensive Django-based AI proctoring system that monitors students during exams using:

- **YOLOv8** for object detection (persons, phones, etc.)
- **OpenCV** for face detection and head pose estimation
- **JavaScript getUserMedia API** for live camera capture
- **Real-time violation tracking** and exam termination

---

## 🎯 Features Implemented

### 1. **Live Camera Feed**
- Automatic camera initialization on exam start
- 24/7 monitoring with 2-second frame intervals
- Mirror display for better UX
- Quality: 80% JPEG compression for optimal speed

### 2. **YOLOv8 Object Detection**
- **Person Detection**: Count students in frame
- **Mobile Phone Detection**: Detect restricted devices
- **Multiple Objects**: Detect person, phone, laptop, books, etc.
- **Confidence Thresholds**: Person (40%), Phone (30%)

### 3. **Face & Head Pose Detection**
- Face detection using pre-trained models
- Head pose estimation via facial landmarks
- Angle tracking (looking away detection)
- Threshold: >48° triggers violation

### 4. **Violation Tracking**
- Face not visible (>5 consecutive frames)
- Multiple persons detected (>1)
- Mobile phone/restricted objects
- Looking away from screen (>3 consecutive times)
- Automatic exam termination at 5+ violations

### 5. **Real-time Alert System**
- SweetAlert2 popup notifications
- Audio alert sound (Web Audio API)
- Violation counter badge
- Progressive warning escalation

---

## 🔧 Technical Architecture

### Backend (Django)

**File**: `exams/views.py` → `video_feed_view()`

```
HTTP POST /exams/detect-cheating/
├── Input: Base64 encoded frame + test ID
├── Processing:
│   ├── Decode image
│   ├── Run YOLOv8 inference
│   ├── Detect faces & head pose
│   ├── Check violation rules
│   ├── Log violations to DB
│   └── Calculate violation score
└── Output: JSON with alerts & termination status
```

### Frontend (JavaScript)

**File**: `static/camera-monitoring.js`

```
Camera Initialization
├── Request getUserMedia permissions
├── Set up video stream
├── Configure canvas for frame capture
└── Start monitoring loop

Monitoring Loop (Every 2 seconds)
├── captureFrame() → Base64
├── sendFrameForDetection() → POST /exams/detect-cheating/
├── handleDetectionResult()
│   ├── Display alerts if violations
│   ├── Update violation counter
│   └── Terminate if limit exceeded
└── setTimeout() → Next cycle
```

### HTML Template

**File**: `templates/testquiz.html`

```html
<!-- Camera Element -->
<video id="stream" width="210" height="160" autoplay muted></video>
<canvas id="capture" width="210" height="160" style="display:none;"></canvas>

<!-- Violation Counter -->
<div id="violation-count">0/5</div>

<!-- Initialize on page load -->
<script>
  window.NocheatZone.initializeMonitoring(testId, proctorType);
</script>
```

---

## 📦 Files Modified/Created

| File | Purpose | Changes |
|------|---------|---------|
| `static/camera-monitoring.js` | **NEW** | Complete camera & monitoring module |
| `exams/views.py` | Video feed handler | Improved YOLO detection & logging |
| `templates/testquiz.html` | Exam page | Added camera UI & initialization |
| `exams/urls.py` | URL routing | Already configured (no change needed) |

---

## ⚙️ Installation & Setup

### 1. **Install Dependencies**

```bash
# Core packages
pip install Django==4.2.28
pip install ultralytics==8.0.0  # YOLOv8
pip install opencv-contrib-python==4.5.2.54
pip install Pillow==8.3.2

# Already should be installed
pip install numpy
pip install tensorflow
```

### 2. **Verify YOLO Model**

```bash
# Check if model file exists
ls -la yolov8n.pt           # Root directory
ls -la yolov8n/yolov8n.pt   # Alternative path

# If missing, download:
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. **Database Migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. **Django Settings**

Ensure `quizapp/settings.py` has:

```python
# CSRF settings
CSRF_TRUSTED_ORIGINS = ['localhost:8000', 'localhost:3000']

# Session settings
SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

---

## 🚀 Usage

### For Students:

1. **Login** → Navigate to exam
2. **Enter Test ID** and **Password**
3. **Allow Camera Permission** when prompted
4. Camera automatically starts
5. receive violations → Warnings appear
6. Exceed 5 violations → Exam terminates

### For Professors:

1. Setup test with **Proctoring Type = 0** (Internal Camera)
2. Monitor dashboard
3. Review violation logs in admin panel

---

## 📊 Violation Log Structure

**Model**: `exams.models.ViolationLog`

```python
class ViolationLog(models.Model):
    student = ForeignKey(User)
    test_id = CharField(max_length=100)
    details = TextField()  # "Mobile phone detected", etc.
    score = IntegerField(default=1)  # Cumulative: 1 point per violation
    timestamp = DateTimeField(auto_now_add=True)
```

**Admin View**: `exams/admin.py`

```python
# Monitor violations in Django admin
admin.site.register(ViolationLog)
```

---

## 🛠️ Configuration Options

### Adjust Sensitivity

**File**: `exams/views.py`

```python
# YOLO confidence thresholds
conf_person = 0.4       # 40% confidence for person
conf_phone = 0.3        # 30% confidence for phone

# Violation triggers
no_face_threshold = 5   # 5 consecutive frames no face
looking_away_threshold = 3  # 3 times looking away

# Termination
VIOLATION_LIMIT = 5     # Terminate at 5 violations
```

### Adjust Frame Rate

**File**: `static/camera-monitoring.js`

```javascript
const FRAME_SEND_INTERVAL = 2000; // 2 seconds (can be 1000 for faster)
const MAX_VIOLATIONS = 5;          // Termination threshold
```

---

## 🔍 Debugging

### Check Model Loading

```bash
python manage.py shell
>>> from exams.views import load_yolo_model, YOLO_MODEL
>>> load_yolo_model()
>>> print(YOLO_MODEL)
```

### Monitor Detection

Check Django logs:

```
✓ Frame decoded successfully. Shape: (720, 1280, 3)
✓ Detected: person (conf: 0.95)
✓ Face(s) detected: 1
✓ Frame processed. Total violations: 0
```

### JavaScript Console

Open browser DevTools (F12):

```javascript
// Check camera status
console.log(cameraStream)

// Manually send frame
window.NocheatZone.sendFrameForDetection(frameB64, testId)

// Get current violations
console.log(violationCount)
```

---

## 🚨 Common Issues & Fixes

### Camera Not Starting

**Issue**: "Camera initialization failed"

**Solutions**:
1. Check browser permissions (Settings → Privacy → Camera)
2. Ensure HTTPS in production (getUserMedia requires secure context)
3. Try incognito mode to reset permissions
4. Check browser logs (F12 → Console)

```javascript
// Check permission status
navigator.permissions.query({ name: 'camera' })
  .then(result => console.log(result.state))
```

### YOLO Model Not Loaded

**Issue**: "YOLO_MODEL is None"

**Solutions**:
1. Verify file path: `python -c "import os; print(os.path.exists('yolov8n.pt'))"`
2. Download model: `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`
3. Check permissions: `ls -la yolov8n*`

### Low Detection Accuracy

**Causes & Fixes**:
- **Lighting**: Ensure good lighting in room
- **Distance**: Student should be 60-90cm from camera
- **Confidence**: Adjust thresholds in `views.py`
- **Model size**: Can switch to `yolov8m.pt` (medium) for better accuracy

### Frames Not Sending

**Debug Steps**:
1. Check Network tab (F12 → Network)
2. Verify endpoint: `/exams/detect-cheating/`
3. Check CSRF token: `getCSRFToken()` in console
4. Monitor Django logs for errors

---

## 📈 Performance Optimization

### 1. **Frame Compression**
Current: JPEG 80% quality
```javascript
const imageData = canvasElement.toDataURL('image/jpeg', 0.8);
```

### 2. **Frame Rate**
Current: 1 frame every 2 seconds
```javascript
const FRAME_SEND_INTERVAL = 2000;
```

### 3. **Model Selection**
Current: `yolov8n` (nano - fastest)
Options:
- `yolov8n`: Fast (fastest)
- `yolov8s`: Small (balanced)
- `yolov8m`: Medium (most accurate)

```python
YOLO_MODEL = YOLO('yolov8n.pt')  # Change model here
```

### 4. **Async Processing**
All frame sending is non-blocking via Fetch API

---

## 🔒 Security Considerations

### 1. **CSRF Protection**
```javascript
// Automatically included in all requests
'X-CSRFToken': getCSRFToken()
```

### 2. **User Authentication**
- All endpoints require `@login_required`
- Student can only monitor their own exam

### 3. **Data Privacy**
- Frames are **not stored** (only decoded and processed)
- Only violation logs are saved to database
- Timestamps are recorded

### 4. **HTTPS (Production)**
```python
# In production settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 📝 API Reference

### POST `/exams/detect-cheating/`

**Request**:
```json
{
  "data[imgData]": "base64_encoded_image",
  "data[testid]": "EXAM001"
}
```

**Response - No Violations**:
```json
{
  "status": "processed",
  "score": 0,
  "person_count": 1,
  "detections": [
    {"class": "person", "confidence": 0.95}
  ]
}
```

**Response - With Violations**:
```json
{
  "status": "warning_popup",
  "alerts": [
    "❌ Mobile phone or restricted object detected",
    "❌ Multiple persons detected (2)"
  ],
  "score": 2,
  "person_count": 2,
  "phone_detected": true
}
```

**Response - Terminate Exam**:
```json
{
  "status": "terminate",
  "message": "Exam terminated due to 5 violations detected",
  "score": 5
}
```

---

## 🧪 Testing

### 1. **Test Camera Permission**
```bash
# Navigate to exam page
http://localhost:8000/give-test/TEST001/
# Allow camera when prompted
```

### 2. **Test Detection**
```javascript
// In browser console
// Manually capture and send a frame
let frame = window.NocheatZone.captureFrame();
window.NocheatZone.sendFrameForDetection(frame, 'TEST001');
```

### 3. **Force Violations**
- Show phone in camera → Should detect
- Have 2 people in frame → Should trigger violation
- Look away → Should count as violation
- Check violation logs in Django admin

---

## 📚 Additional Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com/
- **getUserMedia API**: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia  
- **Web Audio API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- **Django Docs**: https://docs.djangoproject.com/

---

## ✅ Checklist Before Deployment

- [ ] YOLO model downloaded and verified
- [ ] Camera permissions tested in target browser
- [ ] CSRF token properly generated
- [ ] Database migrations applied
- [ ] Violation logs accessible in admin
- [ ] Alert sounds working
- [ ] Frame sending successful (Network tab)
- [ ] Termination logic tested
- [ ] HTTPS configured (production)
- [ ] Error messages logged

---

## 📞 Support

For issues or improvements:

1. Check Django logs: `python manage.py runserver > debug.log`
2. Check browser console: F12 → Console tab
3. Monitor network requests: F12 → Network tab
4. Review violation logs: `/admin/exams/violationlog/`

---

**Version**: 1.0  
**Last Updated**: February 2026  
**Status**: ✅ Fully Functional
