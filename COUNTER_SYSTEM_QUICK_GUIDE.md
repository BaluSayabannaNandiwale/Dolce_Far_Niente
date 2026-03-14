# Dynamic Counter System - Quick Reference

## For Students

### What Do the Counters Mean?

The top panel of your exam shows three important counters that update automatically as you work:

#### ✅ Answered (Green)
- Shows how many questions you've answered
- Increases by 1 when you select any option
- **Does NOT increase again** if you change your answer (prevents double-counting)

#### ❌ Not Answered (Red)
- Shows how many questions are still unanswered
- Includes questions you haven't visited yet
- Automatically updates when you select or remove answers

#### 🔖 Bookmarked (Yellow)
- Shows how many questions you've marked for review
- Helps you track questions to revisit
- Updates instantly when you bookmark/unbookmark

### How to Use the Counters

**Answering Questions:**
1. Select an option (A, B, C, or D)
2. The "Answered" count increases immediately
3. The "Not Answered" count decreases automatically
4. No need to click "Submit Answer" - it's automatic!

**Changing Answers:**
1. Simply click a different option
2. The "Answered" count stays the same
3. Your new answer replaces the old one
4. No penalty for changing your mind!

**Bookmarking Questions:**
1. Click the "Bookmark" button
2. The "Bookmarked" count increases
3. Question turns yellow in the sidebar
4. Click "Bookmark" again to remove

**Removing an Answer:**
1. Click the already-selected option
2. Answer is deselected
3. "Answered" count decreases
4. "Not Answered" count increases

### Example Progression

```
Start of Exam:
Answered: 0 | Not Answered: 10 | Bookmarked: 0

After answering Q1 & Q2:
Answered: 2 | Not Answered: 8 | Bookmarked: 0

After bookmarking Q5:
Answered: 2 | Not Answered: 7 | Bookmarked: 1

After answering Q3 and changing Q1's answer:
Answered: 3 | Not Answered: 6 | Bookmarked: 1
(Changing Q1 didn't increase the count!)
```

### Color Guide

The question sidebar uses colors that match the counters:

- 🟢 **Green** = You've answered this question
- 🔴 **Red** = You haven't attempted this question
- 🟡 **Yellow** = You've bookmarked this question
- 🟡 **Yellow with Green Border** = Answered AND bookmarked

### Tips for Success

1. **Watch the counters** to track your progress
2. **Use bookmarks** for questions you want to review
3. **Don't worry** about changing answers - counts stay accurate
4. **Check "Not Answered"** before submitting to ensure you've attempted all questions
5. **Counters update automatically** - no page refresh needed!

---

## For Developers/Professors

### Technical Implementation

**Location**: `static/app.js`

**Key Functions**:
- `updateQuestionCounter()` - Main calculation function
- `animateCounter(element, newValue)` - Visual animation
- `getAnsweredCount()` - Get current answered count
- `getNotAnsweredCount()` - Get current not answered count  
- `getBookmarkedCount()` - Get current bookmarked count

**Event Triggers**:
- Answer selection (`change` event on radio buttons)
- Bookmark toggle (`bookmarkQuestion()` function)
- Answer deselection (click on selected radio)
- Navigation between questions

**Data Structure**:
```javascript
data[questionNumber] = {
    marked: 'a' | 'b' | 'c' | 'd' | null,
    status: NOT_MARKED | MARKED | SUBMITTED | 
            BOOKMARKED | MARKED_BOOKMARKED | SUBMITTED_BOOKMARKED
}
```

**Status Constants**:
- `NOT_MARKED = 0` - Red, not attempted
- `MARKED = 1` - Blue, marked but not submitted
- `SUBMITTED = 4` - Green, answered
- `BOOKMARKED = 2` - Yellow, bookmarked
- `MARKED_BOOKMARKED = 3` - Yellow, marked + bookmarked
- `SUBMITTED_BOOKMARKED = 5` - Yellow w/ border, answered + bookmarked

### Testing

**Console Commands** (open browser DevTools):
```javascript
// Check current counts
getAnsweredCount()
getNotAnsweredCount()
getBookmarkedCount()

// View all question states
console.log(data)

// Manually trigger counter update
updateQuestionCounter()
```

**Expected Console Output**:
```
✓ Answer selected for Q1: b
✓ Counters updated - Answered: 1, Not Answered: 9, Bookmarked: 0
✓ Bookmark toggled for Q3
✓ Counters updated - Answered: 1, Not Answered: 8, Bookmarked: 1
```

### Customization

**Change Animation Speed**:
Edit `animateCounter()` function in `app.js`:
```javascript
setTimeout(() => {
    element.textContent = newValue;
    element.style.transform = 'scale(1)';
}, 150); // Change this value (milliseconds)
```

**Change Colors**:
Edit CSS classes in `testquiz.html`:
```css
.question-indicator.answered { background-color: #28a745; } /* Green */
.question-indicator.not-attempted { background-color: #dc3545; } /* Red */
.question-indicator.bookmarked { background-color: #ffc107; } /* Yellow */
```

**Add New Counter**:
1. Add HTML element in `testquiz.html`
2. Add calculation logic in `updateQuestionCounter()`
3. Add helper function (e.g., `getMarkedCount()`)
4. Update this documentation

### Troubleshooting

**Counters not updating**:
- Check browser console for errors
- Verify `nos` array is populated
- Ensure `data` object exists

**Wrong counts**:
- Inspect `data` object in console
- Check if status values are correct
- Verify event handlers are attached

**Animation not working**:
- Check CSS transitions are enabled
- Verify element IDs match
- Ensure browser supports CSS transforms

### Performance

- **Time Complexity**: O(n) where n = number of questions
- **Update Frequency**: On user action only (not continuous polling)
- **Memory**: Minimal - uses existing data structures
- **Browser Support**: All modern browsers (Chrome, Firefox, Safari, Edge)

---

**Last Updated**: March 13, 2026  
**Version**: 1.0  
**Maintained By**: Development Team
