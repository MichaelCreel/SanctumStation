################################################################################
# Python Backend for Sanctum Station
# This file handles logic for the psuedo-desktop environment to be used.
################################################################################

import webview
import yaml
import os
import threading
import importlib.util
import sys
import requests
import time
import inspect

apps = [] # List of apps found in the apps directory
version = "v0.0.0" # The current version of the app
updates = "release" # Update preference: "release" or "all"
wallpaper = "None" # The current wallpaper setting
day_gradient = True # Whether to include the time of day gradient overlay on the desktop
fonts = {} # Dictionary of font weights
available_update = None  # Stores update info if available
active_apps = {} # Dict to track running app instances
webview_window = None # Reference to the main webview window
fullscreen = False # Whether the app is in fullscreen mode or not


# Handles initialization of app components
def initialize():
    global available_update
    if not init_settings():
        print("WARNING: Failed to initialize settings. Using default settings.\n\nWARNING 0")
    if not init_apps():
        print("WARNING: No apps found to initialize. No apps will be loaded.\n\nWARNING 1")
    
    # Check for updates
    available_update = check_for_updates()
    
    if not init_webview():
        print("FATAL: Failed to initialize webview.\n\nFATAL 0")
        return False

# Initializes environment settings
def init_settings():
    global version, wallpaper, fonts, updates, day_gradient, fullscreen
    try:
        with open("data/settings.yaml", "r") as file:
            settings = yaml.safe_load(file) or {}
        
        if "version" in settings:
            version = settings["version"]
        if "wallpaper" in settings:
            wallpaper = settings["wallpaper"]
        if "day_gradient" in settings:
            day_gradient = settings["day_gradient"]
        if "updates" in settings:
            updates = settings["updates"]
        if "fullscreen" in settings:
            fullscreen = settings["fullscreen"]
        
        # Load all font weights
        font_keys = ['black_font', 'extra_bold_font', 'bold_font', 'semi_bold_font', 
                     'medium_font', 'regular_font', 'light_font', 'extra_light_font', 'thin_font']
        for key in font_keys:
            if key in settings:
                fonts[key] = settings[key]
        print(f"IS: Settings loaded:\n    -version={version}\n    -wallpaper={wallpaper}\n    -fonts={len(fonts)} weights\n    -updates={updates}\n    -day_gradient={day_gradient}\n    -fullscreen={fullscreen}")
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
        # Apps are now in src/apps/ so they can be served by the webview HTTP server
        app_dir = os.path.join(os.path.dirname(__file__), "apps")
        for app in os.listdir(app_dir):
            if os.path.isdir(os.path.join(app_dir, app)):
                app_path = os.path.join(app_dir, app)
                icon_path = os.path.join(app_path, "icon.png")
                html_path = os.path.join(app_path, "app.html")
                py_path = os.path.join(app_path, "app.py")
                
                if os.path.exists(html_path) and os.path.exists(py_path):
                    # Use simple relative path from src/ directory
                    icon_url = None
                    if os.path.exists(icon_path):
                        icon_url = f"apps/{app}/icon.png"
                        print(f"IA: Icon URL for {app}: {icon_url}")
                    apps.append({
                        "name": app,
                        "icon": icon_url,
                        "htmlpath": html_path,
                        "pypath": py_path,
                        "app_dir": os.path.abspath(app_path)  # Use absolute path for backend
                    })
                    print(f"IA: Added app '{app}' with icon: {icon_url}")
                else:
                    print(f"IA: App '{app}' missing required files (app.html or app.py)")
        
        print(f"IA: Found {len(apps)} valid apps")
        return True
    except FileNotFoundError:
        print("IA: Apps directory not found. No apps will be loaded.")
        return False
    except Exception as e:
        print(f"IA: Error initializing apps: {e}")
        return False

