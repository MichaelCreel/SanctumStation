## 4
# Notification Manager API

Notification API sends notifications from apps.
It is exposed through `window.pywebview.api`.

## Frontend Usage

```javascript
await window.pywebview.api.send_notification('Hello from app');
const result = await window.pywebview.api.get_notifications();
```

## Backend Usage

```python
import backend

def notify(message):
    notification_api = backend.NotificationManagerAPI()
    return notification_api.send_notification(message)
```

## Methods and Return Contracts

### send_notification(message)

Creates a notification entry with:

1. message
2. timestamp
3. source (inferred from calling module when possible)

Returns:

```json
{
    "success": true,
    "notification_id": "1730000000000",
    "source": "AppIdOrUnknown"
}
```

### delete_notification(notification_id)

Success:

```json
{"success": true}
```

Failure:

```json
{"success": false, "error": "Notification ID not found"}
```

### get_notifications()

Returns:

```json
{
    "success": true,
    "notifications": [
        {
            "id": "1730000000000",
            "message": "...",
            "timestamp": 1730000000.0,
            "source": "..."
        }
    ]
}
```

### clear_all_notifications()

Returns:

```json
{"success": true}
```