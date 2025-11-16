import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from database.db import engine, battles
from sqlalchemy import select

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "exports"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTFILE = OUTPUT_DIR / "battles.kml"

ICON_URL = "https://raw.githubusercontent.com/twbaty/world_history_timeline/main/icons/battle.png"


def export_battles_to_kml():
    # Query DB
    with engine.begin() as conn:
        rows = conn.execute(select(battles)).fetchall()

    # Build KML header + style
    kml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        '  <name>Battles</name>',
        '  <Style id="battle_icon_style">',
        '    <IconStyle>',
        '      <scale>1.2</scale>',
        f'      <Icon><href>{ICON_URL}</href></Icon>',
        '    </IconStyle>',
        '  </Style>',
    ]

    # Add battles
    for row in rows:
        if not row.latitude or not row.longitude:
            continue

        qid = row.id
        name = row.label or qid
        desc = row.description or ""
        lat = row.latitude
        lon = row.longitude

        placemark = f"""
    <Placemark>
      <name>{name}</name>
      <description>{desc}</description>
      <styleUrl>#battle_icon_style</styleUrl>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>
"""
        kml_parts.append(placemark)

    # Close document
    kml_parts.append("</Document>")
    kml_parts.append("</kml>")

    OUTFILE.write_text("\n".join(kml_parts), encoding="utf-8")

    print(f"KML written to {OUTFILE}")


if __name__ == "__main__":
    export_battles_to_kml()
