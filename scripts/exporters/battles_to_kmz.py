import sys, pathlib, zipfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from fastkml import kml
from shapely.geometry import Point
from sqlalchemy import select
from database.db import engine, battles


def export_battles_to_kmz():
    ROOT = Path(__file__).resolve().parents[2]
    EXPORTS_DIR = ROOT / "exports"
    EXPORTS_DIR.mkdir(exist_ok=True)

    OUTFILE = EXPORTS_DIR / "battles.kmz"

    # Icon source
    ICON_SRC = ROOT / "icons" / "battle.png"
    if not ICON_SRC.exists():
        raise FileNotFoundError(f"Missing icon: {ICON_SRC}")

    # ----------------------------
    # Build KML root document
    # ----------------------------
    doc = kml.KML()
    ns = "{http://www.opengis.net/kml/2.2}"

    root_folder = kml.Folder(ns, "root", "Battles", "All battle locations")
    doc.append(root_folder)

    # Style definition (via raw XML since fastkml lacks style objects)
    style_id = "battleStyle"

    style_xml = f"""
    <Style id="{style_id}">
      <IconStyle>
        <scale>1.2</scale>
        <Icon>
          <href>files/battle.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.2</scale>
      </LabelStyle>
    </Style>
    """

    root_folder._features.append(style_xml)

    # ----------------------------
    # Pull battles from DB
    # ----------------------------
    with engine.begin() as conn:
        rows = conn.execute(
            select(battles).where(
                battles.c.latitude.is_not(None),
                battles.c.longitude.is_not(None)
            )
        ).fetchall()

    for row in rows:
        name = row.label or row.id
        desc = row.description or ""

        p = Point(float(row.longitude), float(row.latitude))

        placemark = kml.Placemark(
            ns,
            row.id,
            name,
            desc,
            geometry=p,
        )

        placemark.style_url = f"#{style_id}"
        root_folder.append(placemark)

    # ----------------------------
    # Convert KML object to text
    # ----------------------------
    kml_text = doc.to_string(prettyprint=True)

    # ----------------------------
    # Write KMZ (zip) container
    # ----------------------------
    with zipfile.ZipFile(OUTFILE, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml_text)
        kmz.write(ICON_SRC, "files/battle.png")

    print(f"KMZ written to {OUTFILE}")


if __name__ == "__main__":
    export_battles_to_kmz()
