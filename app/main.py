from fastapi import FastAPI
from fastapi.responses import FileResponse
import asyncio
import uvicorn
import requests
import json
from datetime import datetime, timedelta, timezone

app = FastAPI()

url = "https://tm.tapi.videoready.tv/portal-search/pub/api/v1/channels/schedule"
limit = 20

def fetch_epg(date_str):
    all_epg = []
    page = 0
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
            print(f"Request failed for {date_str}: {e}")
            return []

    return all_epg

async def update_epg():
    all_epg = []
    for i in range(3):
        date_str = (datetime.now(timezone.utc) + timedelta(days=i)).strftime("%d-%m-%Y")
        all_epg.extend(fetch_epg(date_str))

    with open("epg.json", "w") as json_file:
        json.dump(all_epg, json_file, indent=4)
    print("EPG data saved to epg.json")

async def epg_scheduler():
    while True:
        await update_epg()
        await asyncio.sleep(172800)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(epg_scheduler())

@app.get("/download_epg")
async def download_epg():
    return FileResponse("epg.json", media_type="application/json", filename="epg.json")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
