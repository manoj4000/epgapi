import requests
import json
from datetime import datetime, timedelta

EPG_FILE = "epg.json"
API_URL = "https://tm.tapi.videoready.tv/portal-search/pub/api/v1/channels/schedule"
LIMIT = 20  # Number of results per request

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
            "limit": LIMIT,
            "offset": page * LIMIT
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            response = requests.get(API_URL, params=params, headers=headers)
            print(f"Fetching URL: {response.url}")  # Show full API URL
            print(f"Status Code: {response.status_code}")  # Show HTTP status

            response.raise_for_status()  # Raise error for bad responses
            data = response.json().get("data", {})

            if not data:
                print(f"No data found for {date_str}")
                return []

            channels_data = data.get("channelList", [])
            print(f"Found {len(channels_data)} channels for {date_str}")  # Show count

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

    print(f"✅ Done fetching EPG for {date_str} ({len(all_epg)} channels processed)")
    return all_epg

def fetch_epg_for_days(days=2):
    """Fetch EPG for multiple days and save to file."""
    all_days_epg = []
    for i in range(days):
        date_str = (datetime.now() + timedelta(days=i)).strftime("%d-%m-%Y")
        epg_data = fetch_epg(date_str)
        if epg_data:
            all_days_epg.extend(epg_data)

    if all_days_epg:
        with open(EPG_FILE, "w", encoding="utf-8") as f:
            json.dump(all_days_epg, f, indent=4)
        print(f"✅ EPG data saved successfully to {EPG_FILE}")
    else:
        print("❌ No EPG data fetched.")

if __name__ == "__main__":
    fetch_epg_for_days()
