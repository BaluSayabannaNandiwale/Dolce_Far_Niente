# Dynamic Counter System - Testing Checklist

## Pre-Deployment Verification

### Environment Setup
- [ ] Browser cache cleared or hard refresh performed (Ctrl+F5)
- [ ] JavaScript console open (F12)
- [ ] Exam page loaded successfully
- [ ] No JavaScript errors in console
- [ ] Counter elements visible in top panel

---

## Functional Testing

### Test 1: Initial State ✅
**Setup**: Load exam with 10 questions

**Expected Results**:
- [ ] Answered count shows "0"
- [ ] Not Answered count shows "10" (or total question count)
- [ ] Bookmarked count shows "0"
- [ ] All question indicators are red (not attempted)
- [ ] Console shows initialization messages

**Console Output Should Show**:
```
Exam page detected
Questions loaded: [...]
✓ Timer setup complete
```

---

### Test 2: Answering First Question ✅
**Action**: Select any option for Question 1

**Expected Results**:
- [ ] Answered count increases to "1"
- [ ] Not Answered count decreases to "9"
- [ ] Bookmarked count stays at "0"
- [ ] Question 1 indicator turns green
- [ ] Counter animation plays (scale effect)
- [ ] Console logs: "✓ Answer selected for Q1: [option]"

**Verification**:
```javascript
// In browser console, type:
getAnsweredCount()    // Should return: 1
getNotAnsweredCount() // Should return: 9
getBookmarkedCount()  // Should return: 0
```

---

### Test 3: Answering Multiple Questions ✅
**Action**: Answer questions 2, 3, and 4

**Expected Results**:
- [ ] After each answer, Answered count increases by 1
- [ ] Not Answered count decreases by 1 each time
- [ ] Counters update immediately (no delay)
- [ ] Each answered question shows green in sidebar
- [ ] Console logs each update

**Final State**:
```
Answered: 4
Not Answered: 6
Bookmarked: 0
```

---

### Test 4: Changing Answers ✅
**Setup**: Q1 has answer "A" selected

**Action**: Change Q1's answer from "A" to "B"

**Expected Results**:
- [ ] Answered count DOES NOT change (stays same)
- [ ] Not Answered count DOES NOT change
- [ ] No double-counting occurs
- [ ] Question 1 remains green
- [ ] Console logs: "✓ Answer selected for Q1: b"

**Critical Check**:
```
Before: Answered: 4, Not Answered: 6
After:  Answered: 4, Not Answered: 6  ← Should be unchanged!
```

---

### Test 5: Bookmarking Unanswered Question ✅
**Setup**: Navigate to Q6 (not answered)

**Action**: Click "Bookmark" button

**Expected Results**:
- [ ] Bookmarked count increases to "1"
- [ ] Not Answered count decreases to "5"
- [ ] Answered count unchanged
- [ ] Q6 indicator turns yellow
- [ ] Console logs: "✓ Bookmark toggled for Q6"

**State Check**:
```
Answered: 4
Not Answered: 5  (decreased because bookmarked)
Bookmarked: 1
```

---

### Test 6: Bookmarking Answered Question ✅
**Setup**: Q1 is already answered (green)

**Action**: Click "Bookmark" button on Q1

**Expected Results**:
- [ ] Bookmarked count increases
- [ ] Answered count DOES NOT change
- [ ] Not Answered count DOES NOT change
- [ ] Q1 shows yellow with green border
- [ ] Question counted in both Answered and Bookmarked

**Visual Check**:
```
Q1 should have:
- Yellow background (#ffc107)
- Green border (#28a745)
- CSS classes: answered-bookmarked
```

---

### Test 7: Removing Bookmark ✅
**Setup**: Q6 is bookmarked (yellow)

**Action**: Click "Bookmark" button again

**Expected Results**:
- [ ] Bookmarked count decreases
- [ ] If Q6 was not answered → Not Answered count increases
- [ ] If Q6 was answered → Answered count stays same
- [ ] Q6 returns to previous color
- [ ] Console logs: "✓ Bookmark toggled for Q6"

---

### Test 8: Deselecting Answer ✅
**Setup**: Q2 has answer selected (green)

**Action**: Click the already-selected radio button

**Expected Results**:
- [ ] Radio button becomes unchecked
- [ ] Answered count decreases
- [ ] Not Answered count increases
- [ ] Q2 indicator changes from green to red
- [ ] Console logs: "✓ Answer deselected for Q2"

