import requests
import re
import unicodedata

SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

attr_re = re.compile(r'(\w+?)="(.*?)"')
extinf_re = re.compile(r'#EXTINF[^,]*,(.*)$', re.IGNORECASE)

def normalize(s: str) -> str:
    if s is None:
        return ""
    # minuscole, rimuovi accenti, togli spazi/punteggiatura/comuni suffissi
    s = s.strip().lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    # rimuovi separatori
    s = re.sub(r'[\s\-\._]+', '', s)
    # sostituzioni comuni
    s = s.replace('raiuno', 'rai1').replace('raidue', 'rai2').replace('raitre', 'rai3')
    s = s.replace('retequattro', 'rete4').replace('canale5', 'canale5')
    s = s.replace('italiauno', 'italia1').replace('italia due', 'italia2').replace('italiadue', 'italia2')
    s = s.replace('la7hd', 'la7').replace('la7dhd', 'la7d').replace('wbn', 'warner')  # cautela
    s = s.replace('topcrime', 'topcrime').replace('realtime', 'realtime').replace('wbtv', 'warnertv')
    s = s.replace('rtl1025', 'rtl1025').replace('rtl102.5', 'rtl1025')
    s = s.replace('nove', 'nove').replace('boing', 'boing')
    s = s.replace('foodnetwork', 'foodnetwork').replace('focus', 'focus')
    s = s.replace('giallo', 'giallo').replace('cielo', 'cielo')
    s = s.replace('cartoonito', 'cartoonito').replace('k2', 'k2')
    s = s.replace('cine34', 'cine34').replace('la5', 'la5')
    s = s.replace('raiyoyo', 'raiyoyo').replace('raigulp', 'raigulp')
    s = s.replace('tv8', 'tv8').replace('twenty', '20').replace('20mediaset', '20')
    # rimuovi suffissi generici
    s = s.replace('hd', '').replace('sd', '').replace('tv', '')
    return s

def parse_extinf_line(line: str):
    # Estrai attributi e display name
    attrs = dict(attr_re.findall(line))
    m = extinf_re.search(line)
    display_name = m.group(1).strip() if m else ""
    tvg_id = attrs.get('tvg-id') or attrs.get('tvg_id')
    tvg_name = attrs.get('tvg-name') or attrs.get('tvg_name')
    return tvg_id, tvg_name, display_name

def next_url_index(lines, start_idx):
    # Trova il primo URL http(s) dopo start_idx
    for j in range(start_idx + 1, len(lines)):
        ln = lines[j].strip()
        if ln.startswith("#"):  # commento/opzione
            continue
        if ln.startswith("http"):
            return j
        if ln == "":
            continue
        # Se troviamo altro testo non http, continuiamo a cercare ma non saltiamo fuori
    return None

print("=== Scarico playlist sorgente da Free-TV ===")
src_text = requests.get(SOURCE_URL, timeout=30).text
src_lines = src_text.splitlines()

# Indici multipli per massimizzare il match
src_by_tvgid = {}
src_by_tvgn = {}
src_by_name = {}
src_by_norm = {}

for i, line in enumerate(src_lines):
    if not line.startswith("#EXTINF"):
        continue
    tvg_id, tvg_name, disp = parse_extinf_line(line)
    url_idx = i + 1 if i + 1 < len(src_lines) else None
    if url_idx is None or not src_lines[url_idx].startswith("http"):
        # fallback: cerca URL successivo (alcune playlist hanno righe intermedie)
        for j in range(i + 1, min(i + 6, len(src_lines))):
            if src_lines[j].startswith("http"):
                url_idx = j
                break
    if url_idx is None:
        continue
    url = src_lines[url_idx].strip()

    if tvg_id:
        src_by_tvgid[tvg_id.strip()] = url
    if tvg_name:
        src_by_tvgn[tvg_name.strip()] = url
    if disp:
        src_by_name[disp.strip()] = url

    # mappa normalizzata (priorità a display, poi tvg-name)
    key_norms = set()
    if disp: key_norms.add(normalize(disp))
    if tvg_name: key_norms.add(normalize(tvg_name))
    if tvg_id: key_norms.add(normalize(tvg_id))
    for k in key_norms:
        if k:
            src_by_norm[k] = url

print(f"Sorgente indicizzata: {len(src_by_tvgid)} by tvg-id, {len(src_by_tvgn)} by tvg-name, {len(src_by_name)} by name, {len(src_by_norm)} by norm.")

# Leggi la tua playlist e applica sostituzioni
with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
    my_lines = f.readlines()

updated = 0
unmatched = []

print("\n=== Inizio matching e aggiornamento ===")
for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue

    tvg_id, tvg_name, disp = parse_extinf_line(line)
    url_idx = next_url_index(my_lines, i)
    if url_idx is None:
        # Nessun URL dopo il blocco: salta ma segnala
        name_for_log = disp or tvg_name or tvg_id or "<sconosciuto>"
        print(f"[WARN] Nessun URL trovato dopo EXTINF per: {name_for_log}")
        continue

    current_url = my_lines[url_idx].strip()

    # Matching a priorità
    new_url = None
    # 1) tvg-id
    if not new_url and tvg_id and tvg_id in src_by_tvgid:
        new_url = src_by_tvgid[tvg_id]
    # 2) tvg-name
    if not new_url and tvg_name and tvg_name in src_by_tvgn:
        new_url = src_by_tvgn[tvg_name]
    # 3) display name
    if not new_url and disp and disp in src_by_name:
        new_url = src_by_name[disp]
    # 4) normalizzato
    if not new_url:
        candidates = [disp, tvg_name, tvg_id]
        for c in candidates:
            if not c:
                continue
            k = normalize(c)
            if k and k in src_by_norm:
                new_url = src_by_norm[k]
                break

    name_for_log = disp or tvg_name or tvg_id or "<sconosciuto>"

    if new_url:
        if new_url != current_url:
            print(f"[UPDATE] {name_for_log}\n  Vecchio: {current_url}\n  Nuovo : {new_url}")
            my_lines[url_idx] = new_url + "\n"
            updated += 1
    else:
        unmatched.append(name_for_log)

# Salva sempre (il workflow farà commit solo se cambia)
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nCompletato. Canali aggiornati: {updated}")
if unmatched:
    print("\nSenza match (controlla differenze di naming o assenza in Free-TV):")
    for ch in unmatched:
        print(" -", ch)
