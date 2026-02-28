/*!
 * NocheatZone - Camera Monitoring Test Suite
 * Automated tests for verification and debugging
 */

// ============= TEST CONFIGURATION =============
const TEST_CONFIG = {
    testId: 'TEST_CAMERA_001',
    framesPerTest: 5,
    delayBetweenFrames: 3000,
    verbose: true
};

// ============= UTILITY FUNCTIONS =============

function log(title, message) {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[${timestamp}]`;
    console.log(`%c${prefix} ${title}`, 'color: #0ea5e9; font-weight: bold;', message);
}

function success(message) {
    console.log(`%c✓ ${message}`, 'color: #10b981; font-weight: bold;');
}

function error(message) {
    console.error(`%c✗ ${message}`, 'color: #ef4444; font-weight: bold;');
}

function warn(message) {
    console.warn(`%c⚠️ ${message}`, 'color: #f59e0b; font-weight: bold;');
}

// ============= ENVIRONMENT TESTS =============

const EnvironmentTests = {
    
    checkBrowser() {
        log('Environment', 'Checking browser compatibility');
        
        const tests = [
            {
                name: 'getUserMedia API',
                check: () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
            },
            {
                name: 'Canvas API',
                check: () => !!document.createElement('canvas').getContext
            },
            {
                name: 'Fetch API',
                check: () => !!window.fetch
            },
            {
                name: 'Web Audio API',
                check: () => !!(window.AudioContext || window.webkitAudioContext)
            }
        ];
        
        let passed = 0;
        tests.forEach(test => {
            if (test.check()) {
                success(`${test.name} supported`);
                passed++;
            } else {
                error(`${test.name} NOT supported`);
            }
        });
        
        return passed === tests.length;
    },
    
    checkDOM() {
        log('DOM', 'Checking required HTML elements');
        
        const required = [
            { id: 'stream', name: 'Video element' },
            { id: 'capture', name: 'Canvas element' },
            { id: 'violation-count', name: 'Violation counter' },
            { id: 'monitoring-overlay', name: 'Monitoring overlay' }
        ];
        
        let found = 0;
        required.forEach(elem => {
            if (document.getElementById(elem.id)) {
                success(`${elem.name} found (#${elem.id})`);
                found++;
            } else {
                error(`${elem.name} NOT found (#${elem.id})`);
            }
        });
        
        return found === required.length;
    },
    
    checkCSRF() {
        log('Security', 'Checking CSRF token');
        
        try {
            const token = getCSRFToken();
            if (token && token.length > 0) {
                success(`CSRF token found (length: ${token.length})`);
                return true;
            } else {
                error('CSRF token is empty');
                return false;
            }
        } catch (e) {
            error(`CSRF check failed: ${e.message}`);
            return false;
        }
    }
};

// ============= CAMERA TESTS =============

const CameraTests = {
    
    async checkPermissions() {
        log('Camera', 'Checking permissions');
        
        try {
            const result = await navigator.permissions.query({ name: 'camera' });
            
            if (result.state === 'granted') {
                success('Camera permission already granted');
                return true;
            } else if (result.state === 'denied') {
                error('Camera permission denied - Reset in browser settings');
                return false;
            } else {
                warn('Camera permission state: prompt - Will ask on first use');
                return true;
            }
        } catch (e) {
            warn(`Permissions API unavailable: ${e.message}`);
            return true; // Not fatal
        }
    },
    
    async checkStream() {
        log('Camera', 'Testing camera stream');
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            
            const videoTracks = stream.getVideoTracks();
            if (videoTracks.length > 0) {
                const track = videoTracks[0];
                success(`Camera stream obtained (${track.label})`);
                
                // Stop the stream
                track.stop();
                return true;
            } else {
                error('No video tracks in stream');
                return false;
            }
        } catch (e) {
            error(`Camera access failed: ${e.message}`);
            return false;
        }
    },
    
    checkVideoElement() {
        log('Camera', 'Checking video element');
        
        const video = document.getElementById('stream');
        if (!video) {
            error('Video element not found');
            return false;
        }
        
        const checks = [
            { prop: 'autoplay', expected: true },
            { prop: 'muted', expected: true },
            { prop: 'playsinline', expected: true }
        ];
        
        let valid = true;
        checks.forEach(check => {
            if (video[check.prop] === check.expected) {
                success(`Video ${check.prop}: ${check.expected}`);
            } else {
                warn(`Video ${check.prop}: ${video[check.prop]} (expected: ${check.expected})`);
            }
        });
        
        return valid;
    }
};

// ============= DETECTION TESTS =============

const DetectionTests = {
    
    async testEndpoint() {
        log('Detection', 'Testing /exams/detect-cheating/ endpoint');
        
        try {
            // Create a simple test image
            const canvas = document.createElement('canvas');
            canvas.width = 210;
            canvas.height = 160;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
            
            const response = await fetch('/exams/detect-cheating/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'data[imgData]': imageData,
                    'data[testid]': TEST_CONFIG.testId
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                success(`Endpoint responsive (status: ${result.status})`);
                
                if (TEST_CONFIG.verbose) {
                    console.log('Response:', result);
                }
                
                return true;
            } else {
                error(`HTTP ${response.status}: ${response.statusText}`);
                return false;
            }
        } catch (e) {
            error(`Endpoint call failed: ${e.message}`);
            return false;
        }
    },
    
    async testFrameCapture() {
        log('Frame Capture', 'Testing frame capture functionality');
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();
            
            // Wait for video to load
            await new Promise(resolve => {
                video.onloadedmetadata = () => resolve();
                setTimeout(resolve, 500);
            });
            
            // Capture frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            if (imageData && imageData.length > 100) {
                success(`Frame captured (size: ${(imageData.length / 1024).toFixed(1)}KB)`);
                
                // Stop stream
                stream.getTracks().forEach(track => track.stop());
                return true;
            } else {
                error('Captured frame is empty');
                return false;
            }
        } catch (e) {
            error(`Frame capture failed: ${e.message}`);
            return false;
        }
    }
};

