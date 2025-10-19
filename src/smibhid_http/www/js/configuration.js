// Configuration Page JavaScript

let currentPollPeriodValue = null;
let pollPeriodUpdateInterval = null;

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeConfigurationPage();
});

function initializeConfigurationPage() {
    // Load initial poll period value
    loadCurrentPollPeriod();
    
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
            const action = value === 0 ? 'disabled' : (currentPollPeriodValue === 0 ? 'enabled' : 'updated');
            showResultMessage('pollPeriodResult', 'success', `Poll period successfully ${action} to ${value === 0 ? 'disabled' : value + ' seconds'}`);
            
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

// Export functions for potential external use
window.configurationPage = {
    updatePollPeriod,
    disablePollPeriod,
    loadCurrentPollPeriod,
    validatePollPeriodInput
};