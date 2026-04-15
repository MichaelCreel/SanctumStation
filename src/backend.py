################################################################################
# Python Backend for Sanctum Station
# This file handles logic for the psuedo-desktop environment to be used.
################################################################################

import json
import os
import base64
import threading
import importlib.util
import sys
import time
import inspect
import concurrent.futures
import mimetypes
import uuid
import queue
import webbrowser
import psutil
from urllib.parse import urlparse
from fuzzywuzzy import process as fuzzy_process

sys.modules.setdefault("backend", sys.modules[__name__])

# Determine platform early (before importing yaml)
IS_MOBILE = (
    hasattr(sys, 'getandroidapilevel') or  # Android
    sys.platform == 'ios' or  # iOS
    'briefcase' in sys.modules or  # BeeWare
    any(keyword in sys.platform.lower() for keyword in ['android', 'samsung'])  # Android variants
)

# Import yaml and force pure Python on mobile (no C extensions)
import yaml
if IS_MOBILE:
    # Force pure Python implementation on mobile
    from yaml import SafeLoader, SafeDumper
    yaml_loader = SafeLoader
    print("Using pure Python YAML loader for mobile")
else:
    # Try to use C loader on desktop for speed, fall back to pure Python
    try:
        from yaml import CSafeLoader as yaml_loader
        print("Using C-optimized YAML loader")
    except ImportError:
        from yaml import SafeLoader as yaml_loader
        print("Using pure Python YAML loader")

# Import requests (needed for update checking)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available, update checking disabled")

MAX_ERROR_LOG_SIZE = 2 * 1024 * 1024  # 2 MB
MAX_FILE_DATA_URL_BYTES = 100 * 1024 * 1024  # 100 MB

# Get the base directory (where backend.py is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# On mobile: BASE_DIR is ...sanctumstation/, data is at <writable location> (set by app.py)
# On desktop: BASE_DIR is .../src, data is at ../data
DATA_DIR = os.path.join(BASE_DIR, "data") if IS_MOBILE else os.path.join(os.path.dirname(BASE_DIR), "data")
APPS_DIR = os.path.join(BASE_DIR, "apps") if IS_MOBILE else os.path.join(BASE_DIR, "apps")

# Note: On mobile, DATA_DIR and APPS_DIR will be overridden by app.py to use writable storage
print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR (initial): {DATA_DIR}")
print(f"APPS_DIR (initial): {APPS_DIR}")

apps = [] # List of apps found in the apps directory
app_names = [] # List of app names
version = "v0.0.0" # The current version of the app
updates = "release" # Update preference: "release" or "all"
wallpaper = "None" # The current wallpaper setting
day_gradient = True # Whether to include the time of day gradient overlay on the desktop
logo = "default" # Logo preference: "default" or "solid"
fonts = {} # Dictionary of font weights
available_update = None  # Stores update info if available
active_apps = {} # Dict to track running app instances
webview_window = None # Reference to the main webview window
main_event_loop = None # Reference to the main event loop (for mobile async calls)
fullscreen = False # Whether the app is in fullscreen mode or not
ui_scale = 1.0 # UI scale multiplier (1.0 = 16px base font, 100%)
notification_bind = "Ctrl+N" # Keyboard shortcut for opening the notification panel
command_palette_bind = "Ctrl+Space" # Keyboard shortcut for opening the command palette
apps_per_ring = 8 # Number of apps to show per ring in the app wheel
reduce_graphics = "level_0" # The level of graphics reduction to apply (0 = none, 1 = no gradients, 2 = 1 + no transparency)
color_theme = "dark" # Color theme for the UI (dark or light)
extension_support = {} # Cache for which apps support which file extensions.

SUPPORTED_WALLPAPER_EXTENSIONS = sorted([
    ".avif", ".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"
])
SUPPORTED_FONT_EXTENSIONS = [".ttf"]
SUPPORTED_FONT_KEYS = {
    "black_font", "extra_bold_font", "bold_font", "semi_bold_font",
    "medium_font", "regular_font", "light_font", "extra_light_font", "thin_font"
}


