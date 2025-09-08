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
                const response = await fetch('/api/version', { 
                    timeout: 5000,
                    cache: 'no-cache'
                });
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

// Make functions globally available
window.refreshSystemInfo = refreshSystemInfo;
window.showResetConfirmation = showResetConfirmation;
window.hideResetConfirmation = hideResetConfirmation;
window.performReset = performReset;