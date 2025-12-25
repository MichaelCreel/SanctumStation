# Sanctum Station

A developer-focused pseudo-desktop environment built with Python and PyWebview.

## Overview

Sanctum Station is a customizable desktop environment designed specifically for developers. It provides a collection of integrated productivity apps in a clean, modern interface.

## Installation

### Requirements
- Python 3.8 or higher
- GTK+ 3 (for Linux)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/MichaelCreel/SanctumStation.git
cd SanctumStation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run Sanctum Station:
```bash
cd src
python3 backend.py
```

## Built-in Apps

### Core Apps
- **Clock** - Display current time and date
- **Calculator** - Scientific calculator with trigonometric functions
- **Text Editor** - Simple text editing capabilities
- **File Browser** - Navigate and manage your file system
- **Focus Timer** - Pomodoro-style focus/break timer

### Developer Apps (New!)

#### Terminal
An embedded terminal emulator for executing shell commands directly within Sanctum Station.
- Execute shell commands with output display
- Command history navigation (up/down arrows)
- Current working directory tracking
- `cd` command support with state persistence

**Security Note**: The terminal executes commands with full shell access. This is intended for local developer use only. Do not expose to untrusted users or networks.

#### Git Manager
Visual Git repository management interface.
- View repository status and changed files
- Commit changes with custom messages
- Branch management (view, create, checkout)
- View commit history
- Pull and push to remote repositories
- Execute custom git commands

#### API Tester
HTTP/REST API testing tool for developers.
- Support for GET, POST, PUT, DELETE, PATCH methods
- Custom headers configuration (JSON or key:value format)
- Request body editor with JSON support
- Response display with status codes and timing
- Pretty-print JSON responses

#### System Monitor
Real-time system resource monitoring.
- CPU usage and frequency monitoring
- Memory and swap usage tracking
- Disk usage for all partitions
- Network statistics (bytes sent/received, packets)
- Top processes by CPU usage
- System information (platform, architecture, uptime)
- Auto-refresh toggle (updates every 2 seconds)

#### Data Formatter
Multi-purpose data formatting and conversion tool.
- JSON formatting (pretty-print with configurable indentation)
- JSON minification
- JSON validation with error messages
- JSON ↔ YAML conversion
- YAML validation
- Base64 encoding/decoding
- Copy output to clipboard

## Usage

### Launching Apps
1. Click the center logo button to open the app launcher
2. Click on any app icon to launch it
3. Apps appear in fullscreen overlay mode
4. Click the × button in the top-right to close an app

### Keyboard Shortcuts
- **Escape** - Close app launcher
- **Space/Enter** - Toggle app launcher
- App-specific shortcuts documented within each app

## Configuration

Settings are stored in `data/settings.yaml`:
- `version` - Current version
- `wallpaper` - Wallpaper setting (currently "None")
- `day_gradient` - Enable/disable time-of-day gradient overlay
- Font settings for the Inter font family

## Development

### Adding New Apps

1. Create a new directory in `src/apps/YourAppName/`
2. Create `app.py` (backend logic)
3. Create `app.html` (frontend UI)
4. Add an `icon.png` (128x128 recommended)

Example app.py structure:
```python
def main(stop_event=None):
    import time
    print("Your App backend started")
    while True:
        if stop_event and stop_event.is_set():
            print("Your App backend stopping...")
            break
        time.sleep(0.5)
```

Functions defined in app.py can be called from the frontend using:
```javascript
await window.pywebview.api.call_app_function('YourAppName', 'function_name', arg1, arg2);
```

## Technologies

- **Backend**: Python 3, PyWebview
- **Frontend**: HTML, CSS, JavaScript
- **Dependencies**: PyYAML, psutil, requests

## License

MIT License - see LICENSE file for details

## Contributing

This project is a work in progress. Contributions, ideas, and feedback are welcome!

## Future Enhancements

Potential additions being considered:
- Code snippet manager with syntax highlighting
- Markdown previewer
- Database query tool
- Docker container manager
- Package manager interfaces
- SSH session manager
- Custom plugin system

## Credits

Developed by Michael Creel
