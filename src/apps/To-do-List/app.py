################################################################################
# To-do List Backend for Sanctum Station
################################################################################

import sys
import yaml
import os

next_id = 0
tasks = {}

# Helper function to get FileManagerAPI from main backend
def get_file_api():
    main_backend = sys.modules.get('__main__')
    if main_backend and hasattr(main_backend, 'FileManagerAPI'):
        return main_backend.FileManagerAPI()
    return None

# Helper function to send notifications
def send_notification(message):
    main_backend = sys.modules.get('__main__')
    if main_backend and hasattr(main_backend, 'NotificationManagerAPI'):
        notification_api = main_backend.NotificationManagerAPI()
        return notification_api.send_notification(message)
    return None

# Loads tasks from file
def load_tasks():
    global tasks, next_id
    try:
        file_api = get_file_api()
        if file_api:
            file_path = "data/to-do-list/tasks.yaml"
            content = file_api.read_file(file_path)
            if content:
                tasks = yaml.safe_load(content) or {}
                # Set next_id to one higher than the highest existing ID
                if tasks:
                    next_id = max(int(k) for k in tasks.keys()) + 1
                else:
                    next_id = 0
                return tasks
    except Exception:
        pass
    
    tasks = {}
    next_id = 0
    return {}

# Saves a new task
def save_task(task_text):
    global next_id, tasks
    try:
        tasks[str(next_id)] = {
            "text": task_text,
            "completed": False
        }
        
        file_api = get_file_api()
        if file_api:
            # Ensure directory exists
            os.makedirs("data/to-do-list", exist_ok=True)
            file_path = "data/to-do-list/tasks.yaml"
            yaml_content = yaml.safe_dump(tasks)
            file_api.write_file(file_path, yaml_content)
            next_id += 1
            return {"success": True, "tasks": tasks}
        else:
            return {"success": False, "error": "File API not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Delete a task
def delete_task(task_id):
    global tasks
    try:
        task_id = str(task_id)
        if task_id in tasks:
            del tasks[task_id]
            
            file_api = get_file_api()
            if file_api:
                os.makedirs("data/to-do-list", exist_ok=True)
                file_path = "data/to-do-list/tasks.yaml"
                yaml_content = yaml.safe_dump(tasks)
                file_api.write_file(file_path, yaml_content)
                return {"success": True, "tasks": tasks}
            else:
                return {"success": False, "error": "File API not available"}
        else:
            return {"success": False, "error": "Task ID not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Toggle completion status of a task
def toggle_task(task_id):
    global tasks
    try:
        task_id = str(task_id)
        if task_id in tasks:
            tasks[task_id]["completed"] = not tasks[task_id]["completed"]
            
            file_api = get_file_api()
            if file_api:
                os.makedirs("data/to-do-list", exist_ok=True)
                file_path = "data/to-do-list/tasks.yaml"
                yaml_content = yaml.safe_dump(tasks)
                file_api.write_file(file_path, yaml_content)
                return {"success": True, "tasks": tasks}
            else:
                return {"success": False, "error": "File API not available"}
        else:
            return {"success": False, "error": "Task ID not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Initialize tasks on import
load_tasks()
