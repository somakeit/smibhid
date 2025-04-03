const version = '0.0.28';

document.getElementById('add_file_form').addEventListener('submit', function(event) {
    console.log('File staging update form submitted.');
    event.preventDefault();

    var request_body = JSON.stringify({"action": "add", "url": document.getElementById('url').value});

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
        }

        else {
            var result_message = "Error updating firmware staging list. API return:", data;
        }
        
        document.getElementById('result').innerText = result_message;

        fetchURLs();
    })
    .catch(error => {
        console.error('Error encountered updating firmware staging list:', error);
        document.getElementById('result').innerText = "Error updating firmware staging list: " + error.message;
    });

});

document.getElementById('remove_file_form').addEventListener('submit', function(event) {
    console.log('File staging update form submitted.');
    event.preventDefault();

    var selectedUrl = document.querySelector('input[name="url"]:checked').value;
    
    var request_body = JSON.stringify({"action": "remove", "url": selectedUrl});

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
        }

        else {
            var result_message = "Error updating firmware staging list. API return:", data;
        }
        
        document.getElementById('result').innerText = result_message;

        fetchURLs();
    })
    .catch(error => {
        console.error('Error encountered updating firmware staging list:', error);
        document.getElementById('result').innerText = "Error updating firmware staging list: " + error.message;
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
                if (data && data.length > 0) {
                    console.log('URLs returned and processing');
                    data.forEach((url, index) => {
                        if (url != "") {
                            console.log('Adding URL:', url);
                            const listItem = document.createElement('li');
                            const radioInput = document.createElement('input');
                            radioInput.type = 'radio';
                            radioInput.name = 'url';
                            radioInput.value = url;
                            radioInput.id = `${index + 1}`;
                            
                            const label = document.createElement('label');
                            label.htmlFor = `${index + 1}`;
                            label.textContent = url;

                            listItem.appendChild(radioInput);
                            listItem.appendChild(label);
                            urlList.appendChild(listItem);
                        }
                    });
                }
            })
            .catch(error => console.error('Error fetching URLs:', error));
    }

        window.fetchURLs = fetchURLs;
        fetchURLs();
});