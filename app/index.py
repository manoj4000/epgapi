import requests
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from flask import Flask, send_file
import os

app = Flask(__name__)

# Base URL for fetching EPG
url = "https://tm.tapi.videoready.tv/portal-search/pub/api/v1/channels/schedule"
limit = 20  # Number of items per page

def fetch_epg(date_str):
    """Fetch EPG data for a given date."""
    all_epg = []
    page = 0  # Start with the first page
    
    print(f"Fetching EPG data for {date_str}...")  # Log fetch start
    
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
                print(f"No data found for {date_str}")
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
            print(f"❌ Error fetching EPG for {date_str}: {e}")
            return []

    print(f"✅ Done fetching EPG for {date_str} ({len(all_epg)} channels processed)")  # Log success
    return all_epg

def update_epg():
    """Fetch and save EPG data every 2 days."""
    while True:
        all_epg = []
        days = 3  # Get EPG for today and next two days
        print(f"🔄 Starting EPG fetch for {days} days...")

        for i in range(days):
            date_str = (datetime.now(timezone.utc) + timedelta(days=i)).strftime("%d-%m-%Y")
            fetched_data = fetch_epg(date_str)
            all_epg.extend(fetched_data)

        if all_epg:
            with open("epg.json", "w") as json_file:
                json.dump(all_epg, json_file, indent=4)
            print(f"✅ EPG data saved for {days} days! ({len(all_epg)} total entries)")

        else:
            print("❌ EPG fetch failed, no data saved!")

        print("⏳ Sleeping for 2 days before the next update...")
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
