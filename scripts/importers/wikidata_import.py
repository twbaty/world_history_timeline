import requests
import json
from pathlib import Path
import sys

# ------------------------------
# Project Root & Path Injection
# ------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ------------------------------
# Directories
# ------------------------------
QUERY_DIR = Path(__file__).resolve().parent / "queries"
CACHE_DIR = ROOT / "cache"
PENDING_DIR = ROOT / "data" / "pending"

CACHE_DIR.mkdir(exist_ok=True)
PENDING_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Wikidata Endpoints
# ------------------------------
SPARQL_URL = "https://query.wikidata.org/sparql"
ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

HEADERS = {
    "Accept": "application/sparql+json",
    "User-Agent": "WorldHistoryTimeline/1.0 (https://github.com/twbaty/world_history_timeline; mailto:twbaty@gmail.com)"
}

# ============================================================
# SPARQL
# ============================================================
def load_sparql(filename):
    return (QUERY_DIR / filename).read_text(encoding="utf-8")


def run_sparql(query_text):
    r = requests.post(
        SPARQL_URL,
        data={"query": query_text, "format": "json"},
        headers={
            "Accept": "application/sparql+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": HEADERS["User-Agent"]
        },
        timeout=60
    )
    r.raise_for_status()
    return r.json()

# ============================================================
# Entity Fetching + Caching
# ============================================================
def fetch_entity_cached(qid):
    """Load from cache if possible, otherwise fetch from Wikidata."""
    cache_file = CACHE_DIR / f"{qid}.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text())

    # Online fetch
    url = ENTITY_URL.format(qid)
    r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]})
    r.raise_for_status()

    data = r.json()
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data

# ============================================================
# Claim extractors
# ============================================================
def extract_time(claims, pid):
    """Extract ISO time string for P580/P582."""
    if pid not in claims:
        return None
    dv = claims[pid][0]["mainsnak"].get("datavalue", {})
    if dv.get("type") != "time":
        return None
    return dv["value"]["time"]


def extract_coord_pair(entity_json):
    """Return (lat, lon) if P625 exists."""
    claims = entity_json.get("claims", {})
    if "P625" not in claims:
        return None
    dv = claims["P625"][0]["mainsnak"].get("datavalue", {})
    if dv.get("type") != "globecoordinate":
        return None
    return (dv["value"]["latitude"], dv["value"]["longitude"])

# ============================================================
# Coordinate Fallback Resolver
# ============================================================
def resolve_coordinates(e):
    """
    Order:
      1. Direct battle coords (P625)
      2. Location (P276)
      3. Admin Div (P131)
      4. Country (P17) → capital (P36)
    """

    claims = e.get("claims", {})

    # --- 1) Direct coordinates ---
    direct = extract_coord_pair(e)
    if direct:
        return direct[0], direct[1], "P625"

    # --- 2) P276 (location) ---
    if "P276" in claims:
        loc_qid = claims["P276"][0]["mainsnak"]["datavalue"]["value"]["id"]
        loc_json = fetch_entity_cached(loc_qid)
        loc_e = loc_json["entities"][loc_qid]
        coords = extract_coord_pair(loc_e)
        if coords:
            return coords[0], coords[1], "P276"

    # --- 3) P131 (administrative entity) ---
    if "P131" in claims:
        adm_qid = claims["P131"][0]["mainsnak"]["datavalue"]["value"]["id"]
        adm_json = fetch_entity_cached(adm_qid)
        adm_e = adm_json["entities"][adm_qid]
        coords = extract_coord_pair(adm_e)
        if coords:
            return coords[0], coords[1], "P131"

    # --- 4) P17 (country) → capital P36 ---
    if "P17" in claims:
        country_qid = claims["P17"][0]["mainsnak"]["datavalue"]["value"]["id"]
        country_json = fetch_entity_cached(country_qid)
        country_e = country_json["entities"][country_qid]

        # Get capital Q-ID
        if "P36" in country_e.get("claims", {}):
            cap_qid = country_e["claims"]["P36"][0]["mainsnak"]["datavalue"]["value"]["id"]
            cap_json = fetch_entity_cached(cap_qid)
            cap_e = cap_json["entities"][cap_qid]

            coords = extract_coord_pair(cap_e)
            if coords:
                return coords[0], coords[1], "capital_fallback"

    # No coords found
    return None, None, "none"

# ============================================================
# Import Battles
# ============================================================
def import_battles():
    print("=== Import Battles ===")

    # 1. Retrieve battle list
    q = load_sparql("battles_ids.sparql")
    data = run_sparql(q)
    qids = [b["battle"]["value"].split("/")[-1] for b in data["results"]["bindings"]]

    print(f"Retrieved {len(qids)} battles")

    # DB function
    from database.db import upsert_battle

    for qid in qids:
        # 2. Fetch with caching
        e_json = fetch_entity_cached(qid)
        e = e_json["entities"][qid]
        claims = e.get("claims", {})

        # 3. Coordinate resolution
        lat, lon, src = resolve_coordinates(e)

        # 4. Build DB record
        record = {
            "id": qid,
            "label": e.get("labels", {}).get("en", {}).get("value"),
            "description": e.get("descriptions", {}).get("en", {}).get("value"),
            "start": extract_time(claims, "P580"),
            "end": extract_time(claims, "P582"),
            "latitude": lat,
            "longitude": lon,
            "coord_source": src,
            "raw_entity": e,     # full entity JSON
        }

        action = upsert_battle(record)
        print(f"{action.upper()} {qid} ({src})")

        # 5. Save record copy to /data/pending/
        (PENDING_DIR / f"{qid}.json").write_text(
            json.dumps(record, indent=2),
            encoding="utf-8"
        )

    print("=== Battles Import Complete ===")


if __name__ == "__main__":
    import_battles()
