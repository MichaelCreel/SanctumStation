################################################################################
# Python Backend for Sanctum Station
# This file handles logic for the psuedo-desktop environment to be used.
################################################################################

import webview
import yaml
import os

apps = [] # List of apps found in the apps directory
version = "v0.0.0" # The current version of the app
wallpaper = "None" # The current wallpaper setting


# Handles initialization of app components
def initialize():
    if not init_settings():
        print("WARNING: Failed to initialize settings. Using default settings.\n\nWARNING 0")
    if not init_apps():
        print("WARNING: No apps found to initialize. No apps will be loaded.\n\nWARNING 1")
    if not init_webview():
        print("FATAL: Failed to initialize webview.\n\nFATAL 0")
        return False

# Initializes environment settings
def init_settings():
    global version, wallpaper
    try:
        with open("data/settings.yaml", "r") as file:
            settings = yaml.safe_load(file) or {}
        
        if "version" in settings:
            version = settings["version"]
        if "wallpaper" in settings:
            wallpaper = settings["wallpaper"]
        
        print(f"IS: Settings loaded:\n    -version={version}\n    -wallpaper={wallpaper}")
        return True
    except FileNotFoundError:
        print("IS: Settings file not found. Using default settings.")
        return False
    except yaml.YAMLError as e:
        print(f"IS: Error parsing YAML file: {e}")
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

# Initializes webview
def init_webview():
    try:
        webview.create_window("Sanctum Station", "http://localhost:8000", width=1280, height=720)
        webview.start()
        return True
    except Exception as e:
        print(f"IW: Error initializing webview: {e}")
        return False

# Handles app starting and running
def main():
    initialize()

# API for file management between the app and the system(s)
class FileManagerAPI:
    # Lists the contents of a directory
    def list_dir(self, path):
        try:
            items = os.listdir(path)
            return items
        except Exception as e:
            print(f"FMAPI LD: Error listing directory {path}: {e}")
            return []

    # Reads the contents of a file
    def read_file(self, path):
        try:
            with open(path, "r") as file:
                content = file.read()
            return content
        except Exception as e:
            print(f"FMAPI RF: Error reading file {path}: {e}")
            return ""
        
    # Writes content to a file
    def write_file(self, path, content):
        try:
            with open(path, "w") as file:
                file.write(content)
            return True
        except Exception as e:
            print(f"FMAPI WF: Error writing file {path}: {e}")
            return False
        
    # Deletes a file
    def delete_file(self, path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"FMAPI DF: Error deleting file {path}: {e}")
            return False
    
    # Creates a directory
    def create_dir(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"FMAPI CD: Error creating directory {path}: {e}")
            return False
    
    # Deletes a directory
    def delete_dir(self, path):
        try:
            os.rmdir(path)
            return True
        except Exception as e:
            print(f"FMAPI DD: Error deleting directory {path}: {e}")
            return False
    
    # Moves a file or directory
    def move(self, src, dest):
        try:
            os.rename(src, dest)
            return True
        except Exception as e:
            print(f"FMAPI M: Error moving {src} to {dest}: {e}")
            return False
        
    # Copies a file
    def copy(self, src, dest):
        try:
            import shutil
            shutil.copy2(src, dest)
            return True
        except Exception as e:
            print(f"FMAPI C: Error copying {src} to {dest}: {e}")
            return False
    
    # Renames a file or directory
    def rename(self, src, new_name):
        try:
            base_dir = os.path.dirname(src)
            dest = os.path.join(base_dir, new_name)
            os.rename(src, dest)
            return True
        except Exception as e:
            print(f"FMAPI R: Error renaming {src} to {new_name}: {e}")
            return False
        
    # Gets file or directory metadata
    def get_metadata(self, path):
        try:
            stats = os.stat(path)
            metadata = {
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "created": stats.st_ctime,
                "is_directory": os.path.isdir(path)
            }
            return metadata
        except Exception as e:
            print(f"FMAPI GM: Error getting metadata for {path}: {e}")
            return {}
        
    # Checks if a file or directory exists
    def exists(self, path):
        return os.path.exists(path)
    
    # Creates an empty file
    def create_file(self, path):
        try:
            with open(path, "w") as file:
                pass
            return True
        except Exception as e:
            print(f"FMAPI CF: Error creating file {path}: {e}")
            return False

if __name__ == "__main__":
    main()