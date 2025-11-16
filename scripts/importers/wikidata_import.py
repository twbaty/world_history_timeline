import requests
import json
from pathlib import Path
import sys

# Resolve the project root (world_history_timeline/)
ROOT = Path(__file__).resolve().parents[2]

# Add project root to Python path so `import database` works everywhere
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
SPARQL_URL = "https://query.wikidata.org/sparql"
ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = Path(__file__).resolve().parent / "queries"
PENDING_DIR = ROOT / "data" / "pending"
PENDING_DIR.mkdir(parents=True, exist_ok=True)

headers = {
    "Accept": "application/sparql+json",
    "User-Agent": "WorldHistoryTimeline/1.0 (https://github.com/twbaty/world_history_timeline; mailto:twbaty@gmail.com)"
}

def load_sparql(filename):
    return (QUERY_DIR / filename).read_text(encoding="utf-8")

def run_sparql(query_text):
    headers = {
        "Accept": "application/sparql+json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "WorldHistoryTimeline/1.0 (https://github.com/twbaty/world_history_timeline; mailto:twbaty@gmail.com)"
    }

    print("REQUEST URL:", SPARQL_URL)
    print("PARAMS:", {"query": query_text[:200]})
    print("HEADERS:", headers)

    r = requests.post(
    SPARQL_URL,
    data={"query": query_text, "format": "json"},
    headers=headers,
    timeout=60
    )

    print("DEBUG STATUS:", r.status_code)
    print("DEBUG CONTENT-TYPE:", r.headers.get("Content-Type"))
    print("BODY PREVIEW:", r.text[:300])

    r.raise_for_status()
    return r.json()

def fetch_entity(qid):
    url = ENTITY_URL.format(qid)
    r = requests.get(url, headers={"User-Agent": headers["User-Agent"]})
    r.raise_for_status()
    return r.json()

def extract_claim(claims, pid):
    if pid not in claims:
        return None
    mainsnak = claims[pid][0].get("mainsnak", {})
    datavalue = mainsnak.get("datavalue", {})
    return datavalue.get("value")

def import_battles():

    print("=== Import Battles (REST API Mode) ===")

    query = load_sparql("battles_ids.sparql")
    print("Fetching Q-IDs from Wikidata...")
    data = run_sparql(query)

    bindings = data["results"]["bindings"]
    qids = [b["battle"]["value"].split("/")[-1] for b in bindings]

    print(f"Retrieved {len(qids)} battles.")
    print("Fetching details...")

    for qid in qids:
        entity = fetch_entity(qid)
        e = entity["entities"][qid]

        claims = e.get("claims", {})

        coord = extract_claim(claims, "P625")

        lat = None
        lon = None
        raw = None

        if isinstance(coord, dict):
            lat = coord.get("latitude")
            lon = coord.get("longitude")
            raw = coord
        else:
            raw = coord

        record = {
            "id": qid,
            "label": e["labels"].get("en", {}).get("value"),
            "description": e["descriptions"].get("en", {}).get("value"),

            "start": extract_claim(claims, "P580"),
            "end": extract_claim(claims, "P582"),

            "latitude": extract_lat(claims),
            "longitude": extract_lon(claims),

            "raw_entity": e,   # FULL Wikidata entity object
        }


        from database.db import upsert_battle

        action = upsert_battle(record)

        out_path = PENDING_DIR / f"{qid}.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        print(f"{action.upper()} {qid}")


    print("=== Battles Import Complete ===")

if __name__ == "__main__":
    import_battles()
