import io
import os
import tempfile
import threading
import queue
import time
from gtts import gTTS

# Try to import playback libraries
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from pydub import AudioSegment
    from pydub.playback import play
except ImportError:
    play = None

# Global queue for TTS tasks
_tts_queue = queue.Queue()
_stop_event = threading.Event()
_worker_thread = None
_current_engine = None

def _tts_worker_loop():
    """
    Dedicated worker thread for pyttsx3. Initializes engine ONCE to avoid errors.
    """
    global _current_engine
    
    # Initialize COM for this thread (Windows requirement)
    engine = None
    if pyttsx3:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
        except Exception as e:
            print(f"pyttsx3 init failed: {e}")
            engine = None

    while True:
        try:
            # Check if engine needs re-initialization (e.g. after a hard stop)
            if _stop_event.is_set():
                print("♻️ Re-initializing engine after stop")
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 150)
                except Exception as e:
                     print(f"Re-init failed: {e}")
                _stop_event.clear()

            # Get text from queue (blocking)
            text = _tts_queue.get()
            
            if text is None: # Sentinel to kill thread
                 break
            
            # Clear stop event for new utterance
            _stop_event.clear()
            
            success = False
            
            # 1. Try pyttsx3 (Preferred)
            if engine:
                try:
                    _current_engine = engine
                    engine.say(text)
                    engine.runAndWait()
                    _current_engine = None
                    success = True
                except Exception as e:
                    print(f"pyttsx3 playback error: {e}")
                    _current_engine = None
                    # Attempt to re-init engine if it crashed?
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 150)
                    except:
                        pass

            # 2. Fallback to pydub/gTTS if pyttsx3 failed or unavailable
            if not success and play and not _stop_event.is_set():
                try:
                    tts = gTTS(text=text, lang='en')
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                        tts.save(f.name)
                        temp_filename = f.name
                    
                    sound = AudioSegment.from_mp3(temp_filename)
                    play(sound)
                    
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
                except Exception as e:
                    print(f"pydub playback error: {e}")

            _tts_queue.task_done()
            
        except Exception as e:
            print(f"TTS Worker Loop Critical Error: {e}")

def _ensure_worker_running():
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_thread = threading.Thread(target=_tts_worker_loop, daemon=True)
        _worker_thread.start()

def text_to_speech(text: str) -> io.BytesIO:
    """
    Convert text to speech using gTTS (for frontend st.audio playback).
    Returns a BytesIO object containing MP3 audio data.
    """
    try:
        if not text.strip():
            return None
        
        tts = gTTS(text=text, lang='en', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp
    except Exception as e:
        print(f"Error generating audio (bytes): {e}")
        return None

def stop_audio():
    """Request server-side audio playback to stop."""
    global _current_engine
    
    # Signal stop logic
    _stop_event.set()
    
    # Clear pending queue
    with _tts_queue.mutex:
        _tts_queue.queue.clear()
        
    # Stop current engine
    if _current_engine:
        try:
            _current_engine.stop()
        except Exception:
            pass

def speak(text: str):
    """
    Queue text to be spoken on the server.
    """
    if not text.strip():
        return
        
    # Stop any current speech before starting new one
    stop_audio()
    # Wait briefly for stop to register
    time.sleep(0.05)
    
    _ensure_worker_running()
    _tts_queue.put(text)
