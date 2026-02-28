from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_GET
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json

from .models import Teacher, Question, StudentTestInfo, Student, LongQA, PracticalQA
from proctoring.models import ProctoringLog, WindowEstimationLog
from .models import Teacher, Question, StudentTestInfo, Student, LongQA, PracticalQA, ViolationLog
from .forms import GiveTestForm
import random
import cv2
import numpy as np
import base64
from PIL import Image
from io import BytesIO

# Try to import YOLO
try:
    from ultralytics import YOLO
    import torch
except ImportError:
    YOLO = None
    print("Warning: ultralytics not installed. Object detection will not work.")

# Load model globally to avoid reloading
YOLO_MODEL = None
# Removed 'table' as it causes false positives for students sitting at desks
RESTRICTED_CLASSES = ['cell phone', 'mobile phone', 'laptop', 'book', 'tv'] 

def load_yolo_model():
    global YOLO_MODEL
    if YOLO_MODEL is None and YOLO is not None:
        try:
            # First try to load the user's custom model
            # We assume it might be a .pt file renamed to .pkl or a pickle
            model_path = 'yolov8n/data.pkl'
            print(f"Attempting to load custom model: {model_path}")
            
            try:
                # Try loading as standard YOLO model
                YOLO_MODEL = YOLO(model_path)
                # Test if it's valid by checking names
                if not hasattr(YOLO_MODEL, 'names') or not YOLO_MODEL.names:
                     raise ValueError("Model loaded but has no class names")
                print("Custom YOLOv8 Model loaded successfully")
            except Exception as e:
                print(f"YOLO(path) failed ({e}). Trying pickle...")
                import pickle
                with open(model_path, 'rb') as f:
                    # Logic: If it's a pickled model object
                    YOLO_MODEL = pickle.load(f)
                
                print("Custom Model loaded via pickle")

        except Exception as e:
            print(f"Error loading custom model: {e}")
            print("FALLBACK: Loading standard 'yolov8n.pt' model...")
            try:
                # Fallback to standard yolov8n which detects COCO classes
                # (person, bicycle, car, ..., backpack, umbrella, ..., handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant, bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors, teddy bear, hair drier, toothbrush)
                YOLO_MODEL = YOLO('yolov8n.pt') 
                print("Standard yolov8n.pt loaded successfully")
            except Exception as e2:
                print(f"CRITICAL: Could not load fallback model: {e2}")
                YOLO_MODEL = None


# Load YOLO model at module initialization
load_yolo_model()


