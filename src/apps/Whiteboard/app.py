################################################################################
# Whiteboard Backend for Sanctum Station
################################################################################

import json
import sys
import os

def get_file_api():
    try:
        main_backend = sys.modules.get('__main__')
        if main_backend and hasattr(main_backend, 'FileManagerAPI'):
            return main_backend.FileManagerAPI()
        return None
    except Exception as e:
        print(f"Error accessing FileManagerAPI: {e}")
        return None

def load_board(name):
    try:
        file_api = get_file_api()
        if not file_api:
            return {"success": False, "error": "File API not available"}
        
        file_path = f"data/whiteboard/{name}.json"
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"success": False, "error": "Board not found"}
        
        # Read the file content
        content = file_api.read_file(file_path)
        if not content:
            return {"success": False, "error": "Failed to read board"}
        
        # Parse JSON
        data = json.loads(content)
        return {"success": True, "data": data}
        
    except Exception as e:
        print(f"Error loading board: {e}")
        return {"success": False, "error": str(e)}

def save_board(name, data):
    try:
        file_api = get_file_api()
        if not file_api:
            return {"success": False, "error": "File API not available"}
        
        # Ensure data/whiteboard directory exists
        os.makedirs("data/whiteboard", exist_ok=True)
        
        file_path = f"data/whiteboard/{name}.json"
        
        # Convert data to JSON string
        json_content = json.dumps(data)
        
        # Write to file
        success = file_api.write_file(file_path, json_content)
        
        if success:
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to write file"}
            
    except Exception as e:
        print(f"Error saving board: {e}")
        return {"success": False, "error": str(e)}

def list_boards():
    try:
        file_api = get_file_api()
        if not file_api:
            return {"success": False, "error": "File API not available"}
        
        data_dir = "data/whiteboard"
        if not os.path.exists(data_dir):
            return {"success": True, "boards": []}
        
        # Get all .json files in data directory
        boards = []
        for file in os.listdir(data_dir):
            if file.endswith(".json"):
                # Remove .json extension
                board_name = file[:-5]
                boards.append(board_name)
        
        # Sort alphabetically
        boards.sort()
        
        return {"success": True, "boards": boards}
        
    except Exception as e:
        print(f"Error listing boards: {e}")
        return {"success": False, "error": str(e)}
