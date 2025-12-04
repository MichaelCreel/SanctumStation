################################################################################
# Python Backend for Sanctum Station
# This file handles logic for the psuedo-desktop environment to be used.
################################################################################

import webview

apps = []

# Handles initialization of app components
def initialize():
    if not init_webview():
        print("FATAL: Failed to initialize webview.\n\nFATAL 0")
        return False
    if not init_settings():
        print("WARNING: Failed to initialize settings. Using default settings.\n\nWARNING 0")
    if not init_apps():
        print("WARNING: No apps found to initialize. No apps will be loaded.\n\nWARNING 1")

# Initializes webview
def init_webview():
    try:
        webview.create_window("Sanctum Station", "http://localhost:8000", width=1280, height=720)
        webview.start()
        return True
    except Exception as e:
        print(f"IW: Error initializing webview: {e}")
        return False

# Initializes environment settings
def init_settings():
    try:
        with open("data/settings.yaml", "r") as file:
            settings = file.read()
        return True
    except FileNotFoundError:
        print("IS: Settings file not found. Using default settings.")
        return False
    except Exception as e:
        print(f"IS: Error reading settings file: {e}")
        return False

# Initializes downloaded apps
def init_apps():
    global apps
    apps = []
    try:
        import os
        app_dir = "data/apps/"
        for app in os.listdir(app_dir):
            if os.path.isdir(os.path.join(app_dir, app)):
                icon_path = os.path.join(app_dir, app, "icon.png")
                apps.append({"name": app, "icon": icon_path})
        return True
    except FileNotFoundError:
        print("IA: Apps directory not found. No apps will be loaded.")
        return False
    except Exception as e:
        print(f"IA: Error initializing apps: {e}")
        return False

# Handles app starting and running
def main():
    initialize()

if __name__ == "__main__":
    main()