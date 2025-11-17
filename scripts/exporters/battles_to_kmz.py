import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from sqlalchemy import select
from database.db import engine, battles
from zipfile import ZipFile, ZIP_DEFLATED


def export_battles_to_kmz():

    BASE = Path(__file__).resolve().parents[2]
    ICON_SRC = BASE / "icons" / "battle.png"
    EXPORT_DIR = BASE / "exports"
    KML_PATH = EXPORT_DIR / "battles.kml"
    KMZ_PATH = EXPORT_DIR / "battles.kmz"

    EXPORT_DIR.mkdir(exist_ok=True)

    if not ICON_SRC.exists():
        raise FileNotFoundError(f"Missing icon: {ICON_SRC}")

    # --- Fetch DB rows ---
    with engine.begin() as conn:
        rows = conn.execute(
            select(battles).where(
                battles.c.latitude.is_not(None),
                battles.c.longitude.is_not(None)
            )
        ).fetchall()

    # --- Build KML manually ---
    parts = []

    parts.append("""<?xml version="1.0" encoding="UTF-8"?>""")
    parts.append("""<kml xmlns="http://www.opengis.net/kml/2.2">""")
    parts.append("""<Document>""")

    # Style block
    parts.append("""
    <Style id="battleStyle">
      <IconStyle>
        <scale>1.2</scale>
        <Icon>
          <href>battle.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.1</scale>
      </LabelStyle>
    </Style>
    """)

    parts.append("""<Folder><name>Battles</name>""")

    for row in rows:
        name = (row.label or row.id).replace("&", "&amp;")
        desc = (row.description or "").replace("&", "&amp;")
        lat = float(row.latitude)
        lon = float(row.longitude)

        parts.append(f"""
        <Placemark>
            <name>{name}</name>
            <description>{desc}</description>
            <styleUrl>#battleStyle</styleUrl>
            <Point>
                <coordinates>{lon},{lat},0</coordinates>
            </Point>
        </Placemark>
        """)

    parts.append("</Folder>")
    parts.append("</Document>")
    parts.append("</kml>")

    # Write KML
    KML_PATH.write_text("\n".join(parts), encoding="utf-8")

    # Build KMZ
    with ZipFile(KMZ_PATH, "w", ZIP_DEFLATED) as z:
        z.write(KML_PATH, "doc.kml")
        z.write(ICON_SRC, "battle.png")

    print(f"KMZ written to {KMZ_PATH}")


if __name__ == "__main__":
    export_battles_to_kmz()
