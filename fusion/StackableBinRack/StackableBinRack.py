"""Stackable Bin Rack (STACKERS rack): native parametric cap, frame and bin for Autodesk Fusion.

Rebuilt from ../../stackable-bin-rack.scad (SOURCE_SHA256). Units: mm.
Parts are constructed in their original print coordinates, then placed for assembly:
  len_n -> cap/frame Y, bin X;  wid_n -> cap/frame X, bin Z;  hgt_n -> frame Z, bin Y.
Modify > Change Parameters recomputes positive whole-cell sizes in place.
The tested size matrix and fit evidence are recorded in ../README.md.
Changing BUILD_POSE rebuilds a new document.
"""
import adsk.core
import adsk.fusion
import json
import math
import os
import traceback

SOURCE_SHA256 = "F377786477FA56ABE9B54C9868E0953C59197B70D1FEED311F759A7B4B74457B"
BUILD_POSE = "assembly"  # assembly or layout; changing pose rebuilds a new document
STAGE = ["init"]
CM = 0.1  # mm -> cm (Fusion database length unit)

# name, expression, unit, comment
PARAMS = [
    ("len_n", "1", "", "cells along the dovetail row (whole number >= 1)"),
    ("wid_n", "1", "", "cells of rack depth (whole number >= 1)"),
    ("hgt_n", "1", "", "cells of stack height (whole number >= 1)"),
    ("cell_len", "120 mm", "mm", "one-cell plate depth before trim"),
    ("cell_wid", "124 mm", "mm", "one-cell plate width"),
    ("cell_hgt", "91 mm", "mm", "stack pitch"),
    ("plate_trim", "0.07 mm", "mm", "MEASURED: plates are 119.93 deep"),
    ("pitch", "cell_len - plate_trim", "mm", "cell pitch when joined by dovetails"),
    ("span", "cell_len + 100 mm * (len_n - 1)", "mm", "n-long frame span, with 20 mm bin end clearance"),
    ("plate_w", "cell_wid + 100 mm * (wid_n - 1)", "mm", "plate width (X)"),
    ("post_top", "cell_hgt + 80 mm * (hgt_n - 1)", "mm", "frame post height = stack pitch"),
    ("plate_t", "8 mm", "mm", "plate thickness"),
    ("corner_r", "2 mm", "mm", "+X vertical corner radius"),
    ("win_corner", "10 mm", "mm", "window 45 deg corner leg"),
    ("win_fillet", "5 mm", "mm", "window corner radius"),
    ("win_chamfer", "2 mm", "mm", "window chamfer, both faces"),
    ("tip_r", "2 mm", "mm", "locator tip offset radius"),
    ("socket_r", "2.1 mm", "mm", "locator socket offset radius (> tip_r)"),
    ("socket_depth", "6 mm", "mm", "socket depth (> tip_h)"),
    ("socket_chamfer", "0.5 mm", "mm", "socket mouth chamfer"),
    ("tip_h", "5 mm", "mm", "tip height"),
    ("tip_chamfer", "0.75 mm", "mm", "tip top chamfer"),
    ("tip_flare", "0.5 mm", "mm", "tip base flare"),
    ("rail_w", "9 mm", "mm", "front/back rail width"),
    ("side_rail_w", "8 mm", "mm", "+X side rail width"),
    ("rail_top", "18 mm", "mm", "rail top height"),
    ("rail_chamfer", "2 mm", "mm", "rail / gusset / post edge chamfer"),
    ("ledge_w", "4 mm", "mm", "bin ledge width"),
    ("ledge_h", "4 mm", "mm", "bin ledge height"),
    ("xpost_len", "15 mm", "mm", "-X post length along X"),
    ("arm_x", "23 mm", "mm", "+X post arm along X"),
    ("arm_y", "24 mm", "mm", "+X post arm along Y"),
    ("gusset_leg", "10 mm", "mm", "45 deg gusset leg"),
    ("gusset_r", "5 mm", "mm", "gusset concave radius"),
    ("bin_W", "100 mm * len_n", "mm", "bin length (X)"),
    ("bin_D", "80 mm * hgt_n", "mm", "bin depth (Y)"),
    ("bin_H", "100 mm * wid_n + 35 mm", "mm", "bin height (Z), including fixed 35 mm nose geometry"),
    ("bin_wall", "4 mm", "mm", "bin wall"),
    ("bin_floor", "4 mm", "mm", "bin floor"),
    ("bin_chamfer_r", "5 mm", "mm", "radius where bottom chamfer meets side"),
    ("panel_depth", "2 mm", "mm", "decor panel depth (< bin_wall)"),
]

TRI = [("plate_w - 5 mm", "6 mm"), ("plate_w - 14.06 mm", "6 mm"), ("plate_w - 5 mm", "15.06 mm")]
SLOT = [("4 mm", "5 mm"), ("11 mm", "5 mm")]
SCOOP_D = 13.31 / math.sqrt(2)


def vi(expr):
    return adsk.core.ValueInput.createByString(expr)


