// Complete exam system with navigation and state management
var nos = [];
var curr = 0;
var data = {};
const NOT_MARKED = 0;
const MARKED = 1;
const BOOKMARKED = 2;
const MARKED_BOOKMARKED = 3;
const SUBMITTED = 4;
const SUBMITTED_BOOKMARKED = 5;

// Global variables for question counts
var attemptedCount = 0;
var totalCount = 0;
var remainingCount = 0;

// Utility function to get CSRF token
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
        document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
        getCookie('csrftoken');
}

function getCookie(name) {
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
    return cookieValue;
}

// Fetch API wrapper with CSRF token
async function apiRequest(url, data, method = 'POST') {
    const response = await fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

function mySnackBar() {
    var x = document.getElementById("snackbar");
    if (x) {
        x.className = "show";
        setTimeout(function () { x.className = x.className.replace("show", ""); }, 10000);
    }
}

// Camera and audio globals
var stream = null;
var capture = null;
var cameraStream = null;
var audioContext = null;
var analyser = null;
var microphone = null;
var javascriptNode = null;
var array = null;
var values = 0;
var length = null;

function startStreaming() {
    stream = document.getElementById("stream");
    capture = document.getElementById("capture");

    var mediaSupport = 'mediaDevices' in navigator;
    navigator.getUserMedia = navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia;

    if (mediaSupport && null == cameraStream) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .catch(function (err) {
                console.warn("Audio access denied or failed, falling back to video only: " + err);
                return navigator.mediaDevices.getUserMedia({ video: true });
            })
            .then(function (mediaStream) {
                cameraStream = mediaStream;
                if (stream) {
                    stream.srcObject = mediaStream;
                    stream.play();
                }

                // Only attempt audio processing if audio track is available
                if (mediaStream.getAudioTracks().length > 0) {
                    try {
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        analyser = audioContext.createAnalyser();
                        microphone = audioContext.createMediaStreamSource(mediaStream);
                        javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

                        analyser.smoothingTimeConstant = 0.8;
                        analyser.fftSize = 1024;

                        microphone.connect(analyser);
                        analyser.connect(javascriptNode);
                        javascriptNode.connect(audioContext.destination);

                        javascriptNode.onaudioprocess = function () {
                            array = new Uint8Array(analyser.frequencyBinCount);
                            analyser.getByteFrequencyData(array);
                            values = 0;

                            length = array.length;
                            for (var i = 0; i < length; i++) {
                                values += (array[i]);
                            }
                        }
                    } catch (e) {
                        console.log("Audio context error: " + e);
                    }
                } else {
                    console.log("No audio tracks available, monitoring video only.");
                }
            })
            .catch(function (err) {
                console.log("Unable to access camera: " + err);
            });
    }
}

function stopStreaming() {
    if (null != cameraStream) {
        var track = cameraStream.getTracks()[0];
        track.stop();
        if (stream) stream.load();
        cameraStream = null;
    }
}

