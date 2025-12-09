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

apps = [] # List of apps found in the apps directory
version = "v0.0.0" # The current version of the app
wallpaper = "None" # The current wallpaper setting
active_apps = {} # Dict to track running app instances
webview_window = None # Reference to the main webview window


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
        
        inject_script = f"""
        // Create app container
        const appContainer = document.createElement('div');
        appContainer.id = '{app_container_id}';
        appContainer.className = 'app-container';
        appContainer.style.cssText = `
            position: fixed;
            top: 10%;
            left: 10%;
            width: 80%;
            height: 80%;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            z-index: 1000;
            overflow: auto;
            padding: 20px;
        `;
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 15px;
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            z-index: 1001;
        `;
        closeBtn.onclick = function() {{
            document.body.removeChild(appContainer);
            // Signal Python backend to stop the app
            window.pywebview.api.stop_app('{app_name}');
        }};
        
        // Add app HTML content
        appContainer.innerHTML = `{app_html.replace('`', '\\`').replace('${', '\\${')}`; 
        appContainer.appendChild(closeBtn);
        
        // Add to DOM
        document.body.appendChild(appContainer);
        
        // Signal that app UI is loaded
        console.log('App {app_name} UI loaded');
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
        class API:
            def launch_app(self, app_name):
                return launch_app(app_name)
            
            def stop_app(self, app_name):
                return stop_app(app_name)
            
            def get_apps(self):
                return apps
            
            def get_running_apps(self):
                return get_running_apps()
        
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
        #webview.start()
        webview.start(debug=True)
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

# API for managing apps within the environment
class AppManagerAPI:
    # Lists all initialized apps
    def list_apps(self):
        global apps
        return apps

# Handles app starting and running  
def main():
    initialize()

if __name__ == "__main__":
    main()