# Launches an app
def launch_app(app_name):
    global active_apps, webview_window
    
    app_info = None
    for app in apps:
        if app["name"] == app_name:
            app_info = app
            break
    
    if not app_info:
        print(f"LA: App '{app_name}' not found")
        return False
    
    try:
        with open(app_info["htmlpath"], "r", encoding="utf-8") as f:
            app_html = f.read()
        
        app_container_id = f"app-{app_name}-{id(app_info)}"
        
        # Use JSON to safely pass the HTML content
        import json
        app_html_escaped = json.dumps(app_html)
        
        inject_script = f"""
        (function() {{
            const appHtml = {app_html_escaped};
            
            // Create app container
        const appContainer = document.createElement('div');
        appContainer.id = '{app_container_id}';
        appContainer.className = 'app-container';
        appContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #1e1e2e;
            z-index: 1000;
            overflow: auto;
        `;
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.style.cssText = `
            position: fixed;
            top: 10px;
            right: 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            color: white;
            font-size: 24px;
            cursor: pointer;
            z-index: 1001;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s ease;
        `;
        closeBtn.onmouseover = function() {{
            this.style.background = 'rgba(255, 255, 255, 0.2)';
        }};
        closeBtn.onmouseout = function() {{
            this.style.background = 'rgba(255, 255, 255, 0.1)';
        }};
        closeBtn.onclick = function() {{
            document.body.removeChild(appContainer);
            // Signal Python backend to stop the app
            window.pywebview.api.stop_app('{app_name}');
        }};
        
        // Parse and inject app HTML content
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = appHtml;
        
        // Extract scripts to execute them separately (innerHTML doesn't execute scripts)
        const scripts = tempDiv.querySelectorAll('script');
        const scriptContents = [];
        scripts.forEach(script => {{
            scriptContents.push(script.textContent);
            script.remove(); // Remove from tempDiv so we don't double-inject
        }});
        
        // Add the HTML content (without scripts)
        appContainer.innerHTML = tempDiv.innerHTML;
        appContainer.appendChild(closeBtn);
        
        // Add to DOM
        document.body.appendChild(appContainer);
        
        // Execute scripts in isolated scope to prevent variable conflicts
        scriptContents.forEach(scriptContent => {{
            const script = document.createElement('script');
            // Don't wrap in IIFE - let scripts manage their own scope
            // Scripts should attach functions to window if they need onclick handlers
            script.textContent = scriptContent;
            document.body.appendChild(script);
        }});
        
        // Signal that app UI is loaded
        console.log('App {app_name} UI loaded');
        }})();
        """
        
        if webview_window:
            webview_window.evaluate_js(inject_script)
        
        if app_name not in active_apps:
            # Create stop event for this app
            stop_event = threading.Event()
            app_thread = threading.Thread(
                target=run_app_backend, 
                args=(app_name, app_info["pypath"], app_info["app_dir"], stop_event),
                daemon=True
            )
            app_thread.start()
            active_apps[app_name] = {
                "thread": app_thread,
                "container_id": app_container_id,
                "stop_event": stop_event
            }
        
        print(f"LA: Successfully launched app '{app_name}'")
        return True
        
    except Exception as e:
        print(f"LA: Error launching app '{app_name}': {e}")
        return False

# Runs the backend logic of an app
def run_app_backend(app_name, py_path, app_dir, stop_event):
    try:
        original_cwd = os.getcwd()
        # app_dir is already absolute, so use it directly
        os.chdir(app_dir)
        # py_path needs to be absolute or relative to app_dir
        py_file = os.path.join(app_dir, "app.py") if not os.path.isabs(py_path) else py_path
        spec = importlib.util.spec_from_file_location(f"app_{app_name}", py_file)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules[f"app_{app_name}"] = app_module
        spec.loader.exec_module(app_module)
        
        # Pass stop_event to app's main/run function if it accepts it
        if hasattr(app_module, 'main'):
            import inspect
            sig = inspect.signature(app_module.main)
            if len(sig.parameters) > 0:
                app_module.main(stop_event)
            else:
                app_module.main()
        elif hasattr(app_module, 'run'):
            import inspect
            sig = inspect.signature(app_module.run)
            if len(sig.parameters) > 0:
                app_module.run(stop_event)
            else:
                app_module.run()
        
        print(f"RAB: App '{app_name}' backend finished")
        
    except Exception as e:
        print(f"RAB: Error running app '{app_name}' backend: {e}")
    finally:
        os.chdir(original_cwd)
        if app_name in active_apps:
            del active_apps[app_name]

def stop_app(app_name):
    global active_apps
    
    if app_name in active_apps:
        print(f"SA: Stopping app '{app_name}'")
        # Signal the app to stop
        if "stop_event" in active_apps[app_name]:
            active_apps[app_name]["stop_event"].set()
        del active_apps[app_name]
        return True
    
    return False

def get_running_apps():
    return list(active_apps.keys())

