/* Index Page JavaScript */

// Load device information on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDeviceInfo();
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

function showSystemStatus() {
    alert('System status coming soon!');
}

// Make functions globally available
window.showSystemStatus = showSystemStatus;