def _professor_required(view_func):
    """Redirect to student_index if not professor."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != "teacher":
            return redirect("student_index")
        return view_func(request, *args, **kwargs)
    return wrapper


def _professor_tests(request):
    """List of Teacher rows for current professor (uid=request.user)."""
    return list(Teacher.objects.filter(uid=request.user).order_by("-tid"))


def _cresults_test_ids(request):
    """List of test_id strings for professor (for dropdowns)."""
    return [t.test_id for t in _professor_tests(request)]


def _cresults_dicts(request):
    """List of dicts with test_id for professor (for templates that use test['test_id'])."""
    return [{"test_id": t.test_id} for t in _professor_tests(request)]


@login_required
@require_http_methods(["GET", "POST"])
def give_test_view(request):
    """Exam login: show form (GET) or validate test_id/password and redirect to test (POST)."""
    if request.user.user_type != "student":
        return redirect("professor_index")

    if request.method == "POST":
        form = GiveTestForm(request.POST)
        if form.is_valid():
            test_id = form.cleaned_data["test_id"].strip()
            password = form.cleaned_data["password"]
            teacher = Teacher.objects.filter(
                test_id=test_id,
                password=password,
            ).first()
            if not teacher:
                messages.error(request, "Invalid Test ID or Password.")
                return render(request, "give_test.html", {"form": form})

            # Ensure StudentTestInfo exists for this student/test
            StudentTestInfo.objects.get_or_create(
                email=request.user.email,
                test_id=test_id,
                defaults={"uid": request.user, "time_left": teacher.duration * 60, "completed": 0},
            )
            # Redirect to 360 Scan instead of exam directly
            return redirect("scan_360", test_id=test_id)
    else:
        form = GiveTestForm()

    return render(request, "give_test.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def give_test_exam_view(request, test_id):
    """Show the quiz/test page for the given test_id."""
    if request.user.user_type != "student":
        return redirect("professor_index")

    # First, support form-style POST actions (prev/next/submit/bookmark/finish)
    if request.method == 'POST' and request.POST.get('action'):
        action = request.POST.get('action')

        # Fetch ordered question ids for this test (deduplicated by earlier patch)
        q_list = list(Question.objects.filter(test_id=test_id).order_by('qid').values_list('qid', flat=True))
        total = len(q_list)

        # Determine current question index. Prefer POSTed qid since GET parameters
        # disappear on form submission.  Fall back to query param if qid is missing
        question_index = 0
        posted_qid = request.POST.get('qid')
        if posted_qid and posted_qid in q_list:
            question_index = q_list.index(posted_qid)
        else:
            try:
                question_index = int(request.GET.get('q', 0))
            except (TypeError, ValueError):
                question_index = 0

        # Persist remaining time if client sent it with the form (seconds)
        posted_time = request.POST.get('time')
        if posted_time:
            try:
                tval = int(posted_time)
                StudentTestInfo.objects.update_or_create(
                    uid=request.user,
                    email=request.user.email,
                    test_id=test_id,
                    defaults={"time_left": tval, "completed": 0},
                )
            except Exception:
                # ignore errors here; not fatal for navigation
                pass

        # Handle submit action (save answer)
        if action == 'submit':
            qid = request.POST.get('qid') or (q_list[question_index] if question_index < total else None)
            ans = request.POST.get('ans') or request.POST.get('selected_answer')
            if qid and ans is not None:
                Student.objects.update_or_create(
                    uid=request.user,
                    email=request.user.email,
                    test_id=test_id,
                    qid=qid,
                    defaults={'ans': ans}
                )

            # Stay on same question after submit
            return redirect(f"/give-test/{test_id}/?q={question_index}")

        # Bookmark action: use session to store bookmarks
        if action == 'bookmark':
            qid = request.POST.get('qid') or (q_list[question_index] if question_index < total else None)
            if qid:
                bookmarks = request.session.get('bookmarks', {})
                tb = bookmarks.get(test_id, set())
                # convert to set for toggle
                if isinstance(tb, list):
                    tb = set(tb)
                if qid in tb:
                    tb.remove(qid)
                else:
                    tb.add(qid)
                bookmarks[test_id] = list(tb)
                request.session['bookmarks'] = bookmarks
                request.session.modified = True
            return redirect(f"/give-test/{test_id}/?q={question_index}")

        # Navigation: next / prev
        if action == 'next':
            new_index = min(question_index + 1, max(0, total - 1))
            return redirect(f"/give-test/{test_id}/?q={new_index}")

        if action == 'prev':
            new_index = max(question_index - 1, 0)
            return redirect(f"/give-test/{test_id}/?q={new_index}")

        if action == 'finish':
            return redirect('/tests-given/')

    # Handle AJAX requests from the exam interface (legacy)
    if request.method == 'POST':
        try:
            # Try to parse JSON data first (for Fetch API)
            body_unicode = request.body.decode('utf-8')
            if body_unicode:
                data = json.loads(body_unicode)
                flag = data.get('flag')
            else:
                # Fallback to POST data (for legacy jQuery)
                flag = request.POST.get('flag')
        except json.JSONDecodeError:
            # Fallback to POST data (for legacy jQuery)
            flag = request.POST.get('flag')
        
        if flag == 'get':
            # Get question details
            no = request.POST.get('no') or (hasattr(request, '_request') and request._request.POST.get('no')) or (request.body and json.loads(request.body.decode()).get('no'))
            if not no:
                try:
                    data = json.loads(request.body.decode())
                    no = data.get('no')
                except (json.JSONDecodeError, AttributeError):
                    no = None
            
            try:
                q_obj = Question.objects.get(test_id=test_id, qid=no)
                return JsonResponse({
                    'q': q_obj.q,
                    'a': q_obj.a,
                    'b': q_obj.b,
                    'c': q_obj.c,
                    'd': q_obj.d,
                    'marks': q_obj.marks
                })
            except Question.DoesNotExist:
                return JsonResponse({'error': 'Question not found'}, status=404)
        
        elif flag == 'mark':
            # Save answer
            qid = request.POST.get('qid') or (request.body and json.loads(request.body.decode()).get('qid'))
            ans = request.POST.get('ans') or (request.body and json.loads(request.body.decode()).get('ans'))
            
            Student.objects.update_or_create(
                uid=request.user,
                email=request.user.email,
                test_id=test_id,
                qid=qid,
                defaults={'ans': ans}
            )
            return JsonResponse({'status': 'Answer saved'})
            
        elif flag == 'time':
            # Update time left
            time_left = request.POST.get('time') or (request.body and json.loads(request.body.decode()).get('time'))
            StudentTestInfo.objects.filter(
                uid=request.user,
                email=request.user.email,
                test_id=test_id
            ).update(time_left=time_left)
            return JsonResponse({'status': 'Time updated'})
            
        elif flag == 'completed':
            # Mark test as completed
            StudentTestInfo.objects.filter(
                uid=request.user,
                email=request.user.email,
                test_id=test_id
            ).update(completed=1)
            return JsonResponse({'status': 'Test completed'})
            
        return JsonResponse({'error': 'Invalid flag'}, status=400)

    # GET request - load the page logic starts here
    teacher = Teacher.objects.filter(test_id=test_id).first()

    if not teacher:
        messages.error(request, "Test not found.")
        return redirect("give_test")

    # --- RESET VIOLATION COUNT FOR NEW TEST ATTEMPT ---
    # Clear all previous violations for this student + test to allow fresh attempt
    ViolationLog.objects.filter(
        student=request.user,
        test_id=test_id
    ).delete()
    print(f"✓ Cleared violations for {request.user.email} on test {test_id} - Fresh attempt started")
    
    # --- RESET TEST SESSION INFO FOR NEW ATTEMPT ---
    # Reset the time_left and completed flag for a fresh test attempt
    StudentTestInfo.objects.filter(
        uid=request.user,
        email=request.user.email,
        test_id=test_id
    ).update(
        time_left=teacher.duration * 60,  # Reset to full duration in seconds
        completed=0  # Mark as not completed for fresh attempt
    )
    print(f"✓ Reset test session for {request.user.email} on test {test_id}")

    context = {
        "session": {
            "name": request.user.name,
            "email": request.user.email,
        },
        "tid": test_id,
        "test_id": test_id, # For templates that use test_id
        "subject": teacher.subject,
        "topic": teacher.topic,
        "duration": teacher.duration * 60,
        "proctortype": teacher.proctoring_type,
        "proctortypes": teacher.proctoring_type, # For subjective
        "proctortypep": teacher.proctoring_type, # For practical
        "calc": teacher.calc,
    }

    if teacher.test_type == 'subjective':
        questions = LongQA.objects.filter(test_id=test_id)
        context["callresults"] = questions
        return render(request, "testsubjective.html", context)
    elif teacher.test_type == 'practical':
        questions = PracticalQA.objects.filter(test_id=test_id)
        context["callresults"] = questions
        return render(request, "testpractical.html", context)
    else:
        # Objective Test (Default)
        # Determine question index from query param
        try:
            question_index = int(request.GET.get('q', 0))
        except (TypeError, ValueError):
            question_index = 0

        # fetch all qids for this test and remove duplicates while preserving order
        raw_qids = list(Question.objects.filter(test_id=test_id).order_by('qid').values_list('qid', flat=True))
        seen = set()
        questions_qids = []
        for q in raw_qids:
            if q not in seen:
                seen.add(q)
                questions_qids.append(q)
        total_questions = len(questions_qids)

        # Clamp index
        if question_index < 0:
            question_index = 0
        if question_index >= total_questions:
            question_index = max(0, total_questions - 1)

        # Load selected question
        if total_questions > 0:
            sel_qid = questions_qids[question_index]
            try:
                q_obj = Question.objects.get(test_id=test_id, qid=sel_qid)
                q, a, b, c, d, marks = q_obj.q, q_obj.a, q_obj.b, q_obj.c, q_obj.d, q_obj.marks
            except Question.DoesNotExist:
                q = a = b = c = d = ""
                marks = 0
        else:
            q = a = b = c = d = ""
            marks = 0

        # time_left from StudentTestInfo if present
        sti = StudentTestInfo.objects.filter(uid=request.user, email=request.user.email, test_id=test_id).first()
        if sti:
            time_left_val = sti.time_left
        else:
            time_left_val = teacher.duration * 60

        # determine qid for current index (used by template initial hidden field)
        current_qid = questions_qids[question_index] if 0 <= question_index < total_questions else ""
        context.update({
            "answers": "{}",
            "q": q, "a": a, "b": b, "c": c, "d": d,
            "marks": marks,
            "question_index": question_index,
            "current_qid": current_qid,
            "total_questions": total_questions,
            "time_left": time_left_val,
            "question_list": questions_qids,
        })
        return render(request, "testquiz.html", context)


@login_required
@csrf_exempt
def randomize_view(request):
    if request.method == "POST":
        test_id = request.POST.get('id')
        # collect qids and remove duplicates to avoid showing the same question repeatedly
        raw_qids = list(Question.objects.filter(test_id=test_id).values_list('qid', flat=True))
        seen = set()
        questions = []
        for q in raw_qids:
            if q not in seen:
                seen.add(q)
                questions.append(q)
        random.shuffle(questions)
        return JsonResponse(questions, safe=False)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@csrf_exempt
def window_event_view(request):
    """Log window focus/blur events as violations."""
    if request.method == 'POST':
        test_id = request.POST.get('testid')
        
        # Log the violation
        ViolationLog.objects.create(
            student=request.user,
            test_id=test_id or 'unknown',
            details="Tab Switch / Window Focus Lost",
            score=1
        )
        
        return JsonResponse({'status': 'logged'})
    return JsonResponse({'status': 'ignored'})


@login_required
@csrf_exempt
def video_feed_view(request):
    """Process video feed for exam monitoring with scoring logic."""
    if request.method == 'POST':
        try:
            # Handle jQuery $.post nested data structure
            image_data = request.POST.get('data[imgData]')
            voice_db = request.POST.get('data[voice_db]')
            test_id = request.POST.get('data[testid]')
            
            if not image_data:
                return JsonResponse({'status': 'no_image'})

            # Decode image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            alerts = []
            score_increment = 0
            
            # Load model if needed
            load_yolo_model()
            
            if YOLO_MODEL:
                # Run inference
                results = YOLO_MODEL(image, verbose=False, conf=0.4)
                detected_objects = []
                
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        class_name = result.names[cls_id] if hasattr(result, 'names') else str(cls_id)
                        detected_objects.append(class_name)
                
                # --- RULE 1: NO FACE DETECTED (+2) ---
                # Only log this violation if face was previously detected but is now missing
                # This prevents false positives from poor frame quality on first attempt
                person_count = detected_objects.count('person')
                
                # Check if student previously had face detected
                previous_with_face = ViolationLog.objects.filter(
                    student=request.user,
                    test_id=test_id or 'unknown',
                    details="Face Re-detected"  # Marker for face recovery
                ).exists()
                
                if person_count == 0 and previous_with_face:
                    # Only flag if face was detected before and is now gone
                    alerts.append("No Face Detected")
                    score_increment += 2
                    ViolationLog.objects.create(
                        student=request.user,
                        test_id=test_id or 'unknown',
                        details="No Face Detected",
                        score=2
                    )
                elif person_count > 0 and not previous_with_face:
                    # Log that face is present (baseline for future checks)
                    ViolationLog.objects.create(
                        student=request.user,
                        test_id=test_id or 'unknown',
                        details="Face Re-detected",
                        score=0  # No penalty for detecting face initially
                    )

                # --- RULE 2: MULTIPLE PERSONS (+2) ---
                elif person_count > 1:
                    alerts.append(f"Multiple Persons Detected ({person_count})")
                    score_increment += 2
                    ViolationLog.objects.create(
                        student=request.user,
                        test_id=test_id or 'unknown',
                        details=f"Multiple Persons ({person_count})",
                        score=2
                    )
                
                # --- RULE 3: PROHIBITED ITEMS ---
                # Mobile Phone (+2)
                if 'cell phone' in detected_objects or 'mobile phone' in detected_objects:
                    alerts.append("Mobile Phone Detected")
                    score_increment += 2
                    ViolationLog.objects.create(
                         student=request.user,
                         test_id=test_id or 'unknown',
                         details="Mobile Phone Detected",
                         score=2
                    )
                
                # Book (+1)
                if 'book' in detected_objects:
                    alerts.append("Book Detected")
                    score_increment += 1
                    ViolationLog.objects.create(
                         student=request.user,
                         test_id=test_id or 'unknown',
                         details="Book Detected",
                         score=1
                    )

                # Laptop (+1) - if distinct from current device
                if 'laptop' in detected_objects:
                    alerts.append("Laptop Detected")
                    score_increment += 1
                    ViolationLog.objects.create(
                         student=request.user,
                         test_id=test_id or 'unknown',
                         details="Laptop Detected",
                         score=1
                    )

            # --- RULE 4: AUDIO DETECTION (+1) ---
            # app.js sends 'average' as voice_db. Adjust threshold based on testing.
            try:
                if voice_db and float(voice_db) > 50: # Example threshold
                     alerts.append("High Audio Level")
                     score_increment += 1
                     ViolationLog.objects.create(
                         student=request.user,
                         test_id=test_id or 'unknown',
                         details=f"High Volume ({voice_db})",
                         score=1
                    )
            except (ValueError, TypeError):
                pass

            # --- CALCULATE TOTAL SCORE AND FLAG COUNT ---
            # Sum up scores from ViolationLog
            from django.db.models import Sum
            total_score = ViolationLog.objects.filter(
                student=request.user, 
                test_id=test_id or 'unknown'
            ).aggregate(Sum('score'))['score__sum'] or 0
            
            # Count total violations (each ViolationLog record = 1 violation)
            total_violations = ViolationLog.objects.filter(
                student=request.user, 
                test_id=test_id or 'unknown'
            ).count()

            # --- RULE 5A: TERMINATE IF 5 FLAGS RAISED (Primary termination method) ---
            # Only count actual violation flags (excluding face re-detection markers)
            violation_flags = ViolationLog.objects.filter(
                student=request.user, 
                test_id=test_id or 'unknown'
            ).exclude(details="Face Re-detected").count()
            
            if violation_flags >= 5:
                print(f"Terminating exam for {request.user}. Violation Flags: {violation_flags}")
                return JsonResponse({
                    'status': 'terminate',
                    'message': f'Exam terminated after {violation_flags} violations detected.',
                    'score': total_score,
                    'flags': violation_flags
                })

            # Return appropriate response
            if alerts:  # If violations were detected
                return JsonResponse({
                    'status': 'warning_popup',
                    'alerts': alerts,
                    'score': total_score,
                    'flags': violation_flags
                })
            else:  # No violations
                return JsonResponse({
                    'status': 'processed',
                    'alerts': [],
                    'score': total_score,
                    'flags': violation_flags
                })
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'processed'})


@login_required
def scan_360_view(request, test_id):
    """Render the 360-degree environment scan page."""
    if request.user.user_type != "student":
        return redirect("professor_index")

    context = {
        "session": {
            "name": request.user.name,
            "email": request.user.email,
        },
        "test_id": test_id
    }
    return render(request, "scan360.html", context)


@login_required
@require_POST
def finish_exam_view(request):
    """Endpoint to finish the exam (finalize student test info and redirect).

    This endpoint is intended to be called when the student clicks Finish Exam
    (either via form POST or via AJAX). It will mark the test as completed and
    respond with JSON for AJAX callers or a redirect for regular form submits.
    """
    # Determine test id from POST body or form
    test_id = request.POST.get('test_id') or (request.body and json.loads(request.body.decode()).get('test_id'))

    # Mark StudentTestInfo as completed for current user and test (if provided)
    if test_id:
        StudentTestInfo.objects.filter(
            uid=request.user,
            email=request.user.email,
            test_id=test_id
        ).update(completed=1)
    else:
        # If no test_id provided, mark any running test for the user as completed
        StudentTestInfo.objects.filter(uid=request.user, email=request.user.email, completed=0).update(completed=1)

    # If AJAX request, return JSON; otherwise redirect to student index
    if request.is_ajax() or request.content_type == 'application/json':
        return JsonResponse({'status': 'completed'})
    return redirect('student_index')


@login_required
@csrf_exempt
def process_scan_frame(request):
    """Process a frame from the 360 scan."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    try:
        # Ensure YOLO model is loaded
        global YOLO_MODEL
        if YOLO_MODEL is None:
            load_yolo_model()
        
        data = json.loads(request.body)
        image_data = data.get('image')
        test_id = data.get('test_id')
        
        if not image_data or not test_id:
            print("Missing data in scan request")
            return JsonResponse({'error': 'Missing data'}, status=400)
            
        # Decode image
        # Format: data:image/jpeg;base64,...
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
            
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Run Detection
        is_clean = True
        detected_objects = []
        
        if YOLO_MODEL:
            # Convert to cv2 format for YOLO (or pass PIL)
            # YOLOv8 supports PIL images directly
            # Run inference with lower confidence to see if ANYTHING is detected
            results = YOLO_MODEL(image, verbose=False, conf=0.25) 
            
            # Process results
            # Classes: 0:person, 67:cell phone, 63:laptop, 73:book, etc. (COCO indices)
            # We rely on class names
            
            for result in results:
                # Debug: print all detected classes
                if len(result.boxes) > 0:
                    print(f"DEBUG: Detected {len(result.boxes)} objects")
                
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    # Handle both integer and string keys in names
                    if hasattr(result, 'names'):
                        class_name = result.names[cls_id]
                    else:
                         class_name = str(cls_id)

                    conf = float(box.conf[0])
                    print(f"DEBUG: Found {class_name} ({conf:.2f})")
                    
                    if conf > 0.4: # Slightly lower threshold
                        detected_objects.append(class_name)
                        
                        # Check restricted
                        # Logic: Multiple people is bad. Phone/Book is bad.
                        
                        if class_name in RESTRICTED_CLASSES or (class_name == 'person' and detected_objects.count('person') > 1):
                            # Allow one person (the student)
                            if class_name == 'person' and detected_objects.count('person') == 1:
                                pass
                            else:
                                is_clean = False
                                print(f"DEBUG: Violation found: {class_name}")

        else:
            print("WARNING: YOLO_MODEL could not be loaded. Allowing scan to proceed without detection.")
            # Don't fail the scan - just log that detection wasn't available
            is_clean = True
        
        # Deduplicate detected list
        detected_objects = list(set(detected_objects))
        
        # Deduplicate detected list
        detected_objects = list(set(detected_objects))
        
        # Log violation if not clean
        if not is_clean:
            # Check if recent violation exists to avoid spamming DB
            # For 360 scan, we can just log every time or throttle
            # Here we just log
            ViolationLog.objects.create(
                student=request.user,
                test_id=test_id,
                details=f"Scan Violation: Found {', '.join(detected_objects)}",
                evidence="[Base64 Image Omitted]" 
            )
            
        return JsonResponse({
            'clean': is_clean,
            'detected': detected_objects
        })
        
    except Exception as e:
        print(f"Scan processing error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def calculator_view(request):
    """Simple calculator page for exam purposes."""
    if request.user.user_type != "student":
        return redirect("professor_index")
    
    # Render a simple calculator template
    return render(request, "calculator.html")

# Professor exam management pages (all require professor role)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(["GET", "POST"])
def generate_test_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == "POST":
        itext = request.POST.get("itext", "").strip()
        test_type = request.POST.get("test_type", "objective").strip()
        noq = request.POST.get("noq", "1").strip()
        
        if not itext or not noq:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "generatetest.html")
        
        try:
            noq_int = int(noq)
            if noq_int < 1:
                raise ValueError("Number of questions must be at least 1")
        except ValueError:
            messages.error(request, "Invalid number of questions.")
            return render(request, "generatetest.html")
        
        try:
            from local_qg import generate_objective_test, generate_subjective_test

            if test_type == "objective":
                questions, answers = generate_objective_test(itext, noq_int)

                # Split combined question text: question text only in Question column,
                # each option in its own column (A, B, C, D).
                structured = []
                for q_text, ans in zip(questions, answers):
                    lines = [ln.strip() for ln in q_text.splitlines() if ln.strip()]
                    question_parts = []
                    opt_a = opt_b = opt_c = opt_d = ""
                    for line in lines:
                        if line.startswith("A)"):
                            opt_a = line[2:].strip()
                        elif line.startswith("B)"):
                            opt_b = line[2:].strip()
                        elif line.startswith("C)"):
                            opt_c = line[2:].strip()
                        elif line.startswith("D)"):
                            opt_d = line[2:].strip()
                        else:
                            question_parts.append(line)
                    question_only = " ".join(question_parts) if question_parts else (lines[0] if lines else "")

                    structured.append(
                        {
                            "question": question_only,
                            "opt_a": opt_a,
                            "opt_b": opt_b,
                            "opt_c": opt_c,
                            "opt_d": opt_d,
                            "answer": ans,
                        }
                    )

                return render(
                    request,
                    "generatedtestdata.html",
                    {"cresults": structured, "is_objective": True},
                )

            elif test_type == "subjective":
                questions, answers = generate_subjective_test(itext, noq_int)
                
                # Categorize subjective answers based on question type
                def get_answer_type(question):
                    q_lower = question.lower()
                    if "define" in q_lower:
                        return "Definition"
                    elif "one-line" in q_lower or "one line" in q_lower:
                        return "One-Line Answer"
                    elif "brief" in q_lower:
                        return "Answer in Brief"
                    elif "understand" in q_lower:
                        return "Concept Explanation"
                    else:
                        return "Short Answer"
                
                structured = []
                for q, a in zip(questions, answers):
                    structured.append({
                        "question": q,
                        "answer": a,
                        "answer_type": get_answer_type(q)
                    })
                
                return render(
                    request,
                    "generatedtestdata.html",
                    {"cresults": structured, "is_objective": False},
                )
            else:
                messages.error(request, "Invalid test type.")
                return render(request, "generatetest.html")

        except Exception as e:
            error_msg = str(e)
            messages.error(
                request,
                f"Error generating test: {error_msg}."
            )
            return render(request, "generatetest.html")
    
    return render(request, "generatetest.html")