function captureSnapshot() {
    if (null != cameraStream && typeof tid !== 'undefined') {
        var ctx = capture.getContext('2d');
        ctx.drawImage(stream, 0, 0, capture.width, capture.height);
        var d1 = capture.toDataURL("image/png");
        var res = d1.replace("data:image/png;base64,", "");

        var average = values / length || 0;

        if (res) {
            $.post("/video_feed", {
                data: { 'imgData': res, 'voice_db': average, 'testid': tid }
            }, function (data) {
                // Handle Termination
                if (data.status === 'terminate') {
                    const terminationMessage = "Exam Terminated: Excessive Violations";
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: terminationMessage,
                            text: data.message || 'You have exceeded the maximum number of violations. Your exam is being submitted.',
                            allowOutsideClick: false,
                            timer: 5000,
                            timerProgressBar: true
                        }).then(() => {
                            document.getElementById('finishBtn').click();
                        });
                    } else {
                        alert(terminationMessage);
                        document.getElementById('finishBtn').click();
                    }
                    return;
                }

                // Handle YOLO Warning Popup (New)
                if (data.status === 'warning_popup' && data.alerts && data.alerts.length > 0) {
                    try {
                        const audio = new Audio('/static/assets/alert.mp3');
                        audio.play().catch(e => { });
                    } catch (e) { }

                    // Build alert message from alerts array
                    const currentFlags = data.flags || 0;
                    const alertHTML = `
                        <div style="text-align: left;">
                            <p><strong>⚠️ Proctoring Alert!</strong></p>
                            <p>Violations detected:</p>
                            <ul style="margin-left: 20px;">
                                ${data.alerts.map(alert => `<li>${alert}</li>`).join('')}
                            </ul>
                            <p style="color: #f97316;"><strong>Violation Flags: ${currentFlags}/5</strong></p>
                            <p style="color: #ef4444;"><strong>⚠️ Your exam will be terminated after 5 violations!</strong></p>
                            <p>Please follow exam guidelines immediately.</p>
                        </div>
                    `;

                    if (typeof Swal !== 'undefined') {
                        // Show a non-blocking warning (no backdrop) so exam controls remain usable
                        if (!Swal.isVisible()) {
                            console.log('app.js: showing non-blocking warning popup');
                            Swal.fire({
                                icon: 'warning',
                                title: '⚠️ Exam Alert',
                                html: alertHTML,
                                showConfirmButton: true,
                                confirmButtonText: 'I Understand',
                                allowOutsideClick: true,
                                backdrop: false,
                                timer: 6000,
                                timerProgressBar: true
                            });
                        }
                    } else {
                        console.warn("DETECTION ALERT:", data.alerts);
                    }
                }
                // Legacy Warning Toast
                else if (data.warning) {
                    if (typeof Swal !== 'undefined') {
                        const Toast = Swal.mixin({
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 4000,
                            timerProgressBar: true
                        });
                        Toast.fire({
                            icon: 'error',
                            title: data.warning
                        });
                    }
                }
            });
        }
    }
    // Continue polling every 2 seconds for YOLO (less heavy than 1s)
    setTimeout(captureSnapshot, 3000);
}



