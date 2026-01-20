/*
JavaScript Frontend for Sanctum Station
This file handles interactive elements and transfer to the python backend for the psuedo-desktop environment to be used.
*/

// Clock functionality
class DesktopClock {
    constructor() {
        this.digitalClockElement = document.getElementById('digitalClock');
        this.dateDisplayElement = document.getElementById('dateDisplay');
        this.sunGlowElement = document.getElementById('sunGlow');
        this.init();
    }

    init() {
        this.updateClock();
        // Update every minute for performance, but still update clock every second
        setInterval(() => this.updateClock(), 1000);
        setInterval(() => this.updateSunGlow(), 60000); // Update glow every minute
    }

    updateClock() {
        const now = new Date();

        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const timeString = `${hours}:${minutes}`;

        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        const dayName = days[now.getDay()];
        const monthName = months[now.getMonth()];
        const date = now.getDate().toString().padStart(2, '0');
        const year = now.getFullYear().toString().slice(-2);
        
        const dateString = `${dayName} ${monthName} ${date} ${year}`;
        
        if (this.digitalClockElement.textContent !== timeString) {
            this.digitalClockElement.textContent = timeString;
            this.digitalClockElement.classList.add('clock-update');
            setTimeout(() => {
                this.digitalClockElement.classList.remove('clock-update');
            }, 300);
        }
        
        this.dateDisplayElement.textContent = dateString;
        
        // Update sun glow on clock update
        this.updateSunGlow();
    }

    updateSunGlow() {
        const now = new Date();
        let hour = now.getHours() + now.getMinutes() / 60;
        
        // Testing Times
        // hour = 7.0; // Test dawn transition (purple to orange-red)
        // hour = 9.0; // Test morning transition (orange-red to yellow)
        // hour = 14.0; // Test midday (bright yellow)
        // hour = 19.0; // Test evening transition (yellow to orange-red)
        // hour = 21.0; // Test dusk transition (orange-red to purple)
        // hour = 2.0; // Test night (dark purple)
        
        let color, intensity;
        
        if (hour >= 6 && hour < 8) {
            // Dawn transition: purple-black to orange-red (6 AM - 8 AM)
            const progress = (hour - 6) / 2;
            color = this.interpolateColor(
                { r: 75, g: 0, b: 130 }, // Dark purple
                { r: 255, g: 69, b: 0 }, // Orange-red
                progress
            );
            intensity = progress * 0.4;
        } else if (hour >= 8 && hour < 10) {
            // Morning transition: orange-red to yellow (8 AM - 10 AM)
            const progress = (hour - 8) / 2;
            color = this.interpolateColor(
                { r: 255, g: 69, b: 0 }, // Orange-red
                { r: 255, g: 255, b: 0 }, // Yellow
                progress
            );
            intensity = progress * 0.3;
        } else if (hour >= 10 && hour < 18) {
            // Day: yellow (10 AM - 6 PM)
            color = { r: 255, g: 255, b: 0 }; // Yellow
            intensity = 0.15;
        } else if (hour >= 18 && hour < 20) {
            // Evening transition: yellow to orange-red (6 PM - 8 PM)
            const progress = (hour - 18) / 2;
            color = this.interpolateColor(
                { r: 255, g: 255, b: 0 }, // Yellow
                { r: 255, g: 69, b: 0 }, // Orange-red
                progress
            );
            intensity = progress * 0.3;
        } else if (hour >= 20 && hour < 22) {
            // Dusk transition: orange-red to purple-black (8 PM - 10 PM)
            const progress = (hour - 20) / 2;
            color = this.interpolateColor(
                { r: 255, g: 69, b: 0 }, // Orange-red
                { r: 75, g: 0, b: 130 }, // Dark purple
                progress
            );
            intensity = progress * 0.4;
        } else {
            // Night: purple-black (10 PM - 6 AM)
            color = { r: 75, g: 0, b: 130 }; // Dark purple
            intensity = 0.3;
        }
        
        const colorString = `rgba(${Math.round(color.r)}, ${Math.round(color.g)}, ${Math.round(color.b)}, ${intensity})`;
        
        if (this.sunGlowElement) {
            this.sunGlowElement.style.setProperty('--sun-color', colorString);
        } else {
            console.log('Sun glow element not found!'); // Debug output
        }
    }

