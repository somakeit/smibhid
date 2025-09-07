async function setAutoMeasure() {
    const action = document.getElementById('autoMeasureAction').value;
    const response = await fetch(`/api/sensors/modules/SCD30/auto_measure/${action}`, {
        method: 'PUT'
    });
    const result = await response.text();
    alert(`Response: ${result}`);
}

async function setCalibration() {
    const value = document.getElementById('calibrationValue').value;
    const response = await fetch(`/api/sensors/modules/SCD30/calibration/${value}`, {
        method: 'PUT'
    });
    const result = await response.text();
    alert(`Response: ${result}`);
}

async function refreshReadings() {
    try {
        const response = await fetch('/api/sensors/readings/latest');
        const data = await response.json();
        
        if (data.SCD30) {
            // Update temperature
            if (data.SCD30.temperature !== undefined) {
                document.getElementById('temperature-value').textContent = `${data.SCD30.temperature.toFixed(1)}°C`;
            }
            
            // Update humidity
            if (data.SCD30.relative_humidity !== undefined) {
                document.getElementById('humidity-value').textContent = `${data.SCD30.relative_humidity.toFixed(1)}%`;
            }
            
            // Update CO2
            if (data.SCD30.co2 !== undefined) {
                document.getElementById('co2-value').textContent = `${data.SCD30.co2} ppm`;
            }
        }
        
        console.log('Readings refreshed successfully');
    } catch (error) {
        console.error('Error refreshing readings:', error);
        alert('Error refreshing readings');
    }
}

// Enhanced UI functions
async function setAutoMeasureEnhanced() {
    const action = document.getElementById('autoMeasureAction').value;
    const resultDiv = document.getElementById('autoMeasureResult');
    
    try {
        resultDiv.className = 'result-message';
        resultDiv.textContent = 'Applying setting...';
        resultDiv.style.display = 'block';
        
        const response = await fetch(`/api/sensors/modules/SCD30/auto_measure/${action}`, {
            method: 'PUT'
        });
        const result = await response.text();
        
        resultDiv.className = 'result-message success';
        resultDiv.textContent = `Measurement ${action} command sent successfully`;
        
        // Refresh status after a delay
        setTimeout(checkMeasurementStatus, 1000);
        
    } catch (error) {
        resultDiv.className = 'result-message error';
        resultDiv.textContent = `Error: ${error.message}`;
    }
}

async function setCalibrationEnhanced() {
    const value = document.getElementById('calibrationValue').value;
    const resultDiv = document.getElementById('calibrationResult');
    
    if (!value || value < 0) {
        resultDiv.className = 'result-message error';
        resultDiv.textContent = 'Please enter a valid calibration value';
        resultDiv.style.display = 'block';
        return;
    }
    
    try {
        resultDiv.className = 'result-message';
        resultDiv.textContent = 'Calibrating sensor...';
        resultDiv.style.display = 'block';
        
        const response = await fetch(`/api/sensors/modules/SCD30/calibration/${value}`, {
            method: 'PUT'
        });
        const result = await response.text();
        
        resultDiv.className = 'result-message success';
        resultDiv.textContent = `Calibration set to ${value} ppm successfully`;
        
    } catch (error) {
        resultDiv.className = 'result-message error';
        resultDiv.textContent = `Calibration error: ${error.message}`;
    }
}

async function checkMeasurementStatus() {
    try {
        const response = await fetch('/api/sensors/modules/SCD30/auto_measure');
        const status = await response.text();
        
        const statusElement = document.getElementById('measurement-status');
        const statusText = document.getElementById('status-text');
        
        if (status === '1') {
            statusElement.innerHTML = '<span class="status-dot active"></span>';
            statusText.textContent = 'Measurement active';
        } else {
            statusElement.innerHTML = '<span class="status-dot inactive"></span>';
            statusText.textContent = 'Measurement stopped';
        }
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

async function refreshReadingsEnhanced() {
    try {
        const response = await fetch('/api/sensors/readings/latest');
        const data = await response.json();
        
        console.log('SCD30 API Response:', data); // Debug log
        
        if (data.SCD30) {
            console.log('SCD30 data found:', data.SCD30); // Debug log
            
            const co2Element = document.getElementById('co2-reading');
            const tempElement = document.getElementById('temp-reading');
            const humidityElement = document.getElementById('humidity-reading');
            
            console.log('Elements found:', {
                co2: co2Element,
                temp: tempElement,
                humidity: humidityElement
            }); // Debug log
            
            if (co2Element) {
                co2Element.textContent = `${data.SCD30.co2 || '--'} ppm`;
                console.log('Updated CO2:', data.SCD30.co2);
            }
            
            if (tempElement) {
                tempElement.textContent = `${data.SCD30.temperature?.toFixed(1) || '--'}°C`;
                console.log('Updated temperature:', data.SCD30.temperature);
            }
            
            if (humidityElement) {
                humidityElement.textContent = `${data.SCD30.relative_humidity?.toFixed(1) || '--'}%`;
                console.log('Updated humidity:', data.SCD30.relative_humidity);
            }
        } else {
            console.log('No SCD30 data in response');
        }
    } catch (error) {
        console.error('Error refreshing readings:', error);
    }
}

// Initialize page functionality
function initializePage() {
    checkMeasurementStatus();
    refreshReadingsEnhanced();
    
    // Auto-refresh readings every 10 seconds
    setInterval(refreshReadingsEnhanced, 10000);
}

// Make functions globally available for onclick handlers
window.setAutoMeasure = setAutoMeasureEnhanced;
window.setCalibration = setCalibrationEnhanced;
window.refreshReadings = refreshReadingsEnhanced;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initializePage);