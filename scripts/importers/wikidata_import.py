import requests
import json
from pathlib import Path

SPARQL_URL = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
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
    r = requests.get(
        SPARQL_URL,
        params={"query": query_text},
        headers=headers,
        timeout=30,
    )
    print("DEBUG STATUS:", r.status_code)
    return r.json()


def fetch_entity(qid):
    url = ENTITY_URL.format(qid)
    r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]})
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

        record = {
            "id": qid,
            "label": e["labels"].get("en", {}).get("value"),
            "description": e["descriptions"].get("en", {}).get("value"),
            "start": extract_claim(claims, "P580"),
            "end": extract_claim(claims, "P582"),
            "coordinates": extract_claim(claims, "P625")
        }

        out_path = PENDING_DIR / f"{qid}.json"
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        print(f"Saved {qid}")

    print("=== Battles Import Complete ===")

if __name__ == "__main__":
    import_battles()
