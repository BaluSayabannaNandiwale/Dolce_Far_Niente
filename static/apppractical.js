var data = {};
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

function mySnackBar() {
  var x = document.getElementById("snackbar");
  if (x) {
    x.className = "show";
    setTimeout(function () { x.className = x.className.replace("show", ""); }, 10000);
  }
}

SEC.ready(function () {
  var SECWidget = SEC.widget("example-widget");
  // SECWidget.setCompilers(["{{test['compiler']}}"]);
  SECWidget.loadSourceCode(["{{test['compiler']}}"]);
  var beforeSendSubmission = function (data) {
    document.getElementById("inputByStudent").innerHTML = data.submissionInput;
    document.getElementById("codeByStudent").innerHTML = data.submissionSource;
    return true;
  };
  SECWidget.events.subscribe('beforeSendSubmission', beforeSendSubmission);
  var checkStatus = function (data) {
    document.getElementById("executedByStudent").innerHTML = data.statusDescription;
  };
  SECWidget.events.subscribe('checkStatus', checkStatus);
});


/*
window.onfocus = function (event) {
  var x = document.getElementById("snackbar");
  x.className = "show";
  setTimeout(function () { x.className = x.className.replace("show", ""); }, 10000);
  $.ajax({
    data: { 'testid': tid },
    type: "POST",
    url: "/window_event"
  });
};
*/

var stream = document.getElementById("stream");
var capture = document.getElementById("capture");
var cameraStream = null;
var array = null;
var values = 0;
var length = null;

function startStreaming() {

  var mediaSupport = 'mediaDevices' in navigator;
  navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia;

  if (mediaSupport && null == cameraStream) {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then(function (mediaStream) {
        cameraStream = mediaStream;
        stream.srcObject = mediaStream;
        stream.play();
        audioContext = new AudioContext();
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
      })
      .catch(function (err) {
        console.log("Unable to access camera: " + err);
      });
  }
  else {
    alert('Your browser does not support media devices.');
    return;
  }
}

function stopStreaming() {

  if (null != cameraStream) {
    var track = cameraStream.getTracks()[0];
    track.stop();
    stream.load();
    cameraStream = null;
  }
}

function captureSnapshot() {

  if (null != cameraStream) {
    var ctx = capture.getContext('2d');
    var img = new Image();
    ctx.drawImage(stream, 0, 0, capture.width, capture.height);
    img.src = capture.toDataURL("image/png");
    img.width = 340;
    var d1 = capture.toDataURL("image/png");
    var res = d1.replace("data:image/png;base64,", "");

    var average = values / length;

    console.log(average)
    console.log(Math.round(average - 40));

    if (res) {
      $.post("/video_feed", {
        data: { 'imgData': res, 'voice_db': average, 'testid': tid }
      },
        function (data) {
          // Handle Termination
          if (data.status === 'terminate') {
            const terminationMessage = "Exam Terminated: Excessive Violations";
            if (typeof Swal !== 'undefined') {
              Swal.fire({
                icon: 'error',
                title: terminationMessage,
                text: 'You have exceeded the maximum number of violations (5). Your exam is being submitted.',
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
          if (data.status === 'warning_popup') {
            try {
              const audio = new Audio('/static/assets/alert.mp3');
              audio.play().catch(e => { });
            } catch (e) { }

            if (typeof Swal !== 'undefined') {
              if (!Swal.isVisible()) {
                Swal.fire({
                  icon: 'warning',
                  title: 'Attention Required',
                  html: data.message,
                  showConfirmButton: true,
                  confirmButtonText: 'I Understand',
                  allowOutsideClick: false,
                  backdrop: `rgba(239, 68, 68, 0.15)`
                });
              }
            } else {
              console.warn("DETECTION ALERT:", data.alerts);
            }
          }
          // Legacy Warning Toast
          else if (data.warning) {
            try {
              const audio = new Audio('/static/assets/alert.mp3');
              audio.play().catch(e => { });
            } catch (e) { }

            if (typeof Swal !== 'undefined') {
              const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
              });
              Toast.fire({
                icon: 'error',
                title: data.warning
              });
            } else {
              console.warn("VIOLATION:", data.warning);
            }
          }
        });
    }

  }
  setTimeout(captureSnapshot, 1000);

}

$(document).ready(function () {
  // Configure global AJAX to include CSRF token
  $.ajaxSetup({
    headers: {
      'X-CSRFToken': getCsrfToken()
    }
  });

  var url = window.location.href;
  var list = url.split('/');
  
  var timeElem = $('#time');
  var timeText = timeElem.text().trim();
  console.log('Practical - Raw time element text:', timeText);
  
  var time = parseInt(timeText);
  console.log('Practical - Parsed time (seconds):', time);
  
  if (!isNaN(time) && time > 0) {
    console.log('Practical - Starting timer with', time, 'seconds');
    
    // Initialize timer display with formatted time
    var hours = parseInt(time / 3600, 10);
    var minutes = parseInt((time % 3600) / 60, 10);
    var seconds = parseInt(time % 60, 10);
    hours = hours < 10 ? "0" + hours : hours;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    timeElem.text(hours + ":" + minutes + ":" + seconds);
    
    startTimer(time, timeElem);
    sendTime();
    flag_time = true;
  } else {
    console.warn('Practical - Invalid time value:', timeText);
    timeElem.text('00:00:00');
  }
})

var flag_time = true;
var timerInterval = null;  // Store timer interval globally for cleanup

function startTimer(duration, display) {
  var timer = duration, hours, minutes, seconds;
  
  // Log timer start for debugging
  console.log('Practical Timer started with duration:', duration, 'seconds');

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
    
    var timeString = hours + ":" + minutes + ":" + seconds;
    display.text(timeString);
    display.html(timeString);
    
    // Log every 30 seconds to avoid console spam
    if (timer % 30 === 0 || timer < 10) {
      console.log('⏱️ Practical Timer:', timeString, '(remaining:', timer, 's)');
    }
    
    if (--timer < 0) {
      console.log('⏰ Practical Timer expired - auto-submitting exam');
      clearInterval(timerInterval);
      timerInterval = null;
      flag_time = false;
      finish_submitformexam();
    }
  }, 1000);
  
  console.log('✓ Practical timer interval started successfully');
}

function sendTime() {
  var sendTimeInterval = setInterval(function () {
    if (flag_time == false) {
      console.log('flag_time is false, stopping sendTime interval');
      clearInterval(sendTimeInterval);
      return;
    }
    
    try {
      var timeElem = $('#time');
      if (!timeElem || timeElem.length === 0) {
        console.warn('Time element not found');
        clearInterval(sendTimeInterval);
        return;
      }
      
      var time = timeElem.text().trim();
      if (!time) {
        console.warn('Time text is empty');
        return;
      }
      
      var parts = time.split(':');
      var hh = parseInt(parts[0]) || 0;
      var mm = parseInt(parts[1]) || 0;
      var ss = parseInt(parts[2]) || 0;
      var seconds = hh * 3600 + mm * 60 + ss;
      
      $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/test_update_time",
        data: { time: seconds, testid: tid },
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
function submitformexam() {
  document.forms["prac"].submit();
}


window.addEventListener('selectstart', function (e) { e.preventDefault(); });
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
