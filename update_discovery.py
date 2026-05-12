import requests
import json
import os

SOURCE_URL = "https://raw.githubusercontent.com/ZapprTV/channels/refs/heads/main/it/dtt/national.json"
OUTPUT_FILE = "discovery_db.json"

def update_db():
    try:
        print(f"Recupero dati da: {SOURCE_URL}")
        response = requests.get(SOURCE_URL, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
        
        # Gestione flessibile: capisce se riceve una lista [...] o un oggetto {"channels": [...]}
        channels = []
        if isinstance(raw_data, list):
            channels = raw_data
        elif isinstance(raw_data, dict):
            channels = raw_data.get("channels", [])
        
        targets = ["NOVE", "Real Time", "DMAX", "Giallo", "Food Network", "Discovery", "Motor Trend"]
        db = {}
        
        for ch in channels:
            # Verifica che 'ch' sia un dizionario prima di usare .get()
            if not isinstance(ch, dict):
                continue
                
            name = ch.get("name", "")
            if name.upper() in [t.upper() for t in targets] and ch.get("license") == "clearkey":
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
        # Forza l'uscita con errore per fermare la GitHub Action
        exit(1)

if __name__ == "__main__":
    update_db()
