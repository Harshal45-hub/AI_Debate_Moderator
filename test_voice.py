#!/usr/bin/env python3
"""
SIMPLE VOICE TEST - Run this first!
"""

import pyttsx3

def test_pyttsx3():
    """Test if pyttsx3 works at all"""
    print("\n🔊 TESTING VOICE SYSTEM")
    print("="*50)
    
    try:
        # Create engine
        engine = pyttsx3.init()
        
        # Test properties
        print(f"✓ Engine created successfully")
        
        # Get voices
        voices = engine.getProperty('voices')
        print(f"✓ Found {len(voices)} voice(s)")
        
        for i, voice in enumerate(voices):
            print(f"  Voice {i}: {voice.name}")
        
        # Test speak
        print("\n🎤 Testing speech...")
        engine.say("Hello, this is a test voice. Can you hear me?")
        engine.runAndWait()
        
        print("\n🎤 Testing second speech...")
        engine.say("This is the second test. Both should work.")
        engine.runAndWait()
        
        print("\n" + "="*50)
        print("✅ VOICE TEST PASSED!")
        print("If you heard both messages, voices work correctly.")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ VOICE TEST FAILED: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure speakers are connected and ON")
        print("2. Check volume is up")
        print("3. Try: pip install --upgrade pyttsx3")
        print("4. On Windows, install voices from Settings")
        return False

def test_multiple_engines():
    """Test creating multiple engines"""
    print("\n🔊 TESTING MULTIPLE ENGINES")
    print("="*50)
    
    try:
        # First engine
        print("\n🎤 First engine...")
        engine1 = pyttsx3.init()
        engine1.say("This is the first voice")
        engine1.runAndWait()
        
        # Second engine
        print("\n🎤 Second engine...")
        engine2 = pyttsx3.init()
        engine2.say("This is the second voice")
        engine2.runAndWait()
        
        print("\n✅ MULTIPLE ENGINE TEST PASSED!")
        print("Both voices should have spoken.")
        return True
        
    except Exception as e:
        print(f"\n❌ Multiple engine test failed: {e}")
        return False

if __name__ == "__main__":
    print("AI VERBAL DEBATE - VOICE DIAGNOSTIC")
    print("\nRun this test FIRST to check if voices work.")
    
    test1 = test_pyttsx3()
    
    if test1:
        test2 = test_multiple_engines()
    
    print("\n🎯 If tests pass, run: python run_debate.py")