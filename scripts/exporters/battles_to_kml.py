import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastkml import kml
from shapely.geometry import Point
from database.db import engine, battles



# Path to the icon
ROOT = Path(__file__).resolve().parents[2]
ICON_PATH = ROOT / "assets" / "icons" / "battle.png"

EXPORT_DIR = ROOT / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def export_battles_to_kml():
    k = kml.KML()
    doc = kml.Document(ns="", name="World History - Battles")
    k.append(doc)

    folder = kml.Folder(ns="", name="Battles")
    doc.append(folder)

    # Apply the style ONCE
    style_id = "battleStyle"
    style = kml.Style(id=style_id)
    style.iconstyle = kml.IconStyle(
        scale=1.2,
        icon_href=str(ICON_PATH.as_uri()),
    )
    doc.append(style)

    # Load battles
    with engine.begin() as conn:
        rows = conn.execute(select(battles)).fetchall()

    for row in rows:
        if row.latitude is None or row.longitude is None:
            continue

        p = kml.Placemark(ns="", name=row.label or row.id)
        p.styleUrl = f"#{style_id}"
        p.geometry = Point(row.longitude, row.latitude)

        desc = []
        if row.description:
            desc.append(f"<p>{row.description}</p>")
        if row.start:
            desc.append(f"<p><b>Start:</b> {row.start}</p>")
        if row.end:
            desc.append(f"<p><b>End:</b> {row.end}</p>")

        p.description = "\n".join(desc)
        folder.append(p)

    out_path = EXPORT_DIR / "battles.kml"
    out_path.write_text(k.to_string(prettyprint=True), encoding="utf-8")
    print(f"KML written to {out_path}")


if __name__ == "__main__":
    export_battles_to_kml()