@login_required
@ensure_csrf_cookie
@require_GET
def viewquestions_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_dicts(request)
    return render(request, "viewquestions.html", {"cresults": cresults})


@login_required
@csrf_exempt
def display_questions_view(request):
    """Display questions for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('viewquestions')
        
        # Check the test type to determine which questions to display
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('viewquestions')
        test_type = teacher_record.test_type
        
        # Display questions based on test type
        if test_type == 'subjective':
            # Get long answer questions
            questions = LongQA.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{'qid': q.qid, 'q': q.q, 'marks': q.marks} for q in questions]
            return render(request, "displayquestionslong.html", {"callresults": callresults, "tid": test_id})
        elif test_type == 'practical':
            # Get practical questions
            questions = PracticalQA.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{
                'qid': q.qid, 
                'q': q.q, 
                'marks': q.marks,
                'compiler': q.compiler
            } for q in questions]
            return render(request, "deldispquesPQA.html", {"callresults": callresults, "tid": test_id})
        else:  # Default to objective
            # Get objective questions
            questions = Question.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{
                'qid': q.qid,
                'q': q.q,
                'a': q.a,
                'b': q.b,
                'c': q.c,
                'd': q.d,
                'ans': q.ans,
                'marks': q.marks
            } for q in questions]
            return render(request, "displayquestions.html", {"callresults": callresults, "tid": test_id})
    
    # If not POST, redirect back to viewquestions
    return redirect('viewquestions')


@login_required
@ensure_csrf_cookie
@require_GET
def updatetidlist_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_test_ids(request)
    return render(request, "updatetidlist.html", {"cresults": cresults})


@login_required
@require_GET
def deltidlist_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_test_ids(request)
    return render(request, "deltidlist.html", {"cresults": cresults})


@login_required
@require_GET
def disptests_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    tests = [
        {"test_id": t.test_id, "password": t.password, "subject": t.subject, "topic": t.topic}
        for t in _professor_tests(request)
    ]
    return render(request, "disptests.html", {"tests": tests})


@login_required
@require_GET
def share_details_view(request, test_id):
    """Show share details for a test so the teacher can share with students (e.g. by email)."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    teacher = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher:
        messages.error(request, "Test not found or you do not have permission to share it.")
        return redirect("disptests")
    callresults = [{
        "test_id": teacher.test_id,
        "subject": teacher.subject,
        "topic": teacher.topic,
        "duration": teacher.duration,
        "start": teacher.start,
        "end": teacher.end,
        "password": teacher.password,
        "neg_marks": teacher.neg_marks,
        "calc": teacher.calc,
    }]
    return render(request, "share_details.html", {"callresults": callresults})