    interpolateColor(color1, color2, progress) {
        return {
            r: color1.r + (color2.r - color1.r) * progress,
            g: color1.g + (color2.g - color1.g) * progress,
            b: color1.b + (color2.b - color1.b) * progress
        };
    }
}

// Button interactions
class DesktopInteractions {
    constructor() {
        this.settingsBtn = document.getElementById('settingsBtn');
        this.centerBtn = document.getElementById('centerBtn');
        this.clockArea = document.getElementById('clockArea');
        this.appLauncher = document.getElementById('appLauncher');
        this.isAppLauncherOpen = false;
        this.apps = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        // Wait for pywebview API to be ready
        this.waitForAPI();
    }

    async waitForAPI() {
        console.log('Waiting for pywebview API...');
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max
        
        while (attempts < maxAttempts) {
            if (window.pywebview && window.pywebview.api) {
                console.log('PyWebview API is ready!');
                await this.loadFont();
                await this.loadApps();
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        console.error('PyWebview API failed to load after 5 seconds');
    }

    async loadFont() {
        try {
            const fonts = await window.pywebview.api.get_fonts();
            if (fonts && Object.keys(fonts).length > 0) {
                console.log('Loading fonts:', fonts);
                
                // Font weight mapping
                const weightMap = {
                    'black_font': 900,
                    'extra_bold_font': 800,
                    'bold_font': 700,
                    'semi_bold_font': 600,
                    'medium_font': 500,
                    'regular_font': 400,
                    'light_font': 300,
                    'extra_light_font': 200,
                    'thin_font': 100
                };
                
                const fontName = 'Inter';
                
                // Load all font weights
                for (const [key, filename] of Object.entries(fonts)) {
                    const weight = weightMap[key];
                    const fontFace = new FontFace(fontName, `url(${filename})`, {
                        weight: weight,
                        style: 'normal'
                    });
                    
                    await fontFace.load();
                    document.fonts.add(fontFace);
                    console.log(`Loaded ${key} (weight ${weight}): ${filename}`);
                }
                
                // Apply the font family to the body
                document.body.style.fontFamily = `"${fontName}", 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`;
                console.log('All fonts loaded and applied successfully');
            }
        } catch (error) {
            console.error('Error loading fonts:', error);
        }
    }

    setupEventListeners() {
        this.settingsBtn.addEventListener('click', () => {
            this.handleSettingsClick();
        });

        this.centerBtn.addEventListener('click', () => {
            this.handleCenterButtonClick();
        });

        document.addEventListener('keydown', (event) => {
            this.handleKeyboardShortcuts(event);
        });

        // Close app launcher when clicking outside (but not on center button)
        document.addEventListener('click', (event) => {
            if (this.isAppLauncherOpen && 
                !this.centerBtn.contains(event.target) && 
                !this.appLauncher.contains(event.target)) {
                // Only close if not clicking the center button
                // The center button has its own handler that toggles
                this.closeAppLauncher();
            }
        });
    }

    async loadApps() {
        try {
            // Load apps from Python backend
            if (window.pywebview && window.pywebview.api) {
                this.apps = await window.pywebview.api.get_apps();
                console.log('=== LOADED APPS ===');
                console.log('Number of apps:', this.apps.length);
                console.log('Apps data:', JSON.stringify(this.apps, null, 2));
                console.log('==================');
            } else {
                console.log('PyWebview API not available yet');
            }
        } catch (error) {
            console.error('Error loading apps:', error);
        }
    }

    handleSettingsClick() {
        console.log('Settings button clicked');
        this.addClickFeedback(this.settingsBtn);
    }

    async handleCenterButtonClick() {
        console.log('Center button clicked');
        console.log('isAppLauncherOpen:', this.isAppLauncherOpen);
        this.addClickFeedback(this.centerBtn);
        
        if (this.isAppLauncherOpen) {
            console.log('Closing app launcher...');
            this.closeAppLauncher();
        } else {
            console.log('Opening app launcher...');
            await this.openAppLauncher();
        }
    }

    async openAppLauncher() {
        this.isAppLauncherOpen = true;
        
        // Reload apps if not loaded yet
        if (!this.apps || this.apps.length === 0) {
            console.log('Apps not loaded, loading now...');
            await this.loadApps();
        }
        
        // Hide clock
        this.clockArea.classList.add('hidden');
        
        // Show app launcher
        this.appLauncher.classList.add('active');
        
        // Display apps in a circle
        this.displayAppsInCircle();
    }

    closeAppLauncher() {
        this.isAppLauncherOpen = false;
        
        // Show clock
        this.clockArea.classList.remove('hidden');
        
        // Hide app launcher
        this.appLauncher.classList.remove('active');
        
        // Clear apps
        this.appLauncher.innerHTML = '';
    }

    displayAppsInCircle() {
        console.log('=== DISPLAY APPS IN CIRCLE ===');
        console.log('App launcher element:', this.appLauncher);
        console.log('Apps array:', this.apps);
        
        this.appLauncher.innerHTML = '';
        
        if (!this.apps || this.apps.length === 0) {
            console.log('No apps to display - apps is empty or null');
            return;
        }

        const numApps = this.apps.length;
        const baseAppsPerRing = 8; // Apps in the first (innermost) ring
        const baseRadius = Math.min(window.innerWidth, window.innerHeight) * 0.25;
        const ringSpacing = Math.min(window.innerWidth, window.innerHeight) * 0.12; // Space between rings
        
        console.log(`Displaying ${numApps} apps with base radius ${baseRadius}px`);
        console.log('Viewport:', window.innerWidth, 'x', window.innerHeight);
        
        // Calculate how many apps fit in each ring to maintain spacing
        const getAppsPerRing = (ringIndex) => {
            const radius = baseRadius + (ringIndex * ringSpacing);
            // Scale apps by radius to maintain arc length between apps
            return Math.round(baseAppsPerRing * (radius / baseRadius));
        };
        
        // Distribute apps across rings
        let appsPlaced = 0;
        let currentRing = 0;
        const ringAssignments = []; // [{ ringIndex, startIndex, count }]
        
        while (appsPlaced < numApps) {
            const appsInThisRing = getAppsPerRing(currentRing);
            const appsToPlace = Math.min(appsInThisRing, numApps - appsPlaced);
            ringAssignments.push({
                ringIndex: currentRing,
                startIndex: appsPlaced,
                count: appsToPlace
            });
            appsPlaced += appsToPlace;
            currentRing++;
        }
        
        console.log('Ring assignments:', ringAssignments);
        
        const maxAppRadius = 10;

        this.apps.forEach((app, index) => {
            // Find which ring this app belongs to
            const ringInfo = ringAssignments.find(r => 
                index >= r.startIndex && index < r.startIndex + r.count
            );
            const ringIndex = ringInfo.ringIndex;
            const indexInRing = index - ringInfo.startIndex;
            const appsInThisRing = ringInfo.count;
            
            // Calculate radius for this ring (increasing outward)
            const radius = baseRadius + (ringIndex * ringSpacing);
            
            // Calculate angle
            const angle = (indexInRing / appsInThisRing) * 2 * Math.PI - Math.PI / 2;
            
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            console.log(`App ${index} (${app.name}): ring=${ringIndex}, indexInRing=${indexInRing}, angle=${angle}, x=${x}, y=${y}, icon=${app.icon}`);
            
            const appIcon = document.createElement('div');
            appIcon.className = 'app-icon';
            appIcon.style.transform = `translate(${x}px, ${y}px)`;
            appIcon.title = app.name;
            console.log('Created app icon element:', appIcon);
            
            // Try to load app icon, fallback to placeholder
            const iconPath = app.icon;
            console.log(`Icon path for ${app.name}:`, iconPath);
            
            if (iconPath) {
                console.log(`Creating img element for ${app.name}`);
                const img = document.createElement('img');
                img.src = iconPath;
                img.alt = app.name;
                img.onload = () => {
                    console.log(`Successfully loaded icon for ${app.name}`);
                };
                img.onerror = () => {
                    console.log(`Failed to load icon for ${app.name}, using placeholder`);
                    appIcon.innerHTML = `<div class="app-icon-placeholder"></div>`;
                };
                appIcon.appendChild(img);
            } else {
                console.log(`No icon path for ${app.name}, using placeholder`);
                appIcon.innerHTML = `<div class="app-icon-placeholder"></div>`;
            }
            
            // Add app name label
            const appLabel = document.createElement('div');
            appLabel.className = 'app-label';
            appLabel.textContent = app.name;
            appIcon.appendChild(appLabel);
            
            // Click handler to launch app
            appIcon.addEventListener('click', async () => {
                console.log(`Launching app: ${app.name}`);
                try {
                    if (window.pywebview && window.pywebview.api) {
                        await window.pywebview.api.launch_app(app.name);
                        this.closeAppLauncher();
                    }
                } catch (error) {
                    console.error(`Error launching app ${app.name}:`, error);
                }
            });
            
            this.appLauncher.appendChild(appIcon);
            console.log(`Appended icon for ${app.name} to launcher`);
        });
        
        console.log('App launcher children count:', this.appLauncher.children.length);
        console.log('App launcher HTML:', this.appLauncher.innerHTML.substring(0, 200));
        console.log('=== END DISPLAY APPS ===');
    }

    handleKeyboardShortcuts(event) {
        const isInInput = event.target.tagName === 'INPUT' || 
                         event.target.tagName === 'TEXTAREA' || 
                         event.target.isContentEditable;
        const isAppOpen = document.querySelector('.app-container') !== null;
        
        // Ctrl+N to toggle notification panel (works anywhere)
        if (event.ctrlKey && event.key === 'n') {
            event.preventDefault();
            toggleNotifications();
            return;
        }
        
        if (isInInput || isAppOpen) {
            return; // Let the event pass through normally
        }
        
        // Escape to close app launcher
        if (event.key === 'Escape' && this.isAppLauncherOpen) {
            this.closeAppLauncher();
        }
        // Space key for center button
        else if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            this.handleCenterButtonClick();
        }
    }

    addClickFeedback(element) {
        element.style.transform = element.style.transform.replace('scale(0.95)', '') + ' scale(0.95)';
        setTimeout(() => {
            element.style.transform = element.style.transform.replace('scale(0.95)', '');
        }, 150);
    }
}

// Responsive design handler
class ResponsiveHandler {
    constructor() {
        this.init();
    }

