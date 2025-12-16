import requests
import re
import unicodedata
import sys

# --- CONFIGURAZIONE ---
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

# Lista canali da NON toccare (minuscolo, copre varianti con/senza spazio)
EXCLUDE_LIST = ["tv8", "tv 8"] 
# ----------------------

def clean_name(s: str) -> str:
    """Normalizza e pulisce il nome canale per confronti parziali."""
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('Ⓖ', '')
    for ch in ['(', ')', '[', ']', '{', '}']:
        s = s.replace(ch, '')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = ' '.join(s.split())
    return s

def parse_extinf(line: str):
    """Estrae tvg-name e nome visualizzato, ignorando tvg-id."""
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

# === 1. SCARICAMENTO SORGENTE ===
print("Scarico playlist sorgente...")
try:
    src_lines = requests.get(SOURCE_URL, timeout=30).text.splitlines()
except Exception as e:
    print(f"Errore download sorgente: {e}")
    sys.exit(1)

# === 2. INDICIZZAZIONE SORGENTE ===
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

print(f"Canali trovati nella sorgente: {len(src_map)}")

# === 3. LETTURA TUA PLAYLIST ===
try:
    with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
        my_lines = f.readlines()
except FileNotFoundError:
    print(f"Errore: File {MY_PLAYLIST} non trovato.")
    sys.exit(1)

# === 4. AGGIORNAMENTO ===
updated = 0
skipped = 0

print("\n=== AVVIO AGGIORNAMENTO ===")

for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue
    
    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(my_lines, i)
    
    if url_idx is None:
        continue
        
    current_url = my_lines[url_idx].strip()
    my_clean = clean_name(tvg_name or disp) 

    # --- CONTROLLO ESCLUSIONI (Tv8) ---
    is_excluded = False
    for ex in EXCLUDE_LIST:
        if ex in my_clean:
            is_excluded = True
            # Log visivo per confermare che sta funzionando
            print(f"⚠️  ESCLUSO: '{disp}' (trovato '{ex}') -> Link manuale mantenuto.")
            skipped += 1
            break
    
    if is_excluded:
        continue
    # ----------------------------------

    # Cerca match
    match_url = None
    for src_name, src_url in src_map.items():
        if my_clean and my_clean in src_name:
            match_url = src_url
            break

    # Aggiorna se diverso
    if match_url and match_url != current_url:
        print(f"[AGGIORNATO] {disp}")
        my_lines[url_idx] = match_url + "\n"
        updated += 1

# === 5. SALVATAGGIO ===
with open(