**Verification**:
```javascript
// Check data structure
console.log(data[2])
// Should show: {marked: null, status: NOT_MARKED}
```

---

### Test 9: Navigation Stability ✅
**Setup**: Various questions answered/bookmarked

**Action**: Navigate through all questions using:
- Next/Previous buttons
- Question sidebar clicks
- URL parameter changes

**Expected Results**:
- [ ] Counters remain stable during navigation
- [ ] No unexpected changes
- [ ] Current question highlighted in sidebar
- [ ] Each question shows correct color
- [ ] Counters match visual state

**Test Pattern**:
```
Navigate: Q1 → Q5 → Q3 → Q8 → Q1
Counters should stay constant throughout!
```

---

### Test 10: Auto-Move After Answer ✅
**Setup**: Answer selection auto-moves to next question

**Action**: Select answer on current question

**Expected Results**:
- [ ] Answer registered immediately
- [ ] Counter updates before move
- [ ] After 2 seconds, moves to next question
- [ ] Next question displays correctly
- [ ] Counters remain accurate after move

**Console Timing**:
```
t=0ms:   ✓ Answer selected
t=100ms: Counters updated
t=2000ms: Moving to next question
```

---

## Edge Case Testing

### Test 11: All Questions Answered ✅
**Setup**: Answer all 10 questions

**Expected Results**:
- [ ] Answered count = Total questions (e.g., "10")
- [ ] Not Answered count = "0"
- [ ] All indicators green
- [ ] Ready to submit

**Mathematical Check**:
```
Answered + Not Answered = Total Questions
10 + 0 = 10 ✓
```

---

### Test 12: All Questions Bookmarked ✅
**Setup**: Bookmark all questions (without answering)

**Expected Results**:
- [ ] Bookmarked count = Total questions
- [ ] Not Answered count = "0" (bookmarked counts as reviewed)
- [ ] All indicators yellow
- [ ] Can still answer questions

---

### Test 13: Single Question Multiple Actions ✅
**Sequence**:
1. Answer Q1
2. Bookmark Q1
3. Change answer
4. Remove bookmark
5. Deselect answer

**Expected Final State**:
- [ ] Q1 marked as not attempted
- [ ] Answered: 0
- [ ] Not Answered: 1
- [ ] Bookmarked: 0

---

### Test 14: Rapid Actions ✅
**Action**: Quickly click bookmark multiple times

**Expected Results**:
- [ ] Counters handle rapid toggling correctly
- [ ] No negative numbers
- [ ] No NaN or undefined values
- [ ] Final state matches last action

---

### Test 15: Page Refresh ✅
**Setup**: Answer some questions, bookmark others

**Action**: Refresh page (F5)

**Expected Results**:
- [ ] Counters restore from server data
- [ ] Answered questions remain answered
- [ ] Bookmarked questions remain bookmarked
- [ ] Counts match pre-refresh state

---

## Visual Testing

### Test 16: Animation Quality ✅
**Check**:
- [ ] Scale animation smooth (no stuttering)
- [ ] Animation completes in ~300ms
- [ ] Text updates cleanly (no flickering)
- [ ] Font weight change subtle
- [ ] No layout shift during animation

---

### Test 17: Color Consistency ✅
**Check**:
- [ ] Green matches #28a745 exactly
- [ ] Red matches #dc3545 exactly
- [ ] Yellow matches #ffc107 exactly
- [ ] Colors consistent across sidebar and counters
- [ ] High contrast for accessibility

---

### Test 18: Responsive Design ✅
**Check on different screens**:
- [ ] Counters visible on mobile (320px)
- [ ] Counters visible on tablet (768px)
- [ ] Counters visible on desktop (1920px)
- [ ] No overflow or truncation
- [ ] Icons scale properly

---

## Browser Compatibility

### Test 19: Chrome/Edge ✅
- [ ] All features work
- [ ] Animations smooth
- [ ] Console logging works
- [ ] No errors

### Test 20: Firefox ✅
- [ ] All features work
- [ ] Animations smooth
- [ ] Console logging works
- [ ] No errors

### Test 21: Safari ✅
- [ ] All features work
- [ ] Animations smooth
- [ ] Console logging works
- [ ] No errors

---

## Integration Testing

### Test 22: With Timer Running ✅
**Setup**: Start exam with timer

**Check**:
- [ ] Counters update independently of timer
- [ ] Timer countdown continues normally
- [ ] No interference between systems
- [ ] Both update smoothly

