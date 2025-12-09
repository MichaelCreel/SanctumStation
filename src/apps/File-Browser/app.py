################################################################################
# File Browser Backend for Sanctum Station
################################################################################

from backend import FileManagerAPI


def list_directory(self, path):
    items = FileManagerAPI.list_directory(self, path)
    return items

def rename_item(self, old_path, new_path):
    success = FileManagerAPI.rename_item(self, old_path, new_path)
    return success

def delete_item(self, path):
    success = FileManagerAPI.delete_item(self, path)
    return success

def create_folder(self, path):
    success = FileManagerAPI.create_folder(self, path)
    return success

def move_item(self, src_path, dest_path):
    success = FileManagerAPI.move_item(self, src_path, dest_path)
    return success

def copy_item(self, src_path, dest_path):
    success = FileManagerAPI.copy_item(self, src_path, dest_path)
    return success

def get_metadata(self, path):
    metadata = FileManagerAPI.get_metadata(self, path)
    return metadata

def main(stop_event=None):
    import time
    print("File-Browser backend started")
    while True:
        # Check if we should stop
        if stop_event and stop_event.is_set():
            print("File-Browser backend stopping...")
            break
        time.sleep(0.5)