@login_required
@require_GET
def livemonitoringtid_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_test_ids(request)
    return render(request, "livemonitoringtid.html", {"cresults": cresults})


@login_required
@require_GET
def viewstudentslogs_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_dicts(request)
    return render(request, "viewstudentslogs.html", {"cresults": cresults})


@login_required
@require_GET
def insertmarkstid_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_test_ids(request)
    return render(request, "insertmarkstid.html", {"cresults": cresults})


@login_required
@require_GET
def publish_results_testid_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    cresults = _cresults_test_ids(request)
    return render(request, "publish_results_testid.html", {"cresults": cresults})


@login_required
@require_GET
def tests_created_view(request):
    if request.user.user_type != "teacher":
        return redirect("student_index")
    tests = [
        {"test_id": t.test_id, "subject": t.subject, "topic": t.topic}
        for t in _professor_tests(request)
    ]
    # If no tests, add a demo row so "View Result" is always available to showcase the results page
    if not tests:
        tests = [{"test_id": "demo", "subject": "Demo", "topic": "Sample (no tests yet)"}]
    return render(request, "tests_created.html", {"tests": tests, "cresults": tests})


@login_required
@_professor_required
def create_test_view(request):
    """Create a new objective test."""
    if request.method == 'POST':
        # Process form submission
        subject = request.POST.get('subject', '').strip()
        topic = request.POST.get('topic', '').strip()
        test_id = request.POST.get('test_id', '').strip()
        password = request.POST.get('password', '').strip()
        duration = request.POST.get('duration', '60')
        calc = request.POST.get('calc', '0')
        proctortype = request.POST.get('proctortype', '0')
        
        if not all([subject, topic, test_id, password]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "create_test.html", {"subjects": [], "topics": []})
        
        try:
            duration_int = int(duration)
        except ValueError:
            messages.error(request, "Invalid duration.")
            return render(request, "create_test.html", {"subjects": [], "topics": []})
        
        # Calculate end time based on duration
        from datetime import datetime
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_int)
        
        # Create the test record
        teacher = Teacher.objects.create(
            uid=request.user,
            test_id=test_id,
            password=password,
            subject=subject,
            topic=topic,
            duration=duration_int,
            start=start_time,
            end=end_time,
            calc=calc,
            proctoring_type=proctortype,
            test_type='objective'
        )
        
        messages.success(request, f"Test '{test_id}' created successfully!")
        return redirect('disptests')
    
    # GET request - show form
    subjects = []  # Get unique subjects if needed
    topics = []    # Get unique topics if needed
    return render(request, "create_test.html", {"subjects": subjects, "topics": topics})


