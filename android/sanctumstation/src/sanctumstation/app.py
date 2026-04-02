"""
A productivity app designed to connect your computer and mobile workflows.
"""

import toga
from toga.style.pack import COLUMN, Pack
from toga.colors import rgb
import sys
import os
import json
import threading
import shutil
import asyncio
import requests
import zipfile
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Android availability will be checked at runtime

# Add the src directory to the path
app_dir = os.path.dirname(__file__)
src_dir = os.path.join(app_dir, 'src')

sys.path.insert(0, src_dir)

# Import the backend
import backend

# Create API instances
file_manager = backend.FileManagerAPI()
settings_manager = backend.SettingsManagerAPI()
notification_manager = backend.NotificationManagerAPI()
error_manager = backend.ErrorManagerAPI()

# Global variable to hold writable apps directory path (set during setup)
writable_apps_dir_global = None
writable_web_dir_global = None

# Paste your startup ASCII art directly into this string.
# If non-empty, it will be used for the splash screen before file/fallback lookup.
INLINE_LOADING_ASCII_ART = r"""
                                                                                                    
                                                .*/,.                                               
                                   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&                                  
                             @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                            
                         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                        
                     @@@@@@@@@@@@@@@@%                         %@@@@@@@@@@@@@@@@                    
                  @@@@@@@@@@@@@@              @@@@@@@@@              @@@@@@@@@@@@@&                 
                @@@@@@@@@@@@         @@@@@@@@@&*     *&@@@@@@@@@         @@@@@@@@@@@@               
              @@@@@@@@@@@       @@@@@%                         (@@@@@       @@@@@@@@@@@             
            @@@@@@@@@@      @@@@@                                   @@@@&      @@@@@@@@@@           
          @@@@@@@@@@      @@@                                          *@@@      @@@@@@@@@@         
         @@@@@@@@@     @@@@                                               @@@@     @@@@@@@@@        
       @@@@@@@@@     @@@@                                                   @@@@     @@@@@@@@&      
      @@@@@@@@@     @@@                                                       @@@     @@@@@@@@@     
     &@@@@@@@@     @@@                                                         /@@     @@@@@@@@%    
     @@@@@@@@    \#@@           @@@@@@@@@@@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@  @@.    @@@@@@@@    
    @@@@@@@@     @@           @@@@@@@@@@@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@.   @@     @@@@@@@@   
    @@@@@@@@    @@@          @@@@@                     @@@@@                      @@@    @@@@@@@@   
   @@@@@@@@     @@          @@@@@                     @@@@@                        @@     @@@@@@@@  
   @@@@@@@@    @@@         @@@@@                     @@@@@                         @@@    @@@@@@@@  
   @@@@@@@@    @@@        @@@@@@@@@@@@@@@@@@@@@@/   (@@@@@@@@@@@@@@@@@@@@@@        @@@    @@@@@@@@  
   @@@@@@@@    @@@                         @@@@@                     @@@@@         @@@    @@@@@@@@  
   @@@@@@@@     @@                        @@@@@                     @@@@@          @@     @@@@@@@@  
    @@@@@@@@    @@@                      @@@@@                     @@@@@          @@@    @@@@@@@@   
    @@@@@@@@     @@   /@@@@@@@@@@@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@           @@     @@@@@@@@   
     @@@@@@@@    %@@  @@@@@@@@@@@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@           @@     @@@@@@@@    
     &@@@@@@@@     @@                                                          /@@     @@@@@@@@&    
      @@@@@@@@@     @@@                                                       @@@     @@@@@@@@@     
       @@@@@@@@@     %@@@                                                   @@@\#     @@@@@@@@%      
         @@@@@@@@@     @@@@                                               @@@@     @@@@@@@@@        
          @@@@@@@@@@      @@@*                                         &@@@      @@@@@@@@@@         
            @@@@@@@@@@      &@@@@                                   @@@@%         @@@@@@@           
              @@@@@@@@@@@       @@@@@\#                         \#@@@@@     @@@@@@@@  @@@             
                @@@@@@@@@@@@         @@@@@@@@@@*     /@@@@@@@@@@         @@@@@@@@@@                 
                  &@@@@@@@@@@@@@              &@@@@@@@@              %   @@@@@@@@@@                 
                     @@@@@@@@@@@@@@@@&                         @@@@@@@@@  @@@@@@@\#                  
                         @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                          
                             @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&                            
                                   %@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&                                  
                                                 ,/,                                                                                   
"""