def P(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


class Ctx:
    design = None
    um = None


def ev(expr):
    """Evaluate a length expression in mm."""
    return Ctx.um.evaluateExpression(expr, "mm") / CM


def back(y):
    return f"span - ({y})"


def stage(name):
    STAGE[0] = name


# ---------------------------------------------------------------- sketch helpers
class Sk:
    """Sketch whose 2D input coordinates are model axes `axes` (e.g. 'xz'); every point is
    fixed by distance dimensions from the sketch origin carrying the coordinate expressions."""

    def __init__(self, comp, plane, axes, name):
        self.comp = comp
        self.sk = comp.sketches.add(plane)
        self.sk.name = name
        self.sk.isComputeDeferred = True
        self.axes = ["xyz".index(a) for a in axes]
        o = self.m2s(0, 0)
        if abs(o[0]) > 1e-7 or abs(o[1]) > 1e-7:
            raise RuntimeError(f"sketch {name}: plane does not contain the model origin projection")
        du = self.m2s(1, 0)
        self.u_is_x = abs(du[0]) > 0.5
        self.n = 0
        # Share a coordinate only when it has the same driving expression.
        # Numeric-only aliasing made distinct expressions which happened to
        # have the same value at len_n=1 become the same point; after a
        # Change Parameters resize one loop then dragged the other to the
        # wrong coordinate and could leave a locator/post profile detached.
        self.axis_pts = {("h", "0 mm"): self.sk.originPoint, ("v", "0 mm"): self.sk.originPoint}

    def m2s(self, a, b):
        c = [0.0, 0.0, 0.0]
        c[self.axes[0]], c[self.axes[1]] = a, b
        p = self.sk.modelToSketchSpace(P(*c))
        return (p.x, p.y)

    def normal(self):
        return self.sk.xDirection.crossProduct(self.sk.yDirection)

    def _clear_inferred(self, sp):
        doomed = []
        for c in self.sk.geometricConstraints:
            ents = []
            for name in ("point", "pointOne", "pointTwo", "entity", "entityOne", "entityTwo"):
                try:
                    ents.append(getattr(c, name))
                except Exception:
                    pass
            if any(e == sp for e in ents):
                doomed.append(c)
        for c in doomed:
            try:
                c.deleteMe()
            except RuntimeError:
                pass

    def _dim(self, sp, expr, val, horizontal):
        sk = self.sk
        gc = sk.geometricConstraints
        if abs(val) < 1e-9:
            if horizontal:
                gc.addVerticalPoints(sk.originPoint, sp)
            else:
                gc.addHorizontalPoints(sk.originPoint, sp)
            return
        orient = (adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation if horizontal
                  else adsk.fusion.DimensionOrientations.VerticalDimensionOrientation)
        g = sp.geometry
        d = sk.sketchDimensions.addDistanceDimension(sk.originPoint, sp, orient, P(g.x + 0.3, g.y + 0.3))
        d.parameter.expression = expr if val > 0 else f"-({expr})"

    def _align(self, sp, expr, val, horizontal):
        key = ("h" if horizontal else "v", " ".join(expr.split()))
        other = self.axis_pts.get(key)
        if other is not None and other != sp:
            # Horizontal dimension locks X, so sharing X is a vertical-points constraint.
            if horizontal:
                self.sk.geometricConstraints.addVerticalPoints(other, sp)
            else:
                self.sk.geometricConstraints.addHorizontalPoints(other, sp)
            return
        self._dim(sp, expr, val, horizontal)
        self.axis_pts[key] = sp

    def fix(self, sp, ae, be):
        a, b = ev(ae), ev(be)
        xe, xv, ye, yv = (ae, a, be, b) if self.u_is_x else (be, b, ae, a)
        self._align(sp, xe, xv, True)
        self._align(sp, ye, yv, False)

    def loop(self, corners):
        """Closed polygon through vertices [(a_expr, b_expr, fillet_expr or None)]."""
        sk = self.sk
        data = []
        for ae, be, re in corners:
            a, b = ev(ae), ev(be)
            data.append(dict(ae=ae, be=be, re=re, c=self.m2s(a * CM, b * CM)))
        area = sum(data[i]["c"][0] * data[(i + 1) % len(data)]["c"][1]
                   - data[(i + 1) % len(data)]["c"][0] * data[i]["c"][1] for i in range(len(data)))
        if area < 0:
            data.reverse()

        # Keep the source polygon as construction geometry.  Its vertices are
        # the expression-driven owners of the dimensions; the visible profile
        # below must not be made by trimming those dimensioned lines.  Native
        # addFillet trims its input curves, and Fusion can leave the generated
        # tangent endpoints at their initial numeric positions after a driving
        # expression changes (the rear frame post was stuck near 118 mm when
        # span became 239.93 mm).
        support_pts = []
        for d in data:
            sp = sk.sketchPoints.add(P(*d["c"]))
            self._clear_inferred(sp)
            self.fix(sp, d["ae"], d["be"])
            support_pts.append(sp)
        support = []
        for i in range(len(support_pts)):
            line = sk.sketchCurves.sketchLines.addByTwoPoints(
                support_pts[i], support_pts[(i + 1) % len(support_pts)])
            line.isConstruction = True
            support.append(line)

        # Actual profile lines start at the same numeric vertices but have no
        # driving dimensions.  addFillet is then free to trim them; their
        # endpoints are subsequently constrained back onto the corresponding
        # expression-driven support edge.
        profile_pts = [sk.sketchPoints.add(P(*d["c"])) for d in data]
        lines = [sk.sketchCurves.sketchLines.addByTwoPoints(
            profile_pts[i], profile_pts[(i + 1) % len(profile_pts)])
                 for i in range(len(profile_pts))]
        arcs = []
        for i, d in enumerate(data):
            if not d["re"]:
                continue
            prev, nxt = lines[(i - 1) % len(lines)], lines[i]
            v = P(*d["c"])
            arc = sk.sketchCurves.sketchArcs.addFillet(
                prev, prev.endSketchPoint.geometry,
                nxt, nxt.startSketchPoint.geometry,
                ev(d["re"]) * CM)
            arcs.append((i, arc))
            rd = None
            for k in range(sk.sketchDimensions.count):
                dim = sk.sketchDimensions.item(k)
                if (dim.objectType == "adsk::fusion::SketchRadialDimension" and
                        dim.entity == arc):
                    rd = dim
                    break
            if rd is None:
                rd = sk.sketchDimensions.addRadialDimension(
                    arc, P(v.x + 0.3, v.y + 0.3))
            if rd is None or rd.objectType != "adsk::fusion::SketchRadialDimension":
                raise RuntimeError(f"loop: radial dimension missing for fillet {i}")
            rd.parameter.expression = d["re"]

        gc = sk.geometricConstraints
        for i, line in enumerate(lines):
            # Point-on-line constraints make the free tangent endpoints follow
            # the dimensioned polygon edges as their expressions recompute.
            gc.addCoincident(line.startSketchPoint, support[i])
            gc.addCoincident(line.endSketchPoint, support[i])
        def tangent_exists(one, two):
            for constraint_index in range(gc.count):
                constraint = gc.item(constraint_index)
                if constraint.objectType != "adsk::fusion::TangentConstraint":
                    continue
                a, b = constraint.curveOne, constraint.curveTwo
                if (a == one and b == two) or (a == two and b == one):
                    return True
            return False

        for i, arc in arcs:
            for one, two in ((lines[(i - 1) % len(lines)], arc), (arc, lines[i])):
                if not tangent_exists(one, two):
                    gc.addTangent(one, two)
        self.n += 1

    def hull(self, centers, r_expr):
        """Convex outer loop of equal-radius circles (locator stadium / offset triangle)."""
        sk = self.sk
        r = ev(r_expr) * CM
        cs, cps = [], []
        for ae, be in centers:
            a, b = ev(ae), ev(be)
            p = self.m2s(a * CM, b * CM)
            sp = sk.sketchPoints.add(P(*p))
            self._clear_inferred(sp)
            self.fix(sp, ae, be)
            cs.append(p)
            cps.append(sp)
        n = len(cs)
        if n == 1:
            cir = sk.sketchCurves.sketchCircles.addByCenterRadius(cps[0], r)
            sk.sketchDimensions.addRadialDimension(
                cir, P(cs[0][0] + r * 1.5, cs[0][1] + r * 1.5)
            ).parameter.expression = r_expr
            self.n += 1
            return

        def outward(i, j):
            (cix, ciy), (cjx, cjy) = cs[i], cs[j]
            dx, dy = cjx - cix, cjy - ciy
            L = math.hypot(dx, dy)
            nx, ny = -dy / L, dx / L
            if n > 2:
                k = (i + 2) % n
                if (cs[k][0] - cix) * nx + (cs[k][1] - ciy) * ny > 0:
                    nx, ny = -nx, -ny
                return [(nx, ny)]
            return [(nx, ny), (-nx, -ny)]

        # Keep the numeric edge endpoints only until the arcs exist.  The
        # final lines are created from the arcs' SketchPoints below, so a
        # change to the radial dimension moves the complete hull instead of
        # leaving fixed line endpoints behind.
        t_in, t_out = [None] * n, [None] * n
        line_specs = []
        for i in range(n if n > 2 else 1):
            j = (i + 1) % n
            for nx, ny in outward(i, j):
                pa = P(cs[i][0] + nx * r, cs[i][1] + ny * r)
                pb = P(cs[j][0] + nx * r, cs[j][1] + ny * r)
                line_specs.append((i, j, pa, pb))
                t_out[i] = pa
                t_in[j] = pb
                if n == 2:
                    t_in[i] = P(cs[i][0] - nx * r, cs[i][1] - ny * r)
                    t_out[j] = P(cs[j][0] - nx * r, cs[j][1] - ny * r)
        arcs = []
        for i in range(n):
            cx, cy = cs[i]
            a0 = math.atan2(t_in[i].y - cy, t_in[i].x - cx)
            a1 = math.atan2(t_out[i].y - cy, t_out[i].x - cx)
            sw = (a1 - a0) % (2 * math.pi)
            start = t_in[i]
            if sw > math.pi:
                sw, start = 2 * math.pi - sw, t_out[i]
            arc = sk.sketchCurves.sketchArcs.addByCenterStartSweep(cps[i].geometry, start, sw)
            sk.geometricConstraints.addCoincident(cps[i], arc.centerSketchPoint)
            sk.sketchDimensions.addRadialDimension(
                arc, P(cx + r * 1.5, cy + r * 1.5)
            ).parameter.expression = r_expr
            arcs.append(arc)

        def arc_point(arc, q):
            s, e = arc.startSketchPoint.geometry, arc.endSketchPoint.geometry
            ds = (s.x - q.x) ** 2 + (s.y - q.y) ** 2
            de = (e.x - q.x) ** 2 + (e.y - q.y) ** 2
            return arc.startSketchPoint if ds <= de else arc.endSketchPoint

        gc = sk.geometricConstraints
        for i, j, pa, pb in line_specs:
            line = sk.sketchCurves.sketchLines.addByTwoPoints(arc_point(arcs[i], pa), arc_point(arcs[j], pb))
            for arc in (arcs[i], arcs[j]):
                gc.addTangent(line, arc)
        self.n += 1

    def poly(self, pts):
        self.loop([(a, b, None) for a, b in pts])

    def point(self, ae, be):
        a, b = ev(ae), ev(be)
        sp = self.sk.sketchPoints.add(P(*self.m2s(a * CM, b * CM)))
        self.fix(sp, ae, be)
        return sp

    def profiles(self):
        self.sk.isComputeDeferred = False
        coll = adsk.core.ObjectCollection.create()
        for p in self.sk.profiles:
            coll.add(p)
        if coll.count == 0:
            raise RuntimeError(f"sketch {self.sk.name}: no profiles")
        return coll


def rrect(x0, y0, x1, y1, r):
    """Rounded rectangle vertices [x0..x1]x[y0..y1] with fillet r for Sk.loop."""
    return [(x0, y0, r), (x1, y0, r), (x1, y1, r), (x0, y1, r)]


def fillet_centre(pts, i, r_expr, r_val=None):
    """Centre of a fillet of radius r at convex vertex i of pts [(a_expr, b_expr)], as expressions."""
    v = [(ev(a), ev(b)) for a, b in pts]
    n = len(v)
    p, c, q = v[(i - 1) % n], v[i], v[(i + 1) % n]
    u1 = (p[0] - c[0], p[1] - c[1]); l1 = math.hypot(*u1); u1 = (u1[0] / l1, u1[1] / l1)
    u2 = (q[0] - c[0], q[1] - c[1]); l2 = math.hypot(*u2); u2 = (u2[0] / l2, u2[1] / l2)
    b = (u1[0] + u2[0], u1[1] + u2[1]); lb = math.hypot(*b); b = (b[0] / lb, b[1] / lb)
    s = abs(u1[0] * b[1] - u1[1] * b[0])  # sin(half angle)
    k = (b[0] / s, b[1] / s)
    if r_val is not None:
        return (f"({pts[i][0]}) + {k[0] * r_val:.9f} mm", f"({pts[i][1]}) + {k[1] * r_val:.9f} mm")
    return (f"({pts[i][0]}) + {k[0]:.12f} * ({r_expr})", f"({pts[i][1]}) + {k[1]:.12f} * ({r_expr})")


def filleted(pts, radii):
    """Sk.loop corners: polygon vertices with a fillet expression (or None) per vertex."""
    return [(a, b, radii[i]) for i, (a, b) in enumerate(pts)]


# ---------------------------------------------------------------- feature helpers
def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z


def V(x, y, z):
    return adsk.core.Vector3D.create(x, y, z)


def extrude(comp, sk, profs, dist, op, wdir, name, taper=None, participants=None):
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(profs, op)
    d = (adsk.fusion.ExtentDirections.PositiveExtentDirection if dot(sk.normal(), wdir) > 0
         else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    extent = adsk.fusion.DistanceExtentDefinition.create(vi(dist))
    if taper is None:
        inp.setOneSideExtent(extent, d)
    else:
        inp.setOneSideExtent(extent, d, vi(taper))
    if participants:
        inp.participantBodies = participants
    f = ext.add(inp)
    f.name = name
    return f


def loft_hull(comp, base, loc, z0, r0, z1, r1, name):
    """Join a native two-section locator hull using expression-driven sketches."""
    sections = []
    for suffix, z_expr, radius_expr in (("base", z0, r0), ("top", z1, r1)):
        plane = oplane(comp, base, z_expr, "z", f"{name} {suffix} plane")
        sketch = Sk(comp, plane, "xy", f"{name} {suffix} profile")
        sketch.hull(loc, radius_expr)
        sections.append(sketch.profiles().item(0))
        sketch.sk.isVisible = False
    inp = comp.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.JoinFeatureOperation)
    for profile in sections:
        inp.loftSections.add(profile)
    inp.isSolid = True
    feature = comp.features.loftFeatures.add(inp)
    if feature is None:
        raise RuntimeError(f"{name}: loft creation failed")
    feature.name = name
    return feature


def cut_panel_loft(comp, body, plane0, plane1, axes, loop0, loop1, name):
    """Cut one deterministic two-section native pocket from a panel surface."""
    sections = []
    for suffix, plane, loops in (("surface", plane0, loop0), ("inset", plane1, loop1)):
        sketch = Sk(comp, plane, axes, f"{name} {suffix} profile")
        sketch.loop(loops)
        sections.append(sketch.profiles().item(0))
        sketch.sk.isVisible = False
    inp = comp.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.CutFeatureOperation)
    for profile in sections:
        inp.loftSections.add(profile)
    inp.isSolid = True
    inp.participantBodies = [body]
    feature = comp.features.loftFeatures.add(inp)
    if feature is None:
        raise RuntimeError(f"{name}: panel loft creation failed")
    feature.name = name
    return feature


