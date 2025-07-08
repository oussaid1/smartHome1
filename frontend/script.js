async function fetchData() {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        document.getElementById('temperature').textContent = data.temperature;
        document.getElementById('humidity').textContent = data.humidity;
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('temperature').textContent = 'Error';
        document.getElementById('humidity').textContent = 'Error';
    }
}

// Fetch data initially
fetchData();

// Fetch data every 5 seconds
setInterval(fetchData, 5000);