LOADING_ASCII_FONT_SIZE = 3.1
LOADING_ASCII_FONT_FAMILY = "monospace"


# Custom HTTP handler that serves files and handles API calls
class APIHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        """Override to serve app files from writable directory."""
        # Parse the URL path
        from urllib.parse import unquote
        path = unquote(path)
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        # If requesting app files, serve from writable apps directory
        if path.startswith('/apps/') and writable_apps_dir_global:
            # Remove leading /apps and construct path to writable location
            relative_path = path[6:]  # Remove '/apps/'
            app_file_path = os.path.join(writable_apps_dir_global, relative_path)
            return app_file_path
        
        # Otherwise, serve from src directory (default behavior)
        return super().translate_path(path)
    
    def do_POST(self):
        """Handle POST requests to /api/* endpoints."""
        if self.path.startswith('/api/'):
            # Extract method name from path
            method = self.path[5:]  # Remove '/api/' prefix
            
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            args = request_data.get('args', [])
            
            try:
                # Route to appropriate handler
                result = self.handle_api_method(method, args)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                # Send error response with full traceback
                import traceback
                print(f"API Error in {method}: {e}")
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_api_method(self, method, args):
        """Route API calls to backend methods."""
        if method == 'js_log':
            # Print JavaScript console logs to Python stdout
            level = args[0] if len(args) > 0 else 'LOG'
            message = args[1] if len(args) > 1 else ''
            print(f"[JS {level}] {message}")
            return {"success": True}
        elif method == 'launch_app':
            return backend.launch_app(*args)
        elif method == 'stop_app':
            return backend.stop_app(*args)
        elif method == 'call_app_function':
            # Route to AppManagerAPI.call_app_function
            app_manager = backend.AppManagerAPI()
            return app_manager.call_app_function(*args)
        elif method == 'get_apps':
            return backend.apps
        elif method == 'get_running_apps':
            return backend.get_running_apps()
        elif method == 'fuzzy_search_apps':
            return backend.fuzzy_search_apps(*args)
        elif method == 'get_available_update':
            return backend.available_update
        elif method == 'send_notification':
            return notification_manager.send_notification(*args)
        elif method == 'delete_notification':
            return notification_manager.delete_notification(*args)
        elif method == 'get_notifications':
            return notification_manager.get_notifications()
        elif method == 'clear_all_notifications':
            return notification_manager.clear_all_notifications()
        elif method == 'display_error':
            return error_manager.display_error(*args)
        elif method == 'get_error':
            return error_manager.get_error(*args)
        elif method == 'list_directory':
            return file_manager.list_directory(*args)
        elif method == 'read_file':
            return file_manager.read_file(*args)
        elif method == 'write_file':
            return file_manager.write_file(*args)
        elif method == 'delete_file':
            return file_manager.delete_file(*args)
        elif method == 'delete_directory':
            return file_manager.delete_directory(*args)
        elif method == 'create_directory':
            return file_manager.create_directory(*args)
        elif method == 'create_file':
            return file_manager.create_file(*args)
        elif method == 'rename_item':
            return file_manager.rename_item(*args)
        elif method == 'move_item':
            return file_manager.move_item(*args)
        elif method == 'copy_item':
            return file_manager.copy_item(*args)
        elif method == 'get_metadata':
            return file_manager.get_metadata(*args)
        elif method == 'exists':
            return file_manager.exists(*args)
        elif method == 'get_storage_path':
            return file_manager.get_storage_path(*args)
        elif method == 'get_fonts':
            return backend.fonts
        elif method == 'get_version':
            return backend.version
        elif method == 'get_wallpaper':
            return backend.wallpaper
        elif method == 'get_wallpaper_data':
            return settings_manager.get_wallpaper_data()
        elif method == 'get_day_gradient':
            return backend.day_gradient
        elif method == 'get_fullscreen':
            return backend.fullscreen
        elif method == 'get_settings':
            return settings_manager.get_settings()
        elif method == 'get_file_processor_support':
            return settings_manager.get_file_processor_support()
        elif method == 'set_wallpaper':
            return settings_manager.set_wallpaper(*args)
        elif method == 'set_day_gradient':
            return settings_manager.set_day_gradient(*args)
        elif method == 'set_fullscreen':
            return settings_manager.set_fullscreen(*args)
        elif method == 'set_font':
            return settings_manager.set_font(*args)
        elif method == 'set_updates':
            return settings_manager.set_updates(*args)
        elif method == 'set_logo':
            return settings_manager.set_logo(*args)
        elif method == 'set_ui_scale':
            return settings_manager.set_ui_scale(*args)
        elif method == 'set_notification_bind':
            return settings_manager.set_notification_bind(*args)
        elif method == 'set_command_palette_bind':
            return settings_manager.set_command_palette_bind(*args)
        elif method == 'set_apps_per_ring':
            return settings_manager.set_apps_per_ring(*args)
        else:
            raise ValueError(f"Unknown API method: {method}")