def cut_socket_flare(comp, body, xy, z0_expr, z1_expr, name):
    """Cut four SCAD-faithful conical socket mouths as native paired lofts."""
    outer_plane = oplane(comp, xy, z0_expr, "z", f"{name} outer plane")
    throat_plane = oplane(comp, xy, z1_expr, "z", f"{name} throat plane")
    outer_sk = Sk(comp, outer_plane, "xy", name)
    throat_sk = Sk(comp, throat_plane, "xy", f"{name} throat")
    for loc in all_locators():
        outer_sk.hull(loc, "socket_r + socket_chamfer")
        throat_sk.hull(loc, "socket_r")
    outer_profiles = outer_sk.profiles()
    throat_profiles = throat_sk.profiles()
    outer_sk.sk.isVisible = False
    throat_sk.sk.isVisible = False
    if outer_profiles.count != 4 or throat_profiles.count != 4:
        raise RuntimeError(
            f"{name}: expected four outer/throat profiles, "
            f"got {outer_profiles.count}/{throat_profiles.count}")

    def centroid_xy(profile):
        bb = profile.boundingBox
        return ((bb.minPoint.x + bb.maxPoint.x) * 0.5,
                (bb.minPoint.y + bb.maxPoint.y) * 0.5)

    outer = [(outer_profiles.item(i), centroid_xy(outer_profiles.item(i)))
             for i in range(outer_profiles.count)]
    throat = [(throat_profiles.item(i), centroid_xy(throat_profiles.item(i)))
              for i in range(throat_profiles.count)]
    pairs = []
    for oi, (_, oc) in enumerate(outer):
        for ti, (_, tc) in enumerate(throat):
            pairs.append(((oc[0] - tc[0]) ** 2 + (oc[1] - tc[1]) ** 2, oi, ti))
    pairs.sort(key=lambda item: item[0])
    used_outer, used_throat, matched = set(), set(), []
    for _, oi, ti in pairs:
        if oi in used_outer or ti in used_throat:
            continue
        used_outer.add(oi)
        used_throat.add(ti)
        matched.append((outer[oi][0], throat[ti][0]))
    if len(matched) != 4:
        raise RuntimeError(f"{name}: profile centroid pairing is not one-to-one")

    features = []
    for index, (outer_profile, throat_profile) in enumerate(matched, 1):
        inp = comp.features.loftFeatures.createInput(
            adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.loftSections.add(outer_profile)
        inp.loftSections.add(throat_profile)
        inp.isSolid = True
        inp.participantBodies = [body]
        feature = comp.features.loftFeatures.add(inp)
        if feature is None:
            raise RuntimeError(f"{name} {index}: socket flare loft creation failed")
        feature.name = name if index == 1 else f"{name} {index}"
        features.append(feature)
    return features


def cut_through(comp, sk, profs, wdir, name, participants):
    ext = comp.features.extrudeFeatures
    first = (adsk.fusion.ExtentDirections.PositiveExtentDirection if dot(sk.normal(), wdir) > 0
             else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    last_err = None
    for d in (first, adsk.fusion.ExtentDirections.NegativeExtentDirection
              if first == adsk.fusion.ExtentDirections.PositiveExtentDirection
              else adsk.fusion.ExtentDirections.PositiveExtentDirection):
        inp = ext.createInput(profs, adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(), d)
        inp.participantBodies = participants
        try:
            f = ext.add(inp)
            f.name = name
            return f
        except RuntimeError as e:
            last_err = e
    raise last_err


def oplane(comp, base, expr, axis, name):
    planes = comp.constructionPlanes
    val = ev(expr)
    for e in (expr, f"-({expr})"):
        inp = planes.createInput()
        inp.setByOffset(base, vi(e))
        pl = planes.add(inp)
        o = pl.geometry.origin
        got = (o.x, o.y, o.z)["xyz".index(axis)] / CM
        if abs(got - val) < 1e-4:
            pl.name = name
            return pl
        pl.deleteMe()
    raise RuntimeError(f"plane {name}: cannot place at {axis}={val}")


def combine(comp, target, tools, op, name):
    coll = adsk.core.ObjectCollection.create()
    for t in tools:
        coll.add(t)
    ci = comp.features.combineFeatures.createInput(target, coll)
    ci.operation = op
    ci.isKeepToolBodies = False
    f = comp.features.combineFeatures.add(ci)
    f.name = name
    return f


def einfo(e):
    ev_ = e.evaluator
    _, t0, t1 = ev_.getParameterExtents()
    pts = []
    for t in (t0, (t0 + t1) / 2, t1):
        _, p = ev_.getPointAtParameter(t)
        pts.append((p.x / CM, p.y / CM, p.z / CM))
    line = e.geometry.objectType == adsk.core.Line3D.classType()
    return dict(s=pts[0], m=pts[1], e=pts[2], line=line)


def find_edges(body, pred, expect=None, what=""):
    out = [e for e in body.edges if pred(einfo(e))]
    if expect is not None and len(out) != expect:
        raise RuntimeError(f"edge selection '{what}': expected {expect}, found {len(out)}")
    return out


def near(a, b, tol=0.02):
    return abs(a - b) < tol


def along(inf, axis):
    i = "xyz".index(axis)
    return inf["line"] and all(near(inf["s"][k], inf["e"][k], 1e-4) for k in range(3) if k != i)


def fillet(comp, edges, r, name):
    done = 0
    for i, e in enumerate(edges):
        coll = adsk.core.ObjectCollection.create()
        coll.add(e)
        fi = comp.features.filletFeatures.createInput()
        try:
            fi.edgeSetInputs.addConstantRadiusEdgeSetInput(coll, vi(r), False)
        except AttributeError:
            fi.addConstantRadiusEdgeSet(coll, vi(r), False)
        try:
            f = comp.features.filletFeatures.add(fi)
            f.name = f"{name} {i + 1}"
            done += 1
        except RuntimeError:
            continue
    if done == 0:
        raise RuntimeError(f"{name}: no edge accepted a fillet ({len(edges)} candidates)")
    return done


def chamfer(comp, edges, d, name):
    cf = comp.features.chamferFeatures

    def apply(group, suffix):
        coll = adsk.core.ObjectCollection.create()
        for e in group:
            coll.add(e)
        try:
            ci = cf.createInput2()
            ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(coll, vi(d), True)
        except AttributeError:
            ci = cf.createInput(coll, True)
            ci.setToEqualDistance(vi(d))
        f = cf.add(ci)
        f.name = name + suffix
        return f

    try:
        return apply(edges, "")
    except RuntimeError:
        done = 0
        for i, e in enumerate(edges):
            try:
                apply([e], f" {i + 1}")
                done += 1
            except RuntimeError:
                continue
        if done == 0:
            raise RuntimeError(f"{name}: no edge accepted a chamfer ({len(edges)} candidates)")
        return done


def hull_dist(p, cs):
    """Signed distance from 2D point p to the convex hull of centres cs (negative inside)."""
    def seg(p, a, b):
        ax, ay = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / (ax * ax + ay * ay)))
        return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)
    if len(cs) == 2:
        return seg(p, cs[0], cs[1])
    d = min(seg(p, cs[i], cs[(i + 1) % len(cs)]) for i in range(len(cs)))
    s = [((cs[(i + 1) % len(cs)][0] - cs[i][0]) * (p[1] - cs[i][1])
          - (cs[(i + 1) % len(cs)][1] - cs[i][1]) * (p[0] - cs[i][0])) for i in range(len(cs))]
    inside = all(v >= 0 for v in s) or all(v <= 0 for v in s)
    return -d if inside else d


