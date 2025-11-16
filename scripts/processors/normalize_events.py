import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[2]
PENDING_DIR = BASE_DIR / "data" / "pending"

def parse_wikidata_coords(coord_str):
    """
    Wikidata format: "Point(longitude latitude)"
    Example: "Point(4.4144 50.6794)"
    """
    try:
        coord_str = coord_str.replace("Point(", "").replace(")", "")
        lon, lat = coord_str.split(" ")
        return [float(lon), float(lat)]
    except:
        return None

def build_event_id(label, start):
    clean = label.lower().replace(" ", "_").replace("‘", "").replace("’", "")
    clean = clean.replace("(", "").replace(")", "").replace(",", "")
    return f"{clean}_{start}"

def normalize_battle_data(raw_file):
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = []
    for row in data["results"]["bindings"]:
        battle_qid = row["battle"]["value"].split("/")[-1]
        label = row.get("battleLabel", {}).get("value", "Unknown Battle")
        desc = row.get("battleDescription", {}).get("value", "")
        start = row.get("start", {}).get("value", None)
        end = row.get("end", {}).get("value", start)
        coord = row.get("coord", {}).get("value", None)

        # Process coordinates
        coordinates = parse_wikidata_coords(coord) if coord else None

        # Convert start/end to year (drop month/day if present)
        def clean_year(val):
            if not val:
                return None
            return int(val.split("-")[0])  # year only

        start_year = clean_year(start)
        end_year = clean_year(end) if end else start_year

        # Build canonical ID
        eid = build_event_id(label, start_year if start_year else "unknown")

        event = {
            "id": eid,
            "name": label,
            "description": desc,
            "start": start_year,
            "end": end_year,
            "coordinates": coordinates,

            # These require manual curation
            "region": [],
            "culture": [],
            "religion": [],
            "event_type": ["Battle"],
            "impact_level": [],
            "timespan_category": "Instant" if start_year == end_year else "Multi-year",
            "themes": [],

            "attribution": {
                "source": "Wikidata",
                "source_id": battle_qid,
                "retrieved": datetime.utcnow().isoformat(),
                "license": "CC-BY-SA",
                "notes": ""
            }
        }

        events.append(event)

    # Write output file
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    out_file = PENDING_DIR / f"normalized_battles_{timestamp}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)

    print(f"Normalized events written to {out_file}")

