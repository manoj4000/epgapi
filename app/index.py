import requests
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from flask import Flask, send_file
import os

app = Flask(__name__)

# Base URL
url = "https://tm.tapi.videoready.tv/portal-search/pub/api/v1/channels/schedule"
limit = 20  # Number of items per page

def fetch_epg(date_str):
    all_epg = []
    page = 0  # Start with the first page
    while True:
        params = {
            "date": date_str,
            "languageFilters": "",
            "genreFilters": "",
            "limit": limit,
            "offset": page * limit
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("data", {})

            if not data:
                return []

            channels_data = data.get("channelList", [])

            for channel in channels_data:
                epg_data = [
                    {
                        "id": epg["id"],
                        "startTime": epg["startTime"],
                        "endTime": epg["endTime"],
                        "title": epg["title"],
                        "desc": epg["desc"],
                    }
                    for epg in channel.get("epg", [])
                ]
                if epg_data:
                    all_epg.append({
                        "date": date_str,
                        "channelId": channel["id"],
                        "channelTitle": channel["title"],
                        "epg": epg_data
                    })

            if data.get("offset", 0) + data.get("limit", 0) >= data.get("total", 0):
                break

            page += 1
        except requests.RequestException as e:
            print(f"Request failed for date {date_str}: {e}")
            return []

    return all_epg

def update_epg():
    """Fetch and save EPG data every 2 days."""
    while True:
        all_epg = []
        for i in range(3):  # Get EPG for today and next two days
            date_str = (datetime.now(timezone.utc) + timedelta(days=i)).strftime("%d-%m-%Y")
            all_epg.extend(fetch_epg(date_str))

        with open("epg.json", "w") as json_file:
            json.dump(all_epg, json_file, indent=4)
        print("EPG data for the next 2 days saved to epg.json")

        time.sleep(172800)  # Wait for 2 days (172800 seconds)

@app.route('/')
def hello():
    return 'Hello world with Flask'

@app.route("/download_epg", methods=["GET"])
def download_epg():
    """API to download the EPG JSON file."""
    return send_file("epg.json", mimetype="application/json", as_attachment=True, download_name="epg.json")

if __name__ == "__main__":
    threading.Thread(target=update_epg, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=True)
