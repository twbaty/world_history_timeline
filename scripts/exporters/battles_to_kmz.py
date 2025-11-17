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

    # Build KML using fastkml
    doc = kml.KML()

    root_folder = kml.Folder(
        name="Battles",
        description="All battle locations"
    )
    doc.append(root_folder)

    with engine.begin() as conn:
        rows = conn.execute(
            select(battles).where(
                battles.c.latitude.is_not(None),
                battles.c.longitude.is_not(None)
            )
        ).fetchall()

    for row in rows:
        p = Point(float(row.longitude), float(row.latitude))

        placemark = kml.Placemark(
            name=row.label or row.id,
            description=row.description or "",
            geometry=p
        )

        # Reference our style (to be injected later)
        placemark.style_url = "#battleStyle"

        root_folder.features.append(placemark)

    # Convert to KML text
    kml_text = doc.to_string(prettyprint=True)

    # Inject style block manually before </Document>
    style_block = f"""
    <Style id="battleStyle">
      <IconStyle>
        <scale>1.4</scale>
        <Icon>
          <href>battle.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.2</scale>
      </LabelStyle>
    </Style>
    """

    if "</Document>" in kml_text:
        kml_text = kml_text.replace("</Document>", style_block + "\n</Document>")

    # Write KMZ
    with zipfile.ZipFile(OUTFILE, "w", zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr("doc.kml", kml_text)
        kmz.write(ICON_SRC, arcname="battle.png")

    print(f"KMZ written to: {OUTFILE}")


if __name__ == "__main__":
    export_battles_to_kmz()
