const version = '0.0.28';

// Validate firmware URL format
function validateFirmwareUrl(url) {
    // Check if URL starts with http:// or https:// and ends with .py
    const urlPattern = /^https?:\/\/.*\.py$/i;
    return urlPattern.test(url);
}

// Check if URL already exists in the pending list
function isDuplicateUrl(url) {
    const existingUrls = Array.from(document.querySelectorAll('input[name="url"]')).map(input => input.value);
    return existingUrls.includes(url);
}

// Add real-time validation feedback
function setupRealtimeValidation() {
    const urlInput = document.getElementById('url');
    const resultDiv = document.getElementById('result');
    
    urlInput.addEventListener('input', function() {
        const url = this.value.trim();
        
        // Clear previous validation messages when user starts typing
        if (resultDiv.classList.contains('error') && resultDiv.style.display === 'block') {
            resultDiv.style.display = 'none';
        }
        
        // Show validation hint for partially entered URLs
        if (url.length > 0 && !validateFirmwareUrl(url)) {
            this.setCustomValidity('URL must start with http:// or https:// and end with .py');
        } else if (url.length > 0 && isDuplicateUrl(url)) {
            this.setCustomValidity('This URL is already in the pending files list');
        } else {
            this.setCustomValidity('');
        }
    });
    
    urlInput.addEventListener('blur', function() {
        const url = this.value.trim();
        if (url.length > 0) {
            if (!validateFirmwareUrl(url)) {
                resultDiv.innerText = "Invalid URL format. Must start with http:// or https:// and end with .py";
                resultDiv.className = 'result-message error';
                resultDiv.style.display = 'block';
            } else if (isDuplicateUrl(url)) {
                resultDiv.innerText = "This URL is already in the pending files list";
                resultDiv.className = 'result-message error';
                resultDiv.style.display = 'block';
            }
        }
    });
}

document.getElementById('add_file_form').addEventListener('submit', function(event) {
    console.log('File staging update form submitted.');
    event.preventDefault();

    const urlInput = document.getElementById('url');
    const url = urlInput.value.trim();
    
    // Custom validation
    if (!validateFirmwareUrl(url)) {
        document.getElementById('result').innerText = "Invalid URL format. Must start with http:// or https:// and end with .py";
        document.getElementById('result').className = 'result-message error';
        document.getElementById('result').style.display = 'block';
        return;
    }

    // Check for duplicate URLs
    if (isDuplicateUrl(url)) {
        document.getElementById('result').innerText = "This URL is already in the pending files list";
        document.getElementById('result').className = 'result-message error';
        document.getElementById('result').style.display = 'block';
        return;
    }

    var request_body = JSON.stringify({"action": "add", "url": url});

    // Show loading state
    document.getElementById('result').innerText = "Adding firmware file...";
    document.getElementById('result').className = 'result-message';
    document.getElementById('result').style.display = 'block';

    fetch('/api/firmware_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: request_body
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log('Request data returned:', data);
        if (data === true) {
            var result_message = "Firmware staging list updated successfully";
            document.getElementById('result').className = 'result-message success';
            // Clear the input field on success
            urlInput.value = '';
        } else {
            var result_message = "Error updating firmware staging list. API return: " + data;
            document.getElementById('result').className = 'result-message error';
        }
        
        document.getElementById('result').innerText = result_message;
        document.getElementById('result').style.display = 'block';

        fetchURLs();
    })
    .catch(error => {
        console.error('Error encountered updating firmware staging list:', error);
        document.getElementById('result').innerText = "Error updating firmware staging list: " + error.message;
        document.getElementById('result').className = 'result-message error';
        document.getElementById('result').style.display = 'block';
    });

});

document.getElementById('remove_file_form').addEventListener('submit', function(event) {
    console.log('File staging removal form submitted.');
    event.preventDefault();

    // Get all selected checkboxes
    var selectedCheckboxes = document.querySelectorAll('input[name="url"]:checked');
    
    if (selectedCheckboxes.length === 0) {
        document.getElementById('result').innerText = "Please select at least one file to remove.";
        document.getElementById('result').className = 'result-message error';
        document.getElementById('result').style.display = 'block';
        return;
    }

    // Remove each selected file
    let promises = [];
    selectedCheckboxes.forEach(checkbox => {
        var request_body = JSON.stringify({"action": "remove", "url": checkbox.value});
        
        promises.push(
            fetch('/api/firmware_files', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: request_body
            })
        );
    });

    // Wait for all removal requests to complete
    Promise.all(promises)
    .then(responses => {
        // Check if all responses are ok
        let allSuccess = responses.every(response => response.ok);
        if (allSuccess) {
            document.getElementById('result').innerText = `Successfully removed ${selectedCheckboxes.length} file(s)`;
            document.getElementById('result').className = 'result-message success';
        } else {
            document.getElementById('result').innerText = "Some files could not be removed";
            document.getElementById('result').className = 'result-message error';
        }
        document.getElementById('result').style.display = 'block';
        fetchURLs();
    })
    .catch(error => {
        console.error('Error encountered removing firmware files:', error);
        document.getElementById('result').innerText = "Error removing firmware files: " + error.message;
        document.getElementById('result').className = 'result-message error';
        document.getElementById('result').style.display = 'block';
    });

});


document.addEventListener("DOMContentLoaded", function() {
    function fetchURLs() {
        fetch('api/firmware_files')
            .then(response => response.json())
            .then(data => {
                console.log(data);
                const urlList = document.getElementById('url-list');
                console.log(urlList);
                urlList.innerHTML = '';
                
                // Check if we have any valid URLs
                const validUrls = data ? data.filter(url => url && url.trim() !== "") : [];
                
                if (validUrls.length > 0) {
                    console.log('URLs returned and processing');
                    validUrls.forEach((url, index) => {
                        console.log('Adding URL:', url);
                        const listItem = document.createElement('li');
                        const checkboxInput = document.createElement('input');
                        checkboxInput.type = 'checkbox';
                        checkboxInput.name = 'url';
                        checkboxInput.value = url;
                        checkboxInput.id = `file-${index + 1}`;
                        
                        const label = document.createElement('label');
                        label.htmlFor = `file-${index + 1}`;
                        label.textContent = url;

                        listItem.appendChild(checkboxInput);
                        listItem.appendChild(label);
                        urlList.appendChild(listItem);
                    });
                } else {
                    // Show empty state message
                    const emptyMessage = document.createElement('li');
                    emptyMessage.className = 'empty-message';
                    emptyMessage.innerHTML = '<span class="empty-icon">📋</span><span>No files are currently selected for update</span>';
                    urlList.appendChild(emptyMessage);
                }
            })
            .catch(error => {
                console.error('Error fetching URLs:', error);
                // Show error state
                const urlList = document.getElementById('url-list');
                urlList.innerHTML = '';
                const errorMessage = document.createElement('li');
                errorMessage.className = 'error-message';
                errorMessage.innerHTML = '<span class="error-icon">❌</span><span>Error loading file list</span>';
                urlList.appendChild(errorMessage);
            });
    }

    // Select all files function
    function selectAllFiles() {
        const checkboxes = document.querySelectorAll('input[name="url"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
    }

    // Select none files function
    function selectNoneFiles() {
        const checkboxes = document.querySelectorAll('input[name="url"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    // Make functions globally available
    window.fetchURLs = fetchURLs;
    window.selectAllFiles = selectAllFiles;
    window.selectNoneFiles = selectNoneFiles;
    
    // Initialize real-time validation
    setupRealtimeValidation();
    
    fetchURLs();
});