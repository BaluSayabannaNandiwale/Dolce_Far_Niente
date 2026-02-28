#!/usr/bin/env python
"""Quick test of Claude/Anthropic question generation."""
import os
import sys

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizapp.settings')

import django
django.setup()

from objective import ObjectiveTest

# Test with a simple text
text = "Python is a high-level programming language. It is easy to learn and read. Python supports multiple programming paradigms."

print("=" * 60)
print("Testing Claude/Anthropic Objective Question Generation")
print("=" * 60)

try:
    test = ObjectiveTest(text, 2)
    questions, answers = test.generate_test()
    print("\n✓ Generation Successful!\n")
    print(f"Generated {len(questions)} questions:\n")
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"Q{i}: {q}\nAnswer: {a}\n")
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    import traceback
    traceback.print_exc()

print("=" * 60)
