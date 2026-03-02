################################################################################
# Clock Backend for Sanctum Station
################################################################################

import subprocess
import time
import threading
import os
import platform

# Stopwatch globals
stopwatch_start_time = 0
stopwatch_end_time = 0
stopwatch_elapsed = 0

# Timer globals
timer_remaining_seconds = 0
timer_thread = None
timer_stop_event = None

def stopwatch_start():
    global stopwatch_start_time
    stopwatch_start_time = time.time()
    return {"success": True}

def stopwatch_stop():
    global stopwatch_end_time, stopwatch_elapsed, stopwatch_start_time
    stopwatch_end_time = time.time()
    stopwatch_elapsed = stopwatch_end_time - stopwatch_start_time
    return {"success": True, "elapsed": stopwatch_elapsed}

def stopwatch_get():
    global stopwatch_start_time
    if stopwatch_start_time == 0:
        return 0
    return time.time() - stopwatch_start_time

def stopwatch_get_formatted(sec):
    hours = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    return f"{hours:02}:{mins:02}:{secs:02}"

def timer_start(duration):
    global timer_remaining_seconds, timer_thread, timer_stop_event
    timer_remaining_seconds = duration
    timer_stop_event = threading.Event()
    timer_thread = threading.Thread(target=timer_manager, daemon=True)
    timer_thread.start()
    return {"success": True}

def timer_manager():
    global timer_remaining_seconds, timer_stop_event
    while timer_remaining_seconds > 0 and not timer_stop_event.is_set():
        time.sleep(1)
        timer_remaining_seconds -= 1
    
    if timer_remaining_seconds <= 0:
        play_notification_sound()

def timer_stop():
    global timer_remaining_seconds, timer_stop_event
    if timer_stop_event:
        timer_stop_event.set()
    timer_remaining_seconds = 0
    return {"success": True}

def timer_get_remaining():
    global timer_remaining_seconds
    return timer_remaining_seconds

def play_notification_sound():
    try:
        # Get the path to session.wav in the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        sound_file = os.path.join(app_dir, 'timer.wav')
        
        if not os.path.exists(sound_file):
            print(f"Sound file not found: {sound_file}")
            print('\a', flush=True)  # Fallback to terminal bell
            return
        
        system = platform.system()
        
        if system == "Linux":
            # Try paplay (PulseAudio) first, then aplay (ALSA)
            try:
                subprocess.run(['paplay', sound_file], 
                             check=False, capture_output=True, timeout=2)
            except:
                try:
                    subprocess.run(['aplay', sound_file], 
                                 check=False, capture_output=True, timeout=2)
                except:
                    print('\a', flush=True)
        
        elif system == "Darwin":  # macOS
            subprocess.run(['afplay', sound_file], 
                         check=False, capture_output=True, timeout=2)
        
        elif system == "Windows":
            import winsound
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
        
    except Exception as e:
        print(f"Could not play notification sound: {e}")
        print('\a', flush=True)