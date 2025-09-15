import requests
import re
import unicodedata

# === CONFIG ===
SOURCE_URL = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
MY_PLAYLIST = "ita.m3u"

# === FUNZIONI ===
def normalize(s: str) -> str:
    """Normalizza il nome canale per confronti robusti."""
    if not s:
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    # Rimuovi simboli speciali
    s = s.replace('ⓖ', '')  # G cerchiata
    s = re.sub(r'[^\w]+', '', s)  # rimuove spazi, punteggiatura, simboli
    # Sostituzioni comuni
    s = s.replace('raiuno', 'rai1').replace('raidue', 'rai2').replace('raitre', 'rai3')
    s = s.replace('retequattro', 'rete4').replace('italiauno', 'italia1')
    s = s.replace('italiadue', 'italia2').replace('venti', '20')
    return s

def parse_extinf(line: str):
    """Estrae tvg-id, tvg-name e nome visualizzato da una riga EXTINF."""
    attrs = dict(re.findall(r'(\w+?)="(.*?)"', line))
    display_name = re.search(r',(.+)$', line)
    return (
        attrs.get('tvg-id') or attrs.get('tvg_id'),
        attrs.get('tvg-name') or attrs.get('tvg_name'),
        display_name.group(1).strip() if display_name else ""
    )

def find_next_url(lines, start_idx):
    """Trova il primo URL http(s) dopo start_idx."""
    for j in range(start_idx + 1, len(lines)):
        if lines[j].startswith("http"):
            return j
    return None

# === SCARICA PLAYLIST SORGENTE ===
print("Scarico playlist sorgente...")
src_text = requests.get(SOURCE_URL, timeout=30).text.splitlines()

# Indicizza canali sorgente
src_by_tvgid, src_by_tvgn, src_by_name, src_by_norm = {}, {}, {}, {}
for i, line in enumerate(src_text):
    if not line.startswith("#EXTINF"):
        continue
    tvg_id, tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(src_text, i)
    if url_idx is None:
        continue
    url = src_text[url_idx].strip()
    if tvg_id: src_by_tvgid[tvg_id] = url
    if tvg_name: src_by_tvgn[tvg_name] = url
    if disp: src_by_name[disp] = url
    for key in {normalize(tvg_id), normalize(tvg_name), normalize(disp)}:
        if key: src_by_norm[key] = url

print(f"Sorgente indicizzata: {len(src_by_tvgid)} tvg-id, {len(src_by_tvgn)} tvg-name, {len(src_by_name)} nomi, {len(src_by_norm)} normalizzati.")

# === LEGGI E AGGIORNA LA TUA PLAYLIST ===
with open(MY_PLAYLIST, "r", encoding="utf-8") as f:
    my_lines = f.readlines()

updated, unmatched = 0, []

for i, line in enumerate(my_lines):
    if not line.startswith("#EXTINF"):
        continue
    tvg_id, tvg_name, disp = parse_extinf(line)
    url_idx = find_next_url(my_lines, i)
    if url_idx is None:
        continue
    current_url = my_lines[url_idx].strip()

    # Matching a priorità
    new_url = (
        src_by_tvgid.get(tvg_id)
        or src_by_tvgn.get(tvg_name)
        or src_by_name.get(disp)
        or src_by_norm.get(normalize(disp))
        or src_by_norm.get(normalize(tvg_name))
        or src_by_norm.get(normalize(tvg_id))
    )

    if new_url:
        if new_url != current_url:
            print(f"[UPDATE] {disp or tvg_name or tvg_id}")
            print(f"  Vecchio: {current_url}")
            print(f"  Nuovo : {new_url}")
            my_lines[url_idx] = new_url + "\n"
            updated += 1
    else:
        unmatched.append(disp or tvg_name or tvg_id)

# === SALVA ===
with open(MY_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(my_lines)

print(f"\nAggiornamento completato. Canali aggiornati: {updated}")
if unmatched:
    print("\nSenza match:")
    for ch in unmatched:
        print(" -", ch)
