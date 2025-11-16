import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
QUERY_DIR = BASE_DIR / "scripts" / "importers" / "queries"
RAW_DIR = BASE_DIR / "sources" / "wikidata"
PENDING_DIR = BASE_DIR / "data" / "pending"
LOG_FILE = BASE_DIR / "logs" / "import_log.txt"

SPARQL_URL = "https://query.wikidata.org/sparql"

def load_sparql_query(filename):
    with open(QUERY_DIR / filename, "r", encoding="utf-8") as f:
        return f.read()

def save_raw_response(data, category):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    filename = RAW_DIR / f"raw_{category}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return filename

def log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as logf:
        logf.write(f"{datetime.utcnow().isoformat()} - {message}\n")

def run_sparql_query(query_text):
    headers = {
        "Accept": "application/sparql+json",
        "User-Agent": "WorldHistoryProject/1.0"
    }
    response = requests.get(SPARQL_URL, params={'query': query_text}, headers=headers)
    response.raise_for_status()
    return response.json()

def import_battles():
    log("Starting Wikidata battles import...")
    query = load_sparql_query("battles.sparql")

    data = run_sparql_query(query)
    raw_file = save_raw_response(data, "battles")
    log(f"Raw battles data saved to: {raw_file}")

    # Send raw data to the normalizer
    from scripts.processors.normalize_events import normalize_battle_data
    normalize_battle_data(raw_file)
    log("Normalization complete for battle data.")

    print("Battle import complete.")

if __name__ == "__main__":
    import_battles()
