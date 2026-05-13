import requests
import re
import unicodedata
import sys
import difflib

# --- CONFIGURAZIONE ---
SOURCE_PRIMARY = "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_italy.m3u8"
SOURCE_SECONDARY = "https://raw.githubusercontent.com/SuperFranky84/IPTV-Italia/refs/heads/main/TV"
OUTPUT_PLAYLIST = "ita.m3u"

EXCLUDE_LIST = ["Nove","Giallo","Real Time","DMAX","Discovery Channel","Food Network","Motor Trend"] 
CUSTOM_UA_SUFFIX = "|User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# IL TUO TEMPLATE MASTER: 40 Canali esatti (i metadati EXTINF restano intoccati)
BASE_PLAYLIST = """#EXTM3U x-tvg-url="https://raw.githubusercontent.com/pangio13/epg/refs/heads/main/epg.xml"

#EXTINF:-1 tvg-name="Rai 1" tvg-logo="https://i.imgur.com/CAx7yRm.png" tvg-id="Rai1.it",Rai 1
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=2606803&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Rai 2" tvg-logo="https://i.imgur.com/zA0PTcs.png" tvg-id="Rai2.it",Rai 2
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=308718&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Rai 3" tvg-logo="https://i.imgur.com/9kuQCIi.png" tvg-id="Rai3.it",Rai 3
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=308709&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Rete 4" tvg-logo="https://i.imgur.com/GWx2Fkl.png" tvg-id="Rete4.it",Rete 4
https://live02-seg.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Canale 5" tvg-logo="https://i.imgur.com/p6YdiR1.png" tvg-id="Canale5.it",Canale 5
https://live02-seg.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Italia 1" tvg-logo="https://i.imgur.com/oCiOxBG.png" tvg-id="Italia1.it",Italia 1
https://live02-seg.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="La7" tvg-logo="https://i.imgur.com/F90mpSa.png" tvg-id="La7.it",La7
https://d1chghleocc9sm.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-evfku205gqrtf/Live.m3u8
#EXTINF:-1 tvg-name="TV8" tvg-logo="https://i.imgur.com/xvoHVOU.png" tvg-id="Tv8.it",TV8
https://hlslive-web-gcdn-skycdn-it.akamaized.net/TACT/11223/tv8web/master.m3u8
#EXTINF:-1 tvg-name="Nove" tvg-logo="https://i.imgur.com/Hp723RU.png" tvg-id="Nove.it",Nove
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://d31mw7o1gs0dap.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-y5pbi2sq9r609/NOVE_IT.m3u8
#EXTINF:-1 tvg-name="20 Mediaset" tvg-logo="https://i.imgur.com/It13jwX.png" tvg-id="20Mediaset.it",20 Mediaset
https://live02-seg.msf.cdn.mediaset.net/live/ch-lb/lb-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Rai 4" tvg-logo="https://i.imgur.com/XFkZRfv.png" tvg-id="Rai4.it",Rai 4
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=746966&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Iris" tvg-logo="https://i.imgur.com/Ixz1BY3.png" tvg-id="Iris.it",Iris
https://live02-seg.msf.cdn.mediaset.net/live/ch-ki/ki-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Cielo" tvg-logo="https://i.imgur.com/cPluF03.png" tvg-id="Cielo.it",Cielo
https://hlslive-web-gcdn-skycdn-it.akamaized.net/TACT/11219/cieloweb/master.m3u8
#EXTINF:-1 tvg-name="La 5" tvg-logo="https://i.imgur.com/UNyJaho.png" tvg-id="LA5.it",La 5
https://live02-seg.msf.cdn.mediaset.net/live/ch-ka/ka-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Real Time" tvg-logo="https://i.imgur.com/9dcTYg1.png" tvg-id="RealTime.it",Real Time
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://d3562mgijzx0zq.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-kizqtzpvvl3i8/Realtime_IT.m3u8
#EXTINF:-1 tvg-name="Food Network" tvg-logo="https://i.imgur.com/i60OYr9.png" tvg-id="FoodNetwork.it",Food Network
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://dk3okdd5036kz.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-o4pw0nc02sthz/Foodnetwork_IT.m3u8
#EXTINF:-1 tvg-name="Focus" tvg-logo="https://i.imgur.com/M4smqpF.png" tvg-id="Focus.it",Focus
https://live02-seg.msf.cdn.mediaset.net/live/ch-fu/fu-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="BOING" tvg-logo="https://i.imgur.com/niSlrqT.png" tvg-id="Boing.it",BOING
https://live02-seg.msf.cdn.mediaset.net/live/ch-kb/kb-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="K2" tvg-logo="https://i.imgur.com/wlLgSiA.png" tvg-id="K2.it",K2
https://d1pmpe0hs35ka5.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-39hsskpppgf72/K2_IT.m3u8
#EXTINF:-1 tvg-name="Cartoonito" tvg-logo="https://i.imgur.com/oK2DcDJ.png" tvg-id="Cartoonito.it",Cartoonito
https://live02-seg.msf.cdn.mediaset.net/live/ch-la/la-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Super!" tvg-logo="https://i.imgur.com/1124YEp.png" tvg-id="Super.it",Super!
https://495c5a85d9074f29acffeaea9e0215eb.msvdn.net/super/super_main/super_main_hbbtv/playlist.m3u8
#EXTINF:-1 tvg-name="Italia 2" tvg-logo="https://i.imgur.com/nq48sjO.png" tvg-id="Italia2.it",Italia 2
https://live02-seg.msf.cdn.mediaset.net/live/ch-i2/i2-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="DMAX" tvg-logo="https://i.imgur.com/dmEmRX7.png" tvg-id="DMAX.it",DMAX
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://d2j2nqgg7bzth.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-02k1gv1j0ufwn/DMAX_IT.m3u8
#EXTINF:-1 tvg-name="Mediaset Extra" tvg-logo="https://i.imgur.com/mM8lopo.png" tvg-id="MediasetExtra.it",Mediaset Extra
https://live02-seg.msf.cdn.mediaset.net/live/ch-kq/kq-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="27 Twentyseven" tvg-logo="https://i.imgur.com/y2PdPCK.png" tvg-id="TwentySeven.it",27 Twentyseven
https://live02-seg.msf.cdn.mediaset.net/live/ch-ts/ts-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="La7 Cinema" tvg-logo="https://i.imgur.com/khPweok.png" tvg-id="La7Cinema.it",La7 Cinema
https://viamotionhsi.netplus.ch/live/eds/la7d/browser-HLS8/la7d.m3u8
#EXTINF:-1 tvg-name="Rai Movie" tvg-logo="https://i.imgur.com/RKpO8CE.png" tvg-id="RaiMovie.it",Rai Movie
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=747002&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Cine34" tvg-logo="https://i.imgur.com/YyldwhI.png" tvg-id="Cine34.it",Cine34
https://live02-seg.msf.cdn.mediaset.net/live/ch-b6/b6-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Discovery Channel" tvg-logo="https://i.imgur.com/5IxIFJ0.png" tvg-id="Discovery.it",Discovery Channel
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://d24aqelmrau4kx.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-l1oas691aj7p2/WBTV_IT.m3u8
#EXTINF:-1 tvg-name="Giallo" tvg-logo="https://i.imgur.com/0PIRwZS.png" tvg-id="Giallo.it",Giallo
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://d9fqo6nfqlv2h.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-ulukbrgm1n3yb/Giallo_IT.m3u8
#EXTINF:-1 tvg-name="Top Crime" tvg-logo="https://i.imgur.com/RFIwv9O.png" tvg-id="TopCrime.it",Top Crime
https://live02-seg.msf.cdn.mediaset.net/live/ch-lt/lt-clr.isml/index.m3u8
#EXTINF:-1 tvg-name="Rai Gulp" tvg-logo="https://i.imgur.com/lu1DPVb.png" tvg-id="RaiGulp.it",Rai Gulp
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=746953&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Frisbee" tvg-logo="https://i.imgur.com/9y1zIAe.png" tvg-id="Frisbee.it",Frisbee
https://d6m7lubks416z.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-zmbstsedxme9s/Frisbee_IT.m3u8
#EXTINF:-1 tvg-name="Rai 5" tvg-logo="https://i.imgur.com/Leu2zTO.png" tvg-id="Rai5.it",Rai 5
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=395276&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Rai Premium" tvg-logo="https://i.imgur.com/RKI4nFy.png" tvg-id="RaiPremium.it",Rai Premium
https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=746992&output=7&forceUserAgent=rainet/4.0.5
#EXTINF:-1 tvg-name="Motor Trend" tvg-logo="https://i.imgur.com/ipj2H0n.png" tvg-id="DiscoveryTurbo.it",Motor Trend
#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha
#KODIPROP:inputstream.adaptive.license_key=https://d54or4x1qhv8g.cloudfront.net/drm/v2/license?drm-type=widevine
https://d205m6k582pec4.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-asg5puyzdtnqu/Motortrend_IT.m3u8
#EXTINF:-1 tvg-name="RTL 102.5" tvg-logo="https://i.imgur.com/KdissvS.png" tvg-id="RTL102.5TV.it",RTL 102.5
https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S97044836/tbbP8T1ZRPBL/playlist.m3u8
#EXTINF:-1 tvg-name="Radiofreccia" tvg-logo="https://i.imgur.com/J5N9F7Z.png" tvg-id="RADIOFRECCIA.HD.it",Radiofreccia
https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S3160845/0tuSetc8UFkF/playlist.m3u8
#EXTINF:-1 tvg-name="RadioItaliaTV" tvg-logo="https://i.imgur.com/4VCEJuJ.png" tvg-id="RadioItaliaTV.HD.it",RadioItaliaTV
https://radioitaliatv.akamaized.net/hls/live/2093117/RadioitaliaTV/master.m3u8
#EXTINF:-1 tvg-name="Deejay TV" tvg-logo="https://i.imgur.com/rlaKH6k.png" tvg-id="DeejayTV.it",Deejay TV
https://4c4b867c89244861ac216426883d1ad0.msvdn.net/live/S85984808/sMO0tz9Sr2Rk/playlist.m3u8
"""