// ============= UI TESTS =============

const UITests = {
    
    checkAlertSystem() {
        log('UI', 'Checking alert system');
        
        const hasSweetAlert = typeof Swal !== 'undefined';
        if (hasSweetAlert) {
            success('SweetAlert2 loaded');
        } else {
            warn('SweetAlert2 not loaded - Fallback to alert()');
        }
        
        return hasSweetAlert;
    },
    
    testAlertSound() {
        log('UI', 'Testing alert sound');
        
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.05, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
            
            success('Alert sound test - You should hear a beep');
            return true;
        } catch (e) {
            error(`Alert sound failed: ${e.message}`);
            return false;
        }
    },
    
    checkViolationCounter() {
        log('UI', 'Checking violation counter');
        
        const counter = document.getElementById('violation-count');
        if (counter) {
            success(`Violation counter found (current: ${counter.textContent})`);
            return true;
        } else {
            error('Violation counter element not found');
            return false;
        }
    }
};

// ============= COMPREHENSIVE TEST SUITE =============

const TestSuite = {
    
    results: {
        passed: 0,
        failed: 0,
        tests: []
    },
    
    async runAll() {
        console.clear();
        console.log('%c🧪 NocheatZone Camera Monitoring - Test Suite', 'font-size: 16px; font-weight: bold; color: #0084ff;');
        console.log('═'.repeat(70));
        
        // Environment Tests
        console.log('%c\n📋 ENVIRONMENT TESTS', 'font-size: 13px; font-weight: bold; color: #0084ff;');
        this.runTest('Browser Compatibility', () => EnvironmentTests.checkBrowser());
        this.runTest('DOM Elements', () => EnvironmentTests.checkDOM());
        this.runTest('CSRF Token', () => EnvironmentTests.checkCSRF());
        
        // Camera Tests
        console.log('%c\n📷 CAMERA TESTS', 'font-size: 13px; font-weight: bold; color: #0084ff;');
        await this.runAsyncTest('Camera Permissions', () => CameraTests.checkPermissions());
        await this.runAsyncTest('Camera Stream', () => CameraTests.checkStream());
        this.runTest('Video Element', () => CameraTests.checkVideoElement());
        
        // Detection Tests
        console.log('%c\n🔍 DETECTION TESTS', 'font-size: 13px; font-weight: bold; color: #0084ff;');
        await this.runAsyncTest('Backend Endpoint', () => DetectionTests.testEndpoint());
        await this.runAsyncTest('Frame Capture', () => DetectionTests.testFrameCapture());
        
        // UI Tests
        console.log('%c\n🎨 UI/UX TESTS', 'font-size: 13px; font-weight: bold; color: #0084ff;');
        this.runTest('Alert System', () => UITests.checkAlertSystem());
        this.runTest('Alert Sound', () => UITests.testAlertSound());
        this.runTest('Violation Counter', () => UITests.checkViolationCounter());
        
        // Summary
        this.printSummary();
    },
    
    runTest(name, fn) {
        try {
            const result = fn();
            this.recordTest(name, result);
        } catch (e) {
            error(`Test ${name} crashed: ${e.message}`);
            this.recordTest(name, false, e.message);
        }
    },
    
    async runAsyncTest(name, fn) {
        try {
            const result = await fn();
            this.recordTest(name, result);
        } catch (e) {
            error(`Test ${name} crashed: ${e.message}`);
            this.recordTest(name, false, e.message);
        }
    },
    
    recordTest(name, passed, error = null) {
        if (passed) {
            this.results.passed++;
        } else {
            this.results.failed++;
        }
        
        this.results.tests.push({
            name,
            passed,
            error
        });
    },
    
    printSummary() {
        console.log('\n═'.repeat(70));
        console.log('%c📊 TEST SUMMARY', 'font-size: 13px; font-weight: bold; color: #0084ff;');
        console.log(`%c✓ Passed: ${this.results.passed}`, 'color: #10b981; font-weight: bold;');
        console.log(`%c✗ Failed: ${this.results.failed}`, this.results.failed > 0 ? 'color: #ef4444; font-weight: bold;' : 'color: #10b981; font-weight: bold;');
        console.log('═'.repeat(70));
        
        if (this.results.failed === 0) {
            console.log('%c\n✅ All tests passed! System is ready for camera monitoring.\n', 'color: #10b981; font-weight: bold; font-size: 12px;');
        } else {
            console.log(`%c\n⚠️ ${this.results.failed} test(s) failed. Please review above.\n`, 'color: #ef4444; font-weight: bold; font-size: 12px;');
        }
    }
};

// ============= EXPORT & INITIALIZATION =============

window.NocheatZoneTests = TestSuite;

// Auto-run tests when script loads (if in test mode)
if (window.location.search.includes('test=true')) {
    console.log('Auto-running tests...');
    TestSuite.runAll();
}

// Instructions
console.log('%c\n📝 INSTRUCTIONS', 'font-size: 12px; font-weight: bold; color: #0084ff;');
console.log('Run tests with: NocheatZoneTests.runAll()');
console.log('Or add ?test=true to URL for auto-run');
console.log('\n');
