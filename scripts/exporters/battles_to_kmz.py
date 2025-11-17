import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from fastkml import kml
from shapely.geometry import Point
from sqlalchemy import select
from database.db import engine, battles
import zipfile


def export_battles_to_kmz():
    ROOT = Path(__file__).resolve().parents[2]
    EXPORTS_DIR = ROOT / "exports"
    EXPORTS_DIR.mkdir(exist_ok=True)

    OUTFILE = EXPORTS_DIR / "battles.kmz"
    ICON_SRC = ROOT / "icons" / "battle.png"

    if not ICON_SRC.exists():
        raise FileNotFoundError(f"Missing icon: {ICON_SRC}")

    # --- Build KML ---
    doc = kml.KML()

    # Folder — fastkml now only accepts (name, description)
    root_folder = kml.Folder(name="Battles", description="All battle locations")
    doc.append(root_folder)

    # Style (manual XML injection)
    style_id = "battleStyle"
    style_xml = f"""
    <Style id="{style_id}">
      <IconStyle>
        <scale>1.3</scale>
        <Icon>
          <href>battle.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.2</scale>
      </LabelStyle>
    </Style>
    """
    root_folder._features.append(style_xml)

    # Fetch DB rows
    with engine.begin() as conn:
        rows = conn.execute(
            select(battles).where(
                battles.c.latitude.is_not(None),
                battles.c.longitude.is_not(None)
            )
        ).fetchall()

    for row in rows:
        p = Point(float(row.longitude), float(row.latitude))
        name = row.label or row.id
        desc = row.description or ""

        placemark = kml.Placemark(
            name=name,
            description=desc,
            geometry=p
        )
        placemark.style_url = f"#{style_id}"
        root_folder.append(placemark)

    # Write KML into KMZ structure
    kmz_path = OUTFILE
    with zipfile.ZipFile(kmz_path, "w", zipfile.ZIP_DEFLATED) as kmz:
        # KML goes in doc.kml
        kmz.writestr(
            "doc.kml",
            doc.to_string(prettyprint=True)
        )
        # Icon sits at top-level
        kmz.write(ICON_SRC, arcname="battle.png")

    print(f"KMZ written to: {kmz_path}")


if __name__ == "__main__":
    export_battles_to_kmz()
