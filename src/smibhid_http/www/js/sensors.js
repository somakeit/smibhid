/* Environmental Sensors Page JavaScript */

let liveDataInterval = null;
let isLiveDataActive = false;
let activeSensorGroups = new Set(); // Track which sensor groups are visible

// Load sensor information on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAvailableSensors();
    loadAlarmStatus();
});

async function loadAvailableSensors() {
    try {
        const response = await fetch('/api/sensors/modules');
        const sensors = await response.json();
        
        console.log('Available sensors:', sensors);
        
        // Update status indicator
        const statusIndicator = document.querySelector('#sensor-status .status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (sensors && sensors.length > 0) {
            statusIndicator.innerHTML = '✅';
            statusIndicator.className = 'status-indicator success';
            statusText.textContent = `Sensors successfully polled - ${sensors.length} sensor(s) detected: ${sensors.join(', ')}`;
            
            // Show relevant sensor panels
            sensors.forEach(sensor => {
                const panel = document.getElementById(`${sensor.toLowerCase()}-panel`);
                if (panel) {
                    panel.style.display = 'block';
                }
            });
        } else {
            statusIndicator.innerHTML = '⚠️';
            statusIndicator.className = 'status-indicator warning';
            statusText.textContent = 'Sensors successfully polled - No sensors detected';
        }
    } catch (error) {
        console.error('Error loading sensors:', error);
        const statusIndicator = document.querySelector('#sensor-status .status-indicator');
        const statusText = document.getElementById('status-text');
        statusIndicator.innerHTML = '❌';
        statusIndicator.className = 'status-indicator error';
        statusText.textContent = 'Sensors unsuccessfully polled - Error loading sensor information';
    }
}

async function loadAlarmStatus() {
    try {
        // Fetch alarm status
        const response = await fetch('/api/sensors/alarm/status');
        const alarmData = await response.json();
        
        // Fetch threshold data
        const thresholdResponse = await fetch('/api/sensors/alarm/threshold');
        const threshold = await thresholdResponse.json();
        
        // Fetch reset threshold data
        const resetThresholdResponse = await fetch('/api/sensors/alarm/reset_threshold');
        const resetThreshold = await resetThresholdResponse.json();
        
        // Fetch snooze remaining (only needed if status is 2)
        let snoozeRemaining = null;
        if (alarmData && alarmData.status === 2) {
            const snoozeResponse = await fetch('/api/sensors/alarm/snooze_remaining');
            snoozeRemaining = await snoozeResponse.json();
        }
        
        // Fetch current CO2 readings (same as live data)
        const readingsResponse = await fetch('/api/sensors/readings/latest');
        const readingsData = await readingsResponse.json();
        
        console.log('Alarm API response:', alarmData); // Debug log
        console.log('Threshold API response:', threshold);
        console.log('Reset Threshold API response:', resetThreshold);
        console.log('Snooze remaining:', snoozeRemaining);
        console.log('Current readings:', readingsData);
        
        const alarmIcon = document.getElementById('alarm-icon');
        const alarmDetails = document.getElementById('alarm-status-text');
        
        // Update alarm display based on status
        if (alarmData && alarmData.status !== undefined && alarmData.status !== null) {
            alarmIcon.textContent = alarmData.active ? '🚨' : '🔔';
            const statusDisplay = alarmData.status_text ? 
                `${alarmData.status} - ${alarmData.status_text}` : 
                alarmData.status;
            
            // Get current CO2 value (same logic as live data cards)
            let currentCo2 = 'N/A';
            if (readingsData.SCD30 && readingsData.SCD30.co2 !== undefined) {
                currentCo2 = readingsData.SCD30.co2;
            }
            
            // Build the alarm details HTML
            let detailsHTML = `
                <div><strong>Status:</strong> ${statusDisplay}</div>`;
            
            // Add snooze remaining if status is 2
            if (alarmData.status === 2 && snoozeRemaining !== null) {
                detailsHTML += `<div><strong>Snooze Remaining:</strong> ${snoozeRemaining} seconds</div>`;
            }
            
            detailsHTML += `
                <div><strong>Threshold:</strong> ${threshold || 'N/A'} ppm</div>
                <div><strong>Reset Threshold:</strong> ${resetThreshold || 'N/A'} ppm</div>
                <div><strong>Current CO2:</strong> ${currentCo2} ppm</div>
            `;
            
            alarmDetails.innerHTML = detailsHTML;
            
            // Update snooze button text based on status
            updateSnoozeButtonText(alarmData.status);
        } else {
            alarmDetails.textContent = 'Alarm information not available';
            // Reset button text if no alarm data
            updateSnoozeButtonText(null);
        }
    } catch (error) {
        console.error('Error loading alarm status:', error);
        document.getElementById('alarm-status-text').textContent = 'Error loading alarm status';
    }
}

