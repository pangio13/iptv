import requests
import json
import os
import sys  # <--- AGGIUNTO: Necessario per exit(1)

SOURCE_URL = "https://raw.githubusercontent.com/ZapprTV/channels/refs/heads/main/it/dtt/national.json"
OUTPUT_FILE = "discovery_db.json"

def update_db():
    try:
        print(f"Recupero dati da: {SOURCE_URL}")
        response = requests.get(SOURCE_URL, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
        
        # Gestione flessibile della struttura JSON
        channels = []
        if isinstance(raw_data, list):
            channels = raw_data
        elif isinstance(raw_data, dict):
            channels = raw_data.get("channels", [])
        
        targets = ["NOVE", "Real Time", "DMAX", "Giallo", "Food Network", "Discovery", "Motor Trend"]
        db = {}
        
        for ch in channels:
            if not isinstance(ch, dict):
                continue
                
            name = ch.get("name", "")
            # Match case-insensitive e filtro per Clearkey
            if name.upper() in [t.upper() for t in targets] and ch.get("license") == "clearkey":
                # Normalizzazione ID per il Worker (es: "Real Time" -> "realtime")
                ch_id = name.lower().replace(" ", "")
                db[ch_id] = {
                    "url": ch.get("url"),
                    "keys": ch.get("licensedetails")
                }
        
        if not db:
            print("Attenzione: nessun canale Discovery trovato con Clearkey.")
            
        with open(OUTPUT_FILE, "w") as f:
            json.dump(db, f, indent=4)
        
        print(f"Database salvato con successo: {len(db)} canali mappati.")
        
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        sys.exit(1) #

if __name__ == "__main__":
    update_db()
