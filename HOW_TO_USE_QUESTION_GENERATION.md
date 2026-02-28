# How to Use the "Generate Questions" Feature

## Current Status
✅ All systems operational
✅ Packages installed and verified
✅ API configured and connected
⏳ Free tier quota temporarily exhausted (resets in ~1 hour)

---

## Quick Start (After Quota Reset)

### Step 1: Access Admin Panel
1. Open your browser
2. Go to: `http://localhost:8000/`
3. Log in with your admin credentials
4. Click: "Admin Panel" or navigate to `/admin/`

### Step 2: Navigate to Generate Test
- Click on: "Exams" → "Generate Test"
- Or direct URL: `http://localhost:8000/admin/exams/generatetest/`

### Step 3: Fill the Form
```
Topic/Text Input:
  Enter the content or topic for questions
  Example: "Python is a high-level programming language 
           introduced in 1991 by Guido van Rossum. It emphasizes 
           code readability..."

Question Type:
  Select one:
  - Objective (Multiple choice: A, B, C, D)
  - Subjective (Long answer/essay type)

Number of Questions:
  Enter: 1-5 (recommended 2-3 for best results)
```

### Step 4: Generate
1. Click the "Generate" button
2. Wait 10-30 seconds for Gemini AI to process
3. Your questions will appear below the form

### Step 5: Save/Use
- Copy the generated questions
- Add to your exam database
- Edit as needed before publishing

---

## What Makes This Feature Special

### Powered by Google Gemini AI
- **Intelligent Content Analysis**: Understands the topic deeply
- **Quality Control**: Generates clear, unambiguous questions
- **Diverse Formats**: 
  - Objective: 4-option multiple choice (A, B, C, D)
  - Subjective: In-depth essay prompts with marking guidelines
- **Customizable**: Generate 1-5 questions per request

### Examples

#### Objective Question Example
```
Question: What is the primary purpose of a Python decorator?
A) To enhance code performance by compiling
B) To modify or wrap a function without changing its source code
C) To replace function parameters
D) To create new Python classes

Answer: B
```

#### Subjective Question Example
```
Question: Explain the Model-View-Controller (MVC) pattern 
          in Django and describe how each component interacts 
          with the others.

Sample Answer Guide:
- Model: Handles data and business logic
- View: Processes requests and returns responses
- Controller: Routes requests to appropriate handlers
- Integration: HTTP request → Controller → Model → View → Response
- Benefits: Separation of concerns, testability, scalability
```

---

## Troubleshooting

### Issue: "API Key not valid" Error
**Solution:**
1. Check if quota has been exceeded
2. Wait 30 minutes for daily reset
3. Or upgrade to paid plan: https://ai.google.dev/pricing

### Issue: "Quota Exceeded" Error
**Reason:** Free tier has limited daily requests
**Solutions:**
- Option 1: Wait ~1 hour for automatic reset
- Option 2: Upgrade to paid plan (instant unlimited access)
- Option 3: Try again in 30 minutes

### Issue: Questions Don't Generate
**Possible Causes:**
1. Network connectivity - check internet connection
2. API quota - wait for reset
3. Django server not running - restart server
4. Database issue - check Django admin connectivity

**Debug Steps:**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for API requests
4. Review Django server logs

---

## API Quota Details

### Free Tier Limits
- **Requests Per Minute**: 1-2 per minute
- **Requests Per Day**: ~50-100 per day
- **Status**: Checked hourly

### When Quota Resets
- **Minute Quota**: Resets every 60 seconds
- **Daily Quota**: Resets daily at midnight UTC
- **Current Time**: Check at https://ai.dev/rate-limit

### How to Check Current Usage
1. Visit: https://ai.dev/rate-limit
2. Sign in with your Google account
3. View remaining quota

---

## Upgrade to Paid Plan

### Why Upgrade?
- Unlimited questions per day
- Faster API responses
- Priority support
- No quota restrictions

### Steps to Upgrade
1. Visit: https://ai.google.dev/pricing
2. Click "Get Started"
3. Set up Google Cloud billing
4. Enable "Generative Language API"
5. System automatically uses higher quotas

### Pricing
- **Input Tokens**: $0.075 per 1M tokens
- **Output Tokens**: $0.30 per 1M tokens
- **Typical Cost**: $0.01-$0.05 per 10 questions
- **Monthly Estimate**: $1-$5 for moderate use

---

## System Architecture

### How Question Generation Works

```
User Input (Topic + Count)
           ↓
    Django Form Handler
           ↓
  ObjectiveTest / SubjectiveTest Class
           ↓
    Google Generative AI (Gemini)
           ↓
    JSON Response Parser
           ↓
    Format & Return Questions
           ↓
  Display in Admin Panel
```

### Technologies Used
- **Backend**: Django 4.2.28
- **AI Engine**: Google Gemini API (gemini-2.0-flash)
- **Language**: Python 3.12
- **Database**: Django ORM (SQLite/PostgreSQL)
- **UI**: Bootstrap 4.3 + HTML5

---

## Best Practices

### For Best Question Quality
1. **Be Specific**: Provide detailed topic text (100+ words)
2. **Request Appropriate Quantity**: 2-3 questions at a time
3. **Review & Edit**: Always proofread generated questions
4. **Provide Context**: Include relevant course information
5. **Test Questions**: Ensure answers are clear and correct

### Topic Examples
```
✓ Good: "Explain machine learning basics including supervised learning,
        unsupervised learning, and reinforcement learning with real-world
        examples..."

✗ Poor: "Machine learning"

✓ Good: "Django models, querysets, and relationships. Cover one-to-many,
        many-to-many, and one-to-one relationships with migration examples..."

✗ Poor: "Django"
```

### Batch Generation
- Generate 2-3 questions at a time
- Wait between requests to avoid quota issues
- Compile generated questions into question bank
- Organize by difficulty level

---

## Support

### Documentation
- Django Integration: See `README_DJANGO.md`
- Camera Monitoring: See `CAMERA_MONITORING_GUIDE.md`
- Conversion Guide: See `CONVERSION_GUIDE.md`

### API Documentation
- Gemini API Docs: https://ai.google.dev/docs/gemini_api_overview
- Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Error Types: https://ai.google.dev/errors

### Contact
- Email: support@nocheatzone.ai
- Issues: Check Django admin logs
- Debug: Run `test_question_generation.py`

---

## FAQ

**Q: Can I generate unlimited questions?**
A: Free tier: ~50-100 per day. Paid plan: Unlimited (based on budget).

**Q: Why do I see "Quota Exceeded"?**
A: Free tier has limits. Wait 1 hour or upgrade to paid plan.

**Q: How long does generation take?**
A: Typically 10-30 seconds per request, depends on question count.

**Q: Can I edit questions after generation?**
A: Yes! Copy to text editor, edit, then add to question bank.

**Q: What if AI generates bad questions?**
A: Regenerate with more specific topic description.

**Q: Multiple users - will quota be shared?**
A: Yes, quota is per API key. All users share the same limit.

---

Last Updated: 2026-02-27
System Version: 3.0 (with Gemini AI Integration)
Status: OPERATIONAL
