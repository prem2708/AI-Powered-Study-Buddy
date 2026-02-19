import sys
import os

print("--- Audio Diagnostic Tool ---")

try:
    import pyttsx3
    print("✅ pyttsx3 imported")
    try:
        import pythoncom
        pythoncom.CoInitialize()
        engine = pyttsx3.init()
        print("✅ pyttsx3 initialized")
        voices = engine.getProperty('voices')
        print(f"✅ Found {len(voices)} voices")
        print("🔊 Attempting to speak with pyttsx3...")
        engine.say("Testing pyttsx3 audio.")
        engine.runAndWait()
        print("✅ pyttsx3 spoken")
    except Exception as e:
        print(f"❌ pyttsx3 failed: {e}")
except ImportError:
    print("❌ pyttsx3 not installed")

print("-" * 20)

try:
    from pydub import AudioSegment
    from pydub.playback import play
    print("✅ pydub imported")
    # Generate a simple beep
    try:
        from gtts import gTTS
        import tempfile
        print("🔊 Attempting to speak with gTTS + pydub...")
        tts = gTTS("Testing gTTS audio.", lang='en')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            fname = f.name
        
        sound = AudioSegment.from_mp3(fname)
        play(sound)
        print("✅ pydub spoken")
        os.remove(fname)
    except Exception as e:
        print(f"❌ pydub/gTTS failed: {e}")
except ImportError:
    print("❌ pydub not installed")

print("--- End Diagnostic ---")
