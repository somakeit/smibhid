// PMSA003I Particulate Matter Sensor Management Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    refreshReadings();
});

async function loadConfig() {
    try {
        const response = await fetch('/api/sensors/modules/PMSA003I/config');
        const data = await response.json();

        if (data.error) {
            setDutyCycleStatus('error', `Error: ${data.error}`);
            setDataConfigStatus('error', `Error: ${data.error}`);
            return;
        }

        // Populate duty cycle inputs with current values
        if (data.fan_run_seconds !== undefined) {
            document.getElementById('fanRunSeconds').placeholder = data.fan_run_seconds.toString();
            document.getElementById('fanRunSeconds').value = data.fan_run_seconds;
        }
        if (data.poll_period_seconds !== undefined) {
            document.getElementById('pollPeriodSeconds').placeholder = data.poll_period_seconds.toString();
            document.getElementById('pollPeriodSeconds').value = data.poll_period_seconds;
        }

        const fanRun = data.fan_run_seconds;
        const pollPeriod = data.poll_period_seconds;
        const sleepSeconds = pollPeriod - fanRun;
        setDutyCycleStatus('active', `Fan runs ${fanRun}s, sleeps ${sleepSeconds}s per ${pollPeriod}s cycle`);

        // Set standard values toggle
        const includeStandard = data.include_standard_values === true;
        document.getElementById('includeStandardValues').checked = includeStandard;
        setDataConfigStatus('active', includeStandard
            ? 'Standard (CF=1) values enabled'
            : 'Standard (CF=1) values disabled — returning atmospheric values only');

        // Show/hide standard readings section based on current config
        document.getElementById('standard-readings-section').style.display = includeStandard ? 'block' : 'none';

        console.log('PMSA003I config loaded:', data);
    } catch (error) {
        console.error('Error loading PMSA003I config:', error);
        setDutyCycleStatus('error', 'Error loading configuration');
        setDataConfigStatus('error', 'Error loading configuration');
    }
}

async function refreshReadings() {
    try {
        const response = await fetch('/api/sensors/readings/latest');
        const data = await response.json();

        const pm = data.PMSA003I;
        if (!pm) {
            setReadingValue('pm10-env-reading', '--');
            setReadingValue('pm25-env-reading', '--');
            setReadingValue('pm100-env-reading', '--');
            setParticleValues(null);
            console.warn('No PMSA003I data in readings response');
            return;
        }

        // Atmospheric PM concentrations (always present)
        setReadingValue('pm10-env-reading', pm.pm10_env !== null && pm.pm10_env !== undefined ? pm.pm10_env : '--');
        setReadingValue('pm25-env-reading', pm.pm25_env !== null && pm.pm25_env !== undefined ? pm.pm25_env : '--');
        setReadingValue('pm100-env-reading', pm.pm100_env !== null && pm.pm100_env !== undefined ? pm.pm100_env : '--');

        // Standard (CF=1) PM concentrations (only when enabled)
        const hasStandard = pm.pm10_standard !== undefined;
        document.getElementById('standard-readings-section').style.display = hasStandard ? 'block' : 'none';
        if (hasStandard) {
            setReadingValue('pm10-std-reading', pm.pm10_standard !== null ? pm.pm10_standard : '--');
            setReadingValue('pm25-std-reading', pm.pm25_standard !== null ? pm.pm25_standard : '--');
            setReadingValue('pm100-std-reading', pm.pm100_standard !== null ? pm.pm100_standard : '--');
        }

        // Particle counts
        setParticleValues(pm);

        console.log('PMSA003I readings refreshed');
    } catch (error) {
        console.error('Error refreshing PMSA003I readings:', error);
        setReadingValue('pm10-env-reading', 'Error');
        setReadingValue('pm25-env-reading', 'Error');
        setReadingValue('pm100-env-reading', 'Error');
    }
}

function setReadingValue(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = value;
    }
}

function setParticleValues(pm) {
    const fields = [
        ['particles-03um-reading', 'particles_03um'],
        ['particles-05um-reading', 'particles_05um'],
        ['particles-10um-reading', 'particles_10um'],
        ['particles-25um-reading', 'particles_25um'],
        ['particles-50um-reading', 'particles_50um'],
        ['particles-100um-reading', 'particles_100um'],
    ];
    fields.forEach(([elId, key]) => {
        const value = pm && pm[key] !== null && pm[key] !== undefined ? pm[key] : '--';
        setReadingValue(elId, value);
    });
}

