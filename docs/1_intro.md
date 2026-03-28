## 1
# Introduction

Welcome to the documentation for Sanctum Station.
These documents have been created to show developers how to use functions of Sanctum Station and start app development.
I cannot garuntee that documentation will be up-to-date, but most functionality should not change with updates.
The source code for this app is open-source, so functions and apps can be looked at directly if the documentation is out-dated.
These docs will not go in-depth on the code for the project; they will summarize how certain features work and describe how to use the backend functions.

## Model

Sanctum Station has two basic platform targets:

1. Desktop
    - Supports Windows, Mac, and Linux
    - Uses PyWebView to locally host the frontend
2. Mobile
    - Supports Android
    - Uses Toga to run the app (downgraded to Python 3.11 for 32-bit device compatibility)
    - Uses a mobile bridge to communicate with backend and work around permission restrictions

Frontend app code should call `window.pywebview.api.*` in both cases.
On mobile, the bridge maps those calls to `http://127.0.0.1:5000/api/<method>`.

## App Model

Apps are loaded from `src/apps/<AppId>/` and require:

1. `app.html`
2. `app.py`

Apps can also have these two files, but are not required to:

1. `icon.png`
2. `app_config.json` (display name + extension metadata)

## Docs Index

1. `1_intro.md` - You're reading it.
2. `2_api.md` - Public API surface exposed to app/frontend code.
3. `3_file_manager_api.md` - File operations and exact return contracts.
4. `4_notification_manager_api.md` - Notification API (still available, mostly legacy/testing use).
5. `5_file_injection.md` - File path injection and launch context patterns.