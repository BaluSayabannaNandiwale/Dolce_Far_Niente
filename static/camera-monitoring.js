/**
 * NocheatZone - Live Camera Monitoring System
 * Complete implementation for real-time proctoring with YOLOv8 detection
 */

// ==================== GLOBAL VARIABLES ====================
let cameraStream = null;
let videoElement = null;
let canvasElement = null;
let violationCount = 0;
let isMonitoring = false;
const FRAME_SEND_INTERVAL = 3000; // 3 seconds (optimized for backend and flag display)
const MAX_VIOLATIONS = 5;
let lastFrameTime = 0;
let frameBuffer = [];

// ==================== CAMERA INITIALIZATION ====================

/**
 * Initialize camera stream with proper error handling
 */
async function initializeCamera() {
    try {
        console.log('🎥 Initializing camera...');
        
        // Request actual permissions first
        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false // Disable audio if not needed
        };

        // Chrome might need this workaround
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Your browser does not support camera access');
        }

        cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        
        videoElement = document.getElementById('stream');
        canvasElement = document.getElementById('capture');
        
        if (videoElement) {
            videoElement.srcObject = cameraStream;
            videoElement.play();
            console.log('✓ Camera stream initialized successfully');
            
            // Wait for video to be ready
            return new Promise((resolve) => {
                videoElement.onloadedmetadata = () => {
                    console.log('✓ Video metadata loaded');
                    resolve(true);
                };
                setTimeout(() => resolve(true), 1000);
            });
        }
    } catch (error) {
        console.error('❌ Camera initialization failed:', error);
        
        // Show user-friendly error message
        let errorMessage = 'Camera access failed. ';
        if (error.name === 'NotAllowedError') {
            errorMessage += 'Please allow camera access when prompted.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No camera device found.';
        } else {
            errorMessage += error.message;
        }
        
        showAlert('Camera Error', errorMessage, 'error');
        return false;
    }
}

/**
 * Stop camera stream safely
 */
function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => {
            track.stop();
        });
        cameraStream = null;
        console.log('✓ Camera stopped');
    }
}

// ==================== FRAME CAPTURE & PROCESSING ====================

/**
 * Capture current frame from video stream
 * @returns {string|null} Base64 encoded image or null
 */
function captureFrame() {
    if (!videoElement || !canvasElement) {
        console.warn('Video or canvas element not found');
        return null;
    }

    try {
        const ctx = canvasElement.getContext('2d');
        
        // Mirror the canvas for better UX (matches what user sees)
        ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(videoElement, -canvasElement.width, 0, canvasElement.width, canvasElement.height);
        ctx.restore();
        
        // Convert to base64
        const imageData = canvasElement.toDataURL('image/jpeg', 0.8); // 0.8 quality for smaller size
        return imageData.split(',')[1]; // Remove data:image/jpeg;base64, prefix
    } catch (error) {
        console.error('Error capturing frame:', error);
        return null;
    }
}

// ==================== BACKEND COMMUNICATION ====================

/**
 * Send frame to backend for detection
 * @param {string} frameB64 Base64 encoded frame
 * @param {string} testId Test ID
 */
async function sendFrameForDetection(frameB64, testId) {
    if (!frameB64 || frameB64.length === 0) {
        console.warn('Empty frame');
        return;
    }

    try {
        const response = await fetch('/exams/detect-cheating/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken()
            },
            body: new URLSearchParams({
                'data[imgData]': frameB64,
                'data[testid]': testId
            })
        });

        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            return;
        }

        const result = await response.json();
        handleDetectionResult(result);
    } catch (error) {
        console.error('Error sending frame:', error);
    }
}

/**
 * Handle detection result from backend
 */
function handleDetectionResult(result) {
    console.log('Detection result:', result);

    // Handle warning popup
    if (result.status === 'warning_popup' && result.alerts && result.alerts.length > 0) {
        violationCount++;
        displayViolationAlert(result.alerts, result.score);
        
        // Check if violations exceed limit
        if (violationCount >= MAX_VIOLATIONS) {
            terminateExam('Excessive violations detected');
        }
    }

    // Handle termination
    if (result.status === 'terminate') {
        terminateExam(result.message || 'Exam terminated due to violations');
    }

    // Update violation badge
    updateViolationBadge(violationCount);
}

/**
 * Display violation alert to student
 */
function displayViolationAlert(alerts, score) {
    console.log('🚨 VIOLATION DETECTED:', alerts);
    
    // Play alert sound
    playAlertSound();
    
    // Construct alert message
    const alertHTML = `
        <div style="text-align: left;">
            <p><strong>⚠️ Proctoring Alert!</strong></p>
            <p>Violations detected:</p>
            <ul style="margin-left: 20px;">
                ${alerts.map(alert => `<li>${alert}</li>`).join('')}
            </ul>
            <p style="color: #f97316;">Violation Count: ${violationCount}/${MAX_VIOLATIONS}</p>
            <p>Please follow exam guidelines or your test may be terminated.</p>
        </div>
    `;

    // Use Swal if available, else alert
    if (typeof Swal !== 'undefined') {
        if (!Swal.isVisible()) {
            Swal.fire({
                icon: 'warning',
                title: '⚠️ Exam Alert',
                html: alertHTML,
                showConfirmButton: true,
                confirmButtonText: 'I Understand',
                allowOutsideClick: false,
                backdrop: `rgba(239, 68, 68, 0.1)`,
                timer: 6000,
                timerProgressBar: true
            });
        }
    } else {
        alert(`VIOLATION ALERT!\n${alerts.join('\n')}`);
    }
}