def open_external_url(url):
    target_url = str(url or "").strip()
    if not target_url:
        return False

    parsed = urlparse(target_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    try:
        opened = webbrowser.open(target_url, new=2)
        return bool(opened)
    except Exception as e:
        print(f"OEU-E1: Error opening external URL: {e}")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("OEU-E1")')
        return False


def _resolve_configured_path(path_value):
    if path_value is None:
        return None

    raw_path = str(path_value).strip()
    if not raw_path:
        return None

    if raw_path.startswith("src:"):
        return os.path.normpath(os.path.join(BASE_DIR, raw_path[4:]))

    expanded_path = os.path.expanduser(raw_path)
    if os.path.isabs(expanded_path):
        return os.path.normpath(expanded_path)

    return os.path.normpath(os.path.join(BASE_DIR, expanded_path))

if IS_MOBILE:
    import toga
    print("Running on mobile platform")
else:
    import webview
    print("Running on desktop platform")

# Handles the initialization of the environment components and apps
# This initializes both essential and non-essential components
# Called on startup of the backend
def initialize():
    global available_update
    if not init_settings():
        print("WARNING: Failed to initialize settings. Using default settings.\n\nWARNING 0")
    if not init_apps():
        print("WARNING: No apps found to initialize. No apps will be loaded.\n\nWARNING 1")
    
    # Check for updates
    available_update = check_for_updates()
    
    # Only initialize webview on desktop
    if not IS_MOBILE:
        if not init_webview():
            print("FATAL: Failed to initialize webview.\n\nFATAL 0")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js(f'displayError("FATAL 0")')
            return False
    else:
        print("Mobile platform detected - skipping webview initialization")
        return True

# Initializes the environment settings from data/settings.yaml
# Returns True on success, False on failure
def init_settings():
    global version, wallpaper, fonts, updates, day_gradient, fullscreen, logo, ui_scale, notification_bind, command_palette_bind, apps_per_ring, reduce_graphics, color_theme
    try:
        settings_path = os.path.join(DATA_DIR, "settings.yaml")
        print(f"Loading settings from: {settings_path}")
        with open(settings_path, "r") as file:
            settings = yaml.load(file, Loader=yaml_loader) or {}
        
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
        if "logo" in settings:
            logo = settings["logo"]
        if "ui_scale" in settings:
            ui_scale = float(settings["ui_scale"])
        if "notification_bind" in settings:
            notification_bind = settings["notification_bind"]
        if "command_palette_bind" in settings:
            command_palette_bind = settings["command_palette_bind"]
        if "apps_per_ring" in settings:
            apps_per_ring = int(settings["apps_per_ring"])
        if "reduce_graphics" in settings:
            reduce_graphics = settings["reduce_graphics"]
        if "color_theme" in settings:
            color_theme = settings["color_theme"]
        
        # Load all font weights
        font_keys = ['black_font', 'extra_bold_font', 'bold_font', 'semi_bold_font', 
                     'medium_font', 'regular_font', 'light_font', 'extra_light_font', 'thin_font']
        for key in font_keys:
            if key in settings:
                fonts[key] = settings[key]
        print(f"IS: Settings loaded:\n    -version={version}\n    -wallpaper={wallpaper}\n    -fonts={len(fonts)} weights\n    -updates={updates}\n    -day_gradient={day_gradient}\n    -fullscreen={fullscreen}\n    -logo={logo}\n    -ui_scale={ui_scale}\n    -notification_bind={notification_bind}\n    -command_palette_bind={command_palette_bind}\n    -apps_per_ring={apps_per_ring}\n    -reduce_graphics={reduce_graphics}\n    -color_theme={color_theme}\n")
        return True
    except FileNotFoundError:
        print("IS-E1: Settings file not found. Using default settings.")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("IS-E1")')
        return False
    except yaml.YAMLError as e:
        print(f"IS-E2: Error parsing YAML file: {e}")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("IS-E2")')
        return False
    except Exception as e:
        print(f"IS-E3: Error reading settings file: {e}")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("IS-E3")')
        return False

# Initializes apps from apps/ directory
# Returns True on success, False on failure
def init_apps():
    global apps, app_names, extension_support
    apps = []
    app_names = []
    extension_support = {}
    try:
        import os
        # Use APPS_DIR which points to writable location on mobile
        app_dir = APPS_DIR
        print(f"IA: Scanning apps directory: {app_dir}")
        dir_contents = sorted(os.listdir(app_dir))
        print(f"IA: Found {len(dir_contents)} items: {dir_contents}")
        for app in dir_contents:
            if os.path.isdir(os.path.join(app_dir, app)):
                app_path = os.path.join(app_dir, app)
                icon_path = os.path.join(app_path, "icon.png")
                html_path = os.path.join(app_path, "app.html")
                py_path = os.path.join(app_path, "app.py")
                config_path = os.path.join(app_path, "app_config.json")
                
                if os.path.exists(html_path) and os.path.exists(py_path):
                    app_name = app
                    extensions = []
                    mime_types = []

                    if os.path.exists(config_path):
                        try:
                            with open(config_path, "r", encoding="utf-8") as config_file:
                                app_config = json.load(config_file) or {}

                            if isinstance(app_config, dict):
                                config_name = app_config.get("name")
                                if isinstance(config_name, str) and config_name.strip():
                                    app_name = config_name.strip()

                                config_extensions = app_config.get("extensions", [])
                                if isinstance(config_extensions, list):
                                    extensions = sorted({
                                        ext.strip().lower()
                                        for ext in config_extensions
                                        if isinstance(ext, str) and ext.strip()
                                    })

                                    for ext in extensions:
                                        if ext not in extension_support:
                                            extension_support[ext] = []
                                        if app not in extension_support[ext]:
                                            extension_support[ext].append(app)

                                config_mime_types = app_config.get("mime_types", [])
                                if isinstance(config_mime_types, list):
                                    mime_types = sorted({
                                        mime.strip().lower()
                                        for mime in config_mime_types
                                        if isinstance(mime, str) and mime.strip()
                                    })
                        except Exception as config_error:
                            print(f"IA: Warning - failed to parse app_config.json for '{app}': {config_error}")

                    # Use simple relative path from src/ directory
                    icon_url = None
                    if os.path.exists(icon_path):
                        icon_url = f"apps/{app}/icon.png"
                        print(f"IA: Icon URL for {app}: {icon_url}")
                    
                    apps.append({
                        "id": app,
                        "name": app_name,
                        "icon": icon_url,
                        "extensions": extensions,
                        "mime_types": mime_types,
                        "htmlpath": html_path,
                        "pypath": py_path,
                        "app_dir": os.path.abspath(app_path)  # Use absolute path for backend
                    })
                    app_names.append(app_name)
                    print(f"IA: Added app '{app_name}' (id='{app}') with icon: {icon_url}")
                else:
                    print(f"IA: App '{app}' missing required files:")
                    print(f"  App path: {app_path}")
                    print(f"  app.html exists: {os.path.exists(html_path)} - {html_path}")
                    print(f"  app.py exists: {os.path.exists(py_path)} - {py_path}")
        
        print(f"IA: Found {len(apps)} valid apps")
        print(f"IA: Found {len(extension_support)} supported extensions: {list(extension_support.keys())}")
        return True
    except FileNotFoundError:
        print("IA-E1: Apps directory not found. No apps will be loaded.")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("IA-E1")')
        return False
    except Exception as e:
        print(f"IA-E2: Error initializing apps: {e}")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("IA-E2")')
        return False

# Launches an app by finding it by its name
# Returns True on success, False on failure
# This injects the app into the webview and starts the backend thread
# This includes the code for the close button and app container
def launch_app(app_name, file_path=None):
    global active_apps, webview_window

    app_info = None
    for app in apps:
        if app.get("id") == app_name or app["name"] == app_name:
            app_info = app
            break
    
    if not app_info:
        print(f"LA: App '{app_name}' not found")
        return False

    app_id = app_info.get("id", app_name)
    app_display_name = app_info.get("name", app_id)
    
    try:
        with open(app_info["htmlpath"], "r", encoding="utf-8") as f:
            app_html = f.read()
        
        app_container_id = f"app-{app_id}-{id(app_info)}"
        
        # Use JSON to safely pass the HTML content
        import json
        app_html_escaped = json.dumps(app_html)
        launch_context_escaped = json.dumps({
            "appId": app_id,
            "appName": app_display_name,
            "filePath": file_path
        })
        
        inject_script = f"""
        (function() {{
            const appHtml = {app_html_escaped};
            const launchContext = {launch_context_escaped};

            window.__SANCTUM_LAUNCH_CONTEXT = launchContext;
            window.__SANCTUM_LAUNCH_CONTEXT_BY_APP = window.__SANCTUM_LAUNCH_CONTEXT_BY_APP || {{}};
            window.__SANCTUM_LAUNCH_CONTEXT_BY_APP[launchContext.appId] = launchContext;
            window.getSanctumLaunchContext = function(appId) {{
                if (!appId) {{
                    return window.__SANCTUM_LAUNCH_CONTEXT || null;
                }}
                return (window.__SANCTUM_LAUNCH_CONTEXT_BY_APP || {{}})[appId] || null;
            }};
            
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
            z-index: 1150;
            overflow: auto;
        `;

        appContainer.dataset.appId = launchContext.appId;
        if (launchContext.filePath) {{
            appContainer.dataset.filePath = launchContext.filePath;
        }}
        
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
            z-index: 1151;
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
            window.pywebview.api.stop_app('{app_id}');
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
        console.log('App {app_display_name} UI loaded');
        }})();
        """
        
        # Inject the script directly if webview is available
        inject_via_return = False
        print(f"LA: webview_window = {webview_window}, IS_MOBILE = {IS_MOBILE}")
        
        if webview_window and not IS_MOBILE:
            # Desktop: use direct injection via webview.evaluate_js()
            print(f"LA: Using desktop direct injection")
            try:
                webview_window.evaluate_js(inject_script)
                print(f"LA: Desktop injection successful!")
            except Exception as e:
                print(f"LA: Error with desktop injection: {e}")
                inject_via_return = True
        else:
            # Mobile: always use fallback method (return script for mobile_bridge.js to execute)
            print(f"LA: Using mobile fallback injection (returning script to HTTP)")
            inject_via_return = True
        
        # Always load the app module (even if it doesn't have main/run)
        # This allows call_app_function to work for apps that only provide API functions
        if app_id not in active_apps:
            # Load the app module first
            try:
                app_dir = app_info["app_dir"]
                py_path = app_info["pypath"]
                py_file = os.path.join(app_dir, "app.py") if not os.path.isabs(py_path) else py_path
                
                if os.path.exists(py_file):
                    spec = importlib.util.spec_from_file_location(f"app_{app_id}", py_file)
                    app_module = importlib.util.module_from_spec(spec)
                    sys.modules[f"app_{app_id}"] = app_module
                    spec.loader.exec_module(app_module)
                    
                    # Only start a backend thread if the app has main() or run()
                    if hasattr(app_module, 'main') or hasattr(app_module, 'run'):
                        stop_event = threading.Event()
                        app_thread = threading.Thread(
                            target=run_app_backend_thread, 
                            args=(app_id, app_module, stop_event, file_path),
                            daemon=True
                        )
                        app_thread.start()
                        active_apps[app_id] = {
                            "thread": app_thread,
                            "container_id": app_container_id,
                            "stop_event": stop_event
                        }
                    else:
                        # App has no background thread, just track the container
                        active_apps[app_id] = {
                            "thread": None,
                            "container_id": app_container_id,
                            "stop_event": None
                        }
            except Exception as e:
                print(f"LA: Error loading app module: {e}")
                # Continue anyway, app might still work without backend
        
        print(f"LA: Successfully launched app '{app_display_name}' (id='{app_id}')")
        
        # Only return the injection script if direct injection failed
        if inject_via_return:
            print(f"LA: Returning injection script for JavaScript to execute (length: {len(inject_script)} chars)")
            return {"success": True, "inject_script": inject_script}
        else:
            return True
        
    except Exception as e:
        print(f"LA-E1: Error launching app '{app_name}': {e}")
        if webview_window and not IS_MOBILE:
            if IS_MOBILE:
                try:
                    webview_window.evaluate_javascript('displayError("LA-E1")')
                except:
                    pass
            else:
                webview_window.evaluate_js('displayError("LA-E1")')
        return False

# Runs the backend script of the app in its own thread
# Passes a stop_event to signal when to stop
def run_app_backend(app_name, py_path, app_dir, stop_event, file_path=None):
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
        
        if hasattr(app_module, 'main'):
            _invoke_app_entrypoint(app_module.main, stop_event=stop_event, file_path=file_path)
        elif hasattr(app_module, 'run'):
            _invoke_app_entrypoint(app_module.run, stop_event=stop_event, file_path=file_path)
        
        print(f"RAB: App '{app_name}' backend finished")
        
    except Exception as e:
        print(f"RAB-E1: Error running app '{app_name}' backend: {e}")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("RAB-E1")')
    finally:
        os.chdir(original_cwd)
        if app_name in active_apps:
            del active_apps[app_name]

def _invoke_app_entrypoint(entrypoint, stop_event=None, file_path=None):
    sig = inspect.signature(entrypoint)
    kwargs = {}

    if "stop_event" in sig.parameters:
        kwargs["stop_event"] = stop_event
    if file_path is not None and "file_path" in sig.parameters:
        kwargs["file_path"] = file_path

    if kwargs:
        return entrypoint(**kwargs)

    params = list(sig.parameters.values())
    args = []

    if params:
        first_name = params[0].name.lower()
        if file_path is not None and first_name in {"file_path", "filepath", "path", "file"}:
            args.append(file_path)
        elif stop_event is not None:
            args.append(stop_event)

    if len(params) > 1 and file_path is not None:
        args.append(file_path)

    return entrypoint(*args)

# Runs the main/run function of an already-loaded app module in a thread
def run_app_backend_thread(app_name, app_module, stop_event, file_path=None):
    try:
        if hasattr(app_module, 'main'):
            _invoke_app_entrypoint(app_module.main, stop_event=stop_event, file_path=file_path)
        elif hasattr(app_module, 'run'):
            _invoke_app_entrypoint(app_module.run, stop_event=stop_event, file_path=file_path)
        
        print(f"RAB: App '{app_name}' backend finished")
        
    except Exception as e:
        print(f"RAB-E1: Error running app '{app_name}' backend: {e}")
        if webview_window and not IS_MOBILE:
            webview_window.evaluate_js('displayError("RAB-E1")')

# Stops a running app by finding it by its name
def stop_app(app_name):
    global active_apps
    
    if app_name in active_apps:
        print(f"SA: Stopping app '{app_name}'")
        # Signal the app to stop (only if it has a background thread)
        if "stop_event" in active_apps[app_name] and active_apps[app_name]["stop_event"] is not None:
            active_apps[app_name]["stop_event"].set()
        del active_apps[app_name]
        return True
    
    return False

# Returns a list of currently running apps
def get_running_apps():
    return list(active_apps.keys())

# Initializes the webview window
# Sets up the API for app interaction with the backend
def init_webview():
    global webview_window
    try:
        file_manager = FileManagerAPI()
        settings_manager = SettingsManagerAPI()
        notification_manager = NotificationManagerAPI()
        error_manager = ErrorManagerAPI()
        usage_monitor = UsageMonitorAPI()
        
        class API:
            def launch_app(self, app_name, file_path=None):
                return launch_app(app_name, file_path)
            
            def stop_app(self, app_name):
                return stop_app(app_name)
            
            def get_apps(self):
                return apps
            
            def get_running_apps(self):
                return get_running_apps()
            
            # Notification Management - Delegate to NotificationManagerAPI
            def send_notification(self, message, source=None):
                return notification_manager.send_notification(message, source)
            
            def delete_notification(self, notification_id):
                return notification_manager.delete_notification(notification_id)
            
            def get_notifications(self):
                return notification_manager.get_notifications()
            
            def clear_all_notifications(self):
                return notification_manager.clear_all_notifications()

            # Error Management - Delegate to ErrorManagerAPI
            def display_error(self, code):
                return error_manager.display_error(code)
            
            def get_error(self, code):
                return error_manager.get_error(code)

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
            
            def get_storage_path(self, sub_path="", is_data=True):
                return file_manager.get_storage_path(sub_path, is_data)

            def get_file_info(self, path):
                return file_manager.get_file_info(path)

            def get_file_data_url(self, path, max_bytes=None, fallback_mime=None):
                return file_manager.get_file_data_url(path, max_bytes, fallback_mime)
            
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

            def get_file_processor_support(self):
                return settings_manager.get_file_processor_support()
            
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
            
            def set_logo(self, logo_type):
                return settings_manager.set_logo(logo_type)

            def set_ui_scale(self, scale):
                return settings_manager.set_ui_scale(scale)
            
            def set_notification_bind(self, key_combination):
                return settings_manager.set_notification_bind(key_combination)
            
            def set_command_palette_bind(self, key_combination):
                return settings_manager.set_command_palette_bind(key_combination)
            
            def set_apps_per_ring(self, number):
                return settings_manager.set_apps_per_ring(number)
            
            def set_reduce_graphics(self, level):
                return settings_manager.set_reduce_graphics(level)
            
            def set_color_theme(self, theme):
                return settings_manager.set_color_theme(theme)

            # Usage Monitor - Delegate to UsageMonitorAPI
            def get_processor_usage(self):
                return usage_monitor.get_processor_usage()
            
            def get_processor_cores_usage(self):
                return usage_monitor.get_processor_cores_usage()
            
            def get_processor_cores(self):
                return usage_monitor.get_processor_cores()

            def get_processor_max_frequency(self):
                return usage_monitor.get_processor_max_frequency()
            
            def get_processor_current_frequency(self):
                return usage_monitor.get_processor_current_frequency()

            def get_memory_usage(self):
                return usage_monitor.get_memory_usage()

            def get_swap_memory_usage(self):
                return usage_monitor.get_swap_memory_usage()

            def get_storage_info(self):
                return usage_monitor.get_storage_info()

            # Other
            def get_available_update(self):
                global available_update
                return available_update

            def open_external_url(self, url):
                return open_external_url(url)

            def js_log(self, level, message):
                print(f"[JS/{level}] {message}")
            
            # Fuzzy search for apps
            def fuzzy_search_apps(self, query):
                return fuzzy_search_apps(query)
            
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
        
        # Debug line - desktop only debug console
        # Uncomment debug line and comment normal line to enable the console
        #webview.start(debug=True, func=on_webview_ready)
        webview.start(func=on_webview_ready)
        return True
    except Exception as e:
        print(f"IW-E1: Error initializing webview: {e}")
        return False

# Called when webview is ready
# Applies the initial fullscreen setting based on the value taken from settings
def on_webview_ready():
    global fullscreen, webview_window
    if fullscreen and webview_window:
        print("OWR: Applying fullscreen setting from startup...")
        webview_window.toggle_fullscreen()

# Shared notifications storage at module level
_notifications = {}
_NOTIFICATION_EVENT_QUEUE_MAX = 512
_notification_event_queue = queue.Queue(maxsize=_NOTIFICATION_EVENT_QUEUE_MAX)
_notification_event_worker_started = False
_notification_event_worker_lock = threading.Lock()


def _evaluate_notification_event_script(script):
    global webview_window
    if not webview_window:
        return False

    if hasattr(webview_window, 'evaluate_javascript'):
        webview_window.evaluate_javascript(script)
        return True
    if hasattr(webview_window, 'evaluate_js'):
        webview_window.evaluate_js(script)
        return True
    return False


def _notification_event_dispatch_worker():
    while True:
        script = _notification_event_queue.get()
        if script is None:
            return

        try:
            _evaluate_notification_event_script(script)
        except Exception as emit_error:
            print(f"NMA: Failed to dispatch notification event: {emit_error}")


def _dispatch_notification_event_on_main_loop(script):
    global main_event_loop

    if not main_event_loop or not hasattr(main_event_loop, 'call_soon_threadsafe'):
        return False

    def _emit_script():
        try:
            _evaluate_notification_event_script(script)
        except Exception as emit_error:
            print(f"NMA: Failed to dispatch notification event on main loop: {emit_error}")

    try:
        main_event_loop.call_soon_threadsafe(_emit_script)
        return True
    except Exception as schedule_error:
        print(f"NMA: Failed to schedule notification event on main loop: {schedule_error}")
        return False


def _ensure_notification_event_worker():
    global _notification_event_worker_started

    if _notification_event_worker_started:
        return

    with _notification_event_worker_lock:
        if _notification_event_worker_started:
            return

        worker = threading.Thread(
            target=_notification_event_dispatch_worker,
            name="notification-event-dispatch",
            daemon=True,
        )
        worker.start()
        _notification_event_worker_started = True


def _dispatch_notification_event(payload):
    if not webview_window:
        return False

    try:
        payload_json = json.dumps(payload, separators=(",", ":"))
    except Exception as encode_error:
        print(f"NMA: Failed to encode notification event payload: {encode_error}")
        return False

    script = f"""
    (function() {{
        const payload = {payload_json};
        window.__SANCTUM_LAST_NOTIFICATION_EVENT = payload;

        if (typeof window.handleSanctumNotificationEvent === 'function') {{
            try {{
                window.handleSanctumNotificationEvent(payload);
            }} catch (handlerError) {{
                console.error('Notification event handler failed:', handlerError);
            }}
        }}

        window.dispatchEvent(new CustomEvent('sanctum-notification-event', {{ detail: payload }}));
    }})();
    """

    # On mobile, evaluating JavaScript from the UI/event loop thread is more reliable.
    if IS_MOBILE and _dispatch_notification_event_on_main_loop(script):
        return True

    _ensure_notification_event_worker()

    try:
        _notification_event_queue.put_nowait(script)
        return True
    except queue.Full:
        try:
            _notification_event_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            _notification_event_queue.put_nowait(script)
            print("NMA: Notification event queue was full, dropped oldest event")
            return True
        except queue.Full:
            print("NMA: Notification event queue full, dropping event")
            return False


def _emit_notification_event(event_name, notification=None, notification_id=None, timestamp=None):
    payload = {
        "event": event_name,
        "count": len(_notifications),
        "timestamp": timestamp if timestamp is not None else time.time(),
    }
    if notification is not None:
        payload["notification"] = notification
    if notification_id is not None:
        payload["notification_id"] = notification_id
    _dispatch_notification_event(payload)

def fuzzy_search_apps(query):
    global app_names

    results = fuzzy_process.extract(query, app_names, limit=5)
    filtered = [r for r in results if r[1] >= 50]
    return filtered

# API for managing the app notifications within the environment
class NotificationManagerAPI:
    def _resolve_source(self, source=None):
        if isinstance(source, str) and source.strip():
            return source.strip()

        for frame_info in inspect.stack():
            frame_module = inspect.getmodule(frame_info.frame)
            if frame_module and hasattr(frame_module, '__name__'):
                module_name = frame_module.__name__
                if module_name.startswith("app_"):
                    return module_name[4:]

        return "Unknown"

    # Sends a notification with a message
    # Finds the calling app by inspecting the call stack
    def send_notification(self, message, source=None):
        global _notifications

        calling_app = self._resolve_source(source)
        notification_id = uuid.uuid4().hex
        notification_timestamp = time.time()
        _notifications[notification_id] = {
            "message": message,
            "timestamp": notification_timestamp,
            "source": calling_app
        }

        notification = {
            "id": notification_id,
            "message": message,
            "timestamp": notification_timestamp,
            "source": calling_app,
        }

        _emit_notification_event(
            "notification-added",
            notification=notification,
            notification_id=notification_id,
            timestamp=notification_timestamp,
        )

        print(f"NMA: Notification sent: {calling_app} - {message} (ID: {notification_id})")
        print(f"NMA: Total notifications: {len(_notifications)}")
        print(f"NMA: Notifications dict id: {id(_notifications)}")
        return {
            "success": True,
            "notification_id": notification_id,
            "source": calling_app,
            "timestamp": notification_timestamp,
        }
    
    # Deletes a notification by finding it by its ID
    # Returns success status
    def delete_notification(self, notification_id):
        global _notifications
        normalized_id = str(notification_id)
        if normalized_id in _notifications:
            del _notifications[normalized_id]
            _emit_notification_event(
                "notification-deleted",
                notification_id=normalized_id,
            )
            return {"success": True}
        else:
            return {"success": False, "error": "Notification ID not found"}
    
    # Returns all current notifications
    # Returns a success status
    def get_notifications(self):
        global _notifications
        # Return all notifications with their IDs
        print(f"Getting notifications: {len(_notifications)} total")
        print(f"Notifications dict id: {id(_notifications)}")
        notifications = [
            {"id": nid, **ndata}
            for nid, ndata in _notifications.items()
        ]
        notifications.sort(key=lambda notif: notif.get("timestamp", 0), reverse=True)
        return {
            "success": True,
            "notifications": notifications
        }
    
    # Clears all notifications in the dictionary
    def clear_all_notifications(self):
        global _notifications
        _notifications.clear()
        _emit_notification_event("notifications-cleared", timestamp=time.time())
        return {"success": True}

#API for managing errors within the environment
class ErrorManagerAPI:
    # Displays an error message
    def display_error(self, code):
        error_data = self.get_error(code)
        self.log_error(error_data)
        return error_data

    # Returns the error information for a given code
    def get_error(self, code):
        try:
            with open("src/errors.json", "r") as f:
                errors = json.load(f)
                return errors.get(str(code), {
                    "code": code,
                    "source": "Unknown",
                    "issue": "Unknown error code.",
                    "effects": "Unknown effects.",
                    "fix": "Please post an issue on the GitHub repository including the steps taken to get this error."
                })
        except Exception as e:
            print(f"Error loading errors.json: {e}")
            return {
                "code": code,
                "source": "Error Manager",
                "issue": "Could not load error information.",
                "effects": "Error details unavailable.",
                "fix": "Check errors.json file."
            }
    
    # Logs the error data to data/error_log.txt and manages log size
    def log_error(self, error_data):
        if os.path.exists("data/error_log.txt") and os.path.getsize("data/error_log.txt") > MAX_ERROR_LOG_SIZE:
            os.rename("data/error_log.txt", "data/old_error_log.txt")

        with open("data/error_log.txt", "a") as f:
            f.write(json.dumps(error_data) + "\n")


# API for file management between the app and the system(s)
class FileManagerAPI:
    def _resolve_path(self, path):
        if not os.path.isabs(path):
            return os.path.join(DATA_DIR, path)
        return path

    # Lists contents of a directory
    def list_directory(self, path):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
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
            print(f"FMAPI-E1: Error listing directory {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E1")')
            return []

    # Reads the contents of a file
    def read_file(self, path):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            with open(path, "r") as file:
                return file.read()
        except Exception as e:
            print(f"FMAPI-E2: Error reading file {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E2")')
            return ""
        
    # Writes content to a file
    def write_file(self, path, content):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, "w") as file:
                file.write(content)
            return True
        except Exception as e:
            print(f"FMAPI-E3: Error writing file {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E3")')
            return False
        
    # Deletes a file
    def delete_file(self, path):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            os.remove(path)
            return True
        except Exception as e:
            print(f"FMAPI-E4: Error deleting file {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E4")')
            return False
    
    # Deletes a directory
    def delete_directory(self, path):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            import shutil
            shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"FMAPI-E5: Error deleting directory {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E5")')
            return False
    
    # Creates a directory
    def create_directory(self, path):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"FMAPI-E6: Error creating directory {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E6")')
            return False
    
    # Creates an empty file
    def create_file(self, path):
        try:
            # Convert relative paths to absolute using DATA_DIR
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            with open(path, "w") as file:
                pass
            return True
        except Exception as e:
            print(f"FMAPI-E7: Error creating file {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E7")')
            return False
    
    # Renames a file or directory
    def rename_item(self, old_path, new_name):
        try:
            base_dir = os.path.dirname(old_path)
            new_path = os.path.join(base_dir, new_name)
            os.rename(old_path, new_path)
            return {'success': True, 'new_path': new_path}
        except Exception as e:
            print(f"FMAPI-E8: Error renaming {old_path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E8")')
            return {'success': False, 'error': str(e)}
    
    # Moves a file or directory
    def move_item(self, src, dest):
        try:
            import shutil
            shutil.move(src, dest)
            return True
        except Exception as e:
            print(f"FMAPI-E9: Error moving {src} to {dest}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E9")')
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
            print(f"FMAPI-E10: Error copying {src} to {dest}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E10")')
            return False
        
    # Gets file or directory metadata
    def get_metadata(self, path):
        try:
            if not os.path.isabs(path):
                path = os.path.join(DATA_DIR, path)
            
            stats = os.stat(path)
            return {
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "created": stats.st_ctime,
                "is_directory": os.path.isdir(path)
            }
        except Exception as e:
            print(f"FMAPI-E11: Error getting metadata for {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E11")')
            return {}

    # Gets extended file info including extension and mime type
    def get_file_info(self, path):
        try:
            resolved_path = self._resolve_path(path)
            if not os.path.exists(resolved_path):
                return {
                    "success": False,
                    "error": "File not found.",
                    "path": path
                }

            stats = os.stat(resolved_path)
            extension = os.path.splitext(resolved_path)[1].lower()
            mime_type, _ = mimetypes.guess_type(resolved_path)

            return {
                "success": True,
                "path": resolved_path,
                "extension": extension,
                "mime_type": mime_type,
                "size": stats.st_size,
                "modified": stats.st_mtime,
                "created": stats.st_ctime,
                "is_directory": os.path.isdir(resolved_path)
            }
        except Exception as e:
            print(f"FMAPI-E12: Error getting file info for {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E12")')
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    # Gets a base64 data URL for a file (useful when file:// loading is blocked)
    def get_file_data_url(self, path, max_bytes=None, fallback_mime=None):
        try:
            resolved_path = self._resolve_path(path)
            if not os.path.isfile(resolved_path):
                return {
                    "success": False,
                    "error": "File not found.",
                    "path": path
                }

            byte_size = os.path.getsize(resolved_path)
            limit = MAX_FILE_DATA_URL_BYTES
            if max_bytes is not None:
                try:
                    parsed_limit = int(max_bytes)
                    if parsed_limit > 0:
                        limit = parsed_limit
                except Exception:
                    pass

            if byte_size > limit:
                return {
                    "success": False,
                    "error": f"File too large for embedded data URL ({byte_size} > {limit} bytes).",
                    "path": path,
                    "byte_size": byte_size,
                    "limit_bytes": limit
                }

            mime_type, _ = mimetypes.guess_type(resolved_path)
            if not mime_type:
                fallback = str(fallback_mime or "").strip()
                mime_type = fallback if fallback else "application/octet-stream"

            with open(resolved_path, "rb") as source_file:
                encoded = base64.b64encode(source_file.read()).decode("utf-8")

            return {
                "success": True,
                "path": resolved_path,
                "mime_type": mime_type,
                "byte_size": byte_size,
                "data_url": f"data:{mime_type};base64,{encoded}"
            }
        except Exception as e:
            print(f"FMAPI-E13: Error creating file data URL for {path}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("FMAPI-E13")')
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    # Checks if a file or directory exists
    def exists(self, path):
        if not os.path.isabs(path):
            path = os.path.join(DATA_DIR, path)
        return os.path.exists(path)
    
    # Returns the proper storage path based on platform
    def get_storage_path(self, sub_path="", is_data=True):
        """Get absolute path for storage location.
        
        Args:
            sub_path: Relative path to append to base directory
            is_data: If True, use data directory; if False, use apps directory
        
        Returns:
            Absolute path as string
        """
        if is_data:
            base = DATA_DIR
        else:
            # Use apps directory (writable on mobile)
            base = APPS_DIR
        
        if sub_path:
            return os.path.join(base, sub_path)
        return base

# API for managing apps within the environment
class AppManagerAPI:
    # Lists all initialized apps
    def list_apps(self):
        global apps
        return apps
    
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

# API for managing the settings for the environment from within
class SettingsManagerAPI:
    # Gets current settings
    def get_settings(self):
        global version, wallpaper, fonts, day_gradient, updates, fullscreen, logo, ui_scale, notification_bind, command_palette_bind, reduce_graphics, color_theme
        return {
            "wallpaper": wallpaper,
            "fonts": fonts,
            "day_gradient": day_gradient,
            "updates": updates,
            "fullscreen": fullscreen,
            "logo": logo,
            "is_mobile": IS_MOBILE,
            "ui_scale": ui_scale,
            "notification_bind": notification_bind,
            "command_palette_bind": command_palette_bind,
            "apps_per_ring": apps_per_ring,
            "reduce_graphics": reduce_graphics,
            "color_theme": color_theme
        }

    # Returns extension support used by settings and file picker filters
    def get_file_processor_support(self):
        return {
            "wallpaper": {
                "extensions": SUPPORTED_WALLPAPER_EXTENSIONS,
                "description": "Any file recognized as image/* by mime type detection"
            },
            "font": {
                "extensions": SUPPORTED_FONT_EXTENSIONS,
                "description": "TrueType font files"
            }
        }
    
    # Gets wallpaper as base64 data URL
    def get_wallpaper_data(self):
        global wallpaper
        import base64
        
        if not wallpaper or wallpaper.lower() == 'none':
            return None
        
        try:
            wallpaper_path = _resolve_configured_path(wallpaper)
            if not wallpaper_path:
                return None
            
            # Get the mime type
            mime_type, _ = mimetypes.guess_type(wallpaper_path)
            if not mime_type:
                mime_type = 'image/png'  # Default to PNG
            
            # Read the file as binary
            with open(wallpaper_path, 'rb') as f:
                image_data = f.read()
            
            # Encode to base64
            b64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Return as data URL
            return f"data:{mime_type};base64,{b64_data}"
        except Exception as e:
            print(f"SMA-E1: Error reading wallpaper file: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E1")')
            return None
    
    # Sets wallpaper path
    def set_wallpaper(self, wallpaper_path):
        global wallpaper
        normalized_value = str(wallpaper_path or "").strip()

        if not normalized_value or normalized_value.lower() == 'none':
            normalized_value = 'None'
        else:
            resolved_path = _resolve_configured_path(normalized_value)
            if not resolved_path or not os.path.isfile(resolved_path):
                print(f"SMA-E2: Wallpaper path does not exist: {normalized_value}")
                return False

            mime_type, _ = mimetypes.guess_type(resolved_path)
            extension = os.path.splitext(resolved_path)[1].lower()
            is_image_mime = bool(mime_type and mime_type.startswith('image/'))

            if not is_image_mime and extension not in SUPPORTED_WALLPAPER_EXTENSIONS:
                print(f"SMA-E2: Unsupported wallpaper format: {extension or 'unknown'}")
                return False

        wallpaper = normalized_value
        # Write to settings.yaml
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["wallpaper"] = normalized_value
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E2: Error setting wallpaper: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E2")')
            return False
        return True
    
    # Sets day gradient preference
    def set_day_gradient(self, enabled):
        global day_gradient
        day_gradient = enabled
        # Write to settings.yaml
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["day_gradient"] = enabled
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E3: Error setting day_gradient: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E3")')
            return False
        return True
    
    # Sets fullscreen preference
    def set_fullscreen(self, enabled):
        global fullscreen, webview_window
        fullscreen = enabled
        
        # Actually toggle the pywebview window fullscreen
        if webview_window and not IS_MOBILE:
            webview_window.toggle_fullscreen()
        
        # Write to settings.yaml
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["fullscreen"] = enabled
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E4: Error setting fullscreen: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E4")')
            return False
        return True
    
    # Sets font path for a given weight
    def set_font(self, weight, font_path):
        global fonts

        weight_key = str(weight or "").strip().lower()
        if not weight_key:
            print("SMA-E5: Missing font weight")
            return False
        if not weight_key.endswith("_font"):
            weight_key = f"{weight_key}_font"

        if weight_key not in SUPPORTED_FONT_KEYS:
            print(f"SMA-E5: Unsupported font weight key: {weight_key}")
            return False

        normalized_path = str(font_path or "").strip()
        if not normalized_path:
            print("SMA-E5: Missing font path")
            return False

        resolved_path = _resolve_configured_path(normalized_path)
        if not resolved_path or not os.path.isfile(resolved_path):
            print(f"SMA-E5: Font path does not exist: {normalized_path}")
            return False

        extension = os.path.splitext(resolved_path)[1].lower()
        if extension not in SUPPORTED_FONT_EXTENSIONS:
            print(f"SMA-E5: Unsupported font extension: {extension or 'unknown'}")
            return False

        fonts[weight_key] = normalized_path
        # Write to settings.yaml
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings[weight_key] = normalized_path
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E5: Error setting font {weight}: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E5")')
            return False
        return True
    
    # Sets update preference
    def set_updates(self, channel):
        global updates
        updates = channel
        # Write to settings.yaml
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["updates"] = channel
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E6: Error setting updates: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E6")')
            return False
        return True
    
    # Sets UI scale multiplier
    def set_ui_scale(self, scale):
        global ui_scale
        ui_scale = float(scale)
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["ui_scale"] = ui_scale
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E8: Error setting ui_scale: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E8")')
            return False
        return True

    # Sets logo preference
    def set_logo(self, logo_type):
        print(f"Setting logo to: {logo_type}")
        global logo
        logo = logo_type
        # Write to settings.yaml
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["logo"] = logo_type
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
            print(f"Logo successfully set to: {logo_type}")
        except Exception as e:
            print(f"SMA-E7: Error setting logo preference: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E7")')
            return False
        return True
    # Sets keybind for notifications
    def set_notification_bind(self, keybind):
        global notification_bind
        notification_bind = keybind
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["notification_bind"] = keybind
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E9: Error setting notification_bind: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E9")')
            return False
        return True
    
    # Sets keybind for command palette
    def set_command_palette_bind(self, keybind):
        global command_palette_bind
        command_palette_bind = keybind
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["command_palette_bind"] = keybind
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E10: Error setting command_palette_bind: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E10")')
            return False
        return True
    
    def get_notification_bind(self):
        global notification_bind
        return notification_bind
    
    def get_command_palette_bind(self):
        global command_palette_bind
        return command_palette_bind

    def set_apps_per_ring(self, count):
        global apps_per_ring
        apps_per_ring = int(count)
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["apps_per_ring"] = apps_per_ring
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E11: Error setting apps_per_ring: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E11")')
            return False
        return True
    
    def set_reduce_graphics(self, level):
        global reduce_graphics
        normalized_level = str(level).strip().lower()
        if normalized_level in ["0", "level_0"]:
            reduce_graphics = "level_0"
        elif normalized_level in ["1", "level_1"]:
            reduce_graphics = "level_1"
        elif normalized_level in ["2", "level_2"]:
            reduce_graphics = "level_2"
        else:
            reduce_graphics = "level_0"
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["reduce_graphics"] = reduce_graphics
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E12: Error setting reduce_graphics: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E12")')
            return False
        return True
    
    def set_color_theme(self, theme):
        global color_theme
        color_theme = theme
        try:
            settings_path = os.path.join(DATA_DIR, "settings.yaml")
            with open(settings_path, "r") as file:
                settings = yaml.load(file, Loader=yaml_loader) or {}
            settings["color_theme"] = color_theme
            with open(settings_path, "w") as file:
                yaml.safe_dump(settings, file)
        except Exception as e:
            print(f"SMA-E13: Error setting color_theme: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("SMA-E13")')
            return False
        return True

class UsageMonitorAPI:
    # PROCESSOR INFORMATION
    # Returns overall CPU usage percentage
    def get_processor_usage(self):
        return psutil.cpu_percent(interval = 0.1)
    
    # Returns a list of CPU usage percentages for each core
    def get_processor_cores_usage(self):
        return psutil.cpu_percent(interval = 0.1, percpu=True)
    
    # Returns the number of physical CPU cores
    def get_processor_cores(self):
        return psutil.cpu_count(logical=False)
    
    # Returns the maximum frequency of the CPU
    def get_processor_max_frequency(self):
        return psutil.cpu_freq().max
    
    # Returns the current frequency of the CPU
    def get_processor_current_frequency(self):
        return psutil.cpu_freq().current

    # MEMORY INFORMATION
    # Returns total, available, used, free memory, and percentage used
    def get_memory_usage(self):
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "free": mem.free,
            "percent": mem.percent
        }
    
    # Returns total, used, free swap memory, percentage used, and swap in/out
    def get_swap_memory_usage(self):
        swap = psutil.swap_memory()
        return {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent,
            "sin": swap.sin,
            "sout": swap.sout
        }

    # STORAGE INFORMATION
    # Returns total, used, free storage in the data directory, and percentage used
    def get_storage_info(self):
        usage = psutil.disk_usage("/")
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent
        }