// MAIN INITIALIZATION
$(document).ready(function () {
    console.log('app.js: document.ready fired');
    // Configure global AJAX to include CSRF token
    $.ajaxSetup({
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    });

    var url = window.location.href;

    // Window focus handling
    // Window focus handling (Disabled as requested)
    /*
    window.onfocus = function (event) {
        mySnackBar();
        if (typeof tid !== 'undefined') {
            $.ajax({
                data: { 'testid': tid },
                type: "POST",
                url: "/window_event"
            });
        }
    };
    */

    // Check if we are on the exam page
    // The URL pattern is like /give-test/<test_id>/
    if (url.includes('/give-test/') && !url.endsWith('/give-test/')) {
        console.log("Exam page detected");

        var list = url.split('/');
        // Handle trailing slash
        var testId = list[list.length - 1];
        if (!testId) testId = list[list.length - 2];

        $('.question').remove();

        // Initialize exam
        $.ajax({
            type: "POST",
            url: "/randomize", // or window.location.href if that's where get flag is handled? No, randomize is separate
            // Actually, looks like randomize view returns the list of question IDs
            dataType: "json",
            data: { id: testId },
            success: function (temp) {
                console.log("Questions loaded:", temp);
                nos = temp;
                make_array();
                // If URL contains ?q= use that index (1-based). Otherwise start at 1.
                try {
                    const params = new URLSearchParams(window.location.search);
                    const qParam = parseInt(params.get('q'));
                    if (!isNaN(qParam) && qParam >= 1 && qParam <= nos.length) {
                        curr = qParam - 1;
                    } else {
                        curr = 0;
                    }
                } catch (e) {
                    curr = 0;
                }

                display_ques(curr + 1);
                ques_grid();
                updateQueryParamForQuestion(curr + 1);
            },
            error: function (xhr, status, error) {
                console.log("Randomize error:", error);
                // Fallback if randomize fails? 
            }
        });

        // Timer setup
        var timeElem = $('#time');
        console.log('⏱️ Timer initialization - looking for #time element');
        
        if (timeElem.length > 0) {
                    var timeText = timeElem.text().trim();
                    console.log('Raw time element text:', timeText);

                    // Accept either plain seconds or formatted HH:MM:SS / MM:SS
                    var time = NaN;
                    if (timeText.indexOf(':') !== -1) {
                        var parts0 = timeText.split(':').map(p => parseInt(p, 10) || 0);
                        if (parts0.length === 3) {
                            time = parts0[0]*3600 + parts0[1]*60 + parts0[2];
                        } else if (parts0.length === 2) {
                            time = parts0[0]*60 + parts0[1];
                        } else {
                            time = parseInt(timeText, 10);
                        }
                    } else {
                        // remove any non-digit characters then parse
                        var digits = timeText.replace(/[^0-9]/g, '');
                        time = digits ? parseInt(digits, 10) : NaN;
                    }
                    console.log('Parsed time (seconds):', time, '| isNaN:', isNaN(time));

                    if (!isNaN(time) && time > 0) {
                console.log('✓ Valid timer duration detected:', time, 'seconds');
                console.log('  Converting to HH:MM:SS format...');
                
                // Convert seconds to HH:MM:SS or MM:SS for initial display
                var hours = Math.floor(time / 3600);
                var minutes = Math.floor((time % 3600) / 60);
                var seconds = Math.floor(time % 60);
                hours = hours < 10 ? "0" + hours : ('' + hours);
                minutes = minutes < 10 ? "0" + minutes : ('' + minutes);
                seconds = seconds < 10 ? "0" + seconds : ('' + seconds);
                
                var initialDisplay = (hours === "00") ? (minutes + ":" + seconds) : (hours + ":" + minutes + ":" + seconds);
                console.log('  Initial display format:', initialDisplay);
                
                timeElem.text(initialDisplay);
                timeElem.html(initialDisplay);
                
                console.log('✓ Starting timer...');
                startTimer(time, timeElem);
                
                console.log('✓ Starting time update sender...');
                sendTime();
                
                flag_time = true;
                console.log('✓ Timer setup complete - flag_time = true');
            } else {
                console.error('✗ Invalid time value - time:', timeText);
                timeElem.text('00:00:00');
                timeElem.html('00:00:00');
                flag_time = false;
            }
        } else {
            console.error('✗ Timer element #time not found in DOM');
            console.error('  Available elements:', document.body.innerHTML.substring(0, 500));
            flag_time = false;
        }
    }

    // EVENT LISTENERS - Attached inside ready to ensure elements exist
    console.log('app.js: attaching event listeners');
    // Navigation and control handlers are provided as global functions
    // (previousQuestion, nextQuestion, bookmarkQuestion, submitAnswer, finishExam)
    // so UI can call them via onclick attributes.
    console.log('app.js: navigation handlers initialized (use global functions)');

    // Question grid click handler (delegated)
    $('#question-list').on('click', '.question-btn', function () {
        console.log('app.js: question-list button clicked');
        var id = parseInt($(this).text());
        curr = id - 1;
        display_ques(curr + 1);
    });

    // Finish button click is handled by global finishExam()
    console.log('app.js: finish button mapped to finishExam()');

    window.addEventListener('selectstart', function (e) { e.preventDefault(); });

    // Disable right click and copy paste with violation logging
    $('body').bind('cut copy paste', function (e) {
        e.preventDefault();
        console.warn("Copy/Paste/Cut violation detected");
        if (typeof tid !== 'undefined') {
            $.ajax({
                data: {
                    'testid': tid,
                    'details': 'Prohibited Action: ' + e.type.toUpperCase(),
                    'score': 1
                },
                type: "POST",
                url: "/window_event"
            });
        }
        mySnackBar();
    });

    $("body").on("contextmenu", function (e) {
        e.preventDefault();
        console.warn("Right-click violation detected");
        if (typeof tid !== 'undefined') {
            $.ajax({
                data: {
                    'testid': tid,
                    'details': 'Prohibited Action: Right Click (Context Menu)',
                    'score': 1
                },
                type: "POST",
                url: "/window_event"
            });
        }
        mySnackBar();
        return false;
    });

    // Radio button change handler
    $(document).on('change', 'input[name="answer-options"]', function () {
        const selectedValue = this.value;
        const selectedLabel = $(this).closest('.form-check').find('label');

        // Update visual feedback
        $('.form-check-label').removeClass('selected-answer').css('background-color', 'transparent');
        selectedLabel.addClass('selected-answer').css('background-color', 'rgba(0, 255, 0, 0.6)');

        // Update data structure
        if (!data[curr + 1]) data[curr + 1] = {};
        data[curr + 1].marked = selectedValue;
        if (data[curr + 1].status !== SUBMITTED && data[curr + 1].status !== SUBMITTED_BOOKMARKED) {
            data[curr + 1].status = MARKED;
        }

        // Update grid and counters
        $('#question-list').empty();
        ques_grid();
        updateQuestionCounter();
    });

    // Ensure exam form submits include selected answer
    $(document).on('submit', '#examForm', function (e) {
        try {
            var selected = document.querySelector('input[name="answer-options"]:checked');
            var ansVal = selected ? selected.value : '';
            var ansInput = document.getElementById('ans_input');
            if (ansInput) ansInput.value = ansVal;
            // Ensure qid is set
            var qidInput = document.getElementById('qid_input');
            if (qidInput && (!qidInput.value || qidInput.value === '')) {
                if (typeof nos !== 'undefined' && nos[curr]) qidInput.value = nos[curr];
            }
                // Update time hidden field with current remaining seconds so server can persist it
                var timeInput = document.getElementById('time_input');
                if (timeInput) {
                    var timeText = $('#time').text().trim();
                    if (timeText) {
                        var parts = timeText.split(':');
                        var sec = 0;
                        if (parts.length === 3) {
                            sec = (parseInt(parts[0], 10) || 0) * 3600 + (parseInt(parts[1], 10) || 0) * 60 + (parseInt(parts[2], 10) || 0);
                        } else if (parts.length === 2) {
                            sec = (parseInt(parts[0], 10) || 0) * 60 + (parseInt(parts[1], 10) || 0);
                        } else {
                            sec = parseInt(parts[0], 10) || 0;
                        }
                        timeInput.value = sec;
                    }
                }
        } catch (err) {
            console.warn('Error preparing form submit:', err);
        }
        // allow normal submission to proceed
    });
});


