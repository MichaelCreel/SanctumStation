## 2
# API

The API is a class in the backend that is accessible through webview.
This API allows apps to call methods in the backend.
It creates the file manager, settings manager, notification manager, and error manager that apps can access.
Some of the functions exposed in the API are not useful for most apps and are designed specifically for the system.
For example, the error manager calls a function to access errors.json.
Only system errors are stored in errors.json, so accessing these functions from an app are useless.