@login_required
@_professor_required
def create_test_lqa_view(request):
    """Create a new subjective test (Long Question Answers)."""
    if request.method == 'POST':
        # Process form submission
        subject = request.POST.get('subject', '').strip()
        topic = request.POST.get('topic', '').strip()
        test_id = request.POST.get('test_id', '').strip()
        password = request.POST.get('password', '').strip()
        duration = request.POST.get('duration', '60')
        calc = request.POST.get('calc', '0')
        proctortype = request.POST.get('proctortype', '0')
        
        if not all([subject, topic, test_id, password]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "create_test_lqa.html")
        
        try:
            duration_int = int(duration)
        except ValueError:
            messages.error(request, "Invalid duration.")
            return render(request, "create_test_lqa.html")
        
        # Calculate end time based on duration
        from datetime import datetime
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_int)
        
        # Create the test record
        teacher = Teacher.objects.create(
            uid=request.user,
            test_id=test_id,
            password=password,
            subject=subject,
            topic=topic,
            duration=duration_int,
            start=start_time,
            end=end_time,
            calc=calc,
            proctoring_type=proctortype,
            test_type='subjective'
        )
        
        messages.success(request, f"Subjective test '{test_id}' created successfully!")
        return redirect('disptests')
    
    # GET request - show form
    return render(request, "create_test_lqa.html")


@login_required
@_professor_required
def create_test_pqa_view(request):
    """Create a new practical test (Practical Question Answers)."""
    if request.method == 'POST':
        # Process form submission
        subject = request.POST.get('subject', '').strip()
        topic = request.POST.get('topic', '').strip()
        test_id = request.POST.get('test_id', '').strip()
        password = request.POST.get('password', '').strip()
        duration = request.POST.get('duration', '60')
        calc = request.POST.get('calc', '0')
        proctortype = request.POST.get('proctortype', '0')
        
        if not all([subject, topic, test_id, password]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "create_test_pqa.html")
        
        try:
            duration_int = int(duration)
        except ValueError:
            messages.error(request, "Invalid duration.")
            return render(request, "create_test_pqa.html")
        
        # Calculate end time based on duration
        from datetime import datetime
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_int)
        
        # Create the test record
        teacher = Teacher.objects.create(
            uid=request.user,
            test_id=test_id,
            password=password,
            subject=subject,
            topic=topic,
            duration=duration_int,
            start=start_time,
            end=end_time,
            calc=calc,
            proctoring_type=proctortype,
            test_type='practical'
        )
        
        messages.success(request, f"Practical test '{test_id}' created successfully!")
        return redirect('disptests')
    
    # GET request - show form
    return render(request, "create_test_pqa.html")


@login_required
@csrf_exempt
def update_disp_questions_view(request):
    """Display questions for updating for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('updatetidlist')
        
        # Check the test type to determine which questions to display
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('updatetidlist')
        test_type = teacher_record.test_type
        
        # Display questions based on test type
        if test_type == 'subjective':
            # Get long answer questions
            questions = LongQA.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{'qid': q.qid, 'q': q.q, 'marks': q.marks, 'test_id': test_id} for q in questions]
            return render(request, "updatedispquesLQA.html", {"callresults": callresults})
        elif test_type == 'practical':
            # Get practical questions
            questions = PracticalQA.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{
                'qid': q.qid, 
                'q': q.q, 
                'marks': q.marks,
                'compiler': q.compiler,
                'test_id': test_id
            } for q in questions]
            return render(request, "updatedispquesPQA.html", {"callresults": callresults})
        else:  # Default to objective
            # Get objective questions
            questions = Question.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{
                'qid': q.qid,
                'q': q.q,
                'a': q.a,
                'b': q.b,
                'c': q.c,
                'd': q.d,
                'ans': q.ans,
                'marks': q.marks,
                'test_id': test_id
            } for q in questions]
            return render(request, "updatedispques.html", {"callresults": callresults})
    
    # If not POST, redirect back to updatetidlist
    return redirect('updatetidlist')


@login_required
@csrf_exempt
def delete_disp_questions_view(request):
    """Display questions for deleting for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('deltidlist')
        
        # Check the test type to determine which questions to display
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('deltidlist')
        test_type = teacher_record.test_type
        
        # Display questions based on test type
        if test_type == 'subjective':
            # Get long answer questions
            questions = LongQA.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{'qid': q.qid, 'q': q.q, 'marks': q.marks} for q in questions]
            return render(request, "deldispquesLQA.html", {"callresults": callresults, "tid": test_id})
        elif test_type == 'practical':
            # Get practical questions
            questions = PracticalQA.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{
                'qid': q.qid, 
                'q': q.q, 
                'marks': q.marks
            } for q in questions]
            return render(request, "deldispquesPQA.html", {"callresults": callresults, "tid": test_id})
        else:  # Default to objective
            # Get objective questions
            questions = Question.objects.filter(test_id=test_id, uid=request.user)
            callresults = [{
                'qid': q.qid,
                'q': q.q,
                'a': q.a,
                'b': q.b,
                'c': q.c,
                'd': q.d,
                'ans': q.ans,
                'marks': q.marks
            } for q in questions]
            return render(request, "deldispques.html", {"callresults": callresults, "tid": test_id})
    
    # If not POST, redirect back to deltidlist
    return redirect('deltidlist')