def locators(backside):
    out = []
    for shape in (TRI, SLOT):
        out.append([(a, back(b) if backside else b) for a, b in shape])
    return out


def all_locators():
    return locators(False) + locators(True)


def loop_seeds(body, z, r, what):
    """One edge per locator loop at height z on the outline offset by r (for tangent-chain chamfers)."""
    seeds = []
    for loc in all_locators():
        cs = [(ev(a), ev(b)) for a, b in loc]
        hit = find_edges(body, lambda inf: all(near(p[2], z, 1e-3) for p in (inf["s"], inf["m"], inf["e"]))
                         and abs(hull_dist(inf["m"][:2], cs) - r) < 0.02)
        if not hit:
            raise RuntimeError(f"{what}: no edge on locator outline at z={z}")
        seeds.append(hit[0])
    return seeds


def window_loop(sk):
    pts = [("15 mm + win_corner", "24 mm"), ("plate_w - 20 mm - win_corner", "24 mm"),
           ("plate_w - 20 mm", "24 mm + win_corner"), ("plate_w - 20 mm", "span - 24 mm - win_corner"),
           ("plate_w - 20 mm - win_corner", "span - 24 mm"), ("15 mm + win_corner", "span - 24 mm"),
           ("15 mm", "span - 24 mm - win_corner"), ("15 mm", "24 mm + win_corner")]
    sk.loop(filleted(pts, ["win_fillet"] * 8))


def window_chamfer(comp, body, name):
    W = ev("plate_w")
    seeds = []
    for z in (0.0, ev("plate_t")):
        seeds += find_edges(body, lambda inf: along(inf, "x") and near(inf["m"][1], 24) and near(inf["m"][2], z, 1e-3)
                            and 20 < inf["m"][0] < W - 25, 1, f"window edge z={z}")
    return chamfer(comp, seeds, "win_chamfer", name)


# ---------------------------------------------------------------- parts
def build_cap(comp):
    stage("cap: plate")
    xy = comp.xYConstructionPlane
    sk = Sk(comp, xy, "xy", "cap plate")
    sk.loop(filleted([("0 mm", "0 mm"), ("plate_w", "0 mm"), ("plate_w", "span - plate_trim"), ("0 mm", "span - plate_trim")],
                     [None, "corner_r", "corner_r", None]))
    f = extrude(comp, sk, sk.profiles(), "plate_t", adsk.fusion.FeatureOperations.NewBodyFeatureOperation, V(0, 0, 1), "cap plate")
    body = f.bodies.item(0)
    body.name = "cap"
    stage("cap: window")
    sk = Sk(comp, xy, "xy", "cap window")
    window_loop(sk)
    extrude(comp, sk, sk.profiles(), "plate_t", adsk.fusion.FeatureOperations.CutFeatureOperation, V(0, 0, 1), "cap window", participants=[body])
    window_chamfer(comp, body, "cap window chamfer")
    stage("cap: sockets")
    top = oplane(comp, xy, "plate_t", "z", "cap top")
    sk = Sk(comp, top, "xy", "cap sockets")
    for loc in all_locators():
        sk.hull(loc, "socket_r")
    extrude(comp, sk, sk.profiles(), "socket_depth", adsk.fusion.FeatureOperations.CutFeatureOperation, V(0, 0, -1), "cap sockets", participants=[body])
    cut_socket_flare(comp, body, xy, "plate_t", "plate_t - socket_chamfer", "cap socket flare")
    return body


