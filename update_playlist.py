import requests
import re
import unicodedata
import sys

# --- CONFIGURAZIONE ---
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

# AGGIORNATO: Canali gestiti dal Cloudflare Worker da NON toccare mai
EXCLUDE_LIST = [
    "nove", 
    "real time", 
    "dmax", 
    "giallo", 
    "food network", 
    "discovery channel", 
    "motor trend",
    "discovery"
] 

# Stringa User-Agent da ri-applicare se il link viene aggiornato (Chrome Desktop)
CUSTOM_UA_SUFFIX = "|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# ----------------------

def clean_name(s: str) -> str:
    """Pulisce il nome per il confronto (es. 'TV8 HD' -> 'tv8 hd')."""
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('Ⓖ', '')
    for ch in ['(', ')', '[', ']', '{', '}']:
        s = s.replace(ch, '')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' '.join(s.split())

def parse_extinf(line: str):
    """Estrae il nome del canale dalla riga EXTINF."""
    attrs = dict(re.findall(r'(\w+?)="(.*?)"', line))
    tvg_name = attrs.get('tvg-name') or attrs.get('tvg_name')
    match_disp = re.search(r',([^,]+)$', line)
    display_name = match_disp.group(1).strip() if match_disp else ""
    return tvg_name, display_name

def find_next_url(lines, start_idx):
    """Trova la prossima riga che inizia con http."""
    for j in range(start_idx + 1, len(lines)):
        line = lines[j].strip()
        if line.startswith("http"):
            return j
        if line.startswith("#EXTINF"):
            return None
    return None

def find_match_in_map(clean_name_target, source_map):
    """Cerca match esatto o parziale nella mappa."""
    if not clean_name_target:
        return None
    if clean_name_target in source_map:
        return source_map[clean_name_target]
    for src_k, src_u in source_map.items():
        if src_k and (clean_name_target in src_k or src_k in clean_name_target):
            return src_u
    return None

def apply_user_agent_logic(url):
    """Applica lo User-Agent se necessario."""
    if ".php" in url or "mediapolis.rai.it" in url or "workers.dev" in url:
        return url
    
    if "|User-Agent=" in url:
        return url

    domains_needing_ua = ["mediaset.net", "cloudfront.net", "akamaized.net", "land3.se"]
    
    if any(d in url for d in domains_needing_ua):
        return url + CUSTOM_UA_SUFFIX
        
    return url

# 1. SCARICAMENTO E INDICIZZAZIONE SORGENTE
print("Scarico playlist sorgente...")
try:
    resp = requests.get(SOURCE_URL, timeout=30)
    resp.raise_for_status()
    src_lines = resp.text.splitlines()
except Exception as e:
    print(f"Errore download sorgente: {e}")
    sys.exit(1)

src_map = {}
for i, line in enumerate(src_lines):
    if not line.startswith("#EXTINF"):
        continue
    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(src_lines, i)
    if url_idx is None:
        continue
    
    url = src_lines[url_idx].strip()
    if "|" in url:
        url = url.split("|")[0]
        
    keys = set()
    if tvg_name: keys.add(clean_name(tvg_name))
    if disp: keys.add(clean_name(disp))
    
    for k in keys:
        if k: src_map[k] = url

# 2. LETTURA PLAYLIST LOCALE
try:
    with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
        my_lines = f.readlines()
except FileNotFoundError:
    print(f"Errore: File {MY_PLAYLIST} non trovato.")
    sys.exit(1)

# 3. AGGIORNAMENTO LINK
print("\n=== AVVIO AGGIORNAMENTO ===")
updated_count = 0
skipped_count = 0

for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue

    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(my_lines, i)
    if url_idx is None:
        continue

    current_full_url = my_lines[url_idx].strip()
    current_base_url = current_full_url.split("|")[0]
    my_clean = clean_name(tvg_name or disp)

    # -- CONTROLLO PROTEZIONE --
    # Salta se il canale è in EXCLUDE_LIST o se l'URL punta già a un Worker
    is_protected = False
    if "workers.dev" in current_base_url:
        is_protected = True
    else:
        for ex in EXCLUDE_LIST:
            if ex in my_clean:
                is_protected = True
                break
    
    if is_protected:
        print(f"🛡️  PROTETTO: '{disp}' -> Integrazione DRM mantenuta.")
        skipped_count += 1
        continue

    # Cerca nuovo URL nella sorgente
    new_base_url = find_match_in_map(my_clean, src_map)
    
    if new_base_url:
        if new_base_url != current_base_url:
            print(f"[AGGIORNATO] {disp}")
            final_new_url = apply_user_agent_logic(new_base_url)
            my_lines[url_idx] = final_new_url + "\n"
            updated_count += 1

# 5. SALVATAGGIO
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nOperazione completata.")
print(f"Link aggiornati: {updated_count}")
print(f"Canali protetti (Worker/Discovery): {skipped_count}")