# Initializes webview
def init_webview():
    global webview_window
    try:
        # Create file manager instance
        file_manager = FileManagerAPI()
        settings_manager = SettingsManagerAPI()
        notification_manager = NotificationManagerAPI()
        
        class API:
            def launch_app(self, app_name):
                return launch_app(app_name)
            
            def stop_app(self, app_name):
                return stop_app(app_name)
            
            def get_apps(self):
                return apps
            
            def get_running_apps(self):
                return get_running_apps()
            
            # Notification Management - Delegate to NotificationManagerAPI
            def send_notification(self, message):
                return notification_manager.send_notification(message)
            
            def delete_notification(self, notification_id):
                return notification_manager.delete_notification(notification_id)
            
            def get_notifications(self):
                return notification_manager.get_notifications()
            
            def clear_all_notifications(self):
                return notification_manager.clear_all_notifications()

            # File Management - Delegate to FileManagerAPI
            def list_directory(self, path):
                return file_manager.list_directory(path)
            
            def read_file(self, path):
                return file_manager.read_file(path)
            
            def write_file(self, path, content):
                return file_manager.write_file(path, content)
            
            def delete_file(self, path):
                return file_manager.delete_file(path)
            
            def delete_directory(self, path):
                return file_manager.delete_directory(path)
            
            def create_directory(self, path):
                return file_manager.create_directory(path)
            
            def create_file(self, path):
                return file_manager.create_file(path)
            
            def rename_item(self, old_path, new_name):
                return file_manager.rename_item(old_path, new_name)
            
            def move_item(self, src, dest):
                return file_manager.move_item(src, dest)
            
            def copy_item(self, src, dest):
                return file_manager.copy_item(src, dest)
            
            def get_metadata(self, path):
                return file_manager.get_metadata(path)
            
            def exists(self, path):
                return file_manager.exists(path)
            
            # Settings access
            def get_fonts(self):
                global fonts
                return fonts
            
            def get_version(self):
                global version
                return version
            
            def get_wallpaper(self):
                global wallpaper
                return wallpaper
            
            def get_wallpaper_data(self):
                return settings_manager.get_wallpaper_data()
            
            def get_day_gradient(self):
                global day_gradient
                return day_gradient
            
            def get_fullscreen(self):
                global fullscreen
                return fullscreen
            
            # Settings Management - Delegate to SettingsManagerAPI
            def get_settings(self):
                return settings_manager.get_settings()
            
            def set_wallpaper(self, wallpaper_path):
                return settings_manager.set_wallpaper(wallpaper_path)
            
            def set_day_gradient(self, enabled):
                return settings_manager.set_day_gradient(enabled)
            
            def set_fullscreen(self, enabled):
                return settings_manager.set_fullscreen(enabled)
            
            def set_font(self, weight, font_path):
                return settings_manager.set_font(weight, font_path)
            
            def set_updates(self, channel):
                return settings_manager.set_updates(channel)
            
            def get_available_update(self):
                global available_update
                return available_update
            
            # Generic app function call - allows apps to expose their own API
            def call_app_function(self, app_name, function_name, *args, **kwargs):
                try:
                    module_name = f"app_{app_name}"
                    if module_name not in sys.modules:
                        return {"success": False, "message": f"App '{app_name}' not running"}
                    
                    app_module = sys.modules[module_name]
                    
                    if not hasattr(app_module, function_name):
                        return {"success": False, "message": f"Function '{function_name}' not found in app '{app_name}'"}
                    
                    func = getattr(app_module, function_name)
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    return {"success": False, "message": f"Error calling {function_name}: {str(e)}"}

        
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
        
        if not os.path.exists(html_path):
            print(f"IW: Error - index.html not found at {html_path}")
            return False
        
        webview_window = webview.create_window(
            "Sanctum Station", 
            html_path,
            width=1280, 
            height=720,
            js_api=API()
        )
        
        # Set window icon for GTK
        try:
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "logo_solid.png"))
            if os.path.exists(icon_path):
                # This will be set when the window is created by GTK
                webview_window.icon = icon_path
        except Exception as e:
            print(f"Warning: Could not set window icon: {e}")
        
        #webview.start()
        webview.start(debug=True, func=on_webview_ready)
        return True
    except Exception as e:
        print(f"IW: Error initializing webview: {e}")
        return False

def on_webview_ready():
    """Called when webview is ready - apply initial fullscreen setting"""
    global fullscreen, webview_window
    if fullscreen and webview_window:
        print("Applying fullscreen setting from startup...")
        webview_window.toggle_fullscreen()

# Handles app starting and running
def main():
    initialize()

# Shared notifications storage at module level
_notifications = {}

