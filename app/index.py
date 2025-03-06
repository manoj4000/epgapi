from flask import Flask, jsonify
import json
import os
from epg_script import fetch_epg_for_days

app = Flask(__name__)

EPG_FILE = "epg.json"

@app.route("/")
def home():
    return "EPG Fetcher API is running!"

@app.route("/download_epg")
def download_epg():
    """Fetch EPG for multiple days and save it."""
    days_to_fetch = 2  # Change to the number of days you want to fetch
    fetch_epg_for_days(days_to_fetch)
    
    if os.path.exists(EPG_FILE):
        return jsonify({"status": "success", "message": "EPG data updated"})
    else:
        return jsonify({"status": "error", "message": "EPG fetching failed"}), 500

@app.route("/epg")
def get_epg():
    """Returns the stored EPG data."""
    if os.path.exists(EPG_FILE):
        with open(EPG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"status": "error", "message": "No EPG data found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
