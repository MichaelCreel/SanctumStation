################################################################################
# Text Editor Backend for Sanctum Station
################################################################################

from backend import FileManagerAPI

def open_file(self, path):
    content = FileManagerAPI.read_file(self, path)
    return content

def save_file(self, path, content):
    success = FileManagerAPI.write_file(self, path, content)
    return success