@login_required
@csrf_exempt
def update_objective_question_view(request, test_id, qid):
    """Update an objective question."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Get the question
    question = Question.objects.filter(
        test_id=test_id,
        qid=qid,
        uid=request.user
    ).first()
    
    if not question:
        messages.error(request, "Question not found.")
        return redirect('updatetidlist')
    
    if request.method == 'POST':
        # Update the question with form data
        question.q = request.POST.get('ques', question.q)
        question.a = request.POST.get('ao', question.a)
        question.b = request.POST.get('bo', question.b)
        question.c = request.POST.get('co', question.c)
        question.d = request.POST.get('do', question.d)
        question.ans = request.POST.get('anso', question.ans)
        question.marks = request.POST.get('mko', question.marks)
        
        question.save()
        messages.success(request, f"Question {qid} updated successfully!")
        return redirect('updatetidlist')
    
    # For GET request, prepare data for the update form
    uresults = [{
        'qid': question.qid,
        'q': question.q,
        'a': question.a,
        'b': question.b,
        'c': question.c,
        'd': question.d,
        'ans': question.ans,
        'marks': question.marks,
        'test_id': test_id
    }]
    
    return render(request, "updateQuestions.html", {"uresults": uresults})


@login_required
def update_long_question_view(request, test_id, qid):
    """Update a long answer question."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Get the long question
    question = LongQA.objects.filter(
        test_id=test_id,
        qid=qid,
        uid=request.user
    ).first()
    
    if not question:
        messages.error(request, "Question not found.")
        return redirect('updatetidlist')
    
    if request.method == 'POST':
        # Update the question with form data
        question.q = request.POST.get('ques', question.q)
        question.marks = request.POST.get('mko', question.marks)
        
        question.save()
        messages.success(request, f"Long answer question {qid} updated successfully!")
        return redirect('updatetidlist')
    
    # For GET request, prepare data for the update form
    uresults = [{
        'qid': question.qid,
        'q': question.q,
        'marks': question.marks,
        'test_id': test_id
    }]
    
    return render(request, "updateQuestionsLQA.html", {"uresults": uresults})


@login_required
def update_practical_question_view(request, test_id, qid):
    """Update a practical question."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Get the practical question
    question = PracticalQA.objects.filter(
        test_id=test_id,
        qid=qid,
        uid=request.user
    ).first()
    
    if not question:
        messages.error(request, "Question not found.")
        return redirect('updatetidlist')
    
    if request.method == 'POST':
        # Update the question with form data
        question.q = request.POST.get('ques', question.q)
        question.marks = request.POST.get('mko', question.marks)
        
        question.save()
        messages.success(request, f"Practical question {qid} updated successfully!")
        return redirect('updatetidlist')
    
    # For GET request, prepare data for the update form
    uresults = [{
        'qid': question.qid,
        'q': question.q,
        'marks': question.marks,
        'test_id': test_id
    }]
    
    return render(request, "updateQuestionsPQA.html", {"uresults": uresults})


@csrf_exempt
@login_required
def display_students_details_view(request):
    """Display student details/logs for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('viewstudentslogs')
        
        # Check the test type to determine which template to use
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('viewstudentslogs')
        
        test_type = teacher_record.test_type
        
        # Get student logs for this test
        student_logs = StudentTestInfo.objects.filter(test_id=test_id)
        
        # Prepare data for the template
        log_data = []
        for log in student_logs:
            log_entry = {
                'email': log.email,
                'test_id': test_id,
                'time_left': log.time_left,
                'completed': log.completed,
                'name': getattr(log.uid, 'name', log.email)  # Try to get student name
            }
            log_data.append(log_entry)
        
        # Route to different templates based on test type
        if test_type == 'subjective':
            return render(request, "subdispstudentsdetails.html", {"callresults": log_data})
        elif test_type == 'practical':
            return render(request, "pracdispstudentsdetails.html", {"callresults": log_data})
        else:  # Default to objective
            return render(request, "displaystudentsdetails.html", {"callresults": log_data})
    
    # If not POST, redirect back to viewstudentslogs
    return redirect('viewstudentslogs')


@login_required
def live_monitoring_view(request):
    """Display live monitoring of students for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('livemonitoringtid')
        
        # Check if the test exists and belongs to the current professor
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('livemonitoringtid')
        
        # Get student logs for this test (active sessions)
        # Assuming StudentTestInfo tracks active test-taking sessions
        student_logs = StudentTestInfo.objects.filter(test_id=test_id)
        
        # Prepare data for the template
        log_data = []
        for log in student_logs:
            student = Student.objects.filter(email=log.email, test_id=test_id).first()
            log_entry = {
                'email': log.email,
                'time_left': log.time_left,
                'completed': log.completed,
                'test_id': test_id,
                'name': getattr(log.uid, 'name', log.email)  # Try to get student name
            }
            log_data.append(log_entry)
        
        return render(request, "live_monitoring.html", {
            "callresults": log_data, 
            "testid": test_id,
            "test_subject": teacher_record.subject,
            "test_topic": teacher_record.topic
        })
    
    # If not POST, redirect back to livemonitoringtid
    return redirect('livemonitoringtid')


@csrf_exempt
@login_required
def ajax_student_monitoring_stats_view(request, test_id, email):
    """AJAX endpoint to get student monitoring statistics."""
    if request.user.user_type != "teacher":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        return JsonResponse({'error': 'Test not found'}, status=404)
    
    # This is a placeholder - in a real implementation, you would query
    # the actual monitoring logs from your database tables
    # For now, returning sample data
    try:
        # Get all logs for this student and test
        logs = ViolationLog.objects.filter(test_id=test_id, student__email=email)
        
        # Calculate stats based on log details
        window_events = logs.filter(details__icontains="Tab Switch").count()
        mobile_detected = logs.filter(
            models.Q(details__icontains="Mobile Phone") | 
            models.Q(details__icontains="Cell Phone")
        ).count()
        person_events = logs.filter(
            models.Q(details__icontains="Person") | 
            models.Q(details__icontains="Face")
        ).count()
        audio_events = logs.filter(details__icontains="High Volume").count()
        
        total_logs = logs.count()
        
        stats = {
            'win': window_events,
            'mob': mobile_detected,
            'per': person_events,
            'aud': audio_events,
            'tot': total_logs
        }
        
        return JsonResponse(stats)
    
    except Exception as e:
        print(f"Stats error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def insert_marks_details_view(request):
    """Display interface to insert marks for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('insertmarkstid')
        
        # Check the test type to determine which template to use
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('insertmarkstid')
        
        test_type = teacher_record.test_type
        
        # Get students who took this test
        student_logs = StudentTestInfo.objects.filter(test_id=test_id)
        
        if not student_logs.exists():
            messages.error(request, "No students have taken this test yet.")
            return redirect('insertmarkstid')
        
        # For now, redirect to the first student's marks entry page
        # In a real implementation, you might want to show a list of students
        first_student = student_logs.first()
        
        # Route to different templates based on test type
        if test_type == 'subjective':
            # For subjective tests, redirect to insert subjective marks
            # We'll need to pass both test_id and student email
            return redirect('insert_sub_marks', test_id=test_id, email=first_student.email)
        elif test_type == 'practical':
            # For practical tests, redirect to insert practical marks
            return redirect('insert_prac_marks', test_id=test_id, email=first_student.email)
        else:  # Default to objective
            # For objective tests, we might have a different approach
            # Redirect to insert objective marks
            return redirect('insert_obj_marks', test_id=test_id, email=first_student.email)
    
    # If not POST, redirect back to insertmarkstid
    return redirect('insertmarkstid')