def build_frame(comp):
    J = adsk.fusion.FeatureOperations.JoinFeatureOperation
    C = adsk.fusion.FeatureOperations.CutFeatureOperation
    xy, xz, yz = comp.xYConstructionPlane, comp.xZConstructionPlane, comp.yZConstructionPlane
    stage("frame: plate")
    sk = Sk(comp, xy, "xy", "frame plate")
    sk.loop(filleted([("0 mm", "plate_trim"), ("plate_w", "plate_trim"), ("plate_w", "span"), ("0 mm", "span")],
                     [None, "corner_r", "corner_r", None]))
    f = extrude(comp, sk, sk.profiles(), "plate_t", adsk.fusion.FeatureOperations.NewBodyFeatureOperation, V(0, 0, 1), "frame plate")
    body = f.bodies.item(0)
    body.name = "frame"
    top = oplane(comp, xy, "plate_t", "z", "plate top")

    stage("frame: rails")
    sk = Sk(comp, top, "xy", "frame rails")
    sk.poly([("7.5 mm", "plate_trim"), ("plate_w - 11.5 mm", "plate_trim"), ("plate_w - 11.5 mm", "rail_w"), ("7.5 mm", "rail_w")])
    sk.poly([("7.5 mm", back("rail_w")), ("plate_w - 11.5 mm", back("rail_w")), ("plate_w - 11.5 mm", "span"), ("7.5 mm", "span")])
    sk.poly([("plate_w - side_rail_w", "12 mm"), ("plate_w", "12 mm"), ("plate_w", back("12 mm")), ("plate_w - side_rail_w", back("12 mm"))])
    extrude(comp, sk, sk.profiles(), "rail_top - plate_t", J, V(0, 0, 1), "frame rails", participants=[body])

    stage("frame: ledges")
    sk = Sk(comp, top, "xy", "frame ledges")
    sk.poly([("0 mm", "rail_w"), ("plate_w - side_rail_w", "rail_w"), ("plate_w - side_rail_w", "rail_w + ledge_w"), ("0 mm", "rail_w + ledge_w")])
    sk.poly([("0 mm", back("rail_w + ledge_w")), ("plate_w - side_rail_w", back("rail_w + ledge_w")),
             ("plate_w - side_rail_w", back("rail_w")), ("0 mm", back("rail_w"))])
    extrude(comp, sk, sk.profiles(), "ledge_h", J, V(0, 0, 1), "frame ledges", participants=[body])

    stage("frame: posts")
    sk = Sk(comp, top, "xy", "frame posts")
    for bk in (False, True):
        y = (lambda e: back(e)) if bk else (lambda e: e)
        y0 = "span" if bk else "plate_trim"
        sk.poly([("0 mm", y0), ("xpost_len", y0), ("xpost_len", y("rail_w")), ("0 mm", y("rail_w"))])
        pts = [("plate_w - arm_x", y0), ("plate_w", y0), ("plate_w", y("arm_y")), ("plate_w - side_rail_w", y("arm_y")),
               ("plate_w - side_rail_w", y("rail_w + 10.2 mm")), ("plate_w - side_rail_w - 10.2 mm", y("rail_w")),
               ("plate_w - arm_x", y("rail_w"))]
        sk.loop(filleted(pts, [None, "corner_r", None, None, None, None, None]))
    extrude(comp, sk, sk.profiles(), "post_top - plate_t", J, V(0, 0, 1), "frame posts", participants=[body])

    stage("frame: gussets")
    g = "rail_top + gusset_leg"
    pl = oplane(comp, xz, "plate_trim", "y", "front rail face")
    sk = Sk(comp, pl, "xz", "front gussets")
    sk.poly([("xpost_len", "rail_top"), ("xpost_len + gusset_leg", "rail_top"), ("xpost_len", g)])
    sk.poly([("plate_w - arm_x", "rail_top"), ("plate_w - arm_x", g), ("plate_w - arm_x - gusset_leg", "rail_top")])
    extrude(comp, sk, sk.profiles(), "rail_w - plate_trim", J, V(0, 1, 0), "front gussets", participants=[body])
    pl = oplane(comp, xz, back("rail_w"), "y", "back rail face")
    sk = Sk(comp, pl, "xz", "back gussets")
    sk.poly([("xpost_len", "rail_top"), ("xpost_len + gusset_leg", "rail_top"), ("xpost_len", g)])
    sk.poly([("plate_w - arm_x", "rail_top"), ("plate_w - arm_x", g), ("plate_w - arm_x - gusset_leg", "rail_top")])
    extrude(comp, sk, sk.profiles(), "rail_w", J, V(0, 1, 0), "back gussets", participants=[body])
    pl = oplane(comp, yz, "plate_w - side_rail_w", "x", "side rail face")
    sk = Sk(comp, pl, "yz", "side gussets")
    sk.poly([("arm_y", "rail_top"), ("arm_y + gusset_leg", "rail_top"), ("arm_y", g)])
    sk.poly([(back("arm_y"), "rail_top"), (back("arm_y"), g), (back("arm_y + gusset_leg"), "rail_top")])
    extrude(comp, sk, sk.profiles(), "side_rail_w", J, V(1, 0, 0), "side gussets", participants=[body])

    stage("frame: gusset fillets")
    W, L, T, G = ev("plate_w"), ev("span"), ev("rail_top"), ev("gusset_leg")
    xp, ax, ay = ev("xpost_len"), ev("arm_x"), ev("arm_y")
    xz_pts = [(xp + G, T), (xp, T + G), (W - ax - G, T), (W - ax, T + G)]
    yz_pts = [(ay + G, T), (ay, T + G), (L - ay - G, T), (L - ay, T + G)]
    edges = find_edges(body, lambda inf: along(inf, "y") and any(near(inf["m"][0], a) and near(inf["m"][2], b) for a, b in xz_pts),
                       8, "front/back gusset concave edges")
    edges += find_edges(body, lambda inf: along(inf, "x") and inf["m"][0] > W - 8.5 and
                        any(near(inf["m"][1], a) and near(inf["m"][2], b) for a, b in yz_pts), 4, "side gusset concave edges")
    try:
        fillet(comp, edges, "gusset_r", "gusset fillets")
    except RuntimeError:
        pass  # concave radius is cosmetic; sharp gusset still stacks and holds the bin

    stage("frame: rail chamfers")
    tr, rw, srw = ev("plate_trim"), ev("rail_w"), ev("side_rail_w")
    seeds = []
    for yy in (tr, rw, L - rw, L):
        seeds += find_edges(body, lambda inf: along(inf, "x") and near(inf["m"][1], yy) and near(inf["m"][2], T)
                            and 30 < inf["m"][0] < W - 40, 1, f"rail top edge y={yy}")
    for xx in (W - srw, W):
        seeds += find_edges(body, lambda inf: along(inf, "y") and near(inf["m"][0], xx) and near(inf["m"][2], T)
                            and 40 < inf["m"][1] < L - 40, 1, f"side rail top edge x={xx}")
    chamfer(comp, seeds, "rail_chamfer", "rail chamfers")

    stage("frame: window")
    sk = Sk(comp, xy, "xy", "frame window")
    window_loop(sk)
    extrude(comp, sk, sk.profiles(), "plate_t", C, V(0, 0, 1), "frame window", participants=[body])
    window_chamfer(comp, body, "frame window chamfer")

    stage("frame: sockets")
    sk = Sk(comp, xy, "xy", "frame sockets")
    for loc in all_locators():
        sk.hull(loc, "socket_r")
    extrude(comp, sk, sk.profiles(), "socket_depth", C, V(0, 0, 1), "frame sockets", participants=[body])
    cut_socket_flare(comp, body, xy, "0 mm", "socket_chamfer", "frame socket flare")

    stage("frame: tips")
    ptop = oplane(comp, xy, "post_top", "z", "post top")
    sk = Sk(comp, ptop, "xy", "frame tips")
    for loc in all_locators():
        sk.hull(loc, "tip_r")
    extrude(comp, sk, sk.profiles(), "tip_h - tip_chamfer", J, V(0, 0, 1), "frame tips", participants=[body])
    for index, loc in enumerate(all_locators(), 1):
        loft_hull(comp, xy, loc, "post_top", "tip_r + tip_flare",
                  "post_top + tip_flare", "tip_r", f"tip flare {index}")
        loft_hull(comp, xy, loc, "post_top + tip_h - tip_chamfer", "tip_r",
                  "post_top + tip_h", "tip_r - tip_chamfer", f"tip crest {index}")

    stage("frame: notch")
    tab = [(23.5, 0), (23.5, 1.4), (21.35, 3.55), (21.35, 5), (24, 5.5), (24, 7)]
    outline = tab + [(-x, y) for x, y in reversed(tab)]

    def tab_pts(y0):
        return [(f"plate_w / 2 - 1 mm + {x} mm" if x >= 0 else f"plate_w / 2 - 1 mm - {-x} mm", f"{y0} + {y} mm") for x, y in outline]
    sk = Sk(comp, xy, "xy", "notch")
    sk.poly(tab_pts("span - 5 mm"))
    extrude(comp, sk, sk.profiles(), "rail_top + 1 mm", C, V(0, 0, 1), "notch", participants=[body])

    stage("frame: tab")
    sk = Sk(comp, xy, "xy", "tab")
    sk.poly(tab_pts("plate_trim - 5 mm"))
    f = extrude(comp, sk, sk.profiles(), "plate_t", adsk.fusion.FeatureOperations.NewBodyFeatureOperation, V(0, 0, 1), "tab")
    tab_body = f.bodies.item(0)
    sk = Sk(comp, yz, "yz", "tab slope")
    sk.poly([("plate_trim - 6 mm", "5.8566 mm"), ("plate_trim", "7.857 mm"), ("plate_trim", "20 mm"), ("plate_trim - 6 mm", "20 mm")])
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles(), C)
    inp.setSymmetricExtent(vi("1000 mm"), True)
    inp.participantBodies = [tab_body]
    ext.add(inp).name = "tab slope"
    combine(comp, body, [tab_body], J, "join tab")

    stage("frame: scoops")
    sk = Sk(comp, xz, "xz", "scoop profile")
    sgk = sk.sk
    D = SCOOP_D
    z0 = 31.19 - math.sqrt(2 * 35.5 * D - D * D)
    zf1 = ev("post_top") - 33.19
    z1 = zf1 + math.sqrt(2 * 33 * D - D * D)

    def arc(c_e, r_e, pa, pb):
        c = (ev(c_e[0]), ev(c_e[1]))
        cs, sa, sb = sk.m2s(c[0] * CM, c[1] * CM), sk.m2s(pa[0] * CM, pa[1] * CM), sk.m2s(pb[0] * CM, pb[1] * CM)
        a0 = math.atan2(sa[1] - cs[1], sa[0] - cs[0])
        a1 = math.atan2(sb[1] - cs[1], sb[0] - cs[0])
        sw = (a1 - a0) % (2 * math.pi)
        start = sa
        if sw > math.pi:
            sw, start = 2 * math.pi - sw, sb
        a = sgk.sketchCurves.sketchArcs.addByCenterStartSweep(P(*cs), P(*start), sw)
        try:
            sk.fix(a.centerSketchPoint, *c_e)
        except RuntimeError:
            pass
        try:
            rd = sgk.sketchDimensions.addRadialDimension(a, P(cs[0] + 0.5, cs[1] + 0.5))
            rd.parameter.expression = r_e
        except RuntimeError:
            pass

        def at(p):
            q = sk.m2s(p[0] * CM, p[1] * CM)
            s, e = a.startSketchPoint.geometry, a.endSketchPoint.geometry
            return a.startSketchPoint if math.hypot(s.x - q[0], s.y - q[1]) < math.hypot(e.x - q[0], e.y - q[1]) else a.endSketchPoint
        return at(pa), at(pb)

    p1, p2 = arc((f"{D - 35.5:.6f} mm", "31.19 mm"), "35.5 mm", (0.0, z0), (D, 31.19))
    p3, p4 = arc((f"{D - 33:.6f} mm", "post_top - 33.19 mm"), "33 mm", (D, zf1), (0.0, z1))
    gc = sgk.geometricConstraints
    for a, b in ((sgk.originPoint, p1), (sgk.originPoint, p4)):
        try:
            gc.addVerticalPoints(a, b)
        except RuntimeError:
            pass
    for args in ((p2, "31.19 mm", 31.19, not sk.u_is_x), (p3, "post_top - 33.19 mm", zf1, not sk.u_is_x)):
        try:
            sk._dim(*args)
        except RuntimeError:
            pass
    p0 = sgk.sketchPoints.add(P(*sk.m2s(-5 * CM, z0 * CM)))
    p5 = sgk.sketchPoints.add(P(*sk.m2s(-5 * CM, z1 * CM)))
    for args in ((p0, "-5 mm", -5.0, sk.u_is_x), (p5, "-5 mm", -5.0, sk.u_is_x)):
        try:
            sk._dim(*args)
        except RuntimeError:
            pass
    lines = sgk.sketchCurves.sketchLines
    l01 = lines.addByTwoPoints(p0, p1)
    lines.addByTwoPoints(p2, p3)
    l45 = lines.addByTwoPoints(p4, p5)
    lines.addByTwoPoints(p5, p0)
    if sk.u_is_x:
        gc.addHorizontal(l01); gc.addHorizontal(l45)
    else:
        gc.addVertical(l01); gc.addVertical(l45)
    profs = sk.profiles()
    cutters = []
    for ang, ye in ((135, "0 mm"), (225, "span")):
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profs, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setSymmetricExtent(vi(f"{4 * 13.31} mm"), True)
        f = ext.add(inp)
        f.name = f"scoop cutter {ang}"
        cb = f.bodies.item(0)
        bodies = adsk.core.ObjectCollection.create()
        bodies.add(cb)
        mv = comp.features.moveFeatures
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(ang), V(0, 0, 1), P(0, 0, 0))
        mi = mv.createInput2(bodies)
        mi.defineAsFreeMove(m)
        mv.add(mi).name = f"scoop rotate {ang}"
        mi = mv.createInput2(bodies)
        mi.defineAsTranslateXYZ(vi("plate_w"), vi(ye), vi("0 mm"), False)
        mv.add(mi).name = f"scoop place {ang}"
        cutters.append(cb)
    combine(comp, body, cutters, C, "scoops")
    return body


