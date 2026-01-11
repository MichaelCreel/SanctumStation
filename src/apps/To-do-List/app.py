################################################################################
# To-do List Backend for Sanctum Station
################################################################################

from backend import FileManagerAPI
import yaml

next_id = 0
tasks = {}

# Loads tasks from file
def load_tasks():
    global tasks, next_id
    try:
        with open("data/todolist.yaml", "r") as file:
            tasks = yaml.safe_load(file) or {}
            # Set next_id to one higher than the highest existing ID
            if tasks:
                next_id = max(int(k) for k in tasks.keys()) + 1
            else:
                next_id = 0
            return tasks
    except FileNotFoundError:
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
        with open("data/todolist.yaml", "w") as file:
            yaml.safe_dump(tasks, file)
        next_id += 1
        return {"success": True, "tasks": tasks}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Delete a task
def delete_task(task_id):
    global tasks
    try:
        task_id = str(task_id)
        if task_id in tasks:
            del tasks[task_id]
            with open("data/todolist.yaml", "w") as file:
                yaml.safe_dump(tasks, file)
            return {"success": True, "tasks": tasks}
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
            with open("data/todolist.yaml", "w") as file:
                yaml.safe_dump(tasks, file)
            return {"success": True, "tasks": tasks}
        else:
            return {"success": False, "error": "Task ID not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Initialize tasks on import
load_tasks()
