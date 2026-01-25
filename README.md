# Sanctum Station

Sanctum Station is a powerful productivity tool designed to connect your desktop and workflows together seamlessly. Automatic connection integrates your devices directly into each other, making parrelel operation simple and easy. Sanctum Station comes with a few productivity apps pre-installed to kickstart your workflow.

The current version of Sanctum Station is not ready for full release and is intended for development and testing only. Installation instructions are included, but these are intended for development only.

## Dependencies

- Python
  - Windows:
    Install [Python 3](https://python.org)
    Check "Add Python to PATH" during installation
  - Mac:
    ```bash
    brew install python
    ```
  - Linux:
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip
    ```
- PyWebView
- PyYAML
- Requests
- Rapid Fuzz

## Installation

1. Install all dependencies
2. Download the Sanctum Station zip file from [Releases](https://github.com/MichaelCreel/SanctumStation/releases)
3. Run `backend.py`

## Known Issues

- App currently has no way to connect your mobile device to your computer. This is planned for a future release.
- App currently has no mobile gestures or support. This is because of the issue above.

## Licenses

MIT License

The Sanctum Station app and pre-installed sub-apps are all under MIT License.