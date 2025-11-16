# World History Timeline Project

This project aims to build a unified, global, unbiased database of world events
—from the Big Bang to the present day—suitable for generating animated
timelines, Google Earth KMZ files, and interactive history tools.

The goals:
- Combine events from Wikidata, Wikipedia, academic datasets, and manual curation
- Normalize all sources into one canonical schema
- Allow filtering by region, culture, religion, event type, themes, and impact level
- Provide full attribution for every data source
- Support a pipeline from ingestion → classification → export

---

## Folder Overview

### `/schema/`
Contains all tag definitions and the canonical event schema (`event_schema.json`).
All events must conform to this schema after normalization.

### `/data/events/by_id/`
Each curated event is stored as its own JSON file.
This directory is the **single source of truth** for the dataset.

### `/data/pending/`
Events that require human review (uncategorized, incomplete, unverified).

### `/sources/`
Raw files pulled directly from APIs. These are not edited.
Used for ingestion and auditing.

### `/scripts/`
Python tools for:
- Importing data (`importers/`)
- Normalizing to schema (`processors/`)
- Validating events
- Finding uncategorized events
- Generating KML/KMZ and other exports

### `/exports/`
Output folder for KMZs, JSON exports, CSVs, and UI-friendly flattened data.

### `/logs/`
Processing logs, classification reports, and audit trails.

---

## How to Add New Events

1. Add raw data to `/sources/`.
2. Run importer script(s), which output normalized files into `/data/pending/`.
3. Run `find_uncategorized_events.py` to fill in missing metadata.
4. Save curated events into `/data/events/by_id/`.
5. Export to KMZ or other formats using tools in `/scripts/tools/`.

---

## Attribution

Every event includes a full attribution block:
- Source (Wikidata, Wikipedia, etc.)
- Source ID (e.g., Wikidata Q-number)
- Retrieval date
- License type
- Notes

---

## Future Work
- Automated tagging improvements using heuristics
- Region polygon support
- Web UI
- Full animated timeline integration
