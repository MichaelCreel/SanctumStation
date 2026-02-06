/**
 * Mobile API Bridge for Sanctum Station
 * Translates pywebview API calls to HTTP requests for mobile Flask backend
 */

(function() {
    let checkCount = 0;
    const maxChecks = 20; // Check for 2 seconds
    
    function checkAndInitialize() {
        checkCount++;
        
        if (window.pywebview && window.pywebview.api) {
            if (typeof window.pywebview.api.get_apps === 'function') {
                try {
                    const testResult = window.pywebview.api.get_apps();
                    if (testResult !== undefined) {
                        console.log('Desktop pywebview detected, skipping mobile bridge');
                        return;
                    }
                } catch (e) {
                }
            }
        }
        
        if (checkCount >= maxChecks) {
            initializeMobileBridge();
            return;
        }
        
        setTimeout(checkAndInitialize, 100);
    }
    
    function initializeMobileBridge() {
        console.log('Initializing mobile API bridge...');
        
        window.pywebview = {
            api: {}
        };
        
        async function callAPI(method, ...args) {
            try {
                const response = await fetch(`http://127.0.0.1:5000/api/${method}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        args: args,
                        kwargs: {}
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                return result;
            } catch (error) {
                console.error(`Error calling ${method}:`, error);
                throw error;
            }
        }
        
        const apiMethods = [
            'launch_app', 'stop_app', 'get_apps', 'get_running_apps',
            'send_notification', 'delete_notification', 'get_notifications', 'clear_all_notifications',
            'display_error', 'get_error',
            'list_directory', 'read_file', 'write_file', 'delete_file', 'delete_directory',
            'create_directory', 'create_file', 'rename_item', 'move_item', 'copy_item',
            'get_metadata', 'exists',
            'get_fonts', 'get_version', 'get_wallpaper', 'get_wallpaper_data',
            'get_day_gradient', 'get_fullscreen',
            'get_settings', 'set_wallpaper', 'set_day_gradient', 'set_fullscreen',
            'set_font', 'set_updates', 'get_available_update',
            'fuzzy_search_apps', 'call_app_function'
        ];
        
        apiMethods.forEach(method => {
            window.pywebview.api[method] = async function(...args) {
                return await callAPI(method, ...args);
            };
        });
        
        console.log('Mobile API bridge initialized');
    }
    
    setTimeout(checkAndInitialize, 50);
})();