def build_bin(comp):
    NB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    I = adsk.fusion.FeatureOperations.IntersectFeatureOperation
    C = adsk.fusion.FeatureOperations.CutFeatureOperation
    xy, xz, yz = comp.xYConstructionPlane, comp.xZConstructionPlane, comp.yZConstructionPlane

    def prism(plane, axes, loops, dist, wdir, name):
        sk = Sk(comp, plane, axes, name)
        for lp in loops:
            sk.loop(lp)
        f = extrude(comp, sk, sk.profiles(), dist, NB, wdir, name)
        return f.bodies.item(0)

    stage("bin: outer")
    outer_xz = [("10 mm", "0 mm"), ("bin_W - 10 mm", "0 mm"), ("bin_W", "10 mm"), ("bin_W", "bin_H - 30 mm"),
                ("bin_W - 5 mm", "bin_H"), ("5 mm", "bin_H"), ("0 mm", "bin_H - 30 mm"), ("0 mm", "10 mm")]
    body = prism(xz, "xz", [filleted(outer_xz, [None, None, "bin_chamfer_r", None, None, None, None, "bin_chamfer_r"])],
                 "bin_D", V(0, 1, 0), "bin outer XZ")
    body.name = "bin"
    b = prism(yz, "yz", [[(a, c, None) for a, c in [("4 mm", "0 mm"), ("bin_D", "0 mm"), ("bin_D", "bin_H - 30 mm"), ("bin_D - 20 mm", "bin_H"),
                                                     ("20 mm", "bin_H"), ("0 mm", "bin_H - 20 mm"), ("0 mm", "8.25 mm"), ("4 mm", "4.25 mm")]]],
              "bin_W", V(1, 0, 0), "bin outer YZ")
    combine(comp, body, [b], I, "bin outer YZ")
    b = prism(xy, "xy", [[(a, c, None) for a, c in [("4.26 mm", "0 mm"), ("bin_W - 4.26 mm", "0 mm"), ("bin_W - 4.26 mm", "4 mm"),
                                                     ("bin_W", "4 mm"), ("bin_W", "bin_D"), ("0 mm", "bin_D"), ("0 mm", "4 mm"), ("4.26 mm", "4 mm")]]],
              "bin_H", V(0, 0, 1), "bin plan")
    combine(comp, body, [b], I, "bin plan")

    stage("bin: facet planes")
    top = oplane(comp, xy, "bin_H", "z", "bin top")
    sa = Sk(comp, xz, "xz", "facet points side")
    sc = Sk(comp, top, "xy", "facet points top")
    pts = []
    for right in (True, False):
        x0 = "bin_W" if right else "0 mm"
        xb = "bin_W - 43.552 mm" if right else "43.552 mm"
        pts.append((right, sa.point(x0, "bin_H - 27.22 mm"), sa.point(xb, "bin_H"), sc.point(x0, "43.552 mm")))
    sa.sk.isComputeDeferred = False
    sc.sk.isComputeDeferred = False
    facets = []
    for right, pa, pb, pc in pts:
        inp = comp.constructionPlanes.createInput()
        inp.setByThreePoints(pa, pb, pc)
        pl = comp.constructionPlanes.add(inp)
        pl.name = "facet " + ("+X" if right else "-X")
        n = V(0.625 if right else -0.625, -0.625, 1)
        n.normalize()
        facets.append((pl, n))

    def facet_cut(pl, n, target, name):
        sk = Sk.__new__(Sk)
        sk.comp, sk.sk = comp, comp.sketches.add(pl)
        sk.sk.name = name
        ci = sk.sk.sketchCurves.sketchCircles.addByCenterRadius(sk.sk.originPoint, 200.0)
        sk.sk.sketchDimensions.addDiameterDimension(ci, P(10, 10)).parameter.expression = "4000 mm"
        v0 = target.physicalProperties.volume
        f = None
        for wdir in (n, V(-n.x, -n.y, -n.z)):
            try:
                f = extrude(comp, sk, sk.profiles(), "200 mm", C, wdir, name, participants=[target])
            except RuntimeError:
                continue
            if target.physicalProperties.volume > v0 * 0.8:
                return f
            f.deleteMe()
            f = None
        if f is None:
            return None

    for pl, n in facets:
        facet_cut(pl, n, body, pl.name + " cut")

    stage("bin: cavity")
    cav = prism(xz, "xz", [[(a, c, None) for a, c in [("12 mm", "4 mm"), ("bin_W - 12 mm", "4 mm"), ("bin_W - 4 mm", "12 mm"),
                                                       ("bin_W - 4 mm", "bin_H - 30 mm"), ("bin_W - 11.5 mm", "bin_H + 15 mm"),
                                                       ("11.5 mm", "bin_H + 15 mm"), ("4 mm", "bin_H - 30 mm"), ("4 mm", "12 mm")]]],
                "bin_D + 2 mm", V(0, 1, 0), "cavity XZ")
    cav.name = "cavity"
    b = prism(yz, "yz", [[(a, c, None) for a, c in [("4 mm", "12 mm"), ("12 mm", "4 mm"), ("bin_D + 1 mm", "4 mm"),
                                                     ("bin_D + 1 mm", "bin_H + bin_D - 24.657 mm"), ("4 mm", "bin_H - 21.657 mm")]]],
              "bin_W", V(1, 0, 0), "cavity YZ")
    combine(comp, cav, [b], I, "cavity YZ")
    b = prism(xy, "xy", [[(a, c, None) for a, c in [("4 mm", "11 mm"), ("11 mm", "4 mm"), ("bin_W - 11 mm", "4 mm"),
                                                     ("bin_W - 4 mm", "11 mm"), ("bin_W - 4 mm", "bin_D + 1 mm"), ("4 mm", "bin_D + 1 mm")]]],
              "bin_H + 14 mm", V(0, 0, 1), "cavity plan")
    combine(comp, cav, [b], I, "cavity plan")
    for pl, n in facets:
        planes = comp.constructionPlanes
        o0 = pl.geometry.origin
        for e in ("bin_wall", "-bin_wall"):
            inp = planes.createInput()
            inp.setByOffset(pl, vi(e))
            ip = planes.add(inp)
            o = ip.geometry.origin
            if dot(V(o.x - o0.x, o.y - o0.y, o.z - o0.z), n) < 0:
                break
            ip.deleteMe()
        ip.name = pl.name + " inset"
        facet_cut(ip, n, cav, ip.name + " cut")
    combine(comp, body, [cav], C, "hollow")

    stage("bin: panels")
    floor_inset = "2.5 * panel_depth"
    fl = oplane(comp, xy, "bin_floor", "z", "bin floor surface")
    floor_inner = oplane(comp, xy, "bin_floor - panel_depth", "z", "bin floor inset")
    floor_loops = [
        rrect("17 mm", "17 mm", "bin_W / 2 - 5 mm", "74 mm + (bin_D - 80 mm)", "9 mm"),
        rrect("bin_W / 2 + 5 mm", "17 mm", "bin_W - 17 mm", "74 mm + (bin_D - 80 mm)", "9 mm"),
    ]
    floor_inner_loops = [
        rrect("17 mm + (" + floor_inset + ")", "17 mm + (" + floor_inset + ")",
              "(bin_W / 2 - 5 mm) - (" + floor_inset + ")",
              "(74 mm + (bin_D - 80 mm)) - (" + floor_inset + ")",
              "9 mm - (" + floor_inset + ")"),
        rrect("(bin_W / 2 + 5 mm) + (" + floor_inset + ")", "17 mm + (" + floor_inset + ")",
              "(bin_W - 17 mm) - (" + floor_inset + ")",
              "(74 mm + (bin_D - 80 mm)) - (" + floor_inset + ")",
              "9 mm - (" + floor_inset + ")"),
    ]
    for index in range(2):
        cut_panel_loft(comp, body, fl, floor_inner, "xy", floor_loops[index], floor_inner_loops[index],
                       f"floor panel {index + 1}")

    back_surface = xz
    back_inner = oplane(comp, xz, "panel_depth", "y", "back panel inset")
    back_loops = [
        rrect("10.2 mm", "13.7 mm", "bin_W / 2 - 5 mm", "bin_H - 25 mm", "6.6 mm"),
        rrect("bin_W / 2 + 5 mm", "13.7 mm", "bin_W - 10.2 mm", "bin_H - 25 mm", "6.6 mm"),
    ]
    back_inner_loops = [
        rrect("10.2 mm + (" + floor_inset + ")", "13.7 mm + (" + floor_inset + ")",
              "(bin_W / 2 - 5 mm) - (" + floor_inset + ")",
              "(bin_H - 25 mm) - (" + floor_inset + ")",
              "6.6 mm - (" + floor_inset + ")"),
        rrect("(bin_W / 2 + 5 mm) + (" + floor_inset + ")", "13.7 mm + (" + floor_inset + ")",
              "(bin_W - 10.2 mm) - (" + floor_inset + ")",
              "(bin_H - 25 mm) - (" + floor_inset + ")",
              "6.6 mm - (" + floor_inset + ")"),
    ]
    for index in range(2):
        cut_panel_loft(comp, body, back_surface, back_inner, "xz", back_loops[index], back_inner_loops[index],
                       f"back panel {index + 1}")

    # Side-wall Y panels retain their measured profile and are intentionally a
    # separate follow-up from the deterministic floor/back pockets above.
    def side_panel_cut(sk, wdir, slope, name):
        profs = sk.profiles()
        area = sum(p.areaProperties().area for p in profs) / CM ** 2
        v0 = body.physicalProperties.volume / CM ** 3
        ang = math.degrees(math.atan(slope))
        budget = area * ev("panel_depth")
        flip = V(-wdir.x, -wdir.y, -wdir.z)
        attempts = [(wdir, f"{s * ang:.6f} deg") for s in (-1, 1)] + [(flip, f"{s * ang:.6f} deg") for s in (-1, 1)]
        attempts += [(wdir, None), (flip, None)]
        for direc, taper in attempts:
            try:
                f = extrude(comp, sk, profs, "panel_depth", C, direc, name, taper=taper, participants=[body])
            except RuntimeError:
                continue
            dv = v0 - body.physicalProperties.volume / CM ** 3
            if 0 < dv < budget * 1.5:
                return f
            f.deleteMe()
        return None

    m, zc, y0, y1, z0, z1 = -1.2649, 58.95, 10.035, 66.435, 17.94, 56.41
    q1 = [(y0, z0), (y1, z0), (y1, 54.53 + m * (y1 - 42.765)), (42.765 + (z1 - 54.53) / m, z1), (y0, z1)]
    q2 = [(y, 2 * zc - z) for y, z in reversed(q1)]
    q3 = [(45.76, zc), (74.965, 22.016), (74.965, 2 * zc - 22.016)]

    def side_expr(y, z):
        ye = f"{y} mm" + (" + (bin_D - 80 mm)" if y > 30 else "")
        ze = f"{z} mm" + (" + (bin_H - 135 mm) / 2" if z > 20 else "") + (" + (bin_H - 135 mm) / 2" if z > 2 * zc - 20 else "")
        return ye, ze

    def side_loops():
        out = []
        for q in (q1, q2, q3):
            pts = [side_expr(y, z) for y, z in q]
            out.append([(a, b, "5.2 mm") for a, b in pts])
        return out

    for name, plane, wdir in (("side panels -X", yz, V(1, 0, 0)), ("side panels +X", oplane(comp, yz, "bin_W", "x", "bin end"), V(-1, 0, 0))):
        sk = Sk(comp, plane, "yz", name)
        for lp in side_loops():
            sk.loop(lp)
        side_panel_cut(sk, wdir, 1.0, name)
    return body


