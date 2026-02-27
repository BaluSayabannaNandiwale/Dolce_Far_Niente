# TEAM NAME :- Dolce_Far_Niente

####################################################################################################################################################################################

# NoCheatZone-AI-BASED-SMART-ONLINE-EXAMINATION-PROCTORING-SYSYTEM

## PROPOSED SYSTEM
# A) Authentication with Image Verification
1) Basic Login, Register, Forgot Password, Change Password, etc
2) System allows only one login per user, so that user can’t do any unfair means.
3) System will verify image of user at every time of login and also in exam using face recognition technology.


# B) Professor 
1) Using AI , professor can generate questions & answers, the 2 types of questions & answer can be generated: objective & subjective.
2) Professor can create exam, view exam history, share details of exam with students, view questions, update, delete questions, but update & delete questions will not work at the time of exam & after the exam.
3) Professor can insert marks of subjective & practical exam & also publish the results, view results.
4) Professor can view Live Monitoring of Exam & also can view proctoring logs of the students.
5) Professor can report problems, recharge exam wallet, view FAQ, contact us.

# C) Students
1) Give/Take Exam
2) Check Exam History
3) Check Results
4) Report Problems

# D) Exam 
1) Types of Exam Supported:
    - Objective
    - Subjective
    - Practical 
2) If webpage is refresh then the timer will not be refreshed
3) Support for Negative Marking.
4) Support for randomize questions.
5) Support for Calculator for Mathematical type of Exam
6) Support for 20 types of Compilers/Interpreter for  programming practical type of Exam.
7) For Objective type of Exam:
     - Single page per question
     - Bookmark question 
      - Question Grid with previous & next button
      - At the time of exam submission all questions statistics will be showed to user for confirmation. 

# E) Proctoring 
1) Making logs of window events whenever user changes tab or opens a new tab.
2) Making logs of audio frequency at every 5 seconds of the students.
3) Detection of Mobile phone.
4) Detection of  More than 1 person in the exam.
5) Gaze Estimation: Estimating the position of student body & eyes movements.
6) Taking Students images logs at every 5 seconds.
7) CUT, COPY, PASTE, Taking Screenshots Function is disabled.
8) VM detection & Detection of Screen-Sharing applications. [Support Desktop App Only]

###########################################################################

# Django Conversion - NoCheatZone

This project has been converted from Flask to Django framework.

## Project Structure

```
quizapp/
├── manage.py
├── quizapp/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/         # User authentication app
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
├── exams/            # Exam management app
│   ├── models.py
│   ├── urls.py
│   └── admin.py
├── proctoring/       # Proctoring features app
│   ├── models.py
│   ├── urls.py
│   └── admin.py
├── templates/        # HTML templates (shared)
├── static/           # Static files (CSS, JS, images)
└── media/            # User uploaded files
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements_django.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create superuser:
```bash
python manage.py createsuperuser
```

4. Run development server:
```bash
python manage.py runserver
```

## Key Changes from Flask

### Models
- All database models converted to Django ORM
- Custom User model extends AbstractBaseUser
- Foreign key relationships properly defined

### Views
- Flask routes converted to Django class-based or function-based views
- Session handling uses Django's session framework
- Authentication uses Django's auth system

### Forms
- Flask-WTF forms converted to Django forms
- Form validation using Django's form validation

### URLs
- Flask `@app.route` decorators converted to Django URL patterns
- URL routing organized by app

### Templates
- Jinja2 templates need to be converted to Django template syntax
- Template inheritance works similarly
- Context variables passed via `render()` function

## Next Steps

1. **Convert remaining views**: Complete conversion of all 73 Flask routes to Django views
2. **Update templates**: Convert Jinja2 syntax to Django template syntax
3. **Add middleware**: Implement custom decorators as middleware if needed
4. **Test functionality**: Test all features after conversion
5. **Deploy**: Configure for production deployment

## Migration Notes

- Database: SQLite (same as Flask version)
- Email: Django's email backend configured
- Static files: Django static files handling
- Media files: Django media files handling
- Sessions: Django session framework

## Status

✅ Project structure created
✅ Models converted
✅ Basic authentication views converted
⏳ Remaining views need conversion
⏳ Templates need Django syntax conversion
⏳ Forms need completion
