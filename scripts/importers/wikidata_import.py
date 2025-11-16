def run_sparql_query(query_text):
    headers = {
        "Accept": "application/sparql+json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "WorldHistoryTimeline/1.0 (https://github.com/twbaty/world_history_timeline; mailto:twbaty@gmail.com)"
    }

    # Normalize to avoid XML fallback
    query_text = query_text.replace('\r\n', '\n').lstrip('\ufeff').lstrip()

    response = requests.post(
        SPARQL_URL,
        data={'query': query_text},
        headers=headers
    )

    print("\n--- WIKIDATA DEBUG ---")
    print("STATUS:", response.status_code)
    print("HEADERS:", dict(response.headers))
    print("BODY PREVIEW:", response.text[:500])
    print("--- END DEBUG ---\n")

    response.raise_for_status()
    return response.json()
