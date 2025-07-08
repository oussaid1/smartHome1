import network
import socket
import time
import json
from machine import Pin
try:
    import dht
except ImportError:
    print("Error: The 'dht' library is not installed.")
    print("Please install it using Thonny: Tools > Manage Packages > search for 'micropython-dht'")
    # Create a dummy class if the import fails to avoid further errors
    class dht:
        class DHT11:
            def __init__(self, pin): pass
            def measure(self): pass
            def temperature(self): return -1
            def humidity(self): return -1

# --- Configuration ---
# Set this to True to generate fake data for testing without a sensor
MOCK_SENSOR = False

# Wi-Fi Credentials
WIFI_SSID = "Wifi+"
WIFI_PASSWORD = "123654789or"

# GPIO Pin for the DHT sensor
SENSOR_PIN = 15

# --- End of Configuration ---


# Initialize the sensor
# If MOCK_SENSOR is True, we'll use a dummy object.
if not MOCK_SENSOR:
    sensor = dht.DHT11(Pin(SENSOR_PIN))
else:
    import random
    class MockSensor:
        def measure(self): pass
        def temperature(self): return random.uniform(20, 25)
        def humidity(self): return random.uniform(40, 50)
    sensor = MockSensor()
    print("Running in MOCK mode. Generating random sensor data.")


# Function to connect to Wi-Fi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    print(f"Connecting to Wi-Fi network: {ssid}...")
    max_wait = 15
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print(".")
        time.sleep(1)
        
    if wlan.status() != 3:
        raise RuntimeError('Network connection failed')
    else:
        print('Connected!')
        status = wlan.ifconfig()
        print(f'IP Address: {status[0]}')
    return status[0]

# Function to read sensor data
def read_sensor():
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        if temp is None or hum is None:
            return None, "Failed to read from sensor"
        return {"temperature": temp, "humidity": hum}, None
    except Exception as e:
        return None, str(e)

# --- Main Script ---

# 1. Connect to Wi-Fi
try:
    ip_address = connect_wifi(WIFI_SSID, WIFI_PASSWORD)
except RuntimeError as e:
    print(e)
    # Loop forever if Wi-Fi fails, so the device can be reprogrammed.
    while True:
        time.sleep(5)

# 2. Open a socket to listen for web requests
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print(f"Web server listening on http://{ip_address}")

# 3. Main loop to handle incoming requests
while True:
    try:
        cl, addr = s.accept()
        print(f"Client connected from {addr}")
        
        # Get the data from the sensor
        data, error = read_sensor()
        
        # Create the HTTP response
        if data:
            response_body = json.dumps(data)
            cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
            cl.send(response_body)
        else:
            response_body = json.dumps({"error": error})
            cl.send('HTTP/1.0 500 Internal Server Error\r\nContent-type: application/json\r\n\r\n')
            cl.send(response_body)
            
        cl.close()
        
    except OSError as e:
        cl.close()
        print('Connection closed')
    except KeyboardInterrupt:
        print("Server stopped by user.")
        s.close()
        break