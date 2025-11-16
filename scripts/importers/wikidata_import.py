import json
import requests
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------
# CONSTANTS & DIRECTORY SETUP
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
QUERY_DIR = BASE_DIR / "scripts" / "importers" / "queries"

RAW_DIR = BASE_DIR / "data" / "raw" / "battles"
NORMALIZED_DIR = BASE_DIR / "data" / "pending"

SPARQL_URL = "https://query.wikidata.org/sparql"


# ---------------------------------------------------------
# LOAD SPARQL QUERY FILE
# ---------------------------------------------------------

def load_sparql_query(filename):
    path = QUERY_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SPARQL query not found: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------
# RUN SPARQL QUERY (POST + JSON)
# ---------------------------------------------------------

def run_sparql_query(query_text):
    headers = {
    "Accept": "application/sparql+json",
    "User-Agent": "WorldHistoryTimeline/1.0 (User:Mapwright; https://github.com/twbaty/world_history_timeline)"
    }

    # Normalize for Wikidata quirks
    query_text = query_text.replace("\r\n", "\n").lstrip("\ufeff").lstrip()

    response = requests.post(
        SPARQL_URL,
        data={'query': query_text},
        headers=headers
    )

    print("\n--- WIKIDATA DEBUG ---")
    print("STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("content-type"))
    print("BODY PREVIEW:", response.text[:300])
    print("--- END DEBUG ---\n")

    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------
# NORMALIZER — Convert Wikidata binding → Event Dict
# ---------------------------------------------------------

def normalize_battle(binding):
    """Convert SPARQL result binding to our event schema."""
    try:
        battle_id = binding["battle"]["value"].split("/")[-1]
        label = binding.get("battleLabel", {}).get("value")
        description = binding.get("battleDescription", {}).get("value")

        start = binding.get("start", {}).get("value")
        end = binding.get("end", {}).get("value")

        coord_raw = binding.get("coord", {}).get("value")

        # Parse coordinates if available
        lat = None
        lon = None
        if coord_raw and coord_raw.startswith("Point("):
            parts = coord_raw.replace("Point(", "").replace(")", "").split(" ")
            lon = float(parts[0])
            lat = float(parts[1])

        return {
            "id": battle_id,
            "type": "battle",
            "label": label,
            "description": description,
            "start": start,
            "end": end,
            "latitude": lat,
            "longitude": lon,
            "source": "wikidata"
        }
    except Exception:
        return None


# ---------------------------------------------------------
# IMPORTER — TALKATIVE VERSION
# ---------------------------------------------------------

def import_battles():
    print("=== World History Timeline Importer ===")
    print("Importing battles from Wikidata...")
    print("----------------------------------------")

    query = load_sparql_query("battles.sparql")
    print("Loaded SPARQL query.")

    print("Sending query to Wikidata...")
    data = run_sparql_query(query)

    bindings = data.get("results", {}).get("bindings", [])
    count = len(bindings)
    print(f"Wikidata returned {count} results.")

    if count == 0:
        print("⚠ No results found. Likely the SPARQL query is too strict.")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat().replace(":", "-")

    # Save raw dump
    raw_path = RAW_DIR / f"raw_battles_{timestamp}.json"
    raw_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Raw data saved → {raw_path}")

    # Normalize
    normalized = [normalize_battle(b) for b in bindings]
    normalized = [n for n in normalized if n]

    if not normalized:
        print("⚠ No normalized results — possibly missing coordinates or labels.")
        return

    norm_path = NORMALIZED_DIR / f"normalized_battles_{timestamp}.json"
    norm_path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False))
    print(f"Normalized events saved → {norm_path}")

    print("=== Import Complete ===")


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    import_battles()
