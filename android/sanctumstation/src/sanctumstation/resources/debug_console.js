// On-screen debug console for mobile debugging
(function() {
    'use strict';
    
    console.log('[Debug Console] Initializing on-screen console');
    
    // Create console UI
    const consoleDiv = document.createElement('div');
    consoleDiv.id = 'debug-console';
    consoleDiv.style.cssText = `
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 300px;
        background: rgba(0, 0, 0, 0.95);
        color: #0f0;
        font-family: monospace;
        font-size: 11px;
        padding: 10px;
        overflow-y: auto;
        z-index: 999999;
        border-top: 2px solid #0f0;
        display: flex;
        flex-direction: column;
    `;
    
    // Create header with controls
    const header = document.createElement('div');
    header.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
        padding-bottom: 5px;
        border-bottom: 1px solid #0f0;
        flex-shrink: 0;
    `;
    
    const title = document.createElement('span');
    title.textContent = 'Debug Console';
    title.style.fontWeight = 'bold';
    
    const controls = document.createElement('div');
    
    const clearBtn = document.createElement('button');
    clearBtn.textContent = 'Clear';
    clearBtn.style.cssText = `
        background: #0f0;
        color: #000;
        border: none;
        padding: 3px 8px;
        margin-right: 5px;
        cursor: pointer;
        font-family: monospace;
    `;
    
    const toggleBtn = document.createElement('button');
    toggleBtn.textContent = 'Hide';
    toggleBtn.style.cssText = `
        background: #0f0;
        color: #000;
        border: none;
        padding: 3px 8px;
        cursor: pointer;
        font-family: monospace;
    `;
    
    controls.appendChild(clearBtn);
    controls.appendChild(toggleBtn);
    header.appendChild(title);
    header.appendChild(controls);
    
    // Create output area
    const output = document.createElement('div');
    output.id = 'debug-console-output';
    output.style.cssText = `
        flex: 1;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
    `;
    
    consoleDiv.appendChild(header);
    consoleDiv.appendChild(output);
    
    // Add to page when DOM is ready
    function addToPage() {
        if (document.body) {
            document.body.appendChild(consoleDiv);
            console.log('[Debug Console] Added to page');
        } else {
            setTimeout(addToPage, 100);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addToPage);
    } else {
        addToPage();
    }
    
    // Toggle visibility
    let isVisible = true;
    toggleBtn.onclick = function() {
        isVisible = !isVisible;
        output.style.display = isVisible ? 'block' : 'none';
        toggleBtn.textContent = isVisible ? 'Hide' : 'Show';
        consoleDiv.style.height = isVisible ? '300px' : '35px';
    };
    
    // Clear console
    clearBtn.onclick = function() {
        output.innerHTML = '';
        addLog('INFO', '[Debug Console] Cleared');
    };
    
    // Add log entry
    function addLog(type, ...args) {
        const entry = document.createElement('div');
        entry.style.marginBottom = '2px';
        
        const timestamp = new Date().toLocaleTimeString();
        let color = '#0f0';
        
        switch(type) {
            case 'ERROR':
                color = '#f00';
                break;
            case 'WARN':
                color = '#ff0';
                break;
            case 'INFO':
                color = '#0ff';
                break;
            case 'LOG':
                color = '#0f0';
                break;
        }
        
        entry.style.color = color;
        
        // Format arguments
        const message = args.map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg, null, 2);
                } catch(e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
        
        entry.textContent = `[${timestamp}] [${type}] ${message}`;
        output.appendChild(entry);
        
        // Auto-scroll to bottom
        output.scrollTop = output.scrollHeight;
        
        // Limit to 500 entries
        while (output.children.length > 500) {
            output.removeChild(output.firstChild);
        }
    }
    
    // Intercept console methods
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    const originalInfo = console.info;
    
    console.log = function(...args) {
        addLog('LOG', ...args);
        originalLog.apply(console, args);
    };
    
    console.error = function(...args) {
        addLog('ERROR', ...args);
        originalError.apply(console, args);
    };
    
    console.warn = function(...args) {
        addLog('WARN', ...args);
        originalWarn.apply(console, args);
    };
    
    console.info = function(...args) {
        addLog('INFO', ...args);
        originalInfo.apply(console, args);
    };
    
    // Catch unhandled errors
    window.addEventListener('error', function(event) {
        addLog('ERROR', 'Uncaught Error:', event.message, 'at', event.filename + ':' + event.lineno);
    });
    
    window.addEventListener('unhandledrejection', function(event) {
        addLog('ERROR', 'Unhandled Promise Rejection:', event.reason);
    });
    
    addLog('INFO', '[Debug Console] Ready - All console outputs will appear here');
})();
