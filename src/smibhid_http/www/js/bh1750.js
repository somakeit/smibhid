// BH1750 Light Sensor Configuration Page JavaScript

// Configuration constants
const THRESHOLD_POLL_DELAY_MS = 1500; // Time to wait between status poll attempts

// Cache for relay configuration
let relayActiveHigh = null;

// Load page data when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadRelayConfiguration();
    loadThresholdConfiguration();
    refreshReadings();
});

async function loadRelayConfiguration() {
    try {
        const response = await fetch('/api/configuration/list');
        const config = await response.json();
        
        // Extract SPACE_OPEN_RELAY_ACTIVE_HIGH from the IO section
        if (config && config.IO && config.IO.SPACE_OPEN_RELAY_ACTIVE_HIGH !== undefined) {
            relayActiveHigh = config.IO.SPACE_OPEN_RELAY_ACTIVE_HIGH;
            console.log('Relay active high configuration loaded:', relayActiveHigh);
        } else {
            console.warn('SPACE_OPEN_RELAY_ACTIVE_HIGH not found in configuration');
        }
    } catch (error) {
        console.error('Error loading relay configuration:', error);
    }
}

async function loadThresholdConfiguration() {
    try {
        const response = await fetch('/api/space/light/threshold');
        const data = await response.json();
        
        const statusDot = document.querySelector('#threshold-status .status-dot');
        const statusText = document.getElementById('threshold-status-text');
        const thresholdInput = document.getElementById('thresholdValue');
        
        if (data && data.light_threshold_lux !== undefined) {
            const threshold = data.light_threshold_lux;
            
            if (threshold === null || threshold === 0) {
                statusDot.className = 'status-dot inactive';
                statusText.textContent = 'Light-based detection disabled';
                thresholdInput.placeholder = '0 (disabled)';
            } else {
                statusDot.className = 'status-dot active';
                statusText.textContent = `Current threshold: ${threshold} lux`;
                thresholdInput.placeholder = threshold.toString();
            }
        } else {
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Failed to load threshold configuration';
        }
    } catch (error) {
        console.error('Error loading threshold configuration:', error);
        
        const statusDot = document.querySelector('#threshold-status .status-dot');
        const statusText = document.getElementById('threshold-status-text');
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Error loading configuration';
    }
}

async function setThreshold() {
    const value = document.getElementById('thresholdValue').value;
    const resultDiv = document.getElementById('thresholdResult');
    
    if (!value || value < 0) {
        resultDiv.className = 'result-message error';
        resultDiv.textContent = 'Please enter a valid threshold value (0 or greater)';
        resultDiv.style.display = 'block';
        return;
    }
    
    try {
        resultDiv.className = 'result-message';
        resultDiv.textContent = 'Setting threshold...';
        resultDiv.style.display = 'block';
        
        const apiValue = value === '0' ? 'none' : value;
        const response = await fetch(`/api/space/light/threshold/${apiValue}`, {
            method: 'PUT'
        });
        const result = await response.json();
        
        if (response.ok && result.success) {
            const thresholdValue = result.light_threshold_lux;
            
            if (thresholdValue === null) {
                resultDiv.className = 'result-message success';
                resultDiv.textContent = 'Light-based detection disabled successfully';
            } else {
                resultDiv.className = 'result-message success';
                resultDiv.textContent = `Threshold set to ${thresholdValue} lux successfully`;
            }
            
            // Update status display after short delay
            await new Promise(resolve => setTimeout(resolve, THRESHOLD_POLL_DELAY_MS));
            await loadThresholdConfiguration();
            await refreshReadings();
        } else {
            resultDiv.className = 'result-message error';
            resultDiv.textContent = `Error: ${result.error || 'Failed to set threshold'}`;
        }
        
    } catch (error) {
        resultDiv.className = 'result-message error';
        resultDiv.textContent = `Error setting threshold: ${error.message}`;
    }
}