class NotificationManagerAPI:
    def send_notification(self, message):
        global _notifications
        # Trace back through the call stack to find which app module called this
        calling_app = "System"  # Default if we can't identify the app
        
        for frame_info in inspect.stack():
            frame_module = inspect.getmodule(frame_info.frame)
            if frame_module and hasattr(frame_module, '__name__'):
                module_name = frame_module.__name__
                # Check if this is an app module (starts with "app_")
                if module_name.startswith("app_"):
                    calling_app = module_name[4:]  # Remove "app_" prefix
                    break
        
        notification_id = str(int(time.time() * 1000))
        _notifications[notification_id] = {
            "message": message,
            "timestamp": time.time(),
            "source": calling_app
        }
        print(f"Notification sent: {calling_app} - {message} (ID: {notification_id})")
        print(f"Total notifications: {len(_notifications)}")
        print(f"Notifications dict id: {id(_notifications)}")
        return {"success": True, "notification_id": notification_id, "source": calling_app}
    
    def delete_notification(self, notification_id):
        global _notifications
        if notification_id in _notifications:
            del _notifications[notification_id]
            return {"success": True}
        else:
            return {"success": False, "error": "Notification ID not found"}
    
    def get_notifications(self):
        global _notifications
        # Return all notifications with their IDs
        print(f"Getting notifications: {len(_notifications)} total")
        print(f"Notifications dict id: {id(_notifications)}")
        return {
            "success": True,
            "notifications": [
                {"id": nid, **ndata}
                for nid, ndata in _notifications.items()
            ]
        }
    
    def clear_all_notifications(self):
        global _notifications
        _notifications.clear()
        return {"success": True}