# ---------------------------------------------------------------- main
def report_path():
    try:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "native-report.json")
    except NameError:
        return None


def measure(design):
    out = {}
    for occ in design.rootComponent.occurrences:
        for b in occ.component.bRepBodies:
            bb = b.boundingBox
            out[b.name] = dict(
                volume_mm3=round(b.physicalProperties.volume / CM ** 3, 3),
                size_mm=[round((bb.maxPoint.x - bb.minPoint.x) / CM, 4), round((bb.maxPoint.y - bb.minPoint.y) / CM, 4),
                         round((bb.maxPoint.z - bb.minPoint.z) / CM, 4)],
                solid=b.isSolid, faces=b.faces.count)
    bad = []
    tl = design.timeline
    for i in range(tl.count):
        it = tl.item(i)
        if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            bad.append([it.name, str(it.healthState), it.errorOrWarningMessage])
    return dict(bodies=out, timeline=tl.count, unhealthy=bad)


def placement_plan(pose):
    """Fixed print-to-assembly rotations and live translation expressions."""
    if pose == 'assembly':
        return {
            'frame': {'rotation':None,'translation':('0 mm','0 mm','0 mm')},
            'cap': {'rotation':(180,(1,0,0)),'translation':('0 mm','span','post_top + plate_t')},
            'bin': {'rotation':(120,(1,-1,-1)),'translation':('plate_w - side_rail_w','(span + bin_W) / 2','plate_t')},
        }
    if pose == 'layout':
        return {
            'cap': {'rotation':None,'translation':('3 mm','65.179 mm','0 mm')},
            'frame': {'rotation':None,'translation':('plate_w + 5 mm','29.465 mm','0 mm')},
            'bin': {'rotation':None,'translation':('plate_w + 29 mm','span + 31.465 mm','0 mm')},
        }
    raise ValueError('pose must be assembly or layout')