def clean_name(s: str) -> str:
    if not s: return ""
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r'\[.*?\]', '', s)
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    for noise in [' hd', ' fhd', ' ita', ' it', ' 1080p']:
        if s.endswith(noise): s = s[:-len(noise)].strip()
    return ' '.join(s.split())

def parse_extinf_name(line: str):
    match = re.search(r',([^,]+)$', line)
    return match.group(1).strip() if match else ""

def get_source_data(url):
    """
    Estrae non solo l'URL ma l'intero blocco di metadati DRM per ogni canale.
    Restituisce un dict: { 'nome_pulito': {'url': '...', 'props': ['#KODIPROP...', ...]} }
    """
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        
        s_map = {}
        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF"):
                disp = parse_extinf_name(lines[i])
                props = []
                raw_url = ""
                # Scansiona le righe successive per intercettare proprietà DRM o link
                for j in range(i+1, min(i+10, len(lines))):
                    line_j = lines[j].strip()
                    if line_j.startswith("#KODIPROP") or line_j.startswith("#EXTVLCOPT"):
                        props.append(line_j)
                    elif line_j.startswith("http"):
                        raw_url = line_j.split("|")[0]
                        s_map[clean_name(disp)] = {"url": raw_url, "props": props}
                        break
        return s_map
    except Exception as e:
        print(f"Errore download {url}: {e}")
        return {}

