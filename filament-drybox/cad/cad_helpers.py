"""Original project helper for absolute OCCT display triangulation.

Ported from the author's original CAD utility; no external project imports.
Display meshes are not manufacturing or metrology qualification.
"""

import math


def absolute_tessellation(shape, *, tolerance=0.08, angular_tolerance=0.2):
    """Extract absolute-mesher triangles without CadQuery's relative remeshing.

    Linear deflection is requested in model millimetres. OCCT can report a face
    deflection greater than that request, so this is not a strict maximum-error
    receipt. These triangles are for display, not fabrication or analysis.
    Finite zero-area seam/pole triangles are retained as emitted by OCCT.
    """
    from cadquery import Vector
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.TopLoc import TopLoc_Location

    if not all(math.isfinite(value) and value > 0 for value in (tolerance, angular_tolerance)):
        raise ValueError('Display meshing requires finite positive linear and angular deflections')
    mesher = BRepMesh_IncrementalMesh(shape.wrapped, tolerance, False, angular_tolerance, True)
    if not mesher.IsDone():
        raise RuntimeError(
            f'Absolute display mesher did not complete; status flags={mesher.GetStatusFlags()}'
        )
    faces = shape.Faces()
    if not faces:
        raise RuntimeError('Absolute display mesher received a shape without faces')
    vertices, triangles = [], []
    for face_index, face in enumerate(faces):
        location = TopLoc_Location()
        poly = BRep_Tool.Triangulation_s(face.wrapped, location)
        if poly is None or poly.NbNodes() == 0 or poly.NbTriangles() == 0:
            raise RuntimeError(
                f'Absolute display mesher omitted triangulation for face {face_index}'
            )
        transform = location.Transformation()
        points = []
        for node_index in range(1, poly.NbNodes() + 1):
            point = poly.Node(node_index).Transformed(transform)
            coordinates = (point.X(), point.Y(), point.Z())
            if not all(math.isfinite(value) for value in coordinates):
                raise RuntimeError(
                    f'Absolute display mesh has nonfinite node {node_index} on face {face_index}'
                )
            points.append(coordinates)
        offset = len(vertices)
        order = (1, 3, 2) if face.wrapped.Orientation() == TopAbs_REVERSED else (1, 2, 3)
        for triangle_index, triangle in enumerate(poly.Triangles()):
            indices = tuple(triangle.Value(corner) - 1 for corner in order)
            if len(set(indices)) != 3 or any(
                index < 0 or index >= len(points) for index in indices
            ):
                raise RuntimeError(
                    f'Absolute display mesh has invalid triangle {triangle_index} on face {face_index}'
                )
            triangles.append(tuple(index + offset for index in indices))
        vertices.extend(Vector(*point) for point in points)
    return vertices, triangles


def export_step(shape, path):
    """Export native STEP; this does not release a manufacturing input."""
    import cadquery as cq
    cq.exporters.export(shape, str(path))