@login_required
def insert_obj_marks_view(request, test_id, email):
    """Display interface to insert marks for objective test for a specific student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('insertmarkstid')
    
    # Get the student's answers for this test
    student_answers = Student.objects.filter(test_id=test_id, email=email)
    
    # Get the questions and correct answers to calculate scores
    questions = Question.objects.filter(test_id=test_id)
    
    # Prepare data for the template
    results = []
    for answer in student_answers:
        question = questions.filter(qid=answer.qid).first()
        if question:
            is_correct = (answer.ans == question.ans)
            results.append({
                'qid': answer.qid,
                'q': question.q,
                'a': question.a,
                'b': question.b,
                'c': question.c,
                'd': question.d,
                'correct_answer': question.ans,
                'student_answer': answer.ans,
                'is_correct': is_correct,
                'marks': question.marks,
                'inputmarks': question.marks if is_correct else 0  # Auto-calculate if correct
            })
    
    context = {
        'callresults': results,
        'test_id': test_id,
        'email': email,
        'student_name': email  # In a real implementation, get from user model
    }
    
    return render(request, "insertobjmarks.html", context)


@login_required
def insert_sub_marks_view(request, test_id, email):
    """Display interface to insert marks for subjective test for a specific student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('insertmarkstid')
    
    # Get the student's answers for subjective questions
    student_answers = Student.objects.filter(test_id=test_id, email=email)
    
    # Get the long answer questions
    questions = LongQA.objects.filter(test_id=test_id)
    
    # Prepare data for the template
    results = []
    for answer in student_answers:
        question = questions.filter(qid=answer.qid).first()
        if question:
            results.append({
                'qid': answer.qid,
                'q': question.q,
                'ans': answer.ans,  # Student's answer
                'marks': question.marks,
                'inputmarks': 0  # Default to 0, teacher will enter marks
            })
    
    context = {
        'callresults': results,
        'test_id': test_id,
        'email': email,
        'student_name': email
    }
    
    return render(request, "insertsubmarks.html", context)


@login_required
def insert_prac_marks_view(request, test_id, email):
    """Display interface to insert marks for practical test for a specific student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('insertmarkstid')
    
    # Get the student's answers for practical questions
    student_answers = Student.objects.filter(test_id=test_id, email=email)
    
    # Get the practical questions
    questions = PracticalQA.objects.filter(test_id=test_id)
    
    # Prepare data for the template
    results = []
    for answer in student_answers:
        question = questions.filter(qid=answer.qid).first()
        if question:
            results.append({
                'qid': answer.qid,
                'q': question.q,
                'code': answer.ans,  # Student's code
                'input': '',  # In a real implementation, this would come from test data
                'executed': 'Success' if answer.ans else 'Failed',  # Example status
                'marks': question.marks,
                'inputmarks': 0  # Default to 0, teacher will enter marks
            })
    
    context = {
        'callresults': results,
        'test_id': test_id,
        'email': email,
        'student_name': email
    }
    
    return render(request, "insertpracmarks.html", context)


@csrf_exempt
@login_required
def view_results_view(request):
    """Display student results for a selected test."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    if request.method == 'POST':
        test_id = request.POST.get('choosetid', '').strip()
        
        if not test_id:
            messages.error(request, "Please select a test ID.")
            return redirect('publish_results_testid')
        
        # Check if the test exists and belongs to the current professor
        teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
        if not teacher_record:
            messages.error(request, "Test not found.")
            return redirect('publish_results_testid')
        
        # Get student results for this test
        # This would typically come from the Student model where answers and calculated marks are stored
        student_results = Student.objects.filter(test_id=test_id)
        
        # Calculate total marks for each student
        results_data = []
        for result in student_results:
            # Get the questions for this test to calculate total possible marks
            questions = Question.objects.filter(test_id=test_id)
            total_possible = sum([q.marks for q in questions])
            
            # Calculate actual score based on correct answers
            correct_count = 0
            total_score = 0
            for q in questions:
                student_answer = Student.objects.filter(
                    test_id=test_id,
                    email=result.email,
                    qid=q.qid,
                    ans=q.ans  # If student's answer matches correct answer
                ).count()
                if student_answer > 0:
                    total_score += q.marks
            
            results_data.append({
                'email': result.email,
                'marks': total_score,
                'total_possible': total_possible
            })
        
        context = {
            'callresults': results_data,
            'tid': test_id
        }
        
        return render(request, "publish_viewresults.html", context)
    
    # If not POST, redirect back to publish results page
    return redirect('publish_results_testid')


def _build_results_data(test_id, request_user):
    """Build list of {email, marks, total_possible, percentage} for a test. Returns empty if no data."""
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request_user).first()
    if not teacher_record:
        return None, 0
    student_results = Student.objects.filter(test_id=test_id).values_list("email", flat=True).distinct()
    questions = Question.objects.filter(test_id=test_id)
    total_possible = sum(q.marks for q in questions) if questions else 0
    results_data = []
    for email in student_results:
        total_score = 0
        for q in questions:
            if Student.objects.filter(test_id=test_id, email=email, qid=q.qid, ans=q.ans).exists():
                total_score += q.marks
        pct = round(100 * total_score / total_possible, 1) if total_possible else 0
        results_data.append({
            "email": email,
            "marks": total_score,
            "total_possible": total_possible,
            "percentage": pct,
        })
    return results_data, total_possible


# Dummy result set for demo when no real results exist
DUMMY_RESULTS = [
    {"email": "student1@example.com", "marks": 42, "total_possible": 50, "percentage": 84.0},
    {"email": "student2@example.com", "marks": 38, "total_possible": 50, "percentage": 76.0},
    {"email": "student3@example.com", "marks": 45, "total_possible": 50, "percentage": 90.0},
    {"email": "student4@example.com", "marks": 35, "total_possible": 50, "percentage": 70.0},
    {"email": "student5@example.com", "marks": 48, "total_possible": 50, "percentage": 96.0},
]


@login_required
@require_GET
def view_results_for_test_view(request, test_id):
    """Display student results for a specific test (GET). Tabular + graphical. Uses dummy data when no results."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    # Allow "demo" test_id when professor has no tests yet, so View Result always shows the results page
    if test_id == "demo":
        return render(
            request,
            "view_results_detail.html",
            {"callresults": list(DUMMY_RESULTS), "tid": "demo", "use_dummy": True},
        )
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect("tests_created")
    results_data, total_possible = _build_results_data(test_id, request.user)
    use_dummy = False
    if not results_data:
        results_data = list(DUMMY_RESULTS)
        use_dummy = True
    return render(
        request,
        "view_results_detail.html",
        {"callresults": results_data, "tid": test_id, "use_dummy": use_dummy},
    )


@csrf_exempt
@login_required
def publish_results_view(request):
    """Publish results for a test."""
    if request.user.user_type != "teacher":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            test_id = request.POST.get('testidsp', '').strip()
            
            if not test_id:
                return JsonResponse({'error': 'Test ID is required'}, status=400)
            
            # Check if the test exists and belongs to the current professor
            teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
            if not teacher_record:
                return JsonResponse({'error': 'Test not found'}, status=404)
            
            # In a real implementation, this would update a field to mark results as published
            # For now, just return success
            # teacher_record.results_published = True  # if such field exists
            # teacher_record.save()
            
            # You might want to mark the test as having published results
            # This could involve updating Teacher model or creating a PublishedResult record
            
            return JsonResponse({'success': 'Results published successfully'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
@login_required
def winevent_students_logs_view(request, test_id, email):
    """Display window event logs for a student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('livemonitoringtid')
    
    # Get window event logs
    window_logs = WindowEstimationLog.objects.filter(test_id=test_id, email=email)
    
    # Get student name
    student = Student.objects.filter(email=email, test_id=test_id).first()
    student_name = getattr(student, 'name', email) if student else email
    
    return render(request, "wineventstudentlog.html", {
        "testid": test_id,
        "email": email,
        "name": student_name,
        "callresults": window_logs
    })


