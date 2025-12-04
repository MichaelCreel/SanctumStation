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
        let hour = now.getHours() + now.getMinutes() / 60; // Include minutes for smoother transitions
        
        // Testing Times - Uncomment ONE line below to test different times:
        // hour = 7.0; // Test dawn transition (purple to orange-red)
        // hour = 9.0; // Test morning transition (orange-red to yellow)
        // hour = 14.0; // Test midday (bright yellow)
        // hour = 19.0; // Test evening transition (yellow to orange-red)
        // hour = 21.0; // Test dusk transition (orange-red to purple)
        // hour = 2.0; // Test night (dark purple)
        
        let color, intensity;
        
        console.log(`Current hour: ${hour.toFixed(2)}`); // Debug output
        
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
        
        console.log(`Sun glow color: ${colorString}`); // Debug output
        
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
        this.init();
    }

    init() {
        this.setupEventListeners();
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
    }

    handleSettingsClick() {
        console.log('Settings button clicked');
        this.addClickFeedback(this.settingsBtn);
    }

    handleCenterButtonClick() {
        console.log('Center button clicked');
        this.addClickFeedback(this.centerBtn);
    }

    handleKeyboardShortcuts(event) {
        // Space key for center button
        if (event.key === ' ' || event.key === 'Enter') {
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

document.addEventListener('DOMContentLoaded', () => {
    console.log('Sanctum Station Desktop Environment initialized');

    const clock = new DesktopClock();
    const interactions = new DesktopInteractions();
    const responsive = new ResponsiveHandler();
    
    window.SanctumStation = {
        clock,
        interactions,
        responsive
    };
});