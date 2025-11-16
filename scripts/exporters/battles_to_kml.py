from pathlib import Path
from database.db import engine, battles
from sqlalchemy import select

OUTPUT = Path(__file__).resolve().parents[2] / "exports" / "battles.kml"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def export_kml():
    with engine.begin() as conn:
        result = conn.execute(select(battles)).fetchall()

    placemarks = []
    for row in result:
        if row.latitude is None or row.longitude is None:
            continue

        name = row.label or row.id
        desc = row.description or ""

        placemark = f"""
        <Placemark>
            <name>{name}</name>
            <description>{desc}</description>
            <Point>
                <coordinates>{row.longitude},{row.latitude},0</coordinates>
            </Point>
        </Placemark>
        """
        placemarks.append(placemark)

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <name>Historical Battles</name>
        {''.join(placemarks)}
      </Document>
    </kml>
    """

    OUTPUT.write_text(kml, encoding="utf-8")
    print(f"KML written to {OUTPUT}")

if __name__ == "__main__":
    export_kml()