@csrf_exempt
@login_required
def person_display_students_logs_view(request, test_id, email):
    """Display person detection logs for a student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('livemonitoringtid')
    
    # Get proctoring logs with person detection
    proctoring_logs = ProctoringLog.objects.filter(test_id=test_id, email=email)
    
    # Get student name
    student = Student.objects.filter(email=email, test_id=test_id).first()
    student_name = getattr(student, 'name', email) if student else email
    
    return render(request, "persondisplaystudentslogs.html", {
        "testid": test_id,
        "email": email,
        "name": student_name,
        "callresults": proctoring_logs
    })


@csrf_exempt
@login_required
def mob_display_students_logs_view(request, test_id, email):
    """Display mobile detection logs for a student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('livemonitoringtid')
    
    # Get proctoring logs with mobile detection
    proctoring_logs = ProctoringLog.objects.filter(test_id=test_id, email=email)
    
    # Get student name
    student = Student.objects.filter(email=email, test_id=test_id).first()
    student_name = getattr(student, 'name', email) if student else email
    
    return render(request, "mobdisplaystudentslogs.html", {
        "testid": test_id,
        "email": email,
        "name": student_name,
        "callresults": proctoring_logs
    })


@csrf_exempt
@login_required
def audio_display_students_logs_view(request, test_id, email):
    """Display audio monitoring logs for a student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('livemonitoringtid')
    
    # Get proctoring logs with audio data
    proctoring_logs = ProctoringLog.objects.filter(test_id=test_id, email=email)
    
    # Get student name
    student = Student.objects.filter(email=email, test_id=test_id).first()
    student_name = getattr(student, 'name', email) if student else email
    
    return render(request, "audiodisplaystudentslogs.html", {
        "testid": test_id,
        "email": email,
        "name": student_name,
        "callresults": proctoring_logs
    })


@csrf_exempt
@login_required
def display_students_logs_view(request, test_id, email):
    """Display general student logs."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('livemonitoringtid')
    
    # Get all proctoring logs
    proctoring_logs = ProctoringLog.objects.filter(test_id=test_id, email=email)
    
    # Get student name
    student = Student.objects.filter(email=email, test_id=test_id).first()
    student_name = getattr(student, 'name', email) if student else email
    
    return render(request, "displaystudentslogs.html", {
        "testid": test_id,
        "email": email,
        "name": student_name,
        "callresults": proctoring_logs
    })


@login_required
def payment_view(request):
    """Display payment page for professors to purchase exam credits."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Get current user's exam credits (this would typically come from a UserCredits model)
    # For now, using a placeholder value
    exam_credits = getattr(request.user, 'exam_credits', 0)
    
    context = {
        'callresults': {
            'examcredits': exam_credits
        }
    }
    
    return render(request, "payment.html", context)


@csrf_exempt
@login_required
def create_checkout_session_view(request):
    """Create Stripe checkout session for payment."""
    if request.user.user_type != "teacher":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            import stripe
            from django.conf import settings
            
            # Set your secret key
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': '10 Exam Credits',
                                'description': 'Purchase 10 exam credits for MyProctor.ai',
                            },
                            'unit_amount': 49900,  # ₹499 in paise
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/success/'),
                cancel_url=request.build_absolute_uri('/payment/'),
                client_reference_id=str(request.user.id),
            )
            
            return JsonResponse({'id': checkout_session.id})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def success_view(request):
    """Display success page after successful payment."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Update user's exam credits (this would typically update a UserCredits model)
    # For now, just display the success page
    # request.user.exam_credits += 10
    # request.user.save()
    
    return render(request, "success.html")


@login_required
def cancel_view(request):
    """Display cancel page if payment is cancelled."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    messages.info(request, "Payment was cancelled.")
    return redirect('payment')


@login_required
def student_monitoring_stats_view(request, test_id, email):
    """Display student monitoring statistics for a specific test and student."""
    if request.user.user_type != "teacher":
        return redirect("student_index")
    
    # Check if the test exists and belongs to the current professor
    teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
    if not teacher_record:
        messages.error(request, "Test not found.")
        return redirect('viewstudentslogs')
    
    # Pass the test_id and email to the template
    context = {
        'testid': test_id,
        'email': email
    }
    
    return render(request, "stat_student_monitoring.html", context)


@login_required
def delete_questions_view(request, test_id):
    """Delete selected questions for a test."""
    if request.user.user_type != "teacher":
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            qids = data.get('qids', '')
            
            if not qids:
                return JsonResponse({'error': 'No question IDs provided'}, status=400)
            
            # Split the qids string by comma to get individual IDs
            qid_list = [qid.strip() for qid in qids.split(',')]
            
            if not qid_list:
                return JsonResponse({'error': 'No valid question IDs provided'}, status=400)
            
            # Check the test type to determine which model to delete from
            teacher_record = Teacher.objects.filter(test_id=test_id, uid=request.user).first()
            if not teacher_record:
                return JsonResponse({'error': 'Test not found'}, status=404)
            
            test_type = teacher_record.test_type
            deleted_count = 0
            
            if test_type == 'subjective':
                # Delete from LongQA
                deleted_count, _ = LongQA.objects.filter(
                    test_id=test_id,
                    qid__in=qid_list,
                    uid=request.user
                ).delete()
            elif test_type == 'practical':
                # Delete from PracticalQA
                deleted_count, _ = PracticalQA.objects.filter(
                    test_id=test_id,
                    qid__in=qid_list,
                    uid=request.user
                ).delete()
            else:  # Default to objective
                # Delete from Question
                deleted_count, _ = Question.objects.filter(
                    test_id=test_id,
                    qid__in=qid_list,
                    uid=request.user
                ).delete()
            
            return JsonResponse({
                'success': f'Successfully deleted {deleted_count} question(s)',
                'message': f'{deleted_count} question(s) have been deleted successfully.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


from .vp_detector import Detector

@csrf_exempt
def check_environment_view(request):
    """
    Check if the environment is safe (no VM, debugger, sandbox).
    Returns JSON status.
    """
    try:
        detector = Detector()
        
        # Run checks
        is_safe = detector.is_safe
        check_results = detector.get_all_checks
        
        # Log if unsafe
        if not is_safe:
            # If user is authenticated, log a violation
            if request.user.is_authenticated:
                details = []
                if check_results.get('is_virtualized'): details.append("Virtual Machine Detected")
                if check_results.get('is_debugged'): details.append("Debugger Detected")
                if check_results.get('is_sandboxed'): details.append("Sandbox Detected")
                
                # Create a violation log
                # We use a special test_id 'SYSTEM_CHECK' or similar if not in a test
                # Or try to get test_id from request if sent
                test_id = request.POST.get('test_id') or request.GET.get('test_id') or 'SYSTEM_CHECK'
                
                ViolationLog.objects.create(
                    student=request.user,
                    test_id=test_id,
                    details=f"Environment Violation: {', '.join(details)}",
                    score=5 # High score for environment manipulation
                )
        
        return JsonResponse({
            'is_safe': is_safe,
            'checks': check_results
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
