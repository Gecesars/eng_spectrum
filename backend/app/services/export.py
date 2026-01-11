from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

import shapefile

from app.models import Contour, ContourPoint


@dataclass(frozen=True)
class ExportResult:
    path: str
    kind: str


def _contour_points(contour: Contour) -> list[ContourPoint]:
    return (
        ContourPoint.query.filter_by(contour_id=contour.id)
        .order_by(ContourPoint.order_idx)
        .all()
    )


def export_kml(contour: Contour, export_dir: str) -> ExportResult:
    points = _contour_points(contour)
    coords = [(p.lon, p.lat) for p in points]
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    coord_str = " ".join(f"{lon},{lat},0" for lon, lat in coords)
    kml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\">
  <Document>
    <Placemark>
      <name>Protected Contour</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coord_str}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""

    filename = f"contour_{contour.id}.kml"
    path = os.path.join(export_dir, filename)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(kml)

    return ExportResult(path=path, kind="kml")


def export_mosaico_txt(contour: Contour, export_dir: str, include_header: bool = True) -> ExportResult:
    points = _contour_points(contour)
    filename = f"contour_{contour.id}_mosaico.txt"
    path = os.path.join(export_dir, filename)

    with open(path, "w", encoding="utf-8") as handle:
        if include_header:
            handle.write("AZIMUTE;DISTANCIA_KM\n")
        for point in points:
            handle.write(f"{point.azimuth_deg};{point.distance_km:.3f}\n")
        if points:
            handle.write(f"{points[0].azimuth_deg};{points[0].distance_km:.3f}\n")

    return ExportResult(path=path, kind="txt")


def export_shapefile(contour: Contour, export_dir: str) -> ExportResult:
    points = _contour_points(contour)
    coords = [(p.lon, p.lat) for p in points]
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    filename = f"contour_{contour.id}"
    shp_path = os.path.join(export_dir, filename)

    writer = shapefile.Writer(shp_path, shapeType=shapefile.POLYGON)
    writer.field("id", "C")
    writer.poly([coords])
    writer.record(str(contour.id))
    writer.close()

    return ExportResult(path=f"{shp_path}.shp", kind="shp")
