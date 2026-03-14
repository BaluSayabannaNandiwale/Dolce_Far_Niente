// ============================================
// COUNTER SYSTEM VERIFICATION SCRIPT
// ============================================
// Run this in your browser console on the exam page
// to verify the counter system is working correctly

console.log('============================================');
console.log('🔍 COUNTER SYSTEM VERIFICATION');
console.log('============================================\n');

// 1. Check if required elements exist
console.log('1️⃣ Checking counter elements...');
var answeredElem = document.getElementById('answered-count');
var notAnsweredElem = document.getElementById('not-answered-count');
var bookmarkedElem = document.getElementById('bookmarked-count');

if (answeredElem) {
    console.log('   ✅ Answered counter element found');
} else {
    console.log('   ❌ Answered counter element NOT found');
}

if (notAnsweredElem) {
    console.log('   ✅ Not Answered counter element found');
} else {
    console.log('   ❌ Not Answered counter element NOT found');
}

if (bookmarkedElem) {
    console.log('   ✅ Bookmarked counter element found');
} else {
    console.log('   ❌ Bookmarked counter element NOT found');
}

// 2. Check data structures
console.log('\n2️⃣ Checking data structures...');
console.log('   nos array:', typeof nos, nos ? 'exists' : 'NOT FOUND');
console.log('   data object:', typeof data, data ? 'exists' : 'NOT FOUND');

if (nos && nos.length > 0) {
    console.log('   ✅ Total questions:', nos.length);
} else {
    console.log('   ⚠️ No questions loaded yet');
}

// 3. Check helper functions
console.log('\n3️⃣ Checking helper functions...');
if (typeof getAnsweredCount === 'function') {
    console.log('   ✅ getAnsweredCount() function available');
    console.log('      Current answered count:', getAnsweredCount());
} else {
    console.log('   ❌ getAnsweredCount() function NOT found');
}

if (typeof getNotAnsweredCount === 'function') {
    console.log('   ✅ getNotAnsweredCount() function available');
    console.log('      Current not answered count:', getNotAnsweredCount());
} else {
    console.log('   ❌ getNotAnsweredCount() function NOT found');
}

if (typeof getBookmarkedCount === 'function') {
    console.log('   ✅ getBookmarkedCount() function available');
    console.log('      Current bookmarked count:', getBookmarkedCount());
} else {
    console.log('   ❌ getBookmarkedCount() function NOT found');
}

// 4. Check update function
console.log('\n4️⃣ Checking update function...');
if (typeof updateQuestionCounter === 'function') {
    console.log('   ✅ updateQuestionCounter() function available');
} else {
    console.log('   ❌ updateQuestionCounter() function NOT found');
}

// 5. Display current question states
console.log('\n5️⃣ Current question states:');
if (data && nos) {
    var statusCounts = {
        NOT_MARKED: 0,
        MARKED: 0,
        SUBMITTED: 0,
        BOOKMARKED: 0,
        MARKED_BOOKMARKED: 0,
        SUBMITTED_BOOKMARKED: 0
    };
    
    for (var i = 1; i <= nos.length; i++) {
        if (data[i]) {
            var status = data[i].status;
            if (status === 0) statusCounts.NOT_MARKED++;
            else if (status === 1) statusCounts.MARKED++;
            else if (status === 2) statusCounts.BOOKMARKED++;
            else if (status === 3) statusCounts.MARKED_BOOKMARKED++;
            else if (status === 4) statusCounts.SUBMITTED++;
            else if (status === 5) statusCounts.SUBMITTED_BOOKMARKED++;
        } else {
            statusCounts.NOT_MARKED++;
        }
    }
    
    console.log('   Status breakdown:');
    console.log('   - Not Attempted (Red):', statusCounts.NOT_MARKED);
    console.log('   - Marked but not submitted (Blue):', statusCounts.MARKED);
    console.log('   - Bookmarked only (Yellow):', statusCounts.BOOKMARKED);
    console.log('   - Answered (Green):', statusCounts.SUBMITTED);
    console.log('   - Marked + Bookmarked:', statusCounts.MARKED_BOOKMARKED);
    console.log('   - Answered + Bookmarked:', statusCounts.SUBMITTED_BOOKMARKED);
}

// 6. Mathematical verification
console.log('\n6️⃣ Mathematical verification:');
if (nos) {
    var totalQuestions = nos.length;
    var answered = getAnsweredCount ? getAnsweredCount() : 0;
    var notAnswered = getNotAnsweredCount ? getNotAnsweredCount() : 0;
    
    console.log('   Total Questions:', totalQuestions);
    console.log('   Answered:', answered);
    console.log('   Not Answered:', notAnswered);
    console.log('   Sum check:', answered + notAnswered, '=', totalQuestions, '?', (answered + notAnswered === totalQuestions ? '✅ PASS' : '❌ FAIL'));
}

// 7. Quick test - simulate counter update
console.log('\n7️⃣ Testing counter update...');
if (updateQuestionCounter && typeof updateQuestionCounter === 'function') {
    updateQuestionCounter();
    console.log('   ✅ Counter update function executed');
    console.log('   Updated values:');
    console.log('   - Answered:', document.getElementById('answered-count')?.textContent || 'N/A');
    console.log('   - Not Answered:', document.getElementById('not-answered-count')?.textContent || 'N/A');
    console.log('   - Bookmarked:', document.getElementById('bookmarked-count')?.textContent || 'N/A');
}

console.log('\n============================================');
console.log('✅ Verification complete!');
console.log('============================================');

// Helper instructions
console.log('\n💡 QUICK COMMANDS:');
console.log('getAnsweredCount() - Get current answered count');
console.log('getNotAnsweredCount() - Get current not answered count');
console.log('getBookmarkedCount() - Get current bookmarked count');
console.log('updateQuestionCounter() - Manually trigger counter update');
console.log('console.log(data) - View all question states');
console.log('console.log(nos) - View question IDs');
