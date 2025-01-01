from flask import Flask, jsonify
import threading
import time
import random
import requests
from collections import deque
from datetime import datetime
import pytz  # For timezone conversion

app = Flask(__name__)

from admin import services, wait_time_start, wait_time_end, deque_length, timeout

# A deque to store the logs
ping_logs = deque(maxlen=deque_length )  # deque length imported from admin.py

def get_indian_time():
    """Get the current time in the Indian timezone."""
    india_timezone = pytz.timezone("Asia/Kolkata")
    return datetime.now(india_timezone).strftime("%Y-%m-%d %H:%M:%S")

def log_group(wait_time, pings):
    """Log a group of pings with a wait message."""
    ping_logs.appendleft({
        "pings": pings,
        "timestamp": get_indian_time(),
        "message": f"Waiting for {wait_time // 60} minutes before the next ping..."
    })

def ping_services():
    """Ping all services at random intervals."""
    while True:
        pings = []
        for service in services:  # services imported from admin.py
            try:
                response = requests.get(service, timeout=timeout)  # timeout imported from admin
                pings.append({
                    "timestamp": get_indian_time(),
                    "service": service,
                    "status": response.status_code,
                    "message": "Ping successful"
                })
                print(f"Pinged {service}, Status Code: {response.status_code}")
            except requests.RequestException as e:
                pings.append({
                    "timestamp": get_indian_time(),
                    "service": service,
                    "status": "Error",
                    "message": str(e)
                })
                print(f"Failed to ping {service}: {e}")
        
        # Log the group of pings with a waiting message
        wait_time = random.randint(wait_time_start, wait_time_end)  # imported from admin.py
        log_group(wait_time, pings)
        print(f"Waiting for {wait_time // 60} minutes before the next ping...")
        time.sleep(wait_time)

# Run the pinging function in a separate thread
thread = threading.Thread(target=ping_services, daemon=True)
thread.start()

@app.route("/")
def home():
    """Return the last 20 grouped logs."""
    if not ping_logs:
        return jsonify({"error": "No pings logged yet. Please wait for the next cycle."})
    return jsonify(list(ping_logs))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)