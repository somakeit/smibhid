/* Index Page JavaScript */

// Space state polling interval
const SPACE_STATE_POLL_INTERVAL = 5000; // 5 seconds
let spaceStateInterval;

// Load device information on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDeviceInfo();
    initializeSpaceControl();
});

async function loadDeviceInfo() {
    try {
        // Load basic device information if needed
        console.log('Index page loaded');
        // Future: Add any device status checks or dynamic content loading
    } catch (error) {
        console.error('Error loading device info:', error);
    }
}

function initializeSpaceControl() {
    // Initial status check
    checkSpaceState();
    
    // Start polling for space state every 5 seconds
    spaceStateInterval = setInterval(checkSpaceState, SPACE_STATE_POLL_INTERVAL);
}

async function checkSpaceState() {
    try {
        const response = await fetch('/api/space/state');
        const isOpen = await response.json();
        
        updateSpaceButtons(isOpen);
        updateStatusDisplay(isOpen);
        
    } catch (error) {
        console.error('Error checking space state:', error);
        updateStatusDisplay(null, 'Error checking space state');
    }
}

function updateSpaceButtons(isOpen) {
    const openButton = document.getElementById('openButton');
    const closeButton = document.getElementById('closeButton');
    
    if (openButton && closeButton) {
        // Reset button states
        openButton.classList.remove('active');
        closeButton.classList.remove('active');
        
        // Set active state based on space state
        if (isOpen === true) {
            openButton.classList.add('active');
        } else if (isOpen === false) {
            closeButton.classList.add('active');
        }
    }
}

function updateStatusDisplay(isOpen, errorMessage = null) {
    const statusElement = document.getElementById('spaceStatus');
    
    if (statusElement) {
        if (errorMessage) {
            statusElement.textContent = errorMessage;
            statusElement.style.color = '#e74c3c';
        } else if (isOpen === true) {
            statusElement.textContent = 'Space is OPEN';
            statusElement.style.color = '#27ae60';
        } else if (isOpen === false) {
            statusElement.textContent = 'Space is CLOSED';
            statusElement.style.color = '#e74c3c';
        } else {
            statusElement.textContent = 'Space state unknown';
            statusElement.style.color = '#f39c12';
        }
    }
}

async function openSpace() {
    try {
        const response = await fetch('/api/space/state/open', {
            method: 'PUT'
        });
        
        if (response.ok) {
            console.log('Open command sent successfully');
            // Force immediate status check
            setTimeout(checkSpaceState, 500);
        } else {
            console.error('Failed to send open command');
            updateStatusDisplay(null, 'Failed to send open command');
        }
    } catch (error) {
        console.error('Error sending open command:', error);
        updateStatusDisplay(null, 'Error sending open command');
    }
}

async function closeSpace() {
    try {
        const response = await fetch('/api/space/state/closed', {
            method: 'PUT'
        });
        
        if (response.ok) {
            console.log('Close command sent successfully');
            // Force immediate status check
            setTimeout(checkSpaceState, 500);
        } else {
            console.error('Failed to send close command');
            updateStatusDisplay(null, 'Failed to send close command');
        }
    } catch (error) {
        console.error('Error sending close command:', error);
        updateStatusDisplay(null, 'Error sending close command');
    }
}

function showSystemStatus() {
    alert('System status coming soon!');
}

// Make functions globally available
window.showSystemStatus = showSystemStatus;
window.openSpace = openSpace;
window.closeSpace = closeSpace;
