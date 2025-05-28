const version = '0.0.2';        

export async function setAutoMeasure() {
    const action = document.getElementById('autoMeasureAction').value;
    const response = await fetch(`/api/sensors/modules/SCD30/auto_measure/${action}`, {
        method: 'PUT'
    });
    const result = await response.text();
    alert(`Response: ${result}`);
}

export async function setCalibration() {
    const value = document.getElementById('calibrationValue').value;
    const response = await fetch(`/api/sensors/modules/SCD30/calibration/${value}`, {
        method: 'PUT'
    });
    const result = await response.text();
    alert(`Response: ${result}`);
}