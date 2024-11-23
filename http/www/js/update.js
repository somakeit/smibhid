const version = '0.0.9';

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
        //fetchURLs();
});