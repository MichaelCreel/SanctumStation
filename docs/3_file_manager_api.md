## 3
# File Manager API

The File Manager API is the interface for accessing file functions.
This interface makes file interactions simple for developers by dealing with directories, permissions, and devices.
The File Manger API is accessed through the public API.

### Accessing the File Manager
To access the file manager, I recommend that you create a method to use for all file functions.

```
def get_file_api():
    main_backend = sys.modules.get('__main__')
    if main_backend and hasattr(main_backend, 'FileManagerAPI')
        return main_backend.FileManagerAPI()
    return None
```

Then the function can be accessed by using this method.
Writing to a file is used as an example here.

```
def write(text, path):
    file_api = get_file_api()
    if file_api():
        file_api.write_file(file_path, text)
```

### Exposed Functions

These are the functions that the File Manager API exposes.

**List Directory**

list_directory

Lists the contents of a directory in an array.
This array contains the name, full path, type (file or folder), size, and the last date of modification of every item accessible in the directory.

*Input*

Path

*Output*

Array of items
[
name:
path:
type:
size:
modified:
]

**Read File**

read_file

Returns the contents of a file as a string.

*Input*

Path

*Output*

String

**Write File**

write_file

Writes a string to a file.

*Input*

Path
Content

*Output*

True/False Success

**Delete File**

delete_file

Deletes a file.

*Input*

Path

*Output*

True/False Success

**Delete Directory**

delete_directory

Deletes a directory/folder.

*Input*

Path

*Output*

True/False Success

**Create Directory**

create_directory

Creates a directory/folder.

*Input*

Path

*Output*

True/False Success

**Create File**

create_file

Creates an empty file.

*Input*

Path

*Output*

True/False Success

**Rename Item**

rename_item

Renames a file or directory/folder.

*Input*

Old Path
New Name

*Output*

True/False Success
Error String

**Move Item**

move_item

Moves a file or directory/folder to a new location

*Input*

Source Path
Destination Path

*Output*

True/False Success

**Copy Item**

copy_item

Duplicates a file or directory/folder in a new location.

*Input*

Source Path
Duplicate Destination Path

*Output*

True/False Success

**Get Metadata**

get_metadata

Returns the size, last modified date, creation date, and is directory boolean of a file or directory/folder.

*Input*

Path

*Output*

Size
Last Modified
Creation
Is Directory

**Exists**

exists

Checks if a file or directory/folder exists.

*Input*

Path

*Output*

True/False