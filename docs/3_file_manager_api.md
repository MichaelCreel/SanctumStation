## 3
# File Manager API

The File Manager API handles file and directory operations for apps.
It is exposed through `window.pywebview.api` and normalized for desktop/mobile path behavior.

## Frontend Usage

```javascript
const items = await window.pywebview.api.list_directory(path);
const content = await window.pywebview.api.read_file(path);
const ok = await window.pywebview.api.write_file(path, content);
```

## Backend Usage

```python
import backend

def get_file_api():
        return backend.FileManagerAPI()
```

## Path Behavior

For most methods, non-absolute paths are resolved relative to `DATA_DIR`.
Use `get_storage_path(sub_path="", is_data=True)` when you need the actual absolute root.

## Methods and Return Contracts

### list_directory(path)

Returns an array of items:

```json
[
    {
        "name": "example.txt",
        "path": "/absolute/path/example.txt",
        "type": "file",
        "size": 123,
        "modified": 1730000000000
    }
]
```

On error: returns `[]`.

### read_file(path)

Returns file content as string.
On error: returns empty string `""`.

### write_file(path, content)

Writes string content. Creates parent directories when needed.
Returns `True` on success, `False` on failure.

### delete_file(path)

Returns `True` on success, `False` on failure.

### delete_directory(path)

Uses recursive removal.
Returns `True` on success, `False` on failure.

### create_directory(path)

Creates directory recursively if needed.
Returns `True` on success, `False` on failure.

### create_file(path)

Creates an empty file.
Returns `True` on success, `False` on failure.

### rename_item(old_path, new_name)

Important: second parameter is `new_name`, not full new path.

Returns:

```json
{"success": true, "new_path": "/new/absolute/path"}
```

On failure:

```json
{"success": false, "error": "..."}
```

### move_item(src, dest)

Moves file/folder to destination.
Returns `True` on success, `False` on failure.

### copy_item(src, dest)

Copies file/folder to destination.
Returns `True` on success, `False` on failure.

### get_metadata(path)

Returns:

```json
{
    "size": 123,
    "modified": 1730000000.0,
    "created": 1730000000.0,
    "is_directory": false
}
```

On failure: returns `{}`.

### exists(path)

Returns `True` / `False`.

### get_storage_path(sub_path="", is_data=True)

Returns absolute base path:

1. `is_data=True`: data storage root
2. `is_data=False`: apps storage root

If `sub_path` is provided, it is appended to the selected root.