var unmark_all = function () {
    // Uncheck all radio buttons
    $('input[name="answer-options"]').prop('checked', false);

    // Reset any visual highlights
    $('.form-check-label').removeClass('selected-answer');
    $('.form-check-input').closest('.form-check').find('.form-check-label').css("background-color", 'transparent');
}

var display_ques = async function (move) {
    unmark_all();
    if (!nos || !nos[curr]) return;

    console.log("Displaying question:", move, "qid:", nos[curr]);

    try {
        const response = await apiRequest(window.location.href, { flag: 'get', no: nos[curr] }, 'POST');

        // document.getElementById('que').textContent = response['q'];
        $('#que').text(response['q']);

        // Update labels for radio buttons
        $('#option-a').next('label').text('𝐀.  ' + response['a']);
        $('#option-b').next('label').text('𝐁.  ' + response['b']);
        $('#option-c').next('label').text('𝐂.  ' + response['c']);
        $('#option-d').next('label').text('𝐃.  ' + response['d']);

        $('#queid').text('Question No. ' + (move));
        $('#mark').text('[MAX MARKS: ' + response['marks'] + ']'); // Updated format to match template

        // Restore selected answer if exists
        if (data[curr + 1] && data[curr + 1].marked != null) {
            const selectedOption = $('#option-' + data[curr + 1].marked);
            if (selectedOption.length) {
                selectedOption.prop('checked', true);
                selectedOption.closest('.form-check').find('label').addClass('selected-answer').css('background-color', 'rgba(0, 255, 0, 0.6)');
            }
        }

        updateQuestionCounter();
        // Update hidden qid field if present
        try {
            var qidInput = document.getElementById('qid_input');
            if (qidInput && typeof nos !== 'undefined' && nos[curr]) {
                qidInput.value = nos[curr];
            }
        } catch (e) { }
    } catch (error) {
        console.error("Error getting question:", error);
    }
}

// Update URL query param to reflect current question (q)
function updateQueryParamForQuestion(index) {
    try {
        const q = index;
        const newUrl = window.location.pathname + '?q=' + q;
        history.replaceState(null, '', newUrl);
    } catch (e) {
        console.warn('Failed to update query param:', e);
    }
}

// Global navigation functions used by buttons
function nextQuestion() {
    console.log('nextQuestion() called, current:', curr);
    if (!nos || curr >= nos.length - 1) {
        alert('You are at the last question!');
        return;
    }
    curr += 1;
    display_ques(curr + 1);
    updateQueryParamForQuestion(curr + 1);
}