class SanctumStation(toga.App):
    def startup(self):
        """Show a splash screen immediately, then initialize app services in background."""
        self._build_loading_screen()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.loading_box
        self.main_window.show()

        self.add_background_task(self.initialize_runtime)

    def _get_loading_ascii_art(self):
        """Load ASCII art from inline constant, file, or fallback."""
        inline_art = INLINE_LOADING_ASCII_ART.strip('\n').replace('\\#', '#')
        if inline_art.strip():
            return inline_art

        candidates = [
            os.path.join(app_dir, 'logo_ascii.txt'),
            os.path.join(app_dir, 'src', 'logo_ascii.txt'),
        ]

        for path in candidates:
            if os.path.isfile(path):
                try: 
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read().rstrip('\n').replace('\\#', '#')
                    if content.strip():
                        return content
                except Exception as e:
                    print(f"Failed to read ASCII logo at {path}: {e}")

        return (
            "  _____                 _                    _____ _        _   _             \n"
            " / ____|               | |                  / ____| |      | | (_)            \n"
            "| (___   __ _ _ __   __| |_   _ _ __ ___   | (___ | |_ __ _| |_ _  ___  _ __  \n"
            " \\___ \\ / _` | '_ \\ / _` | | | | '_ ` _ \\   \\___ \\| __/ _` | __| |/ _ \\| '_ \\ \n"
            " ____) | (_| | | | | (_| | |_| | | | | | |  ____) | || (_| | |_| | (_) | | | |\n"
            "|_____/ \\__,_|_| |_|\\__,_|\\__,_|_| |_| |_| |_____/ \\__\\__,_|\\__|_|\\___/|_| |_|\n"
        )

    def _build_loading_screen(self):
        ascii_art = self._get_loading_ascii_art()
        background = rgb(15, 18, 26)
        primary_text = rgb(232, 238, 255)
        accent_text = rgb(152, 176, 255)

        self.loading_ascii = toga.MultilineTextInput(
            value=ascii_art,
            readonly=True,
            style=Pack(
                flex=1,
                padding=(16, 16, 8, 16),
                font_size=LOADING_ASCII_FONT_SIZE,
                font_family=LOADING_ASCII_FONT_FAMILY,
                background_color=background,
                color=primary_text
            )
        )
        self.loading_status = toga.Label(
            'Loading...',
            style=Pack(
                padding=(0, 16, 16, 16),
                font_size=12,
                background_color=background,
                color=accent_text
            )
        )

        self.loading_box = toga.Box(
            children=[self.loading_ascii, self.loading_status],
            style=Pack(direction=COLUMN, flex=1, background_color=background)
        )

    async def _set_loading_status(self, message):
        print(f"[startup] {message}")
        if hasattr(self, 'loading_status') and self.loading_status is not None:
            self.loading_status.text = message
        await asyncio.sleep(0)

    async def initialize_runtime(self, widget):
        """Run startup steps without showing a blank app window."""
        try:
            await self._set_loading_status('Preparing writable storage...')
            await asyncio.to_thread(self.setup_writable_data)

            await self._set_loading_status('Initializing backend services...')
            await asyncio.to_thread(backend.initialize)

            await self._set_loading_status('Starting local web server...')
            await asyncio.to_thread(self.start_http_server)

            await self._set_loading_status('Launching interface...')
            self._create_main_interface()

            await self._set_loading_status('Applying Android display settings...')
            self._enable_android_immersive_mode()

            await self._set_loading_status('Ready')
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self._set_loading_status(f"Startup failed: {e}")

    def _create_main_interface(self):
        # Create a WebView to display the app from localhost
        self.webview = toga.WebView(
            url='http://127.0.0.1:5000/index.html',
            style=Pack(flex=1)
        )

        # Store webview globally so backend can inject scripts directly
        backend.webview_window = self.webview
        print("WebView stored in backend.webview_window")

        # Store the main event loop for cross-thread async calls
        backend.main_event_loop = asyncio.get_event_loop()
        print("Event loop stored in backend.main_event_loop")

        # Enable WebView debugging and console forwarding on Android
        # Check if we have Android native webview access
        if hasattr(self.webview, '_impl') and hasattr(self.webview._impl, 'native'):
            try:
                from java import jclass, dynamic_proxy
                print("Android detected (Chaquopy), attempting to configure WebView...")

                print("  Getting native webview...")
                native_webview = self.webview._impl.native
                print(f"  Native webview type: {type(native_webview)}")

                print("  Enabling JavaScript...")
                settings = native_webview.getSettings()
                settings.setJavaScriptEnabled(True)
                print("  JavaScript enabled")

                # Clear WebView cache on startup to load fresh content after updates
                print("  Clearing WebView cache on startup...")
                native_webview.clearCache(True)
                print("  WebView cache cleared")

                # Disable WebContents debugging for production (removes green debug bar)
                print("  Disabling WebContents debugging...")
                native_webview.setWebContentsDebuggingEnabled(False)
                print("  WebContents debugging disabled")

            except ImportError as e:
                print(f"Chaquopy java module import failed: {e}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                print(f"Failed to configure WebView: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("WebView does not have native Android implementation")

        # Replace splash content with the main webview
        main_box = toga.Box(
            children=[self.webview],
            style=Pack(direction=COLUMN, flex=1)
        )
        self.main_window.content = main_box

    def _enable_android_immersive_mode(self):
        # Enable immersive fullscreen mode on Android (hides status bar and nav bar)
        # Check platform to determine if we're on Android
        if sys.platform == 'linux' and hasattr(self.webview, '_impl'):
            try:
                from java import jclass, dynamic_proxy
                print("Enabling immersive fullscreen mode (Chaquopy)...")

                # Get Android classes using Chaquopy's jclass
                PythonActivity = jclass('org.beeware.android.MainActivity')
                View = jclass('android.view.View')
                WindowManager = jclass('android.view.WindowManager')

                # Get the native Android activity
                activity = PythonActivity.singletonThis

                # Get the window and decor view
                window = activity.getWindow()
                decorView = window.getDecorView()

                # Set window flags for fullscreen
                window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)
                window.clearFlags(WindowManager.LayoutParams.FLAG_FORCE_NOT_FULLSCREEN)

                # Function to apply immersive mode
                def applyImmersiveMode():
                    # Immersive sticky mode - hides status bar and nav bar, re-hides after swipe
                    uiOptions = (
                        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                        View.SYSTEM_UI_FLAG_FULLSCREEN |
                        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                        View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                        View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                        View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    )
                    decorView.setSystemUiVisibility(uiOptions)

                # Apply immersive mode initially
                applyImmersiveMode()

                # Create listener to re-apply when window regains focus
                @dynamic_proxy(jclass('android.view.View$OnWindowFocusChangeListener'))
                def focusListener(hasFocus):
                    if hasFocus:
                        applyImmersiveMode()

                # Set the listener
                decorView.setOnWindowFocusChangeListener(focusListener)
                print("Immersive fullscreen mode enabled with focus listener")

            except ImportError as e:
                print(f"Chaquopy java module import failed: {e}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                print(f"Failed to enable immersive fullscreen: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Platform {sys.platform} - immersive mode skipped")
    
    def setup_writable_data(self):
        """Copy data from bundled assets and download apps from GitHub to writable location."""
        # Get the writable data directory from Toga
        writable_data_dir = str(self.paths.data)
        bundled_data_dir = os.path.join(app_dir, 'data')
        writable_apps_dir = os.path.join(writable_data_dir, 'apps')
        
        print(f"Writable data directory: {writable_data_dir}")
        print(f"Bundled data directory: {bundled_data_dir}")
        print(f"Writable apps directory: {writable_apps_dir}")
        
        # Check if data has been initialized in writable location
        settings_file = os.path.join(writable_data_dir, 'settings.yaml')
        
        if not os.path.exists(settings_file):
            print(f"First run detected. Copying data from bundled to writable location...")
            # Copy all data to writable location
            if os.path.exists(bundled_data_dir):
                for item in os.listdir(bundled_data_dir):
                    src_path = os.path.join(bundled_data_dir, item)
                    dest_path = os.path.join(writable_data_dir, item)
                    
                    # Skip if already exists
                    if os.path.exists(dest_path):
                        print(f"  Skipping existing: {item}")
                        continue
                        
                    try:
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dest_path)
                            print(f"  Copied directory: {item}")
                        else:
                            shutil.copy2(src_path, dest_path)
                            print(f"  Copied file: {item}")
                    except Exception as e:
                        print(f"  Error copying {item}: {e}")
            print("Data initialization complete")
        else:
            print(f"Using existing data at {writable_data_dir}")
        
        # Extract apps from bundled resources (.txt files)
        bundled_apps_dir = os.path.join(app_dir, 'resources', 'apps')
        
        if os.path.exists(bundled_apps_dir):
            print(f"Checking bundled apps for updates...")
            print(f"  Bundled apps directory: {bundled_apps_dir}")
            print(f"  Writable apps directory: {writable_apps_dir}")
            
            # Ensure writable apps directory exists
            os.makedirs(writable_apps_dir, exist_ok=True)
            
            # Process each bundled app
            for app_name in os.listdir(bundled_apps_dir):
                bundled_app_path = os.path.join(bundled_apps_dir, app_name)
                writable_app_path = os.path.join(writable_apps_dir, app_name)
                
                if not os.path.isdir(bundled_app_path):
                    continue
                    
                # Ensure writable app directory exists
                os.makedirs(writable_app_path, exist_ok=True)
                
                # Process each file in the bundled app
                for root, dirs, files in os.walk(bundled_app_path):
                    for filename in files:
                        bundled_file = os.path.join(root, filename)
                        relative_path = os.path.relpath(bundled_file, bundled_app_path)
                        
                        # Convert .txt back to .py for Python files
                        if filename.endswith('.txt'):
                            writable_filename = relative_path[:-4] + '.py'  # Remove .txt, add .py
                        else:
                            writable_filename = relative_path
                            
                        writable_file = os.path.join(writable_app_path, writable_filename)
                        
                        # Create parent directories if needed
                        os.makedirs(os.path.dirname(writable_file), exist_ok=True)
                        
                        # Copy if file doesn't exist or content is different
                        should_copy = False
                        if not os.path.exists(writable_file):
                            should_copy = True
                        else:
                            # Compare file contents
                            try:
                                with open(bundled_file, 'rb') as f1:
                                    bundled_content = f1.read()
                                with open(writable_file, 'rb') as f2:
                                    writable_content = f2.read()
                                if bundled_content != writable_content:
                                    should_copy = True
                            except (PermissionError, OSError) as e:
                                # If we can't read the file, replace it
                                print(f"  Warning: Can't read {writable_filename}, will replace: {e}")
                                should_copy = True
                        
                        if should_copy:
                            try:
                                # Remove existing file first if it exists (fixes permission issues)
                                if os.path.exists(writable_file):
                                    try:
                                        os.chmod(writable_file, 0o666)  # Make writable
                                    except:
                                        pass
                                    os.remove(writable_file)
                                shutil.copy2(bundled_file, writable_file)
                                # Ensure new file is writable
                                os.chmod(writable_file, 0o666)
                                print(f"  Updated: {app_name}/{writable_filename}")
                            except (PermissionError, OSError) as e:
                                print(f"  Error copying {writable_filename}: {e}")
            
            print(f"  App sync complete")
        else:
            print(f"  Warning: Bundled apps directory not found at {bundled_apps_dir}")
            print(f"  Apps will need to be manually installed")

        # Sync core web assets to writable storage so update installs can refresh
        # frontend files without requiring uninstall/reinstall.
        bundled_web_dir = src_dir
        writable_web_dir = os.path.join(writable_data_dir, 'web')
        os.makedirs(writable_web_dir, exist_ok=True)
        print(f"Syncing web assets from {bundled_web_dir} to {writable_web_dir}...")

        for root, dirs, files in os.walk(bundled_web_dir):
            rel_root = os.path.relpath(root, bundled_web_dir)
            rel_root = '' if rel_root == '.' else rel_root

            # App files are served from writable_apps_dir_global via APIHandler.
            dirs[:] = [d for d in dirs if d not in {'__pycache__', 'apps'}]
            if rel_root.startswith('apps'):
                continue

            for filename in files:
                if filename.endswith(('.py', '.pyc', '.pyo')):
                    continue

                src_file = os.path.join(root, filename)
                relative_path = os.path.normpath(os.path.join(rel_root, filename))
                dest_file = os.path.join(writable_web_dir, relative_path)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)

                should_copy = False
                if not os.path.exists(dest_file):
                    should_copy = True
                else:
                    try:
                        with open(src_file, 'rb') as src_fp:
                            src_content = src_fp.read()
                        with open(dest_file, 'rb') as dest_fp:
                            dest_content = dest_fp.read()
                        if src_content != dest_content:
                            should_copy = True
                    except Exception:
                        should_copy = True

                if should_copy:
                    try:
                        if os.path.exists(dest_file):
                            try:
                                os.chmod(dest_file, 0o666)
                            except Exception:
                                pass
                            os.remove(dest_file)
                        shutil.copy2(src_file, dest_file)
                        os.chmod(dest_file, 0o666)
                        print(f"  Updated web asset: {relative_path}")
                    except Exception as e:
                        print(f"  Error syncing web asset {relative_path}: {e}")

        print("Web asset sync complete")
        
        # Override backend's DATA_DIR and APPS_DIR with writable locations
        backend.DATA_DIR = writable_data_dir
        backend.APPS_DIR = writable_apps_dir
        print(f"Backend DATA_DIR set to: {backend.DATA_DIR}")
        print(f"Backend APPS_DIR set to: {backend.APPS_DIR}")
        
        # Now that APPS_DIR is set to writable location, initialize apps
        print("Initializing apps from writable directory...")
        if not backend.init_apps():
            print("WARNING: No apps found to initialize. No apps will be loaded.")
        else:
            print(f"Successfully initialized {len(backend.apps)} apps")
        
        # Set global variable for HTTP server
        global writable_apps_dir_global
        writable_apps_dir_global = writable_apps_dir

        global writable_web_dir_global
        writable_web_dir_global = writable_web_dir
    
    def start_http_server(self):
        """Start a local HTTP server to serve app files and handle API calls."""
        web_root_dir = writable_web_dir_global if writable_web_dir_global and os.path.isdir(writable_web_dir_global) else src_dir
        os.chdir(web_root_dir)
        
        # Create and start server with custom APIHandler in a background thread
        self.httpd = HTTPServer(('127.0.0.1', 5000), APIHandler)
        
        server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        server_thread.start()
        print(f"HTTP server started at http://127.0.0.1:5000 (root={web_root_dir})")    
    def on_webview_load(self, widget):
        """Called when the webview finishes loading - inject API bridge."""
        print("WebView loaded, setting up API bridge...")
        
        # Inject the Toga bridge that will handle API calls
        self.inject_api_bridge()
    
    def inject_api_bridge(self):
        """Inject JavaScript that creates window.pywebview.api using Toga's bridge."""
        
        bridge_js = """
        (function() {
            console.log('Initializing Toga API bridge...');
            
            // Create pywebview-compatible API object
            window.pywebview = { api: {} };
            
            // Helper to call Python via Toga's message handler
            async function callPython(method, ...args) {
                return new Promise((resolve, reject) => {
                    const callId = Date.now() + Math.random();
                    const message = {
                        id: callId,
                        method: method,
                        args: args
                    };
                    
                    // Store the promise callbacks
                    window.pywebviewCallbacks = window.pywebviewCallbacks || {};
                    window.pywebviewCallbacks[callId] = { resolve, reject };
                    
                    // Send message to Python (Toga handles this)
                    window.webkit.messageHandlers.toga.postMessage(JSON.stringify(message));
                    
                    // Timeout after 30 seconds
                    setTimeout(() => {
                        if (window.pywebviewCallbacks[callId]) {
                            delete window.pywebviewCallbacks[callId];
                            reject(new Error('Request timeout'));
                        }
                    }, 30000);
                });
            }
            
            // Callback handler for Python responses
            window.handlePythonResponse = function(callId, result, error) {
                if (window.pywebviewCallbacks && window.pywebviewCallbacks[callId]) {
                    if (error) {
                        window.pywebviewCallbacks[callId].reject(new Error(error));
                    } else {
                        window.pywebviewCallbacks[callId].resolve(result);
                    }
                    delete window.pywebviewCallbacks[callId];
                }
            };
            
            // Define all API methods
            const methods = [
                'launch_app', 'stop_app', 'get_apps', 'get_running_apps',
                'send_notification', 'delete_notification', 'get_notifications', 'clear_all_notifications',
                'display_error', 'get_error',
                'list_directory', 'read_file', 'write_file', 'delete_file', 'delete_directory',
                'create_directory', 'create_file', 'rename_item', 'move_item', 'copy_item',
                'get_metadata', 'exists',
                'get_fonts', 'get_version', 'get_wallpaper', 'get_wallpaper_data',
                'get_day_gradient', 'get_fullscreen',
                'get_settings', 'set_wallpaper', 'set_day_gradient', 'set_fullscreen',
                'set_font', 'set_updates', 'set_notification_bind', 'set_command_palette_bind', 'set_apps_per_ring', 'get_available_update', 'get_file_processor_support',
                'fuzzy_search_apps', 'call_app_function'
            ];
            
            // Create API method wrappers
            methods.forEach(method => {
                window.pywebview.api[method] = async function(...args) {
                    return await callPython(method, ...args);
                };
            });
            
            console.log('Toga API bridge initialized');
        })();
        """
        
        try:
            self.webview.evaluate_javascript(bridge_js)
            print("API bridge injected successfully")
        except Exception as e:
            print(f"Error injecting API bridge: {e}")
    
    def handle_api_call(self, call_id, method, args):
        """Handle API calls from JavaScript."""
        try:
            # Route to appropriate handler
            if method == 'launch_app':
                result = backend.launch_app(*args)
            elif method == 'stop_app':
                result = backend.stop_app(*args)
            elif method == 'get_apps':
                result = backend.apps
            elif method == 'get_running_apps':
                result = backend.get_running_apps()
            elif method == 'send_notification':
                result = notification_manager.send_notification(*args)
            elif method == 'delete_notification':
                result = notification_manager.delete_notification(*args)
            elif method == 'get_notifications':
                result = notification_manager.get_notifications()
            elif method == 'clear_all_notifications':
                result = notification_manager.clear_all_notifications()
            elif method == 'display_error':
                result = error_manager.display_error(*args)
            elif method == 'get_error':
                result = error_manager.get_error(*args)
            elif method == 'list_directory':
                result = file_manager.list_directory(*args)
            elif method == 'read_file':
                result = file_manager.read_file(*args)
            elif method == 'write_file':
                result = file_manager.write_file(*args)
            elif method == 'delete_file':
                result = file_manager.delete_file(*args)
            elif method == 'delete_directory':
                result = file_manager.delete_directory(*args)
            elif method == 'create_directory':
                result = file_manager.create_directory(*args)
            elif method == 'create_file':
                result = file_manager.create_file(*args)
            elif method == 'rename_item':
                result = file_manager.rename_item(*args)
            elif method == 'move_item':
                result = file_manager.move_item(*args)
            elif method == 'copy_item':
                result = file_manager.copy_item(*args)
            elif method == 'get_metadata':
                result = file_manager.get_metadata(*args)
            elif method == 'exists':
                result = file_manager.exists(*args)
            elif method == 'get_fonts':
                result = backend.fonts
            elif method == 'get_version':
                result = backend.version
            elif method == 'get_wallpaper':
                result = backend.wallpaper
            elif method == 'get_wallpaper_data':
                result = settings_manager.get_wallpaper_data()
            elif method == 'get_day_gradient':
                result = backend.day_gradient
            elif method == 'get_fullscreen':
                result = backend.fullscreen
            elif method == 'get_settings':
                result = settings_manager.get_settings()
            elif method == 'get_file_processor_support':
                result = settings_manager.get_file_processor_support()
            elif method == 'set_wallpaper':
                result = settings_manager.set_wallpaper(*args)
            elif method == 'set_day_gradient':
                result = settings_manager.set_day_gradient(*args)
            elif method == 'set_fullscreen':
                result = settings_manager.set_fullscreen(*args)
            elif method == 'set_font':
                result = settings_manager.set_font(*args)
            elif method == 'set_updates':
                result = settings_manager.set_updates(*args)
            elif method == 'set_notification_bind':
                result = settings_manager.set_notification_bind(*args)
            elif method == 'set_command_palette_bind':
                result = settings_manager.set_command_palette_bind(*args)
            elif method == 'set_apps_per_ring':
                result = settings_manager.set_apps_per_ring(*args)
            elif method == 'get_available_update':
                result = backend.available_update
            elif method == 'fuzzy_search_apps':
                result = backend.fuzzy_search_apps(*args)
            elif method == 'call_app_function':
                result = self.call_app_function_direct(*args)
            else:
                result = {"error": f"Unknown method: {method}"}
            
            # Send response back to JavaScript
            response_js = f"window.handlePythonResponse({call_id}, {json.dumps(result)}, null);"
            self.webview.evaluate_javascript(response_js)
            
        except Exception as e:
            error_msg = str(e)
            response_js = f"window.handlePythonResponse({call_id}, null, {json.dumps(error_msg)});"
            self.webview.evaluate_javascript(response_js)
    
    def call_app_function_direct(self, app_name, function_name, *args):
        """Direct call to app function."""
        try:
            module_name = f"app_{app_name}"
            if module_name not in sys.modules:
                return {"success": False, "message": f"App '{app_name}' not running"}
            
            app_module = sys.modules[module_name]
            
            if not hasattr(app_module, function_name):
                return {"success": False, "message": f"Function '{function_name}' not found"}
            
            func = getattr(app_module, function_name)
            result = func(*args)
            return result
        except Exception as e:
            return {"success": False, "message": str(e)}


def main():
    return SanctumStation()
