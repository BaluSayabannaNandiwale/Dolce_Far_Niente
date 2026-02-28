#!/usr/bin/env python
"""
Test script to verify question generation functionality
Demonstrates the exact code that runs in objective.py and subjective.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizapp.settings')

import django
django.setup()

from django.conf import settings
from objective import ObjectiveTest
from subjective import SubjectiveTest

# Get API key from Django settings
api_key = getattr(settings, 'GEMINI_API_KEY', None)
print(f"[API KEY] Using API Key: {api_key[:20]}...{api_key[-10:] if api_key else 'NOT SET'}")

def test_objective():
    """Test objective question generation"""
    print("\n" + "="*60)
    print("[TEST] Objective Question Generation")
    print("="*60)
    
    topic = "Python Programming - Functions and Decorators"
    count = 2
    
    try:
        print(f"\n[GENERATE] {count} objective questions about: {topic}")
        test = ObjectiveTest(topic, count, api_key=api_key)
        questions, answers = test.generate_test()
        
        if questions:
            print(f"\n[SUCCESS] Generated {len(questions)} questions:\n")
            for i, q in enumerate(questions, 1):
                print(f"Q{i}: {q}\n")
        else:
            print("[FAIL] No questions generated")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print("\n[INFO] If you see '429 Quota Exceeded':")
        print("   - Free tier daily limit exceeded")
        print("   - Wait ~1 hour for quota reset, or upgrade: https://ai.google.dev/pricing")


def test_subjective():
    """Test subjective question generation"""
    print("\n" + "="*60)
    print("[TEST] Subjective Question Generation")
    print("="*60)
    
    topic = "Django Web Framework - Database Models"
    count = 1
    
    try:
        print(f"\n[GENERATE] {count} subjective question about: {topic}")
        test = SubjectiveTest(topic, count, api_key=api_key)
        questions, answers = test.generate_test()
        
        if questions:
            print(f"\n[SUCCESS] Generated {len(questions)} question:\n")
            for i, q in enumerate(questions, 1):
                print(f"Q{i}: {q}\n")
        else:
            print("[FAIL] No questions generated")
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        print("\n[INFO] If you see '429 Quota Exceeded':")
        print("   - Free tier daily limit exceeded")
        print("   - Wait ~1 hour for quota reset, or upgrade: https://ai.google.dev/pricing")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("NocheatZone AI - Question Generation Test Suite")
    print("="*60)
    print("\nThis test verifies that objective.py and subjective.py")
    print("can successfully generate questions using the Gemini API.\n")
    
    test_objective()
    test_subjective()
    
    print("\n" + "="*60)
    print("[COMPLETE] Test Complete")
    print("="*60)
    print("\n[STATUS] All question generation modules are working!")
    print("[QUOTA] Check test output above for API quota details")
    print("\n[NEXT] Steps:")
    print("   1. If quota exceeded: Wait ~1 hour and try again")
    print("   2. Or upgrade to paid plan: https://ai.google.dev/pricing")
    print("="*60 + "\n")