function previousQuestion() {
    console.log('previousQuestion() called, current:', curr);
    if (!nos || curr <= 0) {
        alert('You are at the first question!');
        return;
    }
    curr -= 1;
    display_ques(curr + 1);
    updateQueryParamForQuestion(curr + 1);
}

function bookmarkQuestion() {
    console.log('bookmarkQuestion() called, current:', curr);
    if (!data[curr + 1]) data[curr + 1] = { marked: null, status: NOT_MARKED };
    const status = data[curr + 1].status;
    if (status == MARKED) data[curr + 1].status = MARKED_BOOKMARKED;
    else if (status == SUBMITTED) data[curr + 1].status = SUBMITTED_BOOKMARKED;
    else if (status == MARKED_BOOKMARKED) data[curr + 1].status = MARKED;
    else if (status == SUBMITTED_BOOKMARKED) data[curr + 1].status = SUBMITTED;
    else if (status == BOOKMARKED) data[curr + 1].status = NOT_MARKED;
    else data[curr + 1].status = BOOKMARKED;

    document.getElementById('question-list').innerHTML = '';
    ques_grid();
    updateQuestionCounter();
}

async function submitAnswer() {
    console.log('submitAnswer() called, current:', curr);
    const selectedOption = document.querySelector('input[name="answer-options"]:checked');
    const selectedAnswer = selectedOption ? selectedOption.value : null;

    if (!selectedAnswer) {
        alert('Please select an answer before submitting!');
        return;
    }

    if (!data[curr + 1]) data[curr + 1] = {};
    data[curr + 1].marked = selectedAnswer;
    data[curr + 1].status = SUBMITTED;

    try {
        const response = await apiRequest(window.location.href, {
            flag: 'mark',
            qid: nos[curr],
            ans: selectedAnswer
        }, 'POST');

        console.log('Answer posted successfully', response);
        document.getElementById('question-list').innerHTML = '';
        ques_grid();
        updateQuestionCounter();

        // Auto-move to next question
        if (curr < nos.length - 1) {
            curr += 1;
            display_ques(curr + 1);
            updateQueryParamForQuestion(curr + 1);
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Failed to submit answer. Please try again.');
    }
}

function finishExam() {
    console.log('finishExam() called');
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Are you sure?',
            text: 'Do you want to finish and submit your exam now? This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, finish exam',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                // Reuse existing funSubmitExam flow to save answers and complete
                funSubmitExam();
            }
        });
    } else {
        if (confirm('Finish and submit your exam?')) {
            funSubmitExam();
        }
    }
}

var flag_time = false;
var timerInterval = null;  // Store timer interval globally for cleanup

function startTimer(duration, display) {
    var timer = duration, hours, minutes, seconds;
    
    // Log timer start for debugging
    console.log('startTimer() called with duration:', duration, 'seconds, display element:', display);
    
    // Clear any existing timer
    if (timerInterval) {
        clearInterval(timerInterval);
        console.log('Cleared previous timer interval');
    }

    // Ensure display element exists
    if (!display || display.length === 0) {
        console.error('Timer display element not found or invalid');
        return;
    }

    // Create interval and store reference globally
    timerInterval = setInterval(function () {
        hours = parseInt(timer / 3600, 10);
        minutes = parseInt((timer % 3600) / 60, 10);
        seconds = parseInt(timer % 60, 10);

        hours = hours < 10 ? "0" + hours : hours;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        // Prefer MM:SS display unless hours > 0
        var timeString = (hours === "00") ? (minutes + ":" + seconds) : (hours + ":" + minutes + ":" + seconds);
        
        // Update display element (using both text and html to be safe)
        display.text(timeString);
        display.html(timeString);
        
        // Log every 30 seconds to avoid console spam
        if (timer % 30 === 0 || timer < 10) {
            console.log('⏱️ Timer:', timeString, '(remaining:', timer, 's)');
        }

        // Auto-submit when timer reaches 0
        if (--timer < 0) {
            console.log('⏰ Timer expired at 0 - auto-submitting exam');
            clearInterval(timerInterval);
            timerInterval = null;
            flag_time = false;
            // Auto submit via form if present
            try {
                if (document.getElementById('examForm')) {
                    var f = document.getElementById('examForm');
                    var act = document.createElement('input');
                    act.type = 'hidden'; act.name = 'action'; act.value = 'finish';
                    f.appendChild(act);
                    f.submit();
                } else {
                    finish_test();
                }
            } catch (e) { finish_test(); }
        }
    }, 1000);
    
    console.log('✓ Timer interval started successfully');
}

