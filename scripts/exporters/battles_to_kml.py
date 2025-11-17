import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from fastkml import kml
from shapely.geometry import Point
from sqlalchemy import select
from database.db import engine, battles


def export_battles_to_kml():
    # Where KML goes
    EXPORTS_DIR = Path(__file__).resolve().parents[1] / "exports"
    EXPORTS_DIR.mkdir(exist_ok=True)
    OUTFILE = EXPORTS_DIR / "battles.kml"

    # Where the PNG icon is
    ICON_PATH = Path(__file__).resolve().parents[2] / "icons" / "battle.png"

    # Convert to file:// URI
    icon_href = ICON_PATH.resolve().as_uri()

    # --- Build KML doc ---
    doc = kml.KML()
    ns = "{http://www.opengis.net/kml/2.2}"

    # Root Folder
    root_folder = kml.Folder(ns, "root", "Battles", "All battle points")
    doc.append(root_folder)

    # Manual Style injection (fastkml doesn't have full styling)
    style_id = "battleStyle"
    style_xml = f"""
    <Style id="{style_id}">
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
    """

    # Manually attach the raw XML
    root_folder._features.append(style_xml)

    # Pull DB rows
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
            geometry=p
        )

        # Attach style
        placemark.style_url = f"#{style_id}"

        root_folder.append(placemark)

    # Write file
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write(doc.to_string(prettyprint=True))

    print(f"KML written to {OUTFILE}")
