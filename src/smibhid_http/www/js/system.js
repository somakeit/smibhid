/* System Page JavaScript */

// Load system information on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSystemInfo();
});

async function loadSystemInfo() {
    await Promise.all([
        loadMacAddress(),
        loadHostname(),
        loadFirmwareVersion()
    ]);
}

async function loadMacAddress() {
    try {
        const response = await fetch('/api/wlan/mac');
        if (response.ok) {
            const macAddress = await response.json();
            document.getElementById('mac-address').textContent = macAddress;
        } else {
            document.getElementById('mac-address').textContent = 'Failed to load';
        }
    } catch (error) {
        console.error('Error loading MAC address:', error);
        document.getElementById('mac-address').textContent = 'Error loading';
    }
}

async function loadHostname() {
    try {
        const response = await fetch('/api/hostname');
        if (response.ok) {
            const hostname = await response.json();
            document.getElementById('hostname').textContent = hostname;
        } else {
            document.getElementById('hostname').textContent = 'Failed to load';
        }
    } catch (error) {
        console.error('Error loading hostname:', error);
        document.getElementById('hostname').textContent = 'Error loading';
    }
}

async function loadFirmwareVersion() {
    try {
        const response = await fetch('/api/version');
        if (response.ok) {
            const version = await response.json();
            document.getElementById('firmware-version').textContent = version;
        } else {
            document.getElementById('firmware-version').textContent = 'Failed to load';
        }
    } catch (error) {
        console.error('Error loading firmware version:', error);
        document.getElementById('firmware-version').textContent = 'Error loading';
    }
}

async function refreshSystemInfo() {
    // Show loading state
    document.getElementById('mac-address').textContent = 'Loading...';
    document.getElementById('hostname').textContent = 'Loading...';
    document.getElementById('firmware-version').textContent = 'Loading...';
    
    // Reload all information
    await loadSystemInfo();
}

function showResetConfirmation() {
    const modal = document.getElementById('reset-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Focus the cancel button for accessibility
        const cancelButton = modal.querySelector('.cancel');
        if (cancelButton) {
            cancelButton.focus();
        }
    }
}

function hideResetConfirmation() {
    const modal = document.getElementById('reset-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function performReset() {
    try {
        // Hide the modal immediately
        hideResetConfirmation();
        
        // Show a loading/progress message
        const resetButton = document.querySelector('.reset-button');
        if (resetButton) {
            resetButton.textContent = 'Resetting Device...';
            resetButton.disabled = true;
        }
        
        // Send reset command
        const response = await fetch('/api/reset', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Show success message and countdown
            showResetProgress();
        } else {
            throw new Error('Reset request failed');
        }
    } catch (error) {
        console.error('Error performing reset:', error);
        alert('Failed to reset device. Please try again or reset manually.');
        
        // Reset button state
        const resetButton = document.querySelector('.reset-button');
        if (resetButton) {
            resetButton.textContent = 'Reset Device';
            resetButton.disabled = false;
        }
    }
}

function showResetProgress() {
    // Replace the main content with a reset progress indicator
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.innerHTML = `
            <section class="welcome-section">
                <h2>Device Reset in Progress</h2>
                <div class="reset-progress">
                    <div class="progress-icon">🔄</div>
                    <p class="progress-message">SMIBHID is restarting...</p>
                    <p class="progress-details">
                        The device is now resetting. This page will automatically reload once the device is back online.
                        This typically takes 30-60 seconds.
                    </p>
                    <div class="progress-timer">
                        <span id="countdown">60</span> seconds remaining
                    </div>
                </div>
            </section>
        `;
        
        // Start countdown and auto-reload
        startResetCountdown();
    }
}

