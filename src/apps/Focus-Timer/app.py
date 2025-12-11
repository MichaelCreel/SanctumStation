################################################################################
# Focus Timer Backend for Sanctum Station
################################################################################

import time
import threading
import os
import subprocess
import platform

session = "Idle"
active = False
session_thread = None
stop_event = None
remaining_seconds = 0
focus_dur = 0
short_dur = 0
long_dur = 0

# Starts a timer based on preset type
def start_preset_timer(timer_type):
    global focus_dur, short_dur, long_dur
    
    if timer_type == 'pom short':
        focus_dur = 25
        short_dur = 5
        long_dur = 15
        long_bool = False
    elif timer_type == 'pom long':
        focus_dur = 25
        short_dur = 5
        long_dur = 15
        long_bool = True
    elif timer_type == '52/17':
        focus_dur = 52
        short_dur = 17
        long_dur = 0
        long_bool = False
    else:  # Ultradian Rhythm (default)
        focus_dur = 90
        short_dur = 25
        long_dur = 0
        long_bool = False
    
    return start_custom_timer(focus_dur, short_dur, long_dur, long_bool)

# Starts a custom timer
def start_custom_timer(focus_minutes, short_minutes, long_minutes, use_long_break):
    global session, active, session_thread, stop_event, focus_dur, short_dur, long_dur
    
    if active:
        return {"success": False, "message": "Timer already running"}
    
    focus_dur = focus_minutes
    short_dur = short_minutes
    long_dur = long_minutes
    
    active = True
    stop_event = threading.Event()
    session_thread = threading.Thread(
        target=session_manager,
        args=(focus_minutes, short_minutes, long_minutes, use_long_break),
        daemon=True
    )
    session_thread.start()
    
    return {"success": True, "message": "Timer started"}

def stop_timer():
    global session, active, stop_event
    
    if not active:
        return {"success": False, "message": "No timer running"}
    
    active = False
    if stop_event:
        stop_event.set()
    
    session = "Idle"
    
    return {"success": True, "message": "Timer stopped"}

def get_status():
    global session, active, remaining_seconds, focus_dur, short_dur, long_dur
    return {
        "session": session,
        "active": active,
        "remaining_seconds": remaining_seconds,
        "focus_dur": focus_dur,
        "short_dur": short_dur,
        "long_dur": long_dur
    }

def session_manager(focus_minutes, short_minutes, long_minutes, use_long_break):
    global session, active, remaining_seconds, stop_event
    
    cycles = 0
    
    while active and not stop_event.is_set():
        # Focus session
        session = "Focus"
        if not countdown(focus_minutes * 60):
            break
        cycles += 1
        
        if not active:
            break
        
        # Break session
        if use_long_break and cycles % 4 == 0:
            session = "Long Break"
            if not countdown(long_minutes * 60):
                break
        else:
            session = "Short Break" if use_long_break else "Break"
            if not countdown(short_minutes * 60):
                break
    
    session = "Idle"
    active = False

def countdown(total_seconds):
    global remaining_seconds, stop_event
    
    remaining_seconds = total_seconds
    
    while remaining_seconds > 0 and not stop_event.is_set():
        time.sleep(1)
        remaining_seconds -= 1
    
    # Play sound when countdown completes (not interrupted)
    if not stop_event.is_set() and remaining_seconds == 0:
        play_notification_sound()
    
    return not stop_event.is_set()  # Return True if completed naturally

def play_notification_sound():
    """Play a notification sound when session ends"""
    try:
        # Get the path to session.wav in the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        sound_file = os.path.join(app_dir, 'session.wav')
        
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

