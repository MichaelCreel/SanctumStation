/**
 * Console Bridge - Routes JavaScript console to Python stdout
 */
(function() {
    const isMobile = window.location.protocol === 'http:' && 
                     window.location.hostname === '127.0.0.1' &&
                     window.location.port === '5000';
    
    if (!isMobile) return;
    
    function sendLog(level, ...args) {
        const message = args.map(arg => {
            if (typeof arg === 'object') {
                try { return JSON.stringify(arg); }
                catch(e) { return String(arg); }
            }
            return String(arg);
        }).join(' ');
        
        fetch('/api/js_log', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({args: [level, message]})
        }).catch(() => {});
    }
    
    const orig = {
        log: console.log,
        error: console.error,
        warn: console.warn,
        info: console.info
    };
    
    console.log = function(...args) { sendLog('LOG', ...args); orig.log.apply(console, args); };
    console.error = function(...args) { sendLog('ERROR', ...args); orig.error.apply(console, args); };
    console.warn = function(...args) { sendLog('WARN', ...args); orig.warn.apply(console, args); };
    console.info = function(...args) { sendLog('INFO', ...args); orig.info.apply(console, args); };
    
    window.addEventListener('error', e => sendLog('ERROR', `Uncaught: ${e.message} at ${e.filename}:${e.lineno}`));
    window.addEventListener('unhandledrejection', e => sendLog('ERROR', `Promise rejected: ${e.reason}`));
    
    sendLog('LOG', 'Console bridge active');
})();
