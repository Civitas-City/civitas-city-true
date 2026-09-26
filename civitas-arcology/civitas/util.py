"""Idempotent Blender helpers and pure-python mesh generators.

Every `ensure_*` function may be run any number of times: it creates the
datablock on the first call and rewrites it in place afterwards, so the whole
build is re-runnable without producing `.001` duplicates.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

TAU = math.pi * 2.0


# --------------------------------------------------------------------------
# collections and objects
# --------------------------------------------------------------------------


def ensure_collection(name: str, parent: bpy.types.Collection | None = None):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    target = parent or bpy.context.scene.collection
    if coll.name not in {c.name for c in target.children}:
        for other in bpy.data.collections:
            if coll.name in {c.name for c in other.children}:
                other.children.unlink(coll)
        if coll.name in {c.name for c in bpy.context.scene.collection.children}:
            if target is not bpy.context.scene.collection:
                bpy.context.scene.collection.children.unlink(coll)
        if coll.name not in {c.name for c in target.children}:
            target.children.link(coll)
    return coll


def move_to_collection(obj: bpy.types.Object, coll: bpy.types.Collection):
    for other in list(obj.users_collection):
        if other is not coll:
            other.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def ensure_mesh_object(
    name: str,
    coll: bpy.types.Collection,
    verts,
    faces,
    material: bpy.types.Material | None = None,
    location=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
    shade_smooth: bool = False,
):
    """Create or rewrite a mesh object in place."""
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != "MESH":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None

    if obj is None:
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
    # rewrite the existing datablock in place: cross-section copies share it
    # on purpose, and forking would leak a new mesh on every rebuild
    mesh = obj.data
    mesh.clear_geometry()
    mesh.from_pydata(list(verts), [], [list(f) for f in faces])
    mesh.validate(verbose=False)
    if shade_smooth:
        for poly in mesh.polygons:
            poly.use_smooth = True

    mesh.materials.clear()
    if material is not None:
        mesh.materials.append(material)

    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    move_to_collection(obj, coll)
    return obj


def ensure_instance(
    name: str,
    coll: bpy.types.Collection,
    mesh: bpy.types.Mesh,
    location,
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
):
    """An object that shares an existing mesh datablock (real instancing)."""
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != "MESH":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        obj = bpy.data.objects.new(name, mesh)
    obj.data = mesh
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    move_to_collection(obj, coll)
    return obj


def ensure_light(name, coll, location, rotation=(0.0, 0.0, 0.0),
                 kind="SPOT", energy=1.0e12, color=(1.0, 1.0, 1.0),
                 radius=200.0, spot_size=1.2, spot_blend=0.4,
                 shadow=True):
    """Create or rewrite a light in place, data block reused by name."""
    data = bpy.data.lights.get(name)
    if data is not None and data.type != kind:
        bpy.data.lights.remove(data)
        data = None
    if data is None:
        data = bpy.data.lights.new(name, type=kind)
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    if hasattr(data, "use_shadow"):
        data.use_shadow = shadow
    if kind == "SPOT":
        data.spot_size = spot_size
        data.spot_blend = spot_blend
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        obj = bpy.data.objects.new(name, data)
    obj.data = data
    obj.location = location
    obj.rotation_euler = rotation
    move_to_collection(obj, coll)
    return obj


def ensure_empty(name, coll, location=(0.0, 0.0, 0.0), kind="PLAIN_AXES", size=100.0):
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != "EMPTY":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = kind
    obj.empty_display_size = size
    obj.location = location
    move_to_collection(obj, coll)
    return obj


def ensure_text(name, coll, body, location, size=200.0, material=None,
                rotation=(math.pi / 2.0, 0.0, 0.0)):
    obj = bpy.data.objects.get(name)
    if obj is not None and obj.type != "FONT":
        bpy.data.objects.remove(obj, do_unlink=True)
        obj = None
    if obj is None:
        curve = bpy.data.curves.new(name, type="FONT")
        obj = bpy.data.objects.new(name, curve)
    curve = obj.data
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    font = montserrat()
    if font is not None:
        curve.font = font
    curve.materials.clear()
    if material is not None:
        curve.materials.append(material)
    obj.location = location
    obj.rotation_euler = rotation
    move_to_collection(obj, coll)
    return obj


_FONT_CACHE: dict[str, bpy.types.VectorFont | None] = {}


def montserrat():
    """Montserrat if it is installed, else Blender's built-in face.

    Canon (RTFCT Typography Edict) requires Montserrat; `fetch-montserrat.sh`
    puts it where this looks for it.
    """
    import os

    if "font" in _FONT_CACHE:
        return _FONT_CACHE["font"]
    for existing in bpy.data.fonts:
        if "montserrat" in existing.name.lower():
            _FONT_CACHE["font"] = existing
            return existing
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "fonts", "Montserrat-Bold.ttf"),
        os.path.expanduser("~/.fonts/Montserrat-Bold.ttf"),
        "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            _FONT_CACHE["font"] = bpy.data.fonts.load(path)
            return _FONT_CACHE["font"]
    print("CIVITAS: Montserrat not found; run civitas-arcology/fetch-montserrat.sh")
    _FONT_CACHE["font"] = None
    return None


def prune(coll: bpy.types.Collection, keep: set[str], recursive: bool = False):
    """Delete objects of `coll` that this run did not (re)create."""
    for obj in list(coll.objects):
        if obj.name not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    if recursive:
        for child in list(coll.children):
            prune(child, keep, True)


def world_bounds(obj: bpy.types.Object):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (
        Vector((min(c.x for c in corners), min(c.y for c in corners),
                min(c.z for c in corners))),
        Vector((max(c.x for c in corners), max(c.y for c in corners),
                max(c.z for c in corners))),
    )


def junction_z():
    """Mid height of the real Shaft_L2_L3, not an assumed origin.

    The specification says the junction sits at Z=0; in the canonical .blend the
    shaft's 250 m band is at Z 3700-3950, so the anchor is read off the geometry.
    """
    from . import config

    shaft = bpy.data.objects.get(config.JUNCTION_OBJECT)
    if shaft is None:
        return 0.0
    lo, hi = world_bounds(shaft)
    return (lo.z + hi.z) / 2.0


def custom_prop(obj, name, value, minimum=0.0, maximum=1.0):
    if name not in obj:
        obj[name] = value
    ui = obj.id_properties_ui(name)
    ui.update(min=minimum, max=maximum, soft_min=minimum, soft_max=maximum)
    return obj


# --------------------------------------------------------------------------
# pure-python mesh generators -> (verts, faces)
# --------------------------------------------------------------------------


def box(sx, sy, sz, centre=(0.0, 0.0, 0.0)):
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    cx, cy, cz = centre
    verts = [
        (cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz),
    ]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def ellipsoid(rx, ry, rz, segments=16, rings=8):
    verts = [(0.0, 0.0, -rz)]
    for i in range(1, rings):
        phi = math.pi * i / rings
        z = -rz * math.cos(phi)
        s = math.sin(phi)
        for j in range(segments):
            th = TAU * j / segments
            verts.append((rx * s * math.cos(th), ry * s * math.sin(th), z))
    verts.append((0.0, 0.0, rz))
    top = len(verts) - 1
    faces = []
    for j in range(segments):
        faces.append((0, 1 + (j + 1) % segments, 1 + j))
    for i in range(rings - 2):
        a = 1 + i * segments
        b = a + segments
        for j in range(segments):
            j2 = (j + 1) % segments
            faces.append((a + j, a + j2, b + j2, b + j))
    last = 1 + (rings - 2) * segments
    for j in range(segments):
        faces.append((top, last + j, last + (j + 1) % segments))
    return verts, faces


def icosphere(radius, subdivisions=1):
    t = (1.0 + 5.0 ** 0.5) / 2.0
    verts = [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
        (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
        (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
    ]
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    verts = [list(v) for v in verts]
    for _ in range(subdivisions):
        cache: dict[tuple[int, int], int] = {}
        new_faces = []

        def midpoint(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                va, vb = verts[a], verts[b]
                verts.append([(va[i] + vb[i]) / 2.0 for i in range(3)])
                cache[key] = len(verts) - 1
            return cache[key]

        for a, b, c in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            new_faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = new_faces
    out = []
    for v in verts:
        length = math.sqrt(sum(c * c for c in v)) or 1.0
        out.append(tuple(c / length * radius for c in v))
    return out, faces


def cylinder(radius, height, segments=16, caps=True, radius_top=None):
    rt = radius if radius_top is None else radius_top
    hz = height / 2.0
    verts = []
    for j in range(segments):
        th = TAU * j / segments
        verts.append((radius * math.cos(th), radius * math.sin(th), -hz))
    for j in range(segments):
        th = TAU * j / segments
        verts.append((rt * math.cos(th), rt * math.sin(th), hz))
    faces = []
    for j in range(segments):
        j2 = (j + 1) % segments
        faces.append((j, j2, segments + j2, segments + j))
    if caps:
        faces.append(tuple(range(segments - 1, -1, -1)))
        faces.append(tuple(range(segments, segments * 2)))
    return verts, faces


def annulus(r_inner, r_outer, height, segments=64):
    """A solid ring slab centred on Z=0."""
    hz = height / 2.0
    verts = []
    for z in (-hz, hz):
        for r in (r_inner, r_outer):
            for j in range(segments):
                th = TAU * j / segments
                verts.append((r * math.cos(th), r * math.sin(th), z))
    n = segments
    bi, bo, ti, to = 0, n, 2 * n, 3 * n
    faces = []
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((bi + j, bi + j2, bo + j2, bo + j))          # bottom
        faces.append((to + j, to + j2, ti + j2, ti + j))          # top
        faces.append((bo + j, bo + j2, to + j2, to + j))          # outer wall
        faces.append((ti + j, ti + j2, bi + j2, bi + j))          # inner wall
    return verts, faces


def loft(rings, cap_start=True, cap_end=True):
    """Stitch a list of equal-length closed vertex loops into a tube."""
    verts = [v for ring in rings for v in ring]
    n = len(rings[0])
    faces = []
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if cap_start:
        faces.append(tuple(range(n - 1, -1, -1)))
    if cap_end:
        base = (len(rings) - 1) * n
        faces.append(tuple(range(base, base + n)))
    return verts, faces


def superellipse_ring(a, b, z, power=2.0, segments=24):
    """A closed loop shaped like |x/a|^p + |y/b|^p = 1."""
    ring = []
    for j in range(segments):
        th = TAU * j / segments
        ct, st = math.cos(th), math.sin(th)
        x = a * math.copysign(abs(ct) ** (2.0 / power), ct)
        y = b * math.copysign(abs(st) ** (2.0 / power), st)
        ring.append((x, y, z))
    return ring


def hull(length, beam, profile, power=2.0, segments=24, depth_factor=0.62):
    """A lofted vessel hull running along local +X, bow at +X/2."""
    rings = []
    for t, r in profile:
        x = (t - 0.5) * length
        a = max(beam * r / 2.0, beam * 0.004)
        b = max(beam * r * depth_factor / 2.0, beam * 0.003)
        ring = []
        for j in range(segments):
            th = TAU * j / segments
            ct, st = math.cos(th), math.sin(th)
            y = a * math.copysign(abs(ct) ** (2.0 / power), ct)
            z = b * math.copysign(abs(st) ** (2.0 / power), st)
            ring.append((x, y, z))
        rings.append(ring)
    return loft(rings)


def square_to_round(inner_span, outer_radius, height_inner, height_outer,
                    steps=8, segments=64):
    """Lens junction: a square inner cross-section grown into a round rim.

    Interpolates a `inner_span` square outline out to `outer_radius`, thinning
    from `height_inner` to `height_outer` on a lens (elliptical) curve.
    """
    def square_point(th, half):
        ct, st = math.cos(th), math.sin(th)
        m = max(abs(ct), abs(st)) or 1.0
        return half * ct / m, half * st / m

    rings_top, rings_bottom = [], []
    half = inner_span / 2.0
    for i in range(steps + 1):
        t = i / steps
        r = half + (outer_radius - half) * t
        blend = t ** 0.65  # square outline near the shaft, circular at the rim
        thickness = height_outer + (height_inner - height_outer) * math.sqrt(
            max(0.0, 1.0 - t * t))
        hz = thickness / 2.0
        top, bottom = [], []
        for j in range(segments):
            th = TAU * j / segments
            sx, sy = square_point(th, r)
            rx, ry = r * math.cos(th), r * math.sin(th)
            x = sx * (1.0 - blend) + rx * blend
            y = sy * (1.0 - blend) + ry * blend
            top.append((x, y, hz))
            bottom.append((x, y, -hz))
        rings_top.append(top)
        rings_bottom.append(bottom)

    verts = []
    faces = []
    n = segments

    def add_ring(ring):
        base = len(verts)
        verts.extend(ring)
        return base

    top_bases = [add_ring(r) for r in rings_top]
    bot_bases = [add_ring(r) for r in rings_bottom]
    for bases in (top_bases, bot_bases):
        for i in range(len(bases) - 1):
            a, b = bases[i], bases[i + 1]
            for j in range(n):
                j2 = (j + 1) % n
                faces.append((a + j, a + j2, b + j2, b + j))
    # outer rim wall and inner shaft collar
    a, b = top_bases[-1], bot_bases[-1]
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((a + j, a + j2, b + j2, b + j))
    a, b = top_bases[0], bot_bases[0]
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((b + j, b + j2, a + j2, a + j))
    return verts, faces


def torus(major, minor, major_segments=32, minor_segments=12):
    """A ring lying in XY, `major` to the tube centre, `minor` tube radius."""
    rings = []
    for i in range(major_segments):
        th = TAU * i / major_segments
        ct, st = math.cos(th), math.sin(th)
        ring = []
        for j in range(minor_segments):
            ph = TAU * j / minor_segments
            r = major + minor * math.cos(ph)
            ring.append((r * ct, r * st, minor * math.sin(ph)))
        rings.append(ring)
    verts = [v for ring in rings for v in ring]
    faces = []
    for i in range(major_segments):
        a = i * minor_segments
        b = ((i + 1) % major_segments) * minor_segments
        for j in range(minor_segments):
            j2 = (j + 1) % minor_segments
            faces.append((a + j, a + j2, b + j2, b + j))
    return verts, faces


def sweep(points, radii, sides=10):
    """A tube swept along a polyline, `radii` giving the radius per point.

    Frames are parallel-transported so a curve that loops back on itself does
    not flip its cross-section.
    """
    def unit(v):
        length = math.sqrt(sum(c * c for c in v))
        return tuple(c / length for c in v) if length > 1e-9 else (0.0, 0.0, 1.0)

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    tangents = []
    for i, p in enumerate(points):
        nxt = points[min(i + 1, len(points) - 1)]
        prv = points[max(i - 1, 0)]
        tangents.append(unit(tuple(n - q for n, q in zip(nxt, prv))))

    up = (0.0, 0.0, 1.0)
    normal = unit(cross(tangents[0], up))
    if abs(dot(tangents[0], up)) > 0.98:
        normal = unit(cross(tangents[0], (1.0, 0.0, 0.0)))

    rings = []
    for tangent, centre, radius in zip(tangents, points, radii):
        # re-orthogonalise the carried normal against the new tangent
        normal = unit(tuple(n - tangent[k] * dot(normal, tangent)
                            for k, n in enumerate(normal)))
        binormal = unit(cross(tangent, normal))
        ring = []
        for j in range(sides):
            ph = TAU * j / sides
            ct, st = math.cos(ph), math.sin(ph)
            ring.append(tuple(centre[k] + radius * (normal[k] * ct +
                                                    binormal[k] * st)
                              for k in range(3)))
        rings.append(ring)
    return loft(rings)


def grid_shell(top, bottom, radial, angular):
    """Close two (radial x angular) point grids into one solid membrane.

    `top` and `bottom` are flat lists in radial-major order; the rim and the
    inner collar are walled so the result is watertight.
    """
    verts = list(top) + list(bottom)
    offset = len(top)
    faces = []

    def quad(grid, i, j, flip):
        j2 = (j + 1) % angular
        a = grid + i * angular
        b = grid + (i + 1) * angular
        f = (a + j, a + j2, b + j2, b + j)
        return f[::-1] if flip else f

    for i in range(radial - 1):
        for j in range(angular):
            faces.append(quad(0, i, j, False))
            faces.append(quad(offset, i, j, True))
    for j in range(angular):
        j2 = (j + 1) % angular
        rim = (radial - 1) * angular
        faces.append((rim + j, rim + j2, offset + rim + j2, offset + rim + j))
        faces.append((offset + j, offset + j2, j2, j))
    return verts, faces


def sweep_band(points, widths, thicknesses):
    """A flat ribbon swept along a polyline: wide in plan, thin in Z.

    The width axis is kept horizontal (perpendicular to the path in XY), so a
    band that climbs or dips still reads as linguine rather than rolling over.
    """
    def unit(v, fallback=(1.0, 0.0, 0.0)):
        length = math.sqrt(sum(c * c for c in v))
        return tuple(c / length for c in v) if length > 1e-9 else fallback

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    rings = []
    for i, (centre, width, thick) in enumerate(zip(points, widths,
                                                   thicknesses)):
        nxt = points[min(i + 1, len(points) - 1)]
        prv = points[max(i - 1, 0)]
        tangent = unit(tuple(n - q for n, q in zip(nxt, prv)))
        wide = unit(cross(tangent, (0.0, 0.0, 1.0)))
        tall = unit(cross(wide, tangent), (0.0, 0.0, 1.0))
        hw, ht = width / 2.0, thick / 2.0
        corners = ((hw, ht), (-hw, ht), (-hw, -ht), (hw, -ht))
        rings.append([tuple(centre[k] + a * wide[k] + b * tall[k]
                            for k in range(3)) for a, b in corners])
    return loft(rings)


def helix_about(points, loops, amplitude, phase=0.0, amplitude_z=None):
    """Wind a polyline helically around its own path.

    Uses the same horizontal-width frame as `sweep_band`, so a thread wound
    about a ribbon stays on the ribbon's faces instead of drifting off it.
    """
    def unit(v, fallback=(1.0, 0.0, 0.0)):
        length = math.sqrt(sum(c * c for c in v))
        return tuple(c / length for c in v) if length > 1e-9 else fallback

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    out = []
    last = len(points) - 1
    for i, centre in enumerate(points):
        nxt = points[min(i + 1, last)]
        prv = points[max(i - 1, 0)]
        tangent = unit(tuple(n - q for n, q in zip(nxt, prv)))
        wide = unit(cross(tangent, (0.0, 0.0, 1.0)))
        tall = unit(cross(wide, tangent), (0.0, 0.0, 1.0))
        ph = TAU * loops * (i / last if last else 0.0) + phase

        def at(value):
            return value[i] if isinstance(value, (list, tuple)) else value

        amp = at(amplitude)
        amp_z = amp if amplitude_z is None else at(amplitude_z)
        ca, sa = math.cos(ph) * amp, math.sin(ph) * amp_z
        out.append(tuple(centre[k] + ca * wide[k] + sa * tall[k]
                         for k in range(3)))
    return out


def merge(parts):
    """Concatenate (verts, faces) pairs into one mesh definition."""
    verts, faces = [], []
    for pverts, pfaces in parts:
        offset = len(verts)
        verts.extend(pverts)
        faces.extend([tuple(i + offset for i in f) for f in pfaces])
    return verts, faces


def wedge(r_inner, r_outer, th_start, th_end, z_bottom, z_top, arc_steps=2):
    """A solid annular cell: the building block of a panelled deck."""
    top, bottom = [], []
    for k in range(arc_steps + 1):
        th = th_start + (th_end - th_start) * k / arc_steps
        ct, st = math.cos(th), math.sin(th)
        top.append((r_inner * ct, r_inner * st, z_top))
        bottom.append((r_inner * ct, r_inner * st, z_bottom))
    for k in range(arc_steps, -1, -1):
        th = th_start + (th_end - th_start) * k / arc_steps
        ct, st = math.cos(th), math.sin(th)
        top.append((r_outer * ct, r_outer * st, z_top))
        bottom.append((r_outer * ct, r_outer * st, z_bottom))
    n = len(top)
    verts = top + bottom
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return verts, faces


def points_on_ring(count, radius, jitter=0.0, seed=0):
    import random

    rng = random.Random(seed)
    out = []
    for i in range(count):
        th = TAU * i / count
        r = radius * (1.0 + rng.uniform(-jitter, jitter))
        out.append((r * math.cos(th), r * math.sin(th), th))
    return out


def fibonacci_sphere(count, radius):
    out = []
    golden = math.pi * (3.0 - 5.0 ** 0.5)
    for i in range(count):
        y = 1.0 - (i / max(1, count - 1)) * 2.0
        r = math.sqrt(max(0.0, 1.0 - y * y))
        th = golden * i
        out.append((radius * math.cos(th) * r, radius * y, radius * math.sin(th) * r))
    return out