---

### Test 23: With Camera Monitoring ✅
**Setup**: Enable camera monitoring

**Check**:
- [ ] Counter updates don't trigger violations
- [ ] Camera snapshots continue normally
- [ ] No performance degradation
- [ ] Both systems work independently

---

### Test 24: With Form Submission ✅
**Setup**: Answer questions, then submit form

**Check**:
- [ ] Final counters match submitted data
- [ ] Server receives correct answer count
- [ ] No discrepancy between client/server
- [ ] Redirect works after submission

---

## Performance Testing

### Test 25: Large Question Set ✅
**Setup**: Exam with 100+ questions

**Check**:
- [ ] Counters update efficiently
- [ ] No lag when updating
- [ ] Memory usage reasonable
- [ ] Animation remains smooth

---

### Test 26: Extended Session ✅
**Setup**: Keep exam open for 30+ minutes

**Check**:
- [ ] Counters remain accurate
- [ ] No memory leaks
- [ ] No degradation over time
- [ ] Still responsive after long period

---

## Debugging Tests

### Test 27: Console Commands ✅
**Try these in console**:
```javascript
// Get individual counts
getAnsweredCount()
getNotAnsweredCount()
getBookmarkedCount()

// View data structure
console.log(data)

// Manually update
updateQuestionCounter()

// Check nos array
console.log(nos)
```

**Expected**: All commands execute without errors

---

### Test 28: Error Recovery ✅
**Simulate error**: Try to access non-existent question

**Expected**:
- [ ] Graceful error handling
- [ ] Counters don't break
- [ ] Other functionality unaffected
- [ ] Error logged to console

---

## User Experience Testing

### Test 29: Intuitive Understanding ✅
**Ask test users**:
- [ ] Can they understand what counters mean?
- [ ] Do animations help or distract?
- [ ] Is color coding clear?
- [ ] Do they feel more confident?

---

### Test 30: Accessibility ✅
**Check**:
- [ ] Color blind users can distinguish states
- [ ] Screen readers announce counter changes
- [ ] Keyboard navigation works
- [ ] High contrast sufficient

---

## Sign-Off Criteria

### Required Tests (Must Pass):
- [ ] Test 1: Initial State
- [ ] Test 2: Answering First Question
- [ ] Test 3: Answering Multiple Questions
- [ ] Test 4: Changing Answers
- [ ] Test 5: Bookmarking
- [ ] Test 8: Deselecting Answer
- [ ] Test 9: Navigation Stability

### Recommended Tests (Should Pass):
- [ ] Test 10-15: Edge Cases
- [ ] Test 16-18: Visual Tests
- [ ] Test 19-21: Browser Compatibility
- [ ] Test 27: Debugging

### Optional Tests (Nice to Have):
- [ ] Test 22-24: Integration
- [ ] Test 25-26: Performance
- [ ] Test 29-30: UX/Accessibility

---

## Test Report Template

```
Test Date: ___________
Tester Name: ___________
Browser: ___________
Total Questions: ___________

Results Summary:
- Passed: _____ / 30
- Failed: _____ / 30
- Skipped: _____ / 30

Critical Issues Found:
[ ] None
[ ] Minor (describe below)
[ ] Major (describe below)

Issues Log:
1. ________________________________
2. ________________________________
3. ________________________________

Overall Status:
[ ] Ready for Production
[ ] Needs Minor Fixes
[ ] Needs Major Rework
[ ] Not Ready

Sign-off: _______________
Date: _______________
```

---

## Quick Smoke Test (5 Minutes)

For rapid verification:

1. **Load exam** → Check initial counters (30 sec)
2. **Answer Q1** → Verify Answered increases (30 sec)
3. **Answer Q2, Q3** → Verify multiple updates (30 sec)
4. **Change Q1 answer** → Verify no double-counting (30 sec)
5. **Bookmark Q4** → Verify Bookmarked increases (30 sec)
6. **Navigate Q1→Q5** → Verify stability (30 sec)
7. **Deselect Q2** → verify Not Answered increases (30 sec)
8. **Check console** → Verify logging works (30 sec)
9. **Visual check** → Verify colors/animations (30 sec)
10. **Refresh page** → Verify persistence (30 sec)

**Total: 5 minutes**

---

**Testing Status**: ✅ Ready for QA  
**Last Updated**: March 13, 2026  
**Version**: 1.0