async function viewSensorData(sensorType) {
    try {
        const sensorGroup = document.getElementById(`${sensorType.toLowerCase()}-readings`);
        const button = event.target;
        
        // Toggle the sensor group visibility
        if (activeSensorGroups.has(sensorType)) {
            // Hide this sensor group
            sensorGroup.style.display = 'none';
            activeSensorGroups.delete(sensorType);
            button.textContent = 'View Readings';
            button.classList.remove('active');
        } else {
            // Show this sensor group
            sensorGroup.style.display = 'block';
            activeSensorGroups.add(sensorType);
            button.textContent = 'Hide Readings';
            button.classList.add('active');
            
            // Show live data section if not already visible
            document.getElementById('live-data').style.display = 'block';
            
            // Start live updates if not already active
            if (!isLiveDataActive) {
                startLiveData();
            }
        }
        
        // Hide live data section if no sensor groups are active
        if (activeSensorGroups.size === 0) {
            document.getElementById('live-data').style.display = 'none';
            if (isLiveDataActive) {
                clearInterval(liveDataInterval);
                isLiveDataActive = false;
            }
        } else {
            // Load and update data for visible sensors
            const response = await fetch('/api/sensors/readings/latest');
            const data = await response.json();
            updateDataCards(data);
            
            // Scroll to live data section if we just showed it
            if (activeSensorGroups.size === 1) {
                document.getElementById('live-data').scrollIntoView({ behavior: 'smooth' });
            }
        }
    } catch (error) {
        console.error('Error loading sensor data:', error);
        alert('Error loading sensor data');
    }
}

function updateDataCards(data) {
    console.log('Updating data cards with:', data); // Debug log
    
    // Update SCD30 readings
    if (data.SCD30 && activeSensorGroups.has('SCD30')) {
        console.log('SCD30 data:', data.SCD30); // Debug SCD30 specifically
        if (data.SCD30.temperature !== undefined) {
            document.getElementById('scd30-temperature-value').textContent = `${data.SCD30.temperature.toFixed(1)}°C`;
        }
        if (data.SCD30.relative_humidity !== undefined) {
            console.log('SCD30 relative_humidity value:', data.SCD30.relative_humidity); // Debug humidity
            document.getElementById('scd30-humidity-value').textContent = `${data.SCD30.relative_humidity.toFixed(1)}%`;
        } else {
            console.log('SCD30 relative_humidity is undefined or missing');
        }
        if (data.SCD30.co2 !== undefined) {
            document.getElementById('scd30-co2-value').textContent = `${data.SCD30.co2} ppm`;
        }
    }

    // Update BME280 readings
    if (data.BME280 && activeSensorGroups.has('BME280')) {
        if (data.BME280.temperature !== undefined) {
            document.getElementById('bme280-temperature-value').textContent = `${data.BME280.temperature.toFixed(1)}°C`;
        }
        if (data.BME280.humidity !== undefined) {
            document.getElementById('bme280-humidity-value').textContent = `${data.BME280.humidity.toFixed(1)}%`;
        }
        if (data.BME280.pressure !== undefined) {
            document.getElementById('bme280-pressure-value').textContent = `${data.BME280.pressure.toFixed(1)} hPa`;
        }
    }

    // Update SGP30 readings
    if (data.SGP30 && activeSensorGroups.has('SGP30')) {
        if (data.SGP30.tvoc !== undefined) {
            document.getElementById('sgp30-tvoc-value').textContent = `${data.SGP30.tvoc} ppb`;
        }
        if (data.SGP30.eco2 !== undefined) {
            document.getElementById('sgp30-eco2-value').textContent = `${data.SGP30.eco2} ppm`;
        }
    }
}

function startLiveData() {
    isLiveDataActive = true;
    document.querySelector('#live-data button').textContent = 'Stop Live Updates';
    
    liveDataInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/sensors/readings/latest');
            const data = await response.json();
            updateDataCards(data);
        } catch (error) {
            console.error('Error updating live data:', error);
        }
    }, 5000); // Update every 5 seconds
}

function toggleLiveData() {
    if (isLiveDataActive) {
        clearInterval(liveDataInterval);
        isLiveDataActive = false;
        document.querySelector('#live-data button').textContent = 'Start Live Updates';
    } else {
        startLiveData();
    }
}

function refreshAlarmStatus() {
    loadAlarmStatus();
}

function updateSnoozeButtonText(alarmStatus) {
    const snoozeButton = document.querySelector('.snooze-button');
    if (snoozeButton) {
        if (alarmStatus === 2) {
            snoozeButton.textContent = 'Snoozed';
            snoozeButton.classList.add('snoozed');
        } else {
            snoozeButton.textContent = 'Snooze Alarm';
            snoozeButton.classList.remove('snoozed');
        }
    }
}

async function snoozeAlarm(buttonElement) {
    try {
        console.log('Attempting to snooze alarm...');
        const response = await fetch('/api/sensors/alarm/snooze', {
            method: 'PUT'
        });
        
        console.log('Snooze API response status:', response.status);
        console.log('Snooze API response ok:', response.ok);
        
        // Try to get the response text regardless of status
        const responseText = await response.text();
        console.log('Response body:', responseText);
        
        if (response.ok) {
            console.log('Snooze successful, refreshing alarm status...');
            // Success - refresh the alarm status to show updated info
            await loadAlarmStatus();
            // Button text will be updated by updateSnoozeButtonText after status refresh
        } else {
            console.error('Failed to snooze alarm. Status:', response.status);
            console.error('Error message from server:', responseText);
            alert(`Failed to snooze alarm (Status: ${response.status})\nServer message: ${responseText}`);
        }
    } catch (error) {
        console.error('Error snoozing alarm:', error);
        alert('Error snoozing alarm. Please check your connection.');
    }
}

// Make functions globally available
window.viewSensorData = viewSensorData;
window.toggleLiveData = toggleLiveData;
window.refreshAlarmStatus = refreshAlarmStatus;
window.snoozeAlarm = snoozeAlarm;