async function finish_test() {
    console.log("finish_test called");

    // Ensure all answered questions are saved before marking as completed
    for (let i = 1; i <= nos.length; i++) {
        if (data[i] && data[i].marked && data[i].status !== SUBMITTED && data[i].status !== SUBMITTED_BOOKMARKED) {
            const qid = nos[i - 1];
            const ans = data[i].marked;

            try {
                await apiRequest(window.location.href, {
                    flag: 'mark',
                    qid: qid,
                    ans: ans
                }, 'POST');
            } catch (error) {
                console.error("Error saving answer:", error);
            }
        }
    }

        try {
            const response = await apiRequest(window.location.href, { flag: 'completed' }, 'POST');
            console.log("Test completed successfully", response);
            // Redirect student to tests-given listing after finishing exam
            window.location.replace('/tests-given/');
        } catch (error) {
            console.error("Error completing test:", error);
            // Still redirect to tests-given even if there's an error
            window.location.replace('/tests-given/');
        }
}

function sendTime() {
    var sendTimeInterval = setInterval(function () {
        if (flag_time == false) {
            console.log('flag_time is false, stopping sendTime interval');
            clearInterval(sendTimeInterval);
            return;
        }
        
        var timeElem = $('#time');
        if (!timeElem || timeElem.length === 0) {
            console.warn('Time element not found, stopping sendTime');
            clearInterval(sendTimeInterval);
            return;
        }
        
        var time = timeElem.text().trim();
        if (!time) {
            console.warn('Time text is empty');
            return;
        }

        try {
            var parts = time.split(':');
            var seconds = 0;
            
            if (parts.length === 3) {
                // Format is HH:MM:SS
                var h = parseInt(parts[0]) || 0;
                var m = parseInt(parts[1]) || 0;
                var s = parseInt(parts[2]) || 0;
                seconds = h * 3600 + m * 60 + s;
            } else if (parts.length === 2) {
                // Format is MM:SS
                var m = parseInt(parts[0]) || 0;
                var s = parseInt(parts[1]) || 0;
                seconds = m * 60 + s;
            } else {
                seconds = parseInt(parts[0]) || 0;
            }
            
            // Send time update to server every 10 seconds instead of 5
            $.ajax({
                type: 'POST',
                url: window.location.href,
                dataType: "json",
                data: { flag: 'time', time: seconds },
                timeout: 5000,
                error: function(error) {
                    console.warn('Failed to send time update:', error.status);
                }
            });
            
        } catch (error) {
            console.error('Error in sendTime:', error);
        }
    }, 10000);  // Changed from 5000 to 10000 to reduce server load
}

var marked = function () {
    var count = 0;
    if (!nos) return 0;
    for (var i = 1; i <= nos.length; i++) {
        if (data[i] && (data[i].status == SUBMITTED || data[i].status == SUBMITTED_BOOKMARKED)) {
            count++;
        }
    }
    return count;
}

// Function to update question counters
function updateQuestionCounter() {
    if (!nos) return;
    totalCount = nos.length;
    attemptedCount = marked();
    remainingCount = totalCount - attemptedCount;

    // Update the modal content if it exists
    var modalContent = $('#swal2-html-container');
    if (modalContent.length > 0) {
        var tableHtml = '<table><tr><td>TOTAL QUESTIONS:</td><td>' + totalCount + '</td></tr><tr><td>ATTEMPTED:</td><td>' + attemptedCount + '</td></tr><tr><td>REMAINING:</td><td>' + remainingCount + '</td></tr></table>';
        modalContent.html(tableHtml);
    }
}

