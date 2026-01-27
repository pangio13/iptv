import requests
import re
import unicodedata
import sys

# --- CONFIGURAZIONE ---
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

# AGGIUNTO: Canali da escludere dall'aggiornamento automatico
# Se il nome pulito contiene queste parole, il link non viene toccato.
#EXCLUDE_LIST = ["la7", "tv8", "cielo"] 

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
        # Se incontriamo un altro EXTINF prima dell'URL, stop
        if line.startswith("#EXTINF"):
            return None
    return None

def find_match_in_map(clean_name_target, source_map):
    """Cerca match esatto o parziale nella mappa."""
    if not clean_name_target:
        return None
    # 1. Tentativo esatto
    if clean_name_target in source_map:
        return source_map[clean_name_target]
    # 2. Tentativo parziale
    for src_k, src_u in source_map.items():
        if src_k and (clean_name_target in src_k or src_k in clean_name_target):
            return src_u
    return None

def apply_user_agent_logic(url):
    """
    Se aggiorniamo un link, decide se dobbiamo ri-appendere lo User-Agent.
    """
    # 1. Se è un link PHP (MyTivu) o Rai (Mediapolis), NON aggiungere nulla
    if ".php" in url or "mediapolis.rai.it" in url:
        return url
    
    # 2. Se ha già un User-Agent, non aggiungerlo due volte
    if "|User-Agent=" in url:
        return url

    # 3. Domini che necessitano dell'User-Agent per funzionare bene
    domains_needing_ua = [
        "mediaset.net",    # Mediaset (live02 etc)
        "cloudfront.net",  # Discovery / La7
        "akamaized.net",   # Sky / Vari
        "land3.se"         # Cielo backup
    ]
    
    if any(d in url for d in domains_needing_ua):
        return url + CUSTOM_UA_SUFFIX
        
    return url

# ==========================================
# 1. SCARICAMENTO E INDICIZZAZIONE SORGENTE
# ==========================================
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
    
    # PULIZIA: Rimuoviamo eventuali UA dalla sorgente per indicizzare solo l'URL puro
    if "|" in url:
        url = url.split("|")[0]
        
    # Usa sia tvg-name che display name per creare chiavi di ricerca
    keys = set()
    if tvg_name: keys.add(clean_name(tvg_name))
    if disp: keys.add(clean_name(disp))
    
    for k in keys:
        if k: src_map[k] = url

print(f"Canali trovati nella sorgente: {len(src_map)}")

# ==========================================
# 2. LETTURA PLAYLIST LOCALE
# ==========================================
try:
    with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
        my_lines = f.readlines()
except FileNotFoundError:
    print(f"Errore: File {MY_PLAYLIST} non trovato.")
    sys.exit(1)

# ==========================================
# 3. REPORT PRELIMINARE (PRE-CHECK)
# ==========================================
print("\n=== REPORT STATO CANALI ===")
stats_total = 0
stats_excluded = 0
stats_found = 0
stats_missing = 0
missing_list = []

for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue
    
    stats_total += 1
    tvg_name, disp = parse_extinf(line)
    my_clean = clean_name(tvg_name or disp)

    # Check Esclusione
    is_excluded = False
    for ex in EXCLUDE_LIST:
        if ex in my_clean:
            is_excluded = True
            break
    
    if is_excluded:
        stats_excluded += 1
        continue

    # Check Presenza
    if find_match_in_map(my_clean, src_map):
        stats_found += 1
    else:
        stats_missing += 1
        missing_list.append(disp or tvg_name)

print(f"Canali totali nella tua playlist: {stats_total}")
print(f"Esclusi manualmente ({', '.join(EXCLUDE_LIST)}): {stats_excluded}")
print(f"Trovati nella sorgente: {stats_found}")
print(f"NON trovati nella sorgente: {stats_missing}")

if missing_list:
    print(" -> Canali senza match (non verranno aggiornati):")
    for m in missing_list:
        print(f"    - {m}")

# ==========================================
# 4. AGGIORNAMENTO LINK
# ==========================================
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
    # Separiamo l'URL base dall'UA per il confronto
    current_base_url = current_full_url.split("|")[0]
    
    my_clean = clean_name(tvg_name or disp)

    # -- CONTROLLO ESCLUSIONE --
    is_excluded = False
    for ex in EXCLUDE_LIST:
        if ex in my_clean:
            is_excluded = True
            print(f"⚠️  ESCLUSO: '{disp}' -> Link manuale mantenuto.")
            skipped_count += 1
            break
    
    if is_excluded:
        continue

    # Cerca nuovo URL (questo è l'URL puro dalla sorgente)
    new_base_url = find_match_in_map(my_clean, src_map)
    
    if new_base_url:
        # Confrontiamo solo gli URL base (senza UA)
        if new_base_url != current_base_url:
            print(f"[AGGIORNATO] {disp}")
            
            # Applichiamo la logica UA al nuovo link trovato
            final_new_url = apply_user_agent_logic(new_base_url)
            
            my_lines[url_idx] = final_new_url + "\n"
            updated_count += 1

# ==========================================
# 5. SALVATAGGIO
# ==========================================
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nOperazione completata.")
print(f"Link aggiornati effettivamente: {updated_count}")
