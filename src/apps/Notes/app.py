################################################################################
# Notes Backend for Sanctum Station
################################################################################

import sys
import os

def get_file_api():
    main_backend = sys.modules.get('__main__')
    if main_backend and hasattr(main_backend, 'FileManagerAPI'):
        return main_backend.FileManagerAPI()
    return None

def save_note(title, content):
    file_api = get_file_api()
    if not file_api:
        return {"success": False, "error": "File API not available"}
    
    try:
        os.makedirs("data/notes", exist_ok=True)
        file_path = f"data/notes/{title}.md"
        success = file_api.write_file(file_path, content)
        if success:
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to save note"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def load_note(title):
    file_api = get_file_api()
    if not file_api:
        return {"success": False, "error": "File API not available"}
    
    try:
        file_path = f"data/notes/{title}.md"
        content = file_api.read_file(file_path)
        if content is not None:
            return {"success": True, "content": content}
        else:
            return {"success": False, "error": "Note not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def delete_note(title):
    file_api = get_file_api()
    if not file_api:
        return {"success": False, "error": "File API not available"}
    
    try:
        file_path = f"data/notes/{title}.md"
        success = file_api.delete_file(file_path)
        if success:
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to delete note"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def list_notes():
    file_api = get_file_api()
    if not file_api:
        return {"success": False, "error": "File API not available"}
    
    try:
        os.makedirs("data/notes", exist_ok=True)
        directory_path = "data/notes/"
        files = file_api.list_directory(directory_path)
        
        # Filter for .md files and remove extension
        notes = []
        if files:
            for file_obj in files:
                # file_obj is a dict with 'name', 'type', etc.
                if isinstance(file_obj, dict) and file_obj.get('type') == 'file':
                    filename = file_obj.get('name', '')
                    if filename.endswith('.md'):
                        notes.append(filename[:-3])  # Remove .md extension
        
        return {"success": True, "notes": sorted(notes)}
    except Exception as e:
        return {"success": False, "error": str(e)}