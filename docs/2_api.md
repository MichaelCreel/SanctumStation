## 2
# API

The API is a class in the backend that is accessible through `window.pywebview.api`.
This API allows apps to call methods in the backend.
It creates the file manager, settings manager, notification manager, and error manager that apps can access.
Some of the functions exposed in the API are not useful for most apps and are designed specifically for the system.
For example, the error manager calls a function to access errors.json.
Only system errors are stored in errors.json, so accessing these functions from an app are useless.

## Access Pattern (Frontend)

```javascript
const apps = await window.pywebview.api.get_apps();
await window.pywebview.api.launch_app('Text-Editor', '/absolute/or/relative/path.txt');
```

## Major API Groups

### App Management and App-To-Backend Calls

1. `launch_app(app_name, file_path=None)`
2. `stop_app(app_name)`
3. `get_apps()`
4. `get_running_apps()`
5. `fuzzy_search_apps(query)`
6. `call_app_function(app_name, function_name, *args, **kwargs)`

### File Manager

1. `list_directory(path)`
2. `read_file(path)`
3. `write_file(path, content)`
4. `delete_file(path)`
5. `delete_directory(path)`
6. `create_directory(path)`
7. `create_file(path)`
8. `rename_item(old_path, new_name)`
9. `move_item(src, dest)`
10. `copy_item(src, dest)`
11. `get_metadata(path)`
12. `exists(path)`
13. `get_storage_path(sub_path="", is_data=True)`

### Settings and Environment

1. `get_settings()`
2. `get_fonts()`
3. `get_version()`
4. `get_wallpaper()`
5. `get_wallpaper_data()`
6. `get_day_gradient()`
7. `get_fullscreen()`
8. `set_wallpaper(path)`
9. `set_day_gradient(enabled)`
10. `set_fullscreen(enabled)`
11. `set_font(weight, font_path)`
12. `set_updates(channel)`
13. `set_logo(logo_type)`
14. `set_ui_scale(scale)`
15. `get_available_update()`

### Notifications

1. `send_notification(message)`
2. `delete_notification(notification_id)`
3. `get_notifications()`
4. `clear_all_notifications()`

### Errors and JavaScript Logs

1. `display_error(code)`
2. `get_error(code)`
3. `js_log(level, message)`

## Notes

- `launch_app` supports optional `file_path` for file injection workflows
- `get_apps()` returns app id + display name + extension metadata from `app_config.json` when available
- `call_app_function` expects app id for reliability when display names are duplicated