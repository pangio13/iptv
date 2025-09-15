import requests
import re

# URL sorgente Free-TV
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

print("=== Scarico playlist sorgente da Free-TV ===")
source_data = requests.get(SOURCE_URL).text

# Crea mappa {nome_canale: nuovo_url}
source_map = {}
lines = source_data.splitlines()
for i, line in enumerate(lines):
    if line.startswith("#EXTINF"):
        name_match = re.search(r',(.+)$', line)
        if name_match:
            channel_name = name_match.group(1).strip()
            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                source_map[channel_name] = lines[i+1]

print(f"Trovati {len(source_map)} canali nella playlist sorgente.")
print("Esempio primi 10 canali sorgente:")
for ch in list(source_map.keys())[:10]:
    print(" -", ch)

# Leggi la tua playlist
with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
    my_lines = f.readlines()

print("\n=== Inizio confronto e aggiornamento ===")
updated_count = 0
no_match = []

for i, line in enumerate(my_lines):
    if line.startswith("#EXTINF"):
        name_match = re.search(r',(.+)$', line)
        if name_match:
            channel_name = name_match.group(1).strip()
            if channel_name in source_map:
                old_url = my_lines[i+1].strip()
                new_url = source_map[channel_name]
                if old_url != new_url:
                    print(f"[UPDATE] {channel_name}")
                    print(f"  Vecchio: {old_url}")
                    print(f"  Nuovo : {new_url}")
                    my_lines[i+1] = new_url + "\n"
                    updated_count += 1
            else:
                no_match.append(channel_name)

# Salva file aggiornato
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nAggiornamento completato. Canali aggiornati: {updated_count}")
if no_match:
    print("\nCanali nella tua playlist senza match nella sorgente:")
    for ch in no_match:
        print(" -", ch)