async function applyDutyCycle() {
    const fanRun = parseInt(document.getElementById('fanRunSeconds').value);
    const pollPeriod = parseInt(document.getElementById('pollPeriodSeconds').value);
    const resultDiv = document.getElementById('dutyCycleResult');

    if (!fanRun || fanRun < 5) {
        showResult(resultDiv, 'error', 'Fan run time must be at least 5 seconds');
        return;
    }
    if (!pollPeriod || pollPeriod < 15) {
        showResult(resultDiv, 'error', 'Poll period must be at least 15 seconds');
        return;
    }
    if (fanRun >= pollPeriod) {
        showResult(resultDiv, 'error', 'Fan run time must be less than the poll period');
        return;
    }

    showResult(resultDiv, '', 'Applying...');

    try {
        // Apply fan run seconds first, then poll period
        const fanResp = await fetch(`/api/sensors/modules/PMSA003I/fan_run_seconds/${fanRun}`, { method: 'PUT' });
        const fanResult = await fanResp.json();
        if (!fanResp.ok || fanResult.error) {
            showResult(resultDiv, 'error', `Error setting fan run time: ${fanResult.error || 'Unknown error'}`);
            return;
        }

        const pollResp = await fetch(`/api/sensors/modules/PMSA003I/poll_period_seconds/${pollPeriod}`, { method: 'PUT' });
        const pollResult = await pollResp.json();
        if (!pollResp.ok || pollResult.error) {
            showResult(resultDiv, 'error', `Error setting poll period: ${pollResult.error || 'Unknown error'}`);
            return;
        }

        const sleepSeconds = pollPeriod - fanRun;
        showResult(resultDiv, 'success', `Duty cycle updated: fan runs ${fanRun}s, sleeps ${sleepSeconds}s per ${pollPeriod}s cycle`);
        setDutyCycleStatus('active', `Fan runs ${fanRun}s, sleeps ${sleepSeconds}s per ${pollPeriod}s cycle`);
    } catch (error) {
        showResult(resultDiv, 'error', `Error applying duty cycle: ${error.message}`);
    }
}

async function applyStandardValues(enabled) {
    const resultDiv = document.getElementById('dataConfigResult');
    const value = enabled ? 'true' : 'false';

    try {
        const response = await fetch(`/api/sensors/modules/PMSA003I/include_standard_values/${value}`, { method: 'PUT' });
        const result = await response.json();

        if (!response.ok || result.error) {
            showResult(resultDiv, 'error', `Error: ${result.error || 'Unknown error'}`);
            // Revert the toggle
            document.getElementById('includeStandardValues').checked = !enabled;
            return;
        }

        const statusText = enabled
            ? 'Standard (CF=1) values enabled'
            : 'Standard (CF=1) values disabled — returning atmospheric values only';
        showResult(resultDiv, 'success', statusText);
        setDataConfigStatus('active', statusText);

        // Refresh readings to show/hide standard section immediately
        await refreshReadings();
    } catch (error) {
        showResult(resultDiv, 'error', `Error updating setting: ${error.message}`);
        document.getElementById('includeStandardValues').checked = !enabled;
    }
}

function setDutyCycleStatus(state, text) {
    const dot = document.querySelector('#duty-cycle-status .status-dot');
    const textEl = document.getElementById('duty-cycle-status-text');
    if (dot) dot.className = `status-dot ${state}`;
    if (textEl) textEl.textContent = text;
}

function setDataConfigStatus(state, text) {
    const dot = document.querySelector('#data-config-status .status-dot');
    const textEl = document.getElementById('data-config-status-text');
    if (dot) dot.className = `status-dot ${state}`;
    if (textEl) textEl.textContent = text;
}

function showResult(div, type, message) {
    div.className = `result-message${type ? ' ' + type : ''}`;
    div.textContent = message;
    div.style.display = 'block';
}

// Make functions globally available
window.refreshReadings = refreshReadings;
window.applyDutyCycle = applyDutyCycle;
window.applyStandardValues = applyStandardValues;
