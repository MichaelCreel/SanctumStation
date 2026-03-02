## 4
# Notification Manager API

The Notification Manager API is the interface for accessing notification functions.
This interface links to the notification menu on the homepage of the environment.
The Notification Manager API is accessed through the public API.

### Accessing the Notification Manager
To access the notification manager and send notifications, only one method is necessary.

```
def notify(message):
    main_backend = sys.modules.get('__main__')
    if main_backend and hasattr(main_backend, 'NotificationManagerAPI'):
        notification_api = main_backend.NotificationManagerAPI()
        return notification_api.send_notification(message)
    return None
```

### Exposed Functions

These are the functions that the Notification Mangager API exposes.

**Send Notification**

send_notification

Sends a notification.

*Input*

String

*Output*

True Success
Notification ID
Source