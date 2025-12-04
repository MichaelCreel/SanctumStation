################################################################################
# Python Backend for Sanctum Station
# This file handles logic for the psuedo-desktop environment to be used.
################################################################################

import webview

# Handles initialization of app components
def initialize():
    init_webview()

# Initializes webview
def init_webview():
    webview.create_window("Sanctum Station", "http://localhost:8000", width=1280, height=720)
    webview.start()

# Initializes environment settings
def init_settings():
    settings = file("data/settings.yaml", "r").read()

# Handles app starting and running
def main():
    initialize()

if __name__ == "__main__":
    main()