// Configuration Page JavaScript

let currentPollPeriodValue = null;
let pollPeriodUpdateInterval = null;

// Registry of refresh functions for future-proof extensibility
const refreshFunctions = [];

// Register a refresh function (future-proof for adding more configuration values)
function registerRefreshFunction(refreshFn) {
    if (typeof refreshFn === 'function') {
        refreshFunctions.push(refreshFn);
    }
}

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeConfigurationPage();
});

function initializeConfigurationPage() {
    // Register refresh functions for all dynamic values
    registerRefreshFunction(loadCurrentPollPeriod);
    // Future configuration values can be registered here:
    // registerRefreshFunction(loadOtherConfigValue);
    
    // Load initial poll period value
    loadCurrentPollPeriod();
    
    // Load runtime configuration (one-time load, no refresh needed)
    loadRuntimeConfiguration();
    
    // Set up input validation
    setupInputValidation();
    
    // Start periodic updates of current poll period (every 30 seconds)
    pollPeriodUpdateInterval = setInterval(() => {
        loadCurrentPollPeriod();
    }, 30000);
    
    // Clean up interval when page is unloaded
    window.addEventListener('beforeunload', () => {
        if (pollPeriodUpdateInterval) {
            clearInterval(pollPeriodUpdateInterval);
        }
    });
}

