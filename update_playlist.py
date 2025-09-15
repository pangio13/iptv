import requests
import re
import unicodedata
import sys

SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

def clean_name(s: str) -> str:
    """Normalizza e pulisce il nome canale per confronti parziali."""
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('ⓖ', '')  # simbolo geolocalizzazione
    for ch in ['(', ')', '[', ']', '{', '}']:
        s = s.replace(ch, '')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = ' '.join(s.split())
    return s

def parse_extinf(line: str):
    """Estrae tvg-name e nome visualizzato."""
    attrs = dict(re.findall(r'(\w+?)="(.*?)"', line))
    tvg_name = attrs.get('tvg-name') or attrs.get('tvg_name')
    display_name = re.search(r',(.+)$', line)
    return tvg_name, display_name.group(1).strip() if display_name else ""

def find_next_url(lines, start_idx):
    """Trova il primo URL http(s) dopo start_idx."""
    for j in range(start_idx + 1, len(lines)):
        if lines[j].startswith("http"):
            return j
    return None

print("Scarico playlist sorgente...")
src_lines = requests.get(SOURCE_URL, timeout=30).text.splitlines()

# Indicizza sorgente con nomi puliti
src_map = {}
for i, line in enumerate(src_lines):
    if not line.startswith("#EXTINF"):
        continue
    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(src_lines, i)
    if url_idx is None:
        continue
    url = src_lines[url_idx].strip()
    name_clean = clean_name(tvg_name or disp)
    if name_clean:
        src_map[name_clean] = url

print(f"Canali indicizzati dalla sorgente: {len(src_map)}")

# Leggi la tua playlist
with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
    my_lines = f.readlines()

# === PRE-CHECK MATCH ===
my_names_clean = []
for i, line in enumerate(my_lines):
    if line.startswith("#EXTINF"):
        tvg_name, disp = parse_extinf(line)
        my_names_clean.append((disp or tvg_name, clean_name(tvg_name or disp)))

matched = []
unmatched = []
for original, clean in my_names_clean:
    found = any(clean and clean in src_name for src_name in src_map.keys())
    if found:
        matched.append(original)
    else:
        unmatched.append(original)

print(f"\n=== CHECK PRE-AGGIORNAMENTO ===")
print(f"Canali nella tua playlist: {len(my_names_clean)}")
print(f"Match trovati: {len(matched)}")
print(f"Senza match: {len(unmatched)}")

if unmatched:
    print("\nElenco canali senza match:")
    for ch in unmatched:
        print(" -", ch)

# Se vuoi bloccare l'aggiornamento se non è 100%, decommenta:
# if unmatched:
#     print("\n⚠️ Non tutti i canali hanno match. Aggiornamento interrotto.")
#     sys.exit(1)

# === AGGIORNAMENTO ===
updated = 0
for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue
    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(my_lines, i)
    if url_idx is None:
        continue
    current_url = my_lines[url_idx].strip()
    my_clean = clean_name(tvg_name or disp)

    match_url = None
    for src_name, src_url in src_map.items():
        if my_clean and my_clean in src_name:
            match_url = src_url
            break

    if match_url and match_url != current_url:
        print(f"[UPDATE] {disp or tvg_name}")
        print(f"  Vecchio: {current_url}")
        print(f"  Nuovo : {match_url}")
        my_lines[url_idx] = match_url + "\n"
        updated += 1

# Salva
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nAggiornamento completato. Canali aggiornati: {updated}")