def find_best_match(target, source_map):
    """ Restituisce il dict {'url':..., 'props':...} o None """
    if not target: return None
    if target in source_map: return source_map[target]
    
    source_keys = list(source_map.keys())
    close_matches = difflib.get_close_matches(target, source_keys, n=1, cutoff=0.85)
    if close_matches: return source_map[close_matches[0]]
    
    for src_key, src_data in source_map.items():
        if target in src_key or src_key in target:
            return src_data
    return None

def apply_ua(url):
    if ".php" in url or "mediapolis.rai.it" in url or "|User-Agent=" in url: return url
    if any(d in url for d in ["mediaset.net", "cloudfront.net", "akamaized.net", "land3.se"]):
        return url + CUSTOM_UA_SUFFIX
    return url

# ==========================================
# ESECUZIONE
# ==========================================
map_primary = get_source_data(SOURCE_PRIMARY)
map_secondary = get_source_data(SOURCE_SECONDARY)

template_lines = BASE_PLAYLIST.strip().splitlines()
header = template_lines[0]
blocks = []
current_block = []

for line in template_lines[1:]:
    line = line.strip()
    if not line: continue
    if line.startswith("#EXTINF"):
        if current_block: blocks.append(current_block)
        current_block = [line]
    else:
        if current_block: current_block.append(line)
if current_block: blocks.append(current_block)

final_m3u_lines = [header + "\n\n"]
stats = {"PRI": 0, "SEC": 0, "FAIL": 0}

for block in blocks:
    extinf_line = block[0]
    original_url = block[-1].split("|")[0]
    properties = block[1:-1] # Proprietà originali del template
    
    disp_name = parse_extinf_name(extinf_line)
    clean = clean_name(disp_name)
    
    is_excluded = any(clean_name(ex) in clean for ex in EXCLUDE_LIST)
    target_map = map_secondary if is_excluded else map_primary
    label = "SEC" if is_excluded else "PRI"
    
    new_data = find_best_match(clean, target_map)
    
    if new_data:
        final_url = apply_ua(new_data["url"])
        properties = new_data["props"] # SOVRASCRITTURA CON I DATI DELLA SORGENTE
        stats[label] += 1
        print(f"[{label}] Aggiornato: {disp_name} (Licenze estratte: {len(properties)})")
    else:
        final_url = apply_ua(original_url)
        # Se fallisce, properties rimane quello del template per evitare rotture totali
        stats["FAIL"] += 1
        print(f"[FAIL] Mantenuto originale: {disp_name}")
    
    final_m3u_lines.append(extinf_line + "\n")
    for prop in properties:
        final_m3u_lines.append(prop + "\n")
    final_m3u_lines.append(final_url + "\n\n")

with open(OUTPUT_PLAYLIST, "w", encoding="utf-8") as f:
    f.writelines(final_m3u_lines)

print("\n--- REPORT ---")
print(f"Aggiornati da Primaria: {stats['PRI']}")
print(f"Aggiornati da Secondaria (Dati + DRM): {stats['SEC']}")
print(f"Fallimenti (mantenuti vecchi URL): {stats['FAIL']}")
print(f"File generato: {OUTPUT_PLAYLIST}")
