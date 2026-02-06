"""
Flask HTTP API wrapper for Sanctum Station mobile app.
Wraps the existing backend API for HTTP access on mobile.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys

import backend

def create_app():
    # Get the directory where backend.py is located
    backend_dir = os.path.dirname(os.path.abspath(backend.__file__))
    print(f"Backend directory: {backend_dir}")
    
    app = Flask(__name__, static_folder=backend_dir, static_url_path='')
    CORS(app)
    
    # Create API instances
    file_manager = backend.FileManagerAPI()
    settings_manager = backend.SettingsManagerAPI()
    notification_manager = backend.NotificationManagerAPI()
    error_manager = backend.ErrorManagerAPI()
    
    @app.route('/')
    def index():
        index_path = os.path.join(backend_dir, 'index.html')
        print(f"Serving index.html from: {index_path}")
        return send_from_directory(backend_dir, 'index.html')
    
    # Serve static files
    @app.route('/<path:path>')
    def serve_static(path):
        print(f"Serving static file: {path}")
        return send_from_directory(backend_dir, path)
    
    @app.route('/api/<method>', methods=['POST'])
    def api_call(method):
        try:
            data = request.get_json() or {}
            args = data.get('args', [])
            kwargs = data.get('kwargs', {})
            
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
            elif method == 'get_available_update':
                result = backend.available_update
            elif method == 'fuzzy_search_apps':
                result = backend.fuzzy_search_apps(*args)
            elif method == 'call_app_function':
                result = call_app_function_direct(*args, **kwargs)
            else:
                return jsonify({"error": f"Unknown method: {method}"}), 404
            
            return jsonify(result)
        except Exception as e:
            print(f"API Error in {method}: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app

def call_app_function_direct(app_name, function_name, *args, **kwargs):
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
