## 5
# File Injection

File injection means launching an app with a file path passed into the app to launch with.
This is useful for the File Browser because apps can be launched based on their file extension, but other use cases apply.
There is no pattern that will fit all apps perfectly because of differences in app design, but some patterns can be used as a basis.

### Core Idea

1. The launcher calls the backend with app id and file path.
2. The backend launches the app and forwards the file path to:
   - Python app entrypoint (if supported), and
   - JavaScript launch context.
3. The app reads file path in Python, JS, or both.

### 1. Launch App With File Path

From frontend JavaScript:

```javascript
await window.pywebview.api.launch_app(appId, filePath);
```

- appId should be the app id (folder name), not display name.
- filePath can be absolute or a path your app can resolve.

### 2. Add Extension Metadata To App

In app_config.json:

```json
{
  "name": "Whiteboard",
  "extensions": [
    ".json"
  ]
}
```

This allows launcher logic (like File Browser) to decide which apps can open a file.

### 3. Python Entrypoint Injection Pattern

If your app has backend startup logic, use a main function that accepts file_path.

```python
def main(stop_event=None, file_path=None):
    # Optional startup behavior
    if file_path:
        # Validate extension, parse, preload state, etc.
        pass

    # Optional background loop
    while stop_event and not stop_event.is_set():
        pass
```

You can also use run(stop_event=None, file_path=None).

### 4. JavaScript Launch Context Injection Pattern

When an app is launched with a file path, the global launch context can be read from JavaScript:

```javascript
function getLaunchFilePath(appId) {
    const byApp = window.__SANCTUM_LAUNCH_CONTEXT_BY_APP || {};
    const ctx = byApp[appId] || window.__SANCTUM_LAUNCH_CONTEXT;
    return (ctx && typeof ctx.filePath === 'string' && ctx.filePath.trim())
        ? ctx.filePath
        : null;
}
```

This is usually the easiest way to update UI on startup.

### 5. App-Side Load Pattern (JS)

Use this when your app renders data directly in frontend code.

```javascript
async function loadInjectedFile(appId) {
    const filePath = getLaunchFilePath(appId);
    if (!filePath) return;

    const content = await window.pywebview.api.read_file(filePath);
    // Parse content and render state
}
```

Call it during app startup after UI init.

### 6. Recommended Validation

Before loading injected file:

1. Check extension support.
2. Confirm file exists.
3. Handle parse errors cleanly.
4. Show a user message if load fails.

Example:

```javascript
if (!filePath.toLowerCase().endsWith('.json')) {
    await showMessageModal('Open Failed', 'Unsupported file type for this app.');
    return;
}
```

### 7. Open-With Flow (Multiple Apps)

Recommended behavior in launchers like File Browser:

1. Find all apps whose extensions contain the file extension.
2. If one app matches: launch it directly.
3. If multiple apps match: show picker with icon + display name.
4. If no apps match: offer fallback (for example "Open in Text Editor").

### 8. Practical Notes

1. Use app id for launching and callbacks.
2. Keep display name user-facing only.
3. If one app launches another, close or hide the first app UI if overlap causes conflicts.
4. Keep parsing logic inside the target app; launcher should only route and pass file path.
