import requests
import re
import unicodedata
import sys

# --- CONFIGURAZIONE ---
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"
# Canali da escludere (minuscolo). Se il nome pulito contiene queste parole, il link non viene toccato.
EXCLUDE_LIST = ["tv8", "tv 8"] 
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
    # Cerca il nome visualizzato dopo l'ultima virgola
    match_disp = re.search(r',([^,]+)$', line)
    display_name = match_disp.group(1).strip() if match_disp else ""
    return tvg_name, display_name

def find_next_url(lines, start_idx):
    """Trova la prossima riga che inizia con http."""
    for j in range(start_idx + 1, len(lines)):
        line = lines[j].strip()
        if line.startswith("http"):
            return j
        # Se incontriamo un altro EXTINF prima dell'URL, qualcosa non va (o fine blocco)
        if line.startswith("#EXTINF"):
            return None
    return None

# 1. Scarica la playlist sorgente
print("Scarico playlist sorgente...")
try:
    resp = requests.get(SOURCE_URL, timeout=30)
    resp.raise_for_status()
    src_lines = resp.text.splitlines()
except Exception as e:
    print(f"Errore download sorgente: {e}")
    sys.exit(1)

# 2. Mappa i canali sorgente {nome_pulito: url}
src_map = {}
for i, line in enumerate(src_lines):
    if not line.startswith("#EXTINF"):
        continue
    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(src_lines, i)
    if url_idx is None:
        continue
    
    url = src_lines[url_idx].strip()
    # Usa sia tvg-name che display name per creare chiavi di ricerca
    keys = set()
    if tvg_name: keys.add(clean_name(tvg_name))
    if disp: keys.add(clean_name(disp))
    
    for k in keys:
        if k: src_map[k] = url

print(f"Canali trovati nella sorgente: {len(src_map)}")

# 3. Leggi la tua playlist locale
try:
    with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
        my_lines = f.readlines()
except FileNotFoundError:
    print(f"Errore: File {MY_PLAYLIST} non trovato.")
    sys.exit(1)

# 4. Aggiorna i link
updated = 0
skipped = 0
print("\n=== AVVIO CONTROLLO CANALI ===")

for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue

    tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(my_lines, i)
    
    if url_idx is None:
        continue

    current_url = my_lines[url_idx].strip()
    my_clean = clean_name(tvg_name or disp)

    # -- CONTROLLO ESCLUSIONE (TV8) --
    is_excluded = False
    for ex in EXCLUDE_LIST:
        if ex in my_clean:
            is_excluded = True
            print(f"⚠️  ESCLUSO: '{disp}' (trovato '{ex}') -> Link manuale mantenuto.")
            skipped += 1
            break
    
    if is_excluded:
        continue
    # --------------------------------

    # Cerca match nella mappa sorgente
    match_url = None
    # Prima prova col nome pulito esatto
    if my_clean in src_map:
        match_url = src_map[my_clean]
    else:
        # Se non trova match esatto, cerca parziale (più lento ma più sicuro)
        for src_k, src_u in src_map.items():
            if my_clean and (my_clean in src_k or src_k in my_clean):
                match_url = src_u
                break
    
    # Applica aggiornamento se url diverso
    if match_url and match_url != current_url:
        print(f"[AGGIORNATO] {disp}")
        # print(f"   OLD: {current_url}")
        # print(f"   NEW: {match_url}")
        my_lines[url_idx] = match_url + "\n"
        updated += 1

# 5. Salva il file
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nOperazione completata.")
print(f"Canali aggiornati: {updated}")
print(f"Canali esclusi (es. TV8): {skipped}")
