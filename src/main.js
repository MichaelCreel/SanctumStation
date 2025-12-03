/*
JavaScript Frontend for Sanctum Station
This file handles interactive elements and transfer to the python backend for the psuedo-desktop environment to be used.
*/

// Clock functionality
class DesktopClock {
    constructor() {
        this.digitalClockElement = document.getElementById('digitalClock');
        this.dateDisplayElement = document.getElementById('dateDisplay');
        this.init();
    }

    init() {
        this.updateClock();

        setInterval(() => this.updateClock(), 1000);
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