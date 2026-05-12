import requests
import json

# Sorgente ufficiale ZapprTV
SOURCE_URL = "https://raw.githubusercontent.com/ZapprTV/channels/refs/heads/main/it/dtt/national.json"
OUTPUT_FILE = "discovery_db.json"

def update_db():
    try:
        response = requests.get(SOURCE_URL, timeout=15)
        response.raise_for_status()
        channels = response.json()
        
        # Filtriamo i canali target
        targets = ["NOVE", "Real Time", "DMAX", "Giallo", "Food Network", "Discovery", "Motor Trend"]
        db = {}
        
        for ch in channels:
            if ch.get("name") in targets and ch.get("license") == "clearkey":
                # Normalizziamo l'ID (es: "Real Time" -> "realtime")
                ch_id = ch["name"].lower().replace(" ", "")
                db[ch_id] = {
                    "url": ch["url"],
                    "keys": ch["licensedetails"]
                }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(db, f, indent=4)
        print(f"Successo: {len(db)} canali mappati.")
        
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    update_db()