async function loadCurrentPollPeriod() {
    const currentValueElement = document.getElementById('currentPollPeriod');
    const disableButton = document.getElementById('disablePollPeriodBtn');
    const updateButton = document.getElementById('updatePollPeriodBtn');
    
    try {
        // Add loading state
        if (currentValueElement) {
            currentValueElement.textContent = 'Loading...';
            currentValueElement.className = 'config-value loading';
        }
        
        const response = await fetch('/api/space/state/config/poll_period');
        
        if (response.ok) {
            const data = await response.json();
            currentPollPeriodValue = data.poll_period_seconds;
            
            if (currentValueElement) {
                if (currentPollPeriodValue === 0) {
                    currentValueElement.textContent = 'Disabled';
                    currentValueElement.className = 'config-value disabled';
                    
                    // Show enable button instead of disable
                    if (disableButton) disableButton.style.display = 'none';
                    if (updateButton) updateButton.textContent = 'Enable';
                } else {
                    currentValueElement.textContent = `${currentPollPeriodValue} seconds`;
                    currentValueElement.className = 'config-value enabled';
                    
                    // Show disable button
                    if (disableButton) disableButton.style.display = 'inline-block';
                    if (updateButton) updateButton.textContent = 'Update';
                }
            }
            
            console.log('Current poll period loaded:', currentPollPeriodValue);
        } else {
            throw new Error(`Failed to fetch poll period: ${response.status} ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading current poll period:', error);
        
        if (currentValueElement) {
            currentValueElement.textContent = 'Error loading value';
            currentValueElement.className = 'config-value error';
        }
        
        showResultMessage('pollPeriodResult', 'error', `Failed to load current poll period: ${error.message}`);
    }
}

function setupInputValidation() {
    const input = document.getElementById('pollPeriodInput');
    const validation = document.getElementById('pollPeriodValidation');
    
    if (!input || !validation) return;
    
    // Real-time validation on input
    input.addEventListener('input', function() {
        validatePollPeriodInput();
    });
    
    // Validation on blur
    input.addEventListener('blur', function() {
        validatePollPeriodInput();
    });
    
    // Clear validation on focus
    input.addEventListener('focus', function() {
        clearValidationMessage();
    });
}

function validatePollPeriodInput() {
    const input = document.getElementById('pollPeriodInput');
    const validation = document.getElementById('pollPeriodValidation');
    const updateButton = document.getElementById('updatePollPeriodBtn');
    
    if (!input || !validation || !updateButton) return false;
    
    const value = input.value.trim();
    
    // Clear previous validation styles
    input.classList.remove('valid', 'invalid');
    validation.className = 'validation-message';
    
    // Empty value is allowed (user might be typing)
    if (value === '') {
        updateButton.disabled = true;
        return false;
    }
    
    // Check if it's a valid number
    const numValue = parseInt(value, 10);
    
    if (isNaN(numValue)) {
        input.classList.add('invalid');
        validation.className = 'validation-message error';
        validation.textContent = 'Please enter a valid number';
        updateButton.disabled = true;
        return false;
    }
    
    // Check if it's 0 (disable case)
    if (numValue === 0) {
        input.classList.add('valid');
        validation.className = 'validation-message info';
        validation.textContent = 'Setting to 0 will disable polling';
        updateButton.disabled = false;
        return true;
    }
    
    // Check range for enabled polling
    if (numValue < 5 || numValue > 600) {
        input.classList.add('invalid');
        validation.className = 'validation-message error';
        validation.textContent = 'Value must be between 5-600 seconds, or 0 to disable';
        updateButton.disabled = true;
        return false;
    }
    
    // Valid value
    input.classList.add('valid');
    validation.className = 'validation-message success';
    validation.textContent = `Valid: Polling every ${numValue} seconds`;
    updateButton.disabled = false;
    return true;
}

function clearValidationMessage() {
    const input = document.getElementById('pollPeriodInput');
    const validation = document.getElementById('pollPeriodValidation');
    
    if (input) {
        input.classList.remove('valid', 'invalid');
    }
    
    if (validation) {
        validation.className = 'validation-message';
        validation.textContent = '';
    }
}

async function updatePollPeriod() {
    const input = document.getElementById('pollPeriodInput');
    const updateButton = document.getElementById('updatePollPeriodBtn');
    const resultDiv = document.getElementById('pollPeriodResult');
    
    if (!input || !updateButton) return;
    
    // Validate input first
    if (!validatePollPeriodInput()) {
        showResultMessage('pollPeriodResult', 'error', 'Please enter a valid value before updating');
        return;
    }
    
    const value = parseInt(input.value.trim(), 10);
    
    // Disable button and show loading state
    updateButton.disabled = true;
    updateButton.textContent = 'Updating...';
    
    try {
        const response = await fetch(`/api/space/state/config/poll_period/${value}`, {
            method: 'PUT'
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Show success message
            const successMessage = getUpdateSuccessMessage(value, currentPollPeriodValue);
            showResultMessage('pollPeriodResult', 'success', successMessage);
            
            // Clear input
            input.value = '';
            clearValidationMessage();
            
            // Reload current value immediately
            setTimeout(() => {
                loadCurrentPollPeriod();
            }, 500);
            
            console.log('Poll period updated successfully:', data);
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server returned ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error updating poll period:', error);
        showResultMessage('pollPeriodResult', 'error', `Failed to update poll period: ${error.message}`);
    } finally {
        // Re-enable button
        updateButton.disabled = false;
        updateButton.textContent = currentPollPeriodValue === 0 ? 'Enable' : 'Update';
    }
}

async function disablePollPeriod() {
    const updateButton = document.getElementById('updatePollPeriodBtn');
    const disableButton = document.getElementById('disablePollPeriodBtn');
    
    if (!disableButton) return;
    
    // Disable button and show loading state
    disableButton.disabled = true;
    disableButton.textContent = 'Disabling...';
    
    try {
        const response = await fetch('/api/space/state/config/poll_period/0', {
            method: 'PUT'
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Show success message
            showResultMessage('pollPeriodResult', 'success', 'Poll period successfully disabled');
            
            // Clear any input
            const input = document.getElementById('pollPeriodInput');
            if (input) {
                input.value = '';
                clearValidationMessage();
            }
            
            // Reload current value immediately
            setTimeout(() => {
                loadCurrentPollPeriod();
            }, 500);
            
            console.log('Poll period disabled successfully:', data);
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Server returned ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error disabling poll period:', error);
        showResultMessage('pollPeriodResult', 'error', `Failed to disable poll period: ${error.message}`);
    } finally {
        // Re-enable button
        disableButton.disabled = false;
        disableButton.textContent = 'Disable';
    }
}

function showResultMessage(elementId, type, message) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Clear previous classes
    element.className = 'result-message';
    element.style.display = 'none';
    
    // Set new class and message
    element.classList.add(type);
    element.textContent = message;
    element.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
    
    // Auto-hide error messages after 10 seconds
    if (type === 'error') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 10000);
    }
}

function getUpdateSuccessMessage(newValue, currentValue) {
    let action;
    let valueDescription;
    
    // Determine the action based on current and new values
    if (newValue === 0) {
        return 'Poll period successfully disabled';
    } else if (currentValue === 0) {
        action = 'enabled';
        valueDescription = newValue + ' seconds';
    } else {
        action = 'updated';
        valueDescription = newValue + ' seconds';
    }
    
    return `Poll period successfully ${action} to ${valueDescription}`;
}

async function refreshAllValues() {
    const refreshButton = document.getElementById('refreshValuesBtn');
    const refreshIcon = refreshButton?.querySelector('.refresh-icon');
    const refreshText = refreshButton?.querySelector('.refresh-text');
    
    if (!refreshButton) return;
    
    // Disable button and show loading state
    refreshButton.disabled = true;
    refreshButton.classList.add('refreshing');
    if (refreshText) refreshText.textContent = 'Refreshing...';
    
    try {
        // Execute all registered refresh functions
        const refreshPromises = refreshFunctions.map(fn => {
            try {
                return Promise.resolve(fn());
            } catch (error) {
                console.error('Error in refresh function:', error);
                return Promise.resolve(); // Continue with other refreshes
            }
        });
        
        // Wait for all refresh operations to complete
        await Promise.allSettled(refreshPromises);
        
        console.log('All configuration values refreshed');
        
        // Show brief success feedback
        if (refreshText) {
            refreshText.textContent = 'Refreshed!';
            setTimeout(() => {
                if (refreshText) refreshText.textContent = 'Refresh Values';
            }, 1000);
        }
        
    } catch (error) {
        console.error('Error refreshing values:', error);
        
        // Show error feedback
        if (refreshText) {
            refreshText.textContent = 'Error';
            setTimeout(() => {
                if (refreshText) refreshText.textContent = 'Refresh Values';
            }, 2000);
        }
    } finally {
        // Re-enable button and remove loading state
        refreshButton.disabled = false;
        refreshButton.classList.remove('refreshing');
    }
}

// Export functions for potential external use
window.configurationPage = {
    updatePollPeriod,
    disablePollPeriod,
    loadCurrentPollPeriod,
    loadRuntimeConfiguration,
    validatePollPeriodInput,
    refreshAllValues,
    registerRefreshFunction
};

// Runtime Configuration Functions

// Define the desired section order to match CONFIG_SECTIONS in config.py
// When adding new sections to config.py, add them here to control display order
const SECTION_ORDER = [
    'Logging',
    'IO', 
    'WIFI',
    'NTP',
    'Pinger',
    'Web',
    'Space',
    'I2C',
    'Sensors',
    'CO2_Alarm',
    'Sensor_Logging',
    'Displays',
    'RFID',
    'UI_Logging',
    'Overclocking'
];

async function loadRuntimeConfiguration() {
    const container = document.getElementById('runtimeConfigContainer');
    
    if (!container) return;
    
    try {
        // Show loading state
        container.innerHTML = `
            <div class="loading-placeholder">
                <div class="loading-spinner"></div>
                <span>Loading configuration...</span>
            </div>
        `;
        
        const response = await fetch('/api/configuration/list');
        
        if (response.ok) {
            const configData = await response.json();
            renderRuntimeConfiguration(configData);
            console.log('Runtime configuration loaded successfully');
        } else {
            throw new Error(`Failed to fetch configuration: ${response.status} ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading runtime configuration:', error);
        showConfigurationError(error.message);
    }
}

function renderRuntimeConfiguration(configData) {
    const container = document.getElementById('runtimeConfigContainer');
    
    if (!container) return;
    
    // Create the sections grid
    const sectionsGrid = document.createElement('div');
    sectionsGrid.className = 'config-sections-grid';
    
    // Keep track of processed sections
    const processedSections = new Set();
    
    // Process sections in the defined order first
    SECTION_ORDER.forEach(sectionName => {
        if (configData[sectionName]) {
            const sectionData = configData[sectionName];
            const sectionElement = createConfigSection(sectionName, sectionData);
            sectionsGrid.appendChild(sectionElement);
            processedSections.add(sectionName);
        }
    });
    
    // Process any remaining sections that aren't in the defined order
    // These will be grouped under "Other" or displayed individually
    const remainingSections = Object.keys(configData).filter(name => !processedSections.has(name));
    
    if (remainingSections.length > 0) {
        // Create an "Other" section for unknown sections, or display them individually
        remainingSections.forEach(sectionName => {
            const sectionData = configData[sectionName];
            const sectionElement = createConfigSection(sectionName, sectionData, true); // Mark as unknown
            sectionsGrid.appendChild(sectionElement);
        });
    }
    
    // Replace container content
    container.innerHTML = '';
    container.appendChild(sectionsGrid);
}

function createConfigSection(sectionName, sectionData, isUnknown = false) {
    const section = document.createElement('div');
    const sectionClass = `config-section section-${sectionName.toLowerCase().replace(/_/g, '')}`;
    section.className = isUnknown ? `${sectionClass} unknown-section` : sectionClass;
    
    // Create section header
    const header = document.createElement('div');
    header.className = 'config-section-header';
    
    const icon = document.createElement('div');
    icon.className = 'config-section-icon';
    icon.textContent = getSectionIcon(sectionName, isUnknown);
    
    const title = document.createElement('h3');
    title.className = 'config-section-title';
    title.textContent = formatSectionName(sectionName);
    
    // Add indicator for unknown sections
    if (isUnknown) {
        const indicator = document.createElement('span');
        indicator.className = 'unknown-indicator';
        indicator.textContent = ' (New)';
        indicator.title = 'This section is not yet configured in the frontend. See config.py for instructions.';
        title.appendChild(indicator);
    }
    
    header.appendChild(icon);
    header.appendChild(title);
    
    // Create config items container
    const itemsContainer = document.createElement('div');
    itemsContainer.className = 'config-items';
    
    // Process each config item in order - new variables are automatically handled
    Object.keys(sectionData).forEach(itemName => {
        const itemValue = sectionData[itemName];
        const itemElement = createConfigItem(itemName, itemValue);
        itemsContainer.appendChild(itemElement);
    });
    
    section.appendChild(header);
    section.appendChild(itemsContainer);
    
    return section;
}

function createConfigItem(itemName, itemValue) {
    const row = document.createElement('div');
    row.className = 'config-item-row';
    
    const label = document.createElement('div');
    label.className = 'config-item-label';
    label.textContent = formatConfigName(itemName);
    
    const value = document.createElement('div');
    value.className = 'config-item-value';
    
    // Format and style value based on type
    const formattedValue = formatConfigValue(itemValue);
    value.textContent = formattedValue.text;
    value.classList.add(formattedValue.type);
    
    // Add specific type classes for boolean values
    if (formattedValue.type === 'boolean') {
        value.classList.add(itemValue.toString());
    }
    
    row.appendChild(label);
    row.appendChild(value);
    
    return row;
}

function formatConfigValue(value) {
    if (value === null || value === undefined) {
        return { text: 'null', type: 'null' };
    }
    
    if (typeof value === 'boolean') {
        return { text: value.toString(), type: 'boolean' };
    }
    
    if (typeof value === 'number') {
        return { text: value.toString(), type: 'number' };
    }
    
    if (Array.isArray(value)) {
        const displayText = value.length === 0 ? '[]' : `[${value.join(', ')}]`;
        return { text: displayText, type: 'array' };
    }
    
    if (typeof value === 'string') {
        // Handle empty strings
        if (value === '') {
            return { text: '""', type: 'string' };
        }
        return { text: value, type: 'string' };
    }
    
    // Fallback for objects or other types
    return { text: JSON.stringify(value), type: 'object' };
}

function formatConfigName(configName) {
    // Convert UPPER_CASE_WITH_UNDERSCORES to readable format
    return configName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

function formatSectionName(sectionName) {
    // Handle special cases and format section names
    const specialCases = {
        'CO2_Alarm': 'CO₂ Alarm',
        'I2C': 'I²C',
        'NTP': 'NTP',
        'WIFI': 'WiFi',
        'UI_Logging': 'UI Logging',
        'RFID': 'RFID'
    };
    
    if (specialCases[sectionName]) {
        return specialCases[sectionName];
    }
    
    // Convert section name to readable format
    return sectionName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

function getSectionIcon(sectionName, isUnknown = false) {
    const iconMap = {
        'Logging': '📝',
        'IO': '🔌',
        'WIFI': '📶',
        'NTP': '🕐',
        'Pinger': '📡',
        'Web': '🌐',
        'Space': '🏢',
        'I2C': '🔗',
        'Sensors': '🌡️',
        'CO2_Alarm': '🚨',
        'Sensor_Logging': '📊',
        'Displays': '🖥️',
        'RFID': '💳',
        'UI_Logging': '📋',
        'Overclocking': '⚡'
    };
    
    // Return specific icon if known, otherwise return default or new section indicator
    if (iconMap[sectionName]) {
        return iconMap[sectionName];
    } else if (isUnknown) {
        return '🆕'; // New section indicator
    } else {
        return '⚙️'; // Default fallback
    }
}

function showConfigurationError(errorMessage) {
    const container = document.getElementById('runtimeConfigContainer');
    
    if (!container) return;
    
    container.innerHTML = `
        <div class="error-message">
            <div class="error-icon">❌</div>
            <div class="error-text">
                Failed to load configuration: ${errorMessage}
            </div>
        </div>
    `;
}