// Relay Monitoring Page JavaScript

// On time is calculated live from the last recorded transition, so poll
// periodically to reflect it, rather than only fetching once on load.
const RELAY_DATA_POLL_INTERVAL = 5000; // 5 seconds
let relayDataInterval;

document.addEventListener('DOMContentLoaded', function() {
    refreshRelayData();
    relayDataInterval = setInterval(refreshRelayData, RELAY_DATA_POLL_INTERVAL);
});

function formatSeconds(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined) {
        return 'Not configured';
    }
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
}

async function refreshRelayData() {
    const relayStateValue = document.getElementById('relay-state-value');
    const ontimeReading = document.getElementById('ontime-reading');

    const [relayStateResult, ontimeResult] = await Promise.allSettled([
        fetch('/api/space/relay/state').then(response => response.json()),
        fetch('/api/space/relay/ontime').then(response => response.json())
    ]);

    if (relayStateResult.status === 'fulfilled') {
        const relayStateData = relayStateResult.value;

        if (relayStateData && relayStateData.error) {
            relayStateValue.textContent = 'Error';
            relayStateValue.style.color = '#dc3545';
        } else if (relayStateData && relayStateData.relay_state !== undefined && relayStateData.relay_state !== null) {
            if (relayStateData.relay_state === true) {
                relayStateValue.textContent = '✅ On';
                relayStateValue.style.color = '#28a745';
            } else {
                relayStateValue.textContent = '❌ Off';
                relayStateValue.style.color = '#dc3545';
            }
        } else {
            relayStateValue.textContent = '⚠️ Not Configured';
            relayStateValue.style.color = '#6c757d';
        }
    } else {
        console.error('Error loading relay state:', relayStateResult.reason);
        relayStateValue.textContent = 'Error';
    }

    if (ontimeResult.status === 'fulfilled') {
        const ontimeData = ontimeResult.value;

        if (ontimeData && ontimeData.error) {
            ontimeReading.textContent = 'Error';
        } else if (ontimeData && ontimeData.total_active_seconds !== undefined) {
            ontimeReading.textContent = formatSeconds(ontimeData.total_active_seconds);
        } else {
            ontimeReading.textContent = 'N/A';
        }
    } else {
        console.error('Error loading relay on time:', ontimeResult.reason);
        ontimeReading.textContent = 'Error';
    }
}

function showResetConfirmation() {
    const modal = document.getElementById('reset-modal');
    if (modal) {
        modal.style.display = 'flex';
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

async function performOnTimeReset() {
    hideResetConfirmation();

    const resetButton = document.querySelector('.reset-button');
    const resultDiv = document.getElementById('resetResult');

    try {
        if (resetButton) {
            resetButton.textContent = 'Resetting...';
            resetButton.disabled = true;
        }

        const response = await fetch('/api/space/relay/ontime/reset', { method: 'POST' });
        const result = await response.json();

        if (response.ok && result.success) {
            resultDiv.className = 'result-message success';
            resultDiv.textContent = 'On time counter reset successfully';
            resultDiv.style.display = 'block';
            await refreshRelayData();
        } else {
            resultDiv.className = 'result-message error';
            resultDiv.textContent = `Error: ${result.error || 'Failed to reset on time counter'}`;
            resultDiv.style.display = 'block';
        }
    } catch (error) {
        resultDiv.className = 'result-message error';
        resultDiv.textContent = `Error resetting on time counter: ${error.message}`;
        resultDiv.style.display = 'block';
    } finally {
        if (resetButton) {
            resetButton.textContent = 'Reset On Time Counter';
            resetButton.disabled = false;
        }
    }
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
window.refreshRelayData = refreshRelayData;
window.showResetConfirmation = showResetConfirmation;
window.hideResetConfirmation = hideResetConfirmation;
window.performOnTimeReset = performOnTimeReset;