async function refreshReadings() {
    try {
        // Fetch sensor readings
        const readingsResponse = await fetch('/api/sensors/readings/latest');
        const readingsData = await readingsResponse.json();
        
        // Fetch button-based space state
        const spaceStateResponse = await fetch('/api/space/state');
        const spaceStateData = await spaceStateResponse.json();
        
        // Fetch light state
        const lightStateResponse = await fetch('/api/space/light/state');
        const lightStateData = await lightStateResponse.json();
        
        // Fetch current threshold
        const thresholdResponse = await fetch('/api/space/light/threshold');
        const thresholdData = await thresholdResponse.json();
        
        // Fetch relay state
        const relayStateResponse = await fetch('/api/space/relay/state');
        const relayStateData = await relayStateResponse.json();
        
        // Update light level reading
        if (readingsData.BH1750 && readingsData.BH1750.light !== undefined) {
            const lightValue = readingsData.BH1750.light;
            document.getElementById('light-reading').textContent = `${lightValue.toFixed(2)} lux`;
        } else {
            document.getElementById('light-reading').textContent = 'N/A';
        }
        
        // Update space state reading (light-based)
        if (lightStateData && lightStateData.light_state !== undefined) {
            const lightState = lightStateData.light_state;
            const stateElement = document.getElementById('space-state-reading');
            
            if (lightState === true) {
                stateElement.textContent = 'Open';
                stateElement.style.color = '#28a745';
            } else if (lightState === false) {
                stateElement.textContent = 'Closed';
                stateElement.style.color = '#dc3545';
            } else {
                stateElement.textContent = 'N/A';
                stateElement.style.color = '#6c757d';
            }
        } else {
            document.getElementById('space-state-reading').textContent = 'N/A';
        }
        
        // Update threshold reading
        if (thresholdData && thresholdData.light_threshold_lux !== undefined) {
            const threshold = thresholdData.light_threshold_lux;
            if (threshold === null) {
                document.getElementById('threshold-reading').textContent = 'Disabled';
            } else {
                document.getElementById('threshold-reading').textContent = `${threshold} lux`;
            }
        } else {
            document.getElementById('threshold-reading').textContent = 'N/A';
        }
        
        // Update button-based state card
        if (spaceStateData !== undefined && spaceStateData !== null) {
            const buttonStateValue = document.getElementById('button-state-value');
            
            if (spaceStateData === true) {
                buttonStateValue.textContent = '🟢 Open';
                buttonStateValue.style.color = '#28a745';
            } else if (spaceStateData === false) {
                buttonStateValue.textContent = '🔴 Closed';
                buttonStateValue.style.color = '#dc3545';
            } else {
                buttonStateValue.textContent = '❓ Not Configured';
                buttonStateValue.style.color = '#6c757d';
            }
        } else {
            document.getElementById('button-state-value').textContent = 'N/A';
        }
        
        // Update light state card
        if (lightStateData && lightStateData.light_state !== undefined) {
            const lightState = lightStateData.light_state;
            const lightStateValue = document.getElementById('light-state-value');
            
            if (lightState === true) {
                lightStateValue.textContent = '☀️ Open';
                lightStateValue.style.color = '#28a745';
            } else if (lightState === false) {
                lightStateValue.textContent = '🌙 Closed';
                lightStateValue.style.color = '#dc3545';
            } else {
                lightStateValue.textContent = '❓ Not Configured';
                lightStateValue.style.color = '#6c757d';
            }
        } else {
            document.getElementById('light-state-value').textContent = 'N/A';
        }
        
        // Update overall state card - show On/Off based on relay state and active high/low config
        if (relayStateData && relayStateData.relay_state !== undefined && relayStateData.relay_state !== null) {
            const relayState = relayStateData.relay_state;
            const overallStateValue = document.getElementById('overall-state-value');
            
            // Determine if relay is "On" or "Off"
            // If active high: true = On, false = Off
            // If active low: true = Off, false = On
            let isOn;
            if (relayActiveHigh === true) {
                isOn = relayState === true;
            } else if (relayActiveHigh === false) {
                isOn = relayState === false;
            } else {
                // If we don't know the config, assume active high
                isOn = relayState === true;
            }
            
            if (isOn) {
                overallStateValue.textContent = '✅ On';
                overallStateValue.style.color = '#28a745';
            } else {
                overallStateValue.textContent = '❌ Off';
                overallStateValue.style.color = '#dc3545';
            }
        } else {
            const overallStateValue = document.getElementById('overall-state-value');
            overallStateValue.textContent = '⚠️ Not Configured';
            overallStateValue.style.color = '#6c757d';
        }
        
        console.log('Readings refreshed successfully');
    } catch (error) {
        console.error('Error refreshing readings:', error);
        
        // Set error states for readings that failed
        document.getElementById('light-reading').textContent = 'Error';
        document.getElementById('space-state-reading').textContent = 'Error';
        document.getElementById('threshold-reading').textContent = 'Error';
    }
}

// Make functions globally available
window.setThreshold = setThreshold;
window.refreshReadings = refreshReadings;