/**
 * Terminate exam due to violations
 */
function terminateExam(reason) {
    console.error('🛑 EXAM TERMINATED:', reason);
    isMonitoring = false;
    stopCamera();
    
    const message = `Exam Terminated\n\nReason: ${reason}\n\nYour exam will be submitted automatically.`;
    
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: '❌ Exam Terminated',
            text: message,
            allowOutsideClick: false
        }).then(() => {
            // Try to submit exam
            const finishBtn = document.getElementById('finishBtn');
            if (finishBtn) {
                finishBtn.click();
            }
        });
    } else {
        alert(message);
        const finishBtn = document.getElementById('finishBtn');
        if (finishBtn) {
            finishBtn.click();
        }
    }
}

// ==================== UI UPDATES ====================

/**
 * Update violation badge display
 */
function updateViolationBadge(count) {
    const badge = document.getElementById('violation-count');
    if (badge) {
        badge.textContent = count;
        badge.style.backgroundColor = count >= MAX_VIOLATIONS - 1 ? '#dc2626' : '#ea580c';
    }
}

/**
 * Show custom alert
 */
function showAlert(title, message, type = 'info') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: type,
            title: title,
            text: message,
            allowOutsideClick: false
        });
    } else {
        alert(`${title}\n${message}`);
    }
}

/**
 * Play alert sound
 */
function playAlertSound() {
    try {
        // Create a simple beep using Web Audio API
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.warn('Could not play alert sound:', error);
    }
}

// ==================== MONITORING LOOP ====================

/**
 * Start continuous monitoring
 */
async function startMonitoring(testId) {
    if (!testId) {
        console.warn('Test ID not provided');
        return;
    }

    console.log('▶️ Starting monitoring for test:', testId);
    isMonitoring = true;

    const monitoringLoop = async () => {
        if (!isMonitoring) return;

        try {
            // Capture frame
            const frameB64 = captureFrame();
            if (frameB64) {
                // Send for detection
                await sendFrameForDetection(frameB64, testId);
            }
        } catch (error) {
            console.error('Monitoring error:', error);
        }

        // Schedule next frame
        setTimeout(monitoringLoop, FRAME_SEND_INTERVAL);
    };

    // Start monitoring loop
    monitoringLoop();
}

/**
 * Stop monitoring
 */
function stopMonitoring() {
    console.log('⏹️ Stopping monitoring');
    isMonitoring = false;
    stopCamera();
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Get CSRF token from page
 */
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    // Fallback to meta tag
    if (!cookieValue) {
        const token = document.querySelector('meta[name="csrf-token"]');
        if (token) cookieValue = token.getAttribute('content');
    }
    
    return cookieValue;
}

/**
 * Request camera permission (check before starting)
 */
async function checkCameraPermission() {
    try {
        const result = await navigator.permissions.query({ name: 'camera' });
        return result.state === 'granted';
    } catch (error) {
        console.log('Permissions API not supported, will attempt camera access');
        return null;
    }
}

/**
 * Initialize monitoring system on page load
 */
async function initializeMonitoring(testId, proctorType) {
    console.log('🚀 Initializing monitoring system...');
    console.log('Proctor Type:', proctorType);
    
    // Only start if proctoring is enabled (type 0)
    if (proctorType !== '0') {
        console.log('✓ External proctoring enabled, skipping internal monitoring');
        return;
    }

    // Check camera setup
    const videoEl = document.getElementById('stream');
    const canvasEl = document.getElementById('capture');
    
    if (!videoEl || !canvasEl) {
        console.error('❌ Video or canvas elements not found');
        showAlert('Setup Error', 'Camera elements not found on page', 'error');
        return;
    }

    // Initialize camera
    const cameraReady = await initializeCamera();
    if (!cameraReady) {
        console.error('❌ Camera initialization failed');
        return;
    }

    // Start monitoring
    await startMonitoring(testId);
    console.log('✓ Camera monitoring started');
}

// ==================== PAGE UNLOAD HANDLER ====================

window.addEventListener('beforeunload', () => {
    if (isMonitoring) {
        stopMonitoring();
    }
});

// Export for use in HTML
window.NocheatZone = {
    initializeMonitoring,
    stopMonitoring,
    captureFrame,
    sendFrameForDetection,
    showAlert
};

console.log('✓ NocheatZone camera monitoring module loaded');
