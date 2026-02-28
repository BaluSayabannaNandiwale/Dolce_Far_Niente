#!/usr/bin/env python
"""
Test script for Google Generative AI (Gemini) integration
Verifies API key configuration and tests question generation
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizapp.settings')
django.setup()

from django.conf import settings
import json

print("=" * 70)
print("🧪 Google Generative AI (Gemini) Integration Test")
print("=" * 70)

# Test 1: Check API Key Configuration
print("\n1️⃣  Checking API Key Configuration...")
print("-" * 70)

gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
if gemini_api_key:
    # Show only first and last 5 characters for security
    masked_key = f"{gemini_api_key[:10]}...{gemini_api_key[-10:]}"
    print(f"✓ GEMINI_API_KEY found: {masked_key}")
else:
    print("✗ GEMINI_API_KEY not configured in settings.py")
    sys.exit(1)

# Test 2: Check Package Installation
print("\n2️⃣  Checking Package Installation...")
print("-" * 70)

try:
    import google.generativeai as genai
    print("✓ google-generativeai package installed")
except ImportError:
    print("✗ google-generativeai not installed. Run: pip install google-generativeai")
    sys.exit(1)

try:
    import langchain_google_genai
    print("✓ langchain-google-genai package installed")
except ImportError:
    print("⚠ langchain-google-genai not installed (optional, but recommended)")

# Test 3: Configure API
print("\n3️⃣  Configuring Gemini API...")
print("-" * 70)

try:
    genai.configure(api_key=gemini_api_key)
    print("✓ API configured successfully")
except Exception as e:
    print(f"✗ Failed to configure API: {e}")
    sys.exit(1)

# Test 4: List Available Models
print("\n4️⃣  Listing Available Models...")
print("-" * 70)

try:
    models = list(genai.list_models())
    print(f"✓ Found {len(models)} available models")
    
    # Show Gemini models
    gemini_models = [m.name for m in models if 'gemini' in m.name.lower()]
    if gemini_models:
        print("\n   Available Gemini models:")
        for model in gemini_models[:5]:  # Show first 5
            print(f"   - {model}")
    else:
        print("⚠ No Gemini models found")
except Exception as e:
    print(f"✗ Error listing models: {e}")

# Test 5: Test Simple Generation
print("\n5️⃣  Testing Simple Text Generation...")
print("-" * 70)

try:
    # Use a function to select best available model
    def _select_gemini_model(genai, preferred_name=None):
        """Select the best available Gemini model."""
        candidates = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        
        try:
            models = list(genai.list_models())
            available = []
            for m in models:
                name = getattr(m, "name", None)
                if name and "gemini" in name.lower():
                    available.append(name)
            
            if available:
                # Try exact match first
                for cand in candidates:
                    for avail in available:
                        if cand in avail:
                            return genai.GenerativeModel(avail)
                # Return first available
                return genai.GenerativeModel(available[0])
        except:
            pass
        
        # Fallback
        for cand in candidates:
            try:
                return genai.GenerativeModel(cand)
            except:
                continue
        
        raise RuntimeError("No usable Gemini model found")
    
    model = _select_gemini_model(genai)
    print(f"✓ Selected model: {model.model_name}")
    
    # Test simple prompt
    response = model.generate_content("Say 'Hello, Gemini API is working!' and nothing else.")
    if response.text:
        print(f"✓ API response: {response.text.strip()}")
    else:
        print("✗ No response text received")
except Exception as e:
    print(f"✗ Generation test failed: {e}")
    
    # Provide helpful debugging info
    error_str = str(e).lower()
    if "quota" in error_str or "429" in str(e):
        print("\n⚠️  API QUOTA EXCEEDED:")
        print("   - The free tier has limited requests per day/minute")
        print("   - Wait a few minutes and try again")
        print("   - Or upgrade your API plan: https://ai.google.dev/pricing")
    elif "invalid" in error_str or "auth" in error_str:
        print("\n⚠️  AUTHENTICATION ERROR:")
        print("   - Check your API key is correct")
        print("   - Regenerate key in Google AI Studio: https://aistudio.google.com/")
    
    sys.exit(1)

# Test 6: Test Question Generation (if basic test passed)
print("\n6️⃣  Testing Objective Question Generation...")
print("-" * 70)

try:
    from objective import ObjectiveTest
    
    # Test with small content
    test_content = "Python is a programming language. It was created by Guido van Rossum in 1991."
    generator = ObjectiveTest(test_content, 1, api_key=gemini_api_key)
    
    questions, answers = generator.generate_test()
    
    if questions and answers:
        print("✓ Question generation successful!")
        print(f"\n   Generated {len(questions)} question(s)")
        print(f"\n   Sample question:")
        print(f"   {questions[0][:100]}...")
    else:
        print("✗ No questions generated")
except ImportError as e:
    print(f"⚠ Could not import ObjectiveTest: {e}")
except Exception as e:
    print(f"✗ Question generation failed: {e}")
    if "quota" in str(e).lower():
        print("\n⚠️  API QUOTA EXCEEDED - Try again in a few minutes")

# Final Summary
print("\n" + "=" * 70)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 70)
print("""
Your Gemini API integration is configured and ready to use!

To generate questions:
1. Go to Django admin→ Generate Test
2. Enter text content
3. Choose question type (Objective/Subjective)
4. Number of questions
5. Click Generate

If you encounter quota errors:
- Wait a few minutes (free tier has rate limits)
- Or upgrade: https://ai.google.dev/pricing
""")