# Checks if the installed version is older than the latest version
def is_newer_version(installed, latest):
    def version_tuple(v):
        return tuple(map(int, (v.lstrip('v').split("."))))
    
    return version_tuple(latest) > version_tuple(installed)

# Checks for updates from GitHub releases
# Returns update info if available, None otherwise
def check_for_updates():
    global version, updates
    
    # Skip if requests not available
    if not REQUESTS_AVAILABLE:
        return None
    
    url = "https://api.github.com/repos/MichaelCreel/SanctumStation/releases"
    if updates != "none":
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                releases = response.json()
                latest_release = releases[0]
                tag_name = str(latest_release.get("tag_name", "")).strip()
                latest_version = "v" + tag_name.lstrip("v")
                is_prerelease = latest_release["prerelease"]
                release_type = "Pre-release" if is_prerelease else "Stable Release"
                fallback_url = latest_release.get("html_url", "")
                description = latest_release.get("body", "No description available.")

                asset_version = tag_name.lstrip("v")
                expected_prefix = "MOBILE_" if IS_MOBILE else "DESKTOP_"
                expected_name = f"{expected_prefix}SanctumStation_v{asset_version}.zip"
                download_url = fallback_url
                for asset in latest_release.get("assets", []):
                    asset_name = str(asset.get("name", ""))
                    if asset_name == expected_name:
                        direct_url = str(asset.get("browser_download_url", "")).strip()
                        if direct_url:
                            download_url = direct_url
                        break

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
            print(f"CFU-E1: Error checking for updates: {e}")
            if webview_window and not IS_MOBILE:
                webview_window.evaluate_js('displayError("CFU-E1")')
            return None

# Handles environment startup
def main():
    initialize()

if __name__ == "__main__":
    main()