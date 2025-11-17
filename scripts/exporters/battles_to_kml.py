import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from sqlalchemy import select
from database.db import engine, battles


def export_battles_to_kml():
    # Export folder
    EXPORTS_DIR = Path(__file__).resolve().parents[1] / "exports"
    EXPORTS_DIR.mkdir(exist_ok=True)
    OUTFILE = EXPORTS_DIR / "battles.kml"

    # Icon path
    ICON_PATH = Path(__file__).resolve().parents[2] / "icons" / "battle.png"
    icon_href = ICON_PATH.resolve().as_uri()

    # Pull rows with coordinates
    with engine.begin() as conn:
        rows = conn.execute(
            select(battles)
            .where(
                battles.c.latitude.is_not(None),
                battles.c.longitude.is_not(None)
            )
        ).fetchall()

    # Build KML manually
    kml_parts = []

    kml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    kml_parts.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    kml_parts.append('<Document>')
    kml_parts.append('  <name>Battles</name>')
    kml_parts.append('  <description>Battle locations from Wikidata</description>')

    # ---- Style for battles ----
    kml_parts.append(f"""
    <Style id="battleStyle">
      <IconStyle>
        <scale>1.2</scale>
        <Icon>
          <href>{icon_href}</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.1</scale>
      </LabelStyle>
    </Style>
    """)

    # ---- Placemarks ----
    for row in rows:
        name = row.label or row.id
        desc = (row.description or "").replace("&", "&amp;").replace("<", "&lt;")

        lat = row.latitude
        lon = row.longitude

        kml_parts.append(f"""
        <Placemark>
          <name>{name}</name>
          <description>{desc}</description>
          <styleUrl>#battleStyle</styleUrl>
          <Point>
            <coordinates>{lon},{lat},0</coordinates>
          </Point>
        </Placemark>
        """)

    # ---- Close KML ----
    kml_parts.append("</Document>")
    kml_parts.append("</kml>")

    # Write new file
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write("\n".join(kml_parts))

    print(f"KML written to {OUTFILE}")


if __name__ == "__main__":
    export_battles_to_kml()