# API for file management between the app and the system(s)
class FileManagerAPI:
    # Lists contents of a directory
    def list_directory(self, path):
        try:
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                try:
                    stat_info = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    items.append({
                        'name': item,
                        'path': full_path,
                        'type': 'folder' if is_dir else 'file',
                        'size': 0 if is_dir else stat_info.st_size,
                        'modified': int(stat_info.st_mtime * 1000)
                    })
                except (OSError, PermissionError) as e:
                    print(f"FMAPI: Skipping {full_path}: {e}")
                    continue
            return items
        except Exception as e:
            print(f"FMAPI: Error listing directory {path}: {e}")
            return []

    # Reads the contents of a file
    def read_file(self, path):
        try:
            with open(path, "r") as file:
                return file.read()
        except Exception as e:
            print(f"FMAPI: Error reading file {path}: {e}")
            return ""
        
    # Writes content to a file
    def write_file(self, path, content):
        try:
            with open(path, "w") as file:
                file.write(content)
            return True
        except Exception as e:
            print(f"FMAPI: Error writing file {path}: {e}")
            return False
        
    # Deletes a file
    def delete_file(self, path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"FMAPI: Error deleting file {path}: {e}")
            return False
    
    # Deletes a directory
    def delete_directory(self, path):
        try:
            import shutil
            shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"FMAPI: Error deleting directory {path}: {e}")
            return False
    
    # Creates a directory
    def create_directory(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"FMAPI: Error creating directory {path}: {e}")
            return False
    
    # Creates an empty file
    def create_file(self, path):
        try:
            with open(path, "w") as file:
                pass
            return True
        except Exception as e:
            print(f"FMAPI: Error creating file {path}: {e}")
            return False
    
    # Renames a file or directory
    def rename_item(self, old_path, new_name):
        try:
            base_dir = os.path.dirname(old_path)
            new_path = os.path.join(base_dir, new_name)
            os.rename(old_path, new_path)
            return {'success': True, 'new_path': new_path}
        except Exception as e:
            print(f"FMAPI: Error renaming {old_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    # Moves a file or directory
    def move_item(self, src, dest):
        try:
            import shutil
            shutil.move(src, dest)
            return True
        except Exception as e:
            print(f"FMAPI: Error moving {src} to {dest}: {e}")
            return False
        
    # Copies a file or directory
    def copy_item(self, src, dest):
        try:
            import shutil
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            return True
        except Exception as e:
            print(f"FMAPI: Error copying {src} to {dest}: {e}")
            return False
        
    # Gets file or directory metadata
    def get_metadata(self, path):
        try:
            stats = os.stat(path)
            return {
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "created": stats.st_ctime,
                "is_directory": os.path.isdir(path)
            }
        except Exception as e:
            print(f"FMAPI: Error getting metadata for {path}: {e}")
            return {}

    # Checks if a file or directory exists
    def exists(self, path):
        return os.path.exists(path)
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

# API for managing apps within the environment
class AppManagerAPI:
    # Lists all initialized apps
    def list_apps(self):
        global apps
        return apps

class SettingsManagerAPI:
    # Gets current settings
    def get_settings(self):
        global version, wallpaper, fonts, day_gradient, updates, fullscreen
        return {
            "wallpaper": wallpaper,
            "fonts": fonts,
            "day_gradient": day_gradient,
            "updates": updates,
            "fullscreen": fullscreen
        }
    
    def get_wallpaper_data(self):
        """Read wallpaper file and return as base64 data URL"""
        global wallpaper
        import base64
        import mimetypes
        
        if not wallpaper or wallpaper.lower() == 'none':
            return None
        
        try:
            # Get the mime type
            mime_type, _ = mimetypes.guess_type(wallpaper)
            if not mime_type:
                mime_type = 'image/png'  # Default to PNG
            
            # Read the file as binary
            with open(wallpaper, 'rb') as f:
                image_data = f.read()
            
            # Encode to base64
            b64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Return as data URL
            return f"data:{mime_type};base64,{b64_data}"
        except Exception as e:
            print(f"SettingsManagerAPI: Error reading wallpaper file: {e}")
            return None
    
    def set_wallpaper(self, wallpaper_path):
        global wallpaper
        wallpaper = wallpaper_path
        # Write to settings.yaml
        try:
            with open("data/settings.yaml", "r") as file:
                settings = yaml.safe_load(file) or {}
            settings["wallpaper"] = wallpaper_path
            with open("data/settings.yaml", "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SettingsManagerAPI: Error setting wallpaper: {e}")
            return False
        return True
    
    def set_day_gradient(self, enabled):
        global day_gradient
        day_gradient = enabled
        # Write to settings.yaml
        try:
            with open("data/settings.yaml", "r") as file:
                settings = yaml.safe_load(file) or {}
            settings["day_gradient"] = enabled
            with open("data/settings.yaml", "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SettingsManagerAPI: Error setting day_gradient: {e}")
            return False
        return True
    
    def set_fullscreen(self, enabled):
        global fullscreen, webview_window
        fullscreen = enabled
        
        # Actually toggle the pywebview window fullscreen
        if webview_window:
            webview_window.toggle_fullscreen()
        
        # Write to settings.yaml
        try:
            with open("data/settings.yaml", "r") as file:
                settings = yaml.safe_load(file) or {}
            settings["fullscreen"] = enabled
            with open("data/settings.yaml", "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SettingsManagerAPI: Error setting fullscreen: {e}")
            return False
        return True
    
    def set_font(self, weight, font_path):
        global fonts
        fonts[weight] = font_path
        # Write to settings.yaml
        try:
            with open("data/settings.yaml", "r") as file:
                settings = yaml.safe_load(file) or {}
            settings[f"{weight}_font"] = font_path
            with open("data/settings.yaml", "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SettingsManagerAPI: Error setting font {weight}: {e}")
            return False
        return True
    
    def set_updates(self, channel):
        global updates
        updates = channel
        # Write to settings.yaml
        try:
            with open("data/settings.yaml", "r") as file:
                settings = yaml.safe_load(file) or {}
            settings["updates"] = channel
            with open("data/settings.yaml", "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SettingsManagerAPI: Error setting updates: {e}")
            return False
        return True

# Check if it is a newer version
def is_newer_version(installed, latest):
    def version_tuple(v):
        return tuple(map(int, (v.lstrip('v').split("."))))
    
    return version_tuple(latest) > version_tuple(installed)

# Check for updates
def check_for_updates():
    global version, updates
    url = "https://api.github.com/repos/MichaelCreel/SanctumStation/releases"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            releases = response.json()
            latest_release = releases[0]
            latest_version = "v" + latest_release["tag_name"]
            is_prerelease = latest_release["prerelease"]
            release_type = "Pre-release" if is_prerelease else "Stable Release"
            download_url = latest_release["html_url"]
            description = latest_release.get("body", "No description available.")

            print(f"Latest Version: {latest_version} ({release_type}) - {download_url}")

            if is_newer_version(version, latest_version):
                if updates == "release" and is_prerelease:
                    print("Prerelease skipped by preference.")
                    return None
                else:
                    print(f"Update available: {latest_version}, {release_type}")
                    return {
                        "version": latest_version,
                        "type": release_type,
                        "url": download_url,
                        "description": description
                    }
            else:
                print("No updates available.")
            return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None

# Handles app starting and running  
def main():
    initialize()

if __name__ == "__main__":
    main()