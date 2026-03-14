# How to View Question Counters on Exam Page

## 📍 Location of Counters

When you open **http://localhost:8000/give-test/DEMO001**, you will see the counter panel at the **TOP** of the exam page, just below the student information.

### Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [Student Name]                              [Secure Exam]  │
│  [Email]                                                    │
│                                                             │
│  📚 Subject | 📋 Topic | 🆔 ID: DEMO001                    │
│                                                             │
│  ╔═══════════════════════════════════════════════════╗    │
│  ║  ✅        ❌         🔖         ⏰              ║    │
│  ║ Answered  Not Ans.  Bookmarked  Time Left       ║    │
│  ║    3          7          2      00:45:30        ║    │  ← COUNTERS ARE HERE
│  ╚═══════════════════════════════════════════════════╝    │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Question Text Here...                            │     │
│  │                                                   │     │
│  │  A. Option 1                                      │     │
│  │  B. Option 2                                      │     │
│  │  C. Option 3                                      │     │
│  │  D. Option 4                                      │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  [← Previous] [Next →] [🔖 Bookmark] [✓ Submit]            │
│                                                             │
│  Questions Sidebar (Right side):                           │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐                │
│  │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │                │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤                │
│  │ G │ R │ G │ Y │ R │ R │ Y*│ R │ R │ R │                │
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘                │
│    G=Green(Answered)  R=Red(Not Attempted)                 │
│    Y=Yellow(Bookmarked)  Y*=Answered+Bookmarked            │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 What Each Counter Shows

### 1. ✅ Answered (Green)
- **What it counts**: Questions where you selected ANY answer option
- **When it increases**: When you click on any radio button (A, B, C, or D)
- **When it DOESN'T increase**: When you CHANGE your answer (prevents double-counting)
- **Color in sidebar**: Green (#28a745)

### 2. ❌ Not Answered (Red)
- **What it counts**: Questions where you did NOT select any option
- **When it decreases**: When you select an answer
- **When it increases**: When you deselect/remove your answer
- **Color in sidebar**: Red (#dc3545)

### 3. 🔖 Bookmarked (Yellow)
- **What it counts**: Questions you marked for review using the Bookmark button
- **When it increases**: When you click the "Bookmark" button
- **When it decreases**: When you click "Bookmark" again to remove it
- **Color in sidebar**: Yellow (#ffc107)

### 4. ⏰ Time Left (Blue)
- **What it shows**: Remaining time for the exam
- **Updates**: Every second (counts down)
- **Format**: HH:MM:SS or MM:SS depending on duration

## 📊 Example Scenarios

### Scenario 1: Just Started Exam (10 questions total)
```
✅ Answered: 0
❌ Not Answered: 10
🔖 Bookmarked: 0
```
**Meaning**: You haven't answered any questions yet.

### Scenario 2: After Answering 3 Questions
```
✅ Answered: 3
❌ Not Answered: 7
🔖 Bookmarked: 0
```
**Meaning**: You answered 3 questions, 7 remain unanswered.

### Scenario 3: After Bookmarking 2 Questions
```
✅ Answered: 3
❌ Not Answered: 5
🔖 Bookmarked: 2
```
**Meaning**: 
- 3 questions answered (green)
- 2 questions bookmarked for review (yellow)
- 5 questions not attempted (red)
- Total: 3 + 2 + 5 = 10 ✓

### Scenario 4: Changed One Answer
```
✅ Answered: 3  (stays same!)
❌ Not Answered: 5
🔖 Bookmarked: 2
```
**Meaning**: Changing an answer doesn't increase the count - prevents double-counting!

## 🔧 How to Use Counters

### To Track Your Progress:
1. **Look at "Answered"** - See how many you've completed
2. **Look at "Not Answered"** - See how many are left
3. **Look at "Bookmarked"** - See how many you want to review

### Before Submitting:
- Check that **"Not Answered" = 0** (if you want to attempt all questions)
- Review **bookmarked questions** if time permits
- Verify the counts match your expectation

## 🎨 Color Guide in Question Sidebar

The question numbers on the right side use colors:

| Color | Meaning | Counter Impact |
|-------|---------|----------------|
| 🟢 Green | You answered this | Counts in "Answered" |
| 🔴 Red | You didn't attempt | Counts in "Not Answered" |
| 🟡 Yellow | You bookmarked it | Counts in "Bookmarked" |
| 🟡 Yellow + 🟢 Green Border | Answered AND bookmarked | Counts in BOTH |

## 🐛 Troubleshooting

### If counters show 0 when they shouldn't:

**Step 1: Open Browser Console**
- Press `F12` (or right-click → Inspect)
- Click the "Console" tab

**Step 2: Run Verification**
Copy and paste this into the console:
```javascript
console.log('Answered:', getAnsweredCount());
console.log('Not Answered:', getNotAnsweredCount());
console.log('Bookmarked:', getBookmarkedCount());
```

**Step 3: Check Data**
```javascript
console.log('Question data:', data);
console.log('Question IDs:', nos);
```

**Step 4: Manual Update**
```javascript
updateQuestionCounter();
```

### If counters don't update when you select answers:

1. **Check if JavaScript is enabled** in your browser
2. **Hard refresh** the page: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
3. **Clear browser cache** and reload
4. **Try a different browser** (Chrome, Firefox, Edge)

## 📝 Quick Commands for Testing

Open browser console (`F12`) and type:

```javascript
// Get current counts
getAnsweredCount()
getNotAnsweredCount()
getBookmarkedCount()

// View all question states
console.log(data)

// Manually trigger counter update
updateQuestionCounter()

// Check total questions
nos.length
```

## ✅ Expected Behavior

### When You Select an Answer:
1. Counter updates **immediately** (no delay)
2. You hear a visual "pop" (animation)
3. Question turns **green** in sidebar
4. "Answered" increases by 1
5. "Not Answered" decreases by 1

### When You Change an Answer:
1. Counter **does NOT change** (stays same)
2. No animation (because count is unchanged)
3. Question stays green
4. This is CORRECT behavior (prevents double-counting)

### When You Bookmark:
1. Counter updates immediately
2. Question turns **yellow** in sidebar
3. "Bookmarked" increases by 1

### When You Navigate Between Questions:
1. Counters **stay stable** (don't change)
2. Current question gets blue border highlight
3. All counts remain accurate

## 📞 Need Help?

If counters still don't work:

1. **Take a screenshot** of the exam page showing the issue
2. **Open browser console** (F12) and take screenshot of any errors
3. **Note what actions** you performed before the issue occurred
4. **Share with development team** for investigation

---

**Last Updated**: March 13, 2026  
**System Version**: 1.0  
**Status**: ✅ Operational
