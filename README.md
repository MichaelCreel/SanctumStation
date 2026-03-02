# Sanctum Station

Sanctum Station is a powerful psuedo-desktop designed to connect your desktop and workflows together seamlessly. Automatic connection integrates your devices directly into each other, making parallel operation simple and easy. Sanctum Station comes with productivity apps pre-installed to kickstart your workflow and is available on both desktop and Android mobile devices.

The current version of Sanctum Station is not ready for full release and is intended for development and testing only. Installation instructions are included but are intended for a technologically experienced audience.

## Features

- **Cross-Platform**: Sanctum Station runs on Windows, Mac, Linux, and Android to link your workflow on almost any device.
- **Built-in Apps**: Sanctum Station comes with built in apps to kickstart your workflow without delay.
- **Mobile Support**: The Sanctum Station Android APK supports both 32-bit and 64-bit Android devices for maximum compatibility.

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

**Desktop:**
1. Install all dependencies.
2. Download the 'Desktop' zip file from [Releases](https://github.com/MichaelCreel/SanctumStation/releases)
3. Extract the zip file and open the extracted folder.
4. Run `./src/backend.py`.

**Mobile:** ([Installation Guide](https://michaelcreel.github.io/android-instructions/android-instructions.html))
1. Download the 'Mobile' zip file from [Releases](https://github.com/MichaelCreel/SanctumStation/releases)
2. Open files app.
3. Open downloads folder.
4. Open the downloaded zip file.
5. Extract the files and open the extracted folder.
6. Open the APK file.
7. Install the app.
8. Run the app.

## Testing Notes

- The app is tested mainly on three devices. Missing functionality may be missed disproportionately on some devices.
  - **Mobile Devices**:
    - 64 Bit Android 9 Samsung Galaxy Tab S3
    - 32 Bit Android 13 Samsung Galaxy A13 5G
  - **Desktop Devices**
    - 64 Bit Linux Mint Dell Precision 7780
      - *Why Not Report The System Version*: The system is kept up-to-date with packages and versions. No persistent versions are kept.

## Known Issues

- The app currently has no way to connect your mobile device to your computer. This is planned for a future release.
- The Android package occasionally fails to work with 32-bit devices. This is repeatedly fixed to stay compatible with these devices, but may not work consistently.

## Development Notes

- This app is packaged using a packaging script that contains sensitive information like keystores. This script is kept hidden for security reasons. This may slow modification to the main app but should not prevent development inside the app.
- The app uses Python 3.11 to ensure compatibility with both 32-bit and 64-bit devices. If library imports fail, check what version of Python they require to run.

## Licenses

MIT License

The published Sanctum Station app and pre-installed sub-apps are all under MIT License. Some related items are withheld for security and fraud prevention.