def place_parts(comps, pose):
    expressions={}
    for name, spec in placement_plan(pose).items():
        comp=comps[name].component
        if comp.bRepBodies.count != 1:
            raise RuntimeError(f'{name}: expected one body before placement')
        coll=adsk.core.ObjectCollection.create()
        coll.add(comp.bRepBodies.item(0))
        moves=comp.features.moveFeatures
        if spec['rotation']:
            angle,axis=spec['rotation']
            matrix=adsk.core.Matrix3D.create()
            matrix.setToRotation(math.radians(angle),V(*axis),P(0,0,0))
            inp=moves.createInput2(coll)
            inp.defineAsFreeMove(matrix)
            moves.add(inp).name=name+' assembly orientation'
        xyz=spec['translation']
        if xyz != ('0 mm','0 mm','0 mm'):
            inp=moves.createInput2(coll)
            inp.defineAsTranslateXYZ(*(vi(e) for e in xyz),False)
            feature=moves.add(inp)
            feature.name=name+' '+pose+' position'
            definition=adsk.fusion.MoveFeatureTranslateXYZDefinition.cast(feature.definition)
            expressions[name]=[definition.xDistance.expression,definition.yDistance.expression,definition.zDistance.expression]
    return expressions


def build(app, pose=None):
    pose=BUILD_POSE if pose is None else pose
    placement_plan(pose)
    stage("document")
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    Ctx.design, Ctx.um = design, design.unitsManager
    stage("parameters")
    for name, expr, unit, comment in PARAMS:
        design.userParameters.add(name, vi(expr), unit, comment)
    root = design.rootComponent
    comps = {}
    for name, builder in (("cap", build_cap), ("frame", build_frame), ("bin", build_bin)):
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        comps[name] = occ
        builder(occ.component)
    stage(pose+' placement')
    design.activateRootComponent()
    expressions=place_parts(comps,pose)
    design.timeline.moveToEnd()
    design.activateRootComponent()
    for comp in design.allComponents:
        for sketch in comp.sketches:
            sketch.isVisible=False
    info = dict(source_sha256=SOURCE_SHA256, fusion=app.version, pose=pose,
                placement_expressions=expressions, **measure(design))
    rp = report_path()
    if rp:
        with open(rp, "w", encoding="utf-8") as fh:
            json.dump(info, fh, indent=2)
    return info


def run(context):
    app = adsk.core.Application.get()
    try:
        info = build(app)
    except Exception as e:
        msg = f"Stackable Bin Rack build failed at stage '{STAGE[0]}': {e}"
        if isinstance(context, str):
            raise RuntimeError(msg) from e
        app.userInterface.messageBox(msg + "\n\n" + traceback.format_exc())
        return
    print(json.dumps(info))
    if not isinstance(context, str):
        app.userInterface.messageBox(f"Stackable Bin Rack built: {len(info['bodies'])} bodies, {len(info['unhealthy'])} timeline warnings")