    init() {
        this.handleResize();
        window.addEventListener('resize', () => this.handleResize());
    }

    handleResize() {
        const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
        
        if (vw < 320) {
            document.documentElement.style.fontSize = '14px';
        } else {
            document.documentElement.style.fontSize = '16px';
        }
    }
}

// Settings functionality
async function loadDayGradient() {
    try {
        console.log('Loading day gradient setting...');
        const dayGradient = await window.pywebview.api.get_day_gradient();
        console.log('Day gradient setting:', dayGradient);
        const sunGlow = document.getElementById('sunGlow');
        
        if (dayGradient !== false) {
            sunGlow.style.display = '';
            console.log('Day gradient enabled');
        } else {
            sunGlow.style.display = 'none';
            console.log('Day gradient disabled');
        }
    } catch (error) {
        console.error('Error loading day gradient:', error);
    }
}

async function loadWallpaper() {
    try {
        console.log('Loading wallpaper...');
        const wallpaperData = await window.pywebview.api.get_wallpaper_data();
        console.log('Wallpaper data received:', wallpaperData ? 'Yes (base64)' : 'None');
        const wallpaperElement = document.getElementById('wallpaper');
        console.log('Wallpaper element:', wallpaperElement);
        
        if (wallpaperData) {
            console.log('Setting wallpaper from data URL');
            wallpaperElement.src = wallpaperData;
            wallpaperElement.style.display = 'block';
            console.log('Wallpaper element display:', wallpaperElement.style.display);
            console.log('Wallpaper loaded successfully');
        } else {
            wallpaperElement.style.display = 'none';
            console.log('Wallpaper is None or empty');
        }
    } catch (error) {
        console.error('Error loading wallpaper:', error);
        document.getElementById('wallpaper').style.display = 'none';
    }
}

// Wait for pywebview API to be ready
function waitForPywebview(callback, maxAttempts = 50) {
    let attempts = 0;
    const checkAPI = setInterval(() => {
        attempts++;
        if (window.pywebview && window.pywebview.api) {
            clearInterval(checkAPI);
            console.log('Pywebview API ready');
            callback();
        } else if (attempts >= maxAttempts) {
            clearInterval(checkAPI);
            console.error('Pywebview API not available after', maxAttempts, 'attempts');
        }
    }, 100);
}

// Notification panel functions
async function toggleNotifications() {
    const notificationPanel = document.getElementById('notificationPanel');
    const isOpen = notificationPanel.classList.contains('open');
    
    if (!isOpen) {
        notificationPanel.classList.add('open');
        await loadNotifications();
    } else {
        notificationPanel.classList.remove('open');
    }
}

async function loadNotifications() {
    try {
        const result = await window.pywebview.api.get_notifications();
        if (result.success) {
            const notifications = result.notifications;
            const content = document.getElementById('notificationPanelContent');
            const badge = document.getElementById('notificationBadge');
            
            if (notifications.length === 0) {
                content.innerHTML = '<p class="no-notifications">No notifications</p>';
                badge.style.display = 'none';
            } else {
                // Sort by timestamp, newest first
                notifications.sort((a, b) => b.timestamp - a.timestamp);
                
                content.innerHTML = notifications.map(notif => {
                    const time = new Date(notif.timestamp * 1000);
                    const timeStr = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                    
                    return `
                        <div class="notification-item">
                            <div class="notification-item-header">
                                <span class="notification-source">${notif.source || 'System'}</span>
                                <span class="notification-time">${timeStr}</span>
                            </div>
                            <div class="notification-message">${notif.message}</div>
                            <button class="notification-delete" onclick="deleteNotification('${notif.id}')">Delete</button>
                        </div>
                    `;
                }).join('');
                
                badge.textContent = notifications.length;
                badge.style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('Failed to load notifications:', error);
    }
}

async function deleteNotification(notificationId) {
    try {
        const result = await window.pywebview.api.delete_notification(notificationId);
        if (result.success) {
            await loadNotifications();
        }
    } catch (error) {
        console.error('Failed to delete notification:', error);
    }
}

async function clearAllNotifications() {
    try {
        const result = await window.pywebview.api.clear_all_notifications();
        if (result.success) {
            await loadNotifications();
        }
    } catch (error) {
        console.error('Failed to clear notifications:', error);
    }
}

// Update notification badge periodically and refresh panel if open
setInterval(async () => {
    try {
        const result = await window.pywebview.api.get_notifications();
        if (result.success) {
            const badge = document.getElementById('notificationBadge');
            const count = result.notifications.length;
            
            if (count === 0) {
                badge.style.display = 'none';
            } else {
                badge.textContent = count;
                badge.style.display = 'flex';
            }
            
            // If notification panel is open, reload it
            const notificationPanel = document.getElementById('notificationPanel');
            if (notificationPanel && notificationPanel.classList.contains('open')) {
                await loadNotifications();
            }
        }
    } catch (error) {
        console.error('Failed to update notification badge:', error);
    }
}, 2000); // Check every 2 seconds

async function toggleSettings() {
    const overlay = document.getElementById('settingsOverlay');
    if (overlay.style.display === 'none' || overlay.style.display === '') {
        // Load current settings
        const settings = await window.pywebview.api.get_settings();
        document.getElementById('wallpaperInput').value = settings.wallpaper || '';
        document.getElementById('dayGradientToggle').checked = settings.day_gradient !== false;
        document.getElementById('fullscreenToggle').checked = settings.fullscreen === true;
        document.getElementById('updatesSelect').value = settings.updates || 'release';
        overlay.style.display = 'flex';
    } else {
        overlay.style.display = 'none';
    }
}

async function saveWallpaper() {
    const wallpaperPath = document.getElementById('wallpaperInput').value.trim();
    try {
        const result = await window.pywebview.api.set_wallpaper(wallpaperPath || 'None');
        if (result) {
            await loadWallpaper();
            alert('Wallpaper updated!');
        } else {
            alert('Failed to update wallpaper.');
        }
    } catch (error) {
        console.error('Error setting wallpaper:', error);
        alert('Error setting wallpaper.');
    }
}

async function removeWallpaper() {
    try {
        const result = await window.pywebview.api.set_wallpaper('None');
        if (result) {
            await loadWallpaper();
            document.getElementById('wallpaperInput').value = '';
        } else {
            alert('Failed to remove wallpaper.');
        }
    } catch (error) {
        console.error('Error removing wallpaper:', error);
        alert('Error removing wallpaper.');
    }
}

async function setDefaultWallpaper(path) {
    try {
        const result = await window.pywebview.api.set_wallpaper(path);
        if (result) {
            await loadWallpaper();
            document.getElementById('wallpaperInput').value = path;
        } else {
            alert('Failed to set wallpaper.');
        }
    } catch (error) {
        console.error('Error setting wallpaper:', error);
        alert('Error setting wallpaper.');
    }
}

async function saveDayGradient() {
    const enabled = document.getElementById('dayGradientToggle').checked;
    try {
        const result = await window.pywebview.api.set_day_gradient(enabled);
        if (result) {
            // Update the sun glow immediately
            const sunGlow = document.getElementById('sunGlow');
            if (enabled) {
                sunGlow.style.display = '';
                const clock = window.SanctumStation?.clock;
                if (clock) clock.updateSunGlow();
            } else {
                sunGlow.style.display = 'none';
            }
        } else {
            alert('Failed to update day gradient setting.');
        }
    } catch (error) {
        console.error('Error setting day gradient:', error);
        alert('Error setting day gradient.');
    }
}

async function saveFullscreen() {
    const enabled = document.getElementById('fullscreenToggle').checked;
    try {
        const result = await window.pywebview.api.set_fullscreen(enabled);
        if (!result) {
            alert('Failed to update fullscreen setting.');
        }
    } catch (error) {
        console.error('Error setting fullscreen:', error);
        alert('Error setting fullscreen.');
    }
}

async function toggleFullscreen() {
    try {
        // Get current setting and toggle it
        const settings = await window.pywebview.api.get_settings();
        const newState = !settings.fullscreen;
        
        await window.pywebview.api.set_fullscreen(newState);
        
        // Update toggle in settings if it exists
        const toggle = document.getElementById('fullscreenToggle');
        if (toggle) toggle.checked = newState;
    } catch (error) {
        console.error('Error toggling fullscreen:', error);
    }
}

async function saveUpdates() {
    const channel = document.getElementById('updatesSelect').value;
    try {
        const result = await window.pywebview.api.set_updates(channel);
        if (result) {
            console.log('Updates channel set to:', channel);
        } else {
            alert('Failed to update channel setting.');
        }
    } catch (error) {
        console.error('Error setting updates channel:', error);
        alert('Error setting updates channel.');
    }
}

// Check if there's an update available and show notification
async function checkForUpdateNotification() {
    try {
        const updateInfo = await window.pywebview.api.get_available_update();
        if (updateInfo) {
            // Store the download URL globally
            window.updateUrl = updateInfo.url;
            
            // Populate the update popup
            document.getElementById('updateVersion').textContent = updateInfo.version;
            document.getElementById('updateType').textContent = updateInfo.type;
            
            // Clean up and parse markdown in description
            let description = updateInfo.description || 'No description available.';
            
            // Remove "Changes:\n" from the beginning
            if (description.startsWith('Changes:')) {
                description = description.substring(9);
            }
            
            // Remove "\nAll Changes: [link]" from the end
            const allChangesIndex = description.indexOf('\nAll Changes:');
            if (allChangesIndex !== -1) {
                description = description.substring(0, allChangesIndex);
            }
            
            const changesElement = document.getElementById('updateChanges');
            if (typeof marked !== 'undefined') {
                changesElement.innerHTML = marked.parse(description);
            } else {
                changesElement.textContent = description;
            }
            
            // Show the overlay
            const updateOverlay = document.getElementById('updateOverlay');
            updateOverlay.style.display = 'flex';
        }
    } catch (error) {
        console.error('Error checking for update notification:', error);
    }
}

// Dismiss the update notification
function dismissUpdate() {
    const updateOverlay = document.getElementById('updateOverlay');
    updateOverlay.style.display = 'none';
}

// Listen for fullscreen changes (not needed for pywebview but kept for compatibility)
document.addEventListener('fullscreenchange', async () => {
    const toggle = document.getElementById('fullscreenToggle');
    if (toggle) {
        toggle.checked = !!document.fullscreenElement;
    }
});


document.addEventListener('DOMContentLoaded', () => {
    console.log('Sanctum Station Desktop Environment initialized');

    const clock = new DesktopClock();
    const interactions = new DesktopInteractions();
    const responsive = new ResponsiveHandler();
    
    // Global variable to store update URL
    window.updateUrl = '';
    
    // Wait for pywebview API to be ready before loading wallpaper
    waitForPywebview(() => {
        loadWallpaper();
        loadDayGradient();
        checkForUpdateNotification();
    });
    
    window.SanctumStation = {
        clock,
        interactions,
        responsive
    };
});