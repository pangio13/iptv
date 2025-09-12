import requests
import re

# URL sorgente Free-TV
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

# Scarica playlist sorgente
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

# Leggi la tua playlist e sostituisci solo gli URL
with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
    my_lines = f.readlines()

for i, line in enumerate(my_lines):
    if line.startswith("#EXTINF"):
        name_match = re.search(r',(.+)$', line)
        if name_match:
            channel_name = name_match.group(1).strip()
            if channel_name in source_map:
                my_lines[i+1] = source_map[channel_name] + "\n"

# Salva
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print("Playlist aggiornata con successo!")