function startResetCountdown() {
    let countdown = 60;
    const countdownElement = document.getElementById('countdown');
    
    const interval = setInterval(() => {
        countdown--;
        if (countdownElement) {
            countdownElement.textContent = countdown;
        }
        
        if (countdown <= 0) {
            clearInterval(interval);
            // Try to reload the page
            window.location.reload();
        }
    }, 1000);
    
    // Also try to reload when the device comes back online
    // Check every 5 seconds after the first 30 seconds
    setTimeout(() => {
        const checkInterval = setInterval(async () => {
            try {
                // Create AbortController for timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                
                const response = await fetch('/api/version', { 
                    signal: controller.signal,
                    cache: 'no-cache'
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    clearInterval(checkInterval);
                    clearInterval(interval);
                    window.location.reload();
                }
            } catch (error) {
                // Device not ready yet, keep checking
            }
        }, 5000);
    }, 30000);
}

// Close modal when clicking outside of it
document.addEventListener('click', function(event) {
    const modal = document.getElementById('reset-modal');
    if (modal && event.target === modal) {
        hideResetConfirmation();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideResetConfirmation();
    }
});

async function refreshLogs() {
    const refreshButton = document.getElementById('refresh-logs-btn');
    const refreshIcon = document.getElementById('refresh-logs-icon');
    const refreshText = document.getElementById('refresh-logs-text');
    const textarea = document.getElementById('logs-textarea');
    const statusDiv = document.getElementById('logs-status');
    
    // Show loading state
    if (refreshButton) refreshButton.disabled = true;
    if (refreshIcon) refreshIcon.textContent = '🔄';
    if (refreshText) refreshText.textContent = 'Loading...';
    if (refreshIcon) refreshIcon.style.animation = 'spin 1s linear infinite';
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = 'Loading log files...';
        statusDiv.className = 'logs-status loading';
    }
    
    try {
        const response = await fetch('/api/logs/read');
        
        if (response.ok) {
            const contentType = response.headers.get('content-type');
            let logData;
            
            // Check if the response is JSON
            if (contentType && contentType.includes('application/json')) {
                // API returns JSON - parse it first
                logData = await response.json();
                // If it's a JSON string, it might be escaped
                if (typeof logData === 'string') {
                    // Handle JSON-escaped newlines
                    try {
                        logData = JSON.parse('"' + logData + '"'); // Safely parse escaped string
                    } catch (e) {
                        // If parsing fails, use the string as-is
                        console.warn('Failed to parse escaped JSON string, using as-is:', e);
                    }
                }
            } else {
                // API returns plain text
                logData = await response.text();
            }
            
            // Ensure logData is a string for further processing
            if (typeof logData !== 'string') {
                // If it's an object or array, extract log content
                if (logData === null || logData === undefined) {
                    logData = '';
                } else if (typeof logData === 'object') {
                    // Try to extract log content from common JSON structures
                    if (logData.logs) {
                        logData = logData.logs;
                    } else if (logData.content) {
                        logData = logData.content;
                    } else if (logData.data) {
                        logData = logData.data;
                    } else if (logData.log) {
                        logData = logData.log;
                    } else if (Array.isArray(logData)) {
                        // If it's an array of log lines, join them
                        logData = logData.join('\n');
                    } else {
                        // If no common log property found, check if it has a single string property
                        const keys = Object.keys(logData);
                        if (keys.length === 1 && typeof logData[keys[0]] === 'string') {
                            logData = logData[keys[0]];
                        } else {
                            // Last resort: stringify but remove outer braces for cleaner display
                            logData = JSON.stringify(logData, null, 2)
                                .replace(/^\{\s*/, '')  // Remove opening brace and whitespace
                                .replace(/\s*\}$/, '')  // Remove closing brace and whitespace
                                .replace(/^\s*"[^"]+"\s*:\s*/, '') // Remove key: prefix if single property
                                .replace(/,\s*$/m, ''); // Remove trailing comma
                        }
                    }
                } else {
                    logData = String(logData);
                }
                
                // Ensure we have a string after extraction
                if (typeof logData !== 'string') {
                    logData = String(logData);
                }
            }
            
            if (logData === "" || logData.trim() === "") {
                // No log files present
                if (textarea) {
                    textarea.value = '';
                    textarea.placeholder = 'No log files present';
                }
                if (statusDiv) {
                    statusDiv.textContent = 'No log files present';
                    statusDiv.className = 'logs-status info';
                }
            } else {
                // Ensure we have proper line breaks regardless of format
                let formattedLogs = logData;
                
                // Handle different newline formats
                if (typeof formattedLogs === 'string') {
                    // Replace various newline representations with actual newlines
                    formattedLogs = formattedLogs
                        .replace(/\\r\\n/g, '\n')  // Windows CRLF
                        .replace(/\\r/g, '\n')     // Old Mac CR
                        .replace(/\\n/g, '\n');    // Unix LF
                }
                
                if (textarea) {
                    textarea.value = formattedLogs;
                    textarea.placeholder = 'Log contents will appear here after pressing refresh...';
                }
                if (statusDiv) {
                    const lineCount = formattedLogs.split('\n').filter(line => line.trim() !== '').length;
                    statusDiv.textContent = `Logs loaded successfully (${lineCount} lines)`;
                    statusDiv.className = 'logs-status success';
                }
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        if (textarea) {
            textarea.value = '';
            textarea.placeholder = 'Error loading logs. Please try again.';
        }
        if (statusDiv) {
            statusDiv.textContent = `Error loading logs: ${error.message}`;
            statusDiv.className = 'logs-status error';
        }
    } finally {
        // Reset button state
        if (refreshButton) refreshButton.disabled = false;
        if (refreshIcon) {
            refreshIcon.textContent = '🔄';
            refreshIcon.style.animation = '';
        }
        if (refreshText) refreshText.textContent = 'Refresh Logs';
        
        // Hide status after 5 seconds if successful
        if (statusDiv && statusDiv.className.includes('success')) {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }
}

// Make functions globally available
window.refreshSystemInfo = refreshSystemInfo;
window.showResetConfirmation = showResetConfirmation;
window.hideResetConfirmation = hideResetConfirmation;
window.performReset = performReset;
window.refreshLogs = refreshLogs;