import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pathlib import Path
from sqlalchemy import select
from fastkml import kml
from shapely.geometry import Point
from database.db import engine, battles
from xml.etree.ElementTree import Element, SubElement, tostring
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

    ns = "{http://www.opengis.net/kml/2.2}"
    doc = kml.KML()

    folder = kml.Folder(
        ns=ns,
        id="root",
        name="Battles",
        description="All battle locations"
    )
    doc.append(folder)

    # --- Style creation using ElementTree ---
    style_el = Element("Style", id="battleStyle")

    iconstyle = SubElement(style_el, "IconStyle")
    scale = SubElement(iconstyle, "scale")
    scale.text = "1.2"

    icon = SubElement(iconstyle, "Icon")
    href = SubElement(icon, "href")
    href.text = "battle.png"  # file inside KMZ

    labelstyle = SubElement(style_el, "LabelStyle")
    label_scale = SubElement(labelstyle, "scale")
    label_scale.text = "1.1"

    # Inject style XML at top level
    doc.features.append(style_el)

    # --- Load battles ---
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
        point = Point(float(row.longitude), float(row.latitude))

        pm = kml.Placemark(
            ns=ns,
            id=str(row.id),
            name=name,
            description=desc,
            geometry=point
        )
        pm.style_url = "#battleStyle"
        folder.append(pm)

    # --- Write KML to disk ---
    with open(KML_PATH, "w", encoding="utf-8") as f:
        f.write(doc.to_string(prettyprint=True))

    # --- Build KMZ ---
    with ZipFile(KMZ_PATH, "w", ZIP_DEFLATED) as z:
        z.write(KML_PATH, "doc.kml")
        z.write(ICON_SRC, "battle.png")

    print(f"KMZ written to {KMZ_PATH}")


if __name__ == "__main__":
    export_battles_to_kmz()