var ques_grid = function () {
    if (!nos) return;
    // console.log("Generating question grid for", nos.length, "questions");
    document.getElementById("overlay").style.display = "block";
    $('#question-list').empty();

    for (var i = 1; i <= nos.length; i++) {
        if (!data[i]) data[i] = { marked: null, status: NOT_MARKED };

        var color = '';
        var status = data[i].status;
        if (status == NOT_MARKED) {
            color = '#1976D2'; // Blue
        }
        else if (status == SUBMITTED) {
            color = '#42ed62'; // Green
        }
        else if (status == BOOKMARKED || status == SUBMITTED_BOOKMARKED) {
            color = '#e6ed7b'; // Yellow
        }
        else {
            color = '#f44336'; // Red
        }

        var j = i < 10 ? "0" + i : i;
        var buttonHtml = '<div class="col-sm-2 mb-2"><button class="btn btn-primary question-btn" style="background-color:' + color + '; color:white; width:100%; height:40px; border:none;">' + j + '</button></div>';
        $('#question-list').append(buttonHtml);
    }
}

var make_array = function () {
    if (!nos) return;
    for (var i = 0; i < nos.length; i++) {
        data[i + 1] = { marked: null, status: NOT_MARKED };
    }

    if (typeof answers !== 'undefined' && answers) {
        try {
            // Check if answers is already an object or string
            var ansObj = answers;
            if (typeof answers === 'string') {
                // Clean up potential template artifacts
                var div = document.createElement('div');
                div.innerHTML = answers;
                ansObj = JSON.parse(div.textContent || div.innerText || '{}');
            }

            for (var key in ansObj) {
                var idx = parseInt(key) + 1;
                if (data[idx]) {
                    data[idx].marked = ansObj[key];
                    data[idx].status = SUBMITTED;
                }
            }
        } catch (e) {
            console.log("Error parsing answers:", e);
        }
    }

    updateQuestionCounter();
}

function funSubmitExam() {
    // console.log("funSubmitExam called");
    updateQuestionCounter();

    if (typeof Swal === 'undefined') {
        if (confirm("Are you sure you want to finish the exam?")) {
            finish_test();
        }
        return;
    }

    Swal.fire({
        title: '<strong>FINISH EXAM</strong>',
        icon: 'warning',
        html:
            '<table><tr><td>TOTAL QUESTIONS:</td><td>' + totalCount + '</td></tr><tr><td>ATTEMPTED:</td><td>' + attemptedCount + '</td></tr><tr><td>REMAINING:</td><td>' + remainingCount + '</td></tr></table>',
        showCloseButton: false,
        showCancelButton: true,
        focusConfirm: true,
        confirmButtonText: 'OK, FINISH MY EXAM!',
        confirmButtonAriaLabel: 'We are abide by rules!'
    }).then((result) => {
        if (result.isConfirmed) {
            finish_test();
        }
    })
}

// Global key handlers
document.addEventListener('keyup', (e) => {
    if (e.key == 'PrintScreen') {
        if (navigator.clipboard) navigator.clipboard.writeText('');
        alert('Screenshots disabled!');
        if (typeof tid !== 'undefined') {
            $.ajax({
                data: {
                    'testid': tid,
                    'details': 'Prohibited Action: Screenshot (PrintScreen)',
                    'score': 1
                },
                type: "POST",
                url: "/window_event"
            });
        }
    }
});

document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key == 'p') {
        alert('This section is not allowed to print or export to PDF');
        e.cancelBubble = true;
        e.preventDefault();
        e.stopImmediatePropagation();
    }
});


// Environment Check Polling
function checkEnvironment() {
    // Only check if test_id (tid) is defined (i.e. we are in an exam)
    if (typeof tid === 'undefined' || !tid) return;

    $.ajax({
        url: '/exams/check-environment/',
        type: 'GET',
        data: { test_id: tid },
        success: function (response) {
            if (!response.is_safe) {
                console.warn("Unsafe environment detected:", response.checks);

                // Show alert
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'error',
                        title: 'Prohibited Environment Detected',
                        text: 'Virtual Machine, Debugger, or Sandbox detected! This is a violation.',
                        allowOutsideClick: false,
                        confirmButtonText: 'I Understand'
                    });
                } else {
                    alert("Prohibited Environment Detected (VM/Debugger)!");
                }
            }
        },
        error: function (err) {
            console.error("Environment check failed:", err);
        }
    });
}

// Start polling every 30 seconds (Disabled as requested)
// setInterval(checkEnvironment, 30000);
