// Stackable Bin Rack: stackable frame, cap plate and jerry-can drawer box,
// rebuilt as parametric CSG from bb_file.stl (SHA-256 886E3A97?3AB0FB).
// Units: mm. Plate parts: X = width, Y = depth, Z = up; feature coordinates
// keep locators/window centred on plate_d/2 (see plate_trim).

part = "assembly"; // [layout, cap, frame, bin, stand, stand_bin, assembly, assembly_bin]
// Size in cells: [length (along the dovetail row), width (rack depth), height (stack pitch)]; 1x1x1 = bb_file.stl.
// In-use bin dimensions: [100*size.x, 100*size.y+35, 80*size.z] mm.
// The 35 mm nose, wall thickness and mating features stay fixed across sizes.
// Each part keeps its print pose from bb_file.stl, so one rack axis maps to different part axes:
//   length -> cap/frame Y, bin X;  width -> cap/frame X, bin Z;  height -> frame Z, bin Y (cap: none).
// Corner features keep their size; n-long spans follow the 100 mm bin length, while joined singles use pitch_y.
size = [1, 1, 1];

/* [Assembly preview] */
asm_spec = [[size[0]]];     // rows bottom-up; override with [[1, 2], [1, 2]] for matching mixed rows
asm_bins = true;
asm_stand = true;      // feet under the bottom row; air gap is foot_h
bin_gap = 0;           // gap between bin bottom and +X rail
fn = 64;

/* [Plate shared by cap and frame] */
cell = [120, 124, 91];  // one-cell plate depth (Y), plate width (X), stack pitch (Z)
dx = (size[1] - 1) * 100;
dz = (size[2] - 1) * 80;
plate_w = cell[1] + dx;
plate_d = cell[0];      // per-cell; n-long parts use span(n)
plate_t = 8;
plate_trim = 0.07;      // MEASURED: plates are 119.93 deep; cap trims back edge, frame trims front edge
plate_corner_r = 2;     // +X vertical corners only
win_size = [89 + dx, 72];    // window at mid-thickness, one cell long
win_center = [plate_w / 2 - 2.5, plate_d / 2];
win_corner = 10;        // 45? corner-cut leg
win_fillet = 5;
win_chamfer = 2;        // 45?, both faces

/* [Stacking locators: triangle at +X, stadium at -X, front + mirrored back] */
tri_vertex = [plate_w - 5, 6];
tri_leg = 9.06;
slot_ends = [4, 11];
slot_y = 5;
tip_r = 2.0;
socket_r = 2.1;         // clearance 0.1 over tip_r
socket_depth = 6;
socket_chamfer = 0.5;
tip_h = 5;
tip_chamfer = 0.75;
tip_flare = 0.5;

/* [Frame] */
foot_h = 20;            // clearance from floor to underside of either stand plate
foot_chamfer = 2;
stand_inset = 4;         // inner stand keeps a 4 mm perimeter clearance
post_top = cell[2] + dz;
rail_w = 9;
side_rail_w = 8;
rail_top = 18;
rail_chamfer = 2;
ledge = [4, 4];         // [width, height] inside front/back rails
xpost_len = 15;         // -X post length along X
arm_len = [23, 24];     // +X post arms: along X, along Y
arm_chamfer = 2;
web_leg = 10.2;         // 45? web in +X post inner corner
gusset_leg = 10;
gusset_r = 5;
scoop_leg = 13.31;      // 45? corner scoop on +X posts
scoop_flat = [31.19, 57.81 + dz];
scoop_r = [35.5, 33];   // run-out radii below / above the flat
dovetail_x = plate_w / 2 - 1;
dovetail_len = 5;
tab_top = [6.19, 7.857]; // tab height at tip / at mouth

/* [Bin] */
bin_size = [100, 80, 135];   // one-cell local [length, depth, height]; height growth keeps a fixed 35 mm nose
bin_wall = 4;
bin_floor = 4;
bin_chamfer = 10;       // 45? bottom chamfer along X sides
bin_chamfer_r = 5;
shoulder_drop = 30;     // shoulder starts this far below the top
shoulder_taper = 6;     // side walls lean in 1:6 above the shoulder
roof_drop = 20;         // 45? roof lip starts this far below the top, at the back face
front_slope = 1.5;      // side-wall front edge drops 1.5 per mm of Y
heel = [4, 4.25];       // back-bottom rebate: Y inset, height
corner_notch = [4.26, 4];
inner_chamfer = 8;
inner_plan_chamfer = 7;
facet_n = [0.625, -0.625, 1];
facet_offset = 35.28;   // roof-corner facet plane on the 1-cell bin: facet_n . p = height + facet_offset
panel_depth = 2;
panel_slope = 2.5;      // floor/back panels: lateral run per mm depth
floor_panel = [[17, 17], [45, 74], 9];   // [min, max, r] at floor surface
back_panel = [[10.2, 13.7], [45, 110], 6.6];
side_r = 5;

eps = 0.01;

assert(foot_h > foot_chamfer + gusset_leg, "stand legs must leave room for the bevel and braces");
assert(stand_inset >= foot_chamfer && stand_inset < min(rail_w, side_rail_w, win_center.x - win_size.x / 2), "stand inset must fit inside the rail and window border");
assert(socket_r > tip_r, "socket must clear tip");
assert(socket_depth > tip_h, "tip must not bottom out");
assert(bin_wall < bin_size.x / 2 && panel_depth < bin_wall);
assert(min(size) >= 1 && size == [for (s = size) round(s)], "size is whole cells, each >= 1");

// ---------- helpers ----------
function _u(v) = v / norm(v);
function _arc(p0, p1, p2, r) =
    let(a = _u(p0 - p1), b = _u(p2 - p1), th = acos(a * b),
        t = r / tan(th / 2), s = p1 + a * t, e = p1 + b * t,
        c = p1 + _u(a + b) * r / sin(th / 2),
        a0 = atan2(s.y - c.y, s.x - c.x), a1 = atan2(e.y - c.y, e.x - c.x),
        da = ((a1 - a0 + 540) % 360) - 180, n = max(1, ceil(abs(da) * fn / 360)))
    [for (i = [0:n]) c + r * [cos(a0 + da * i / n), sin(a0 + da * i / n)]];
function rounded(p, r) = let(n = len(p))
    [for (i = [0:n - 1]) each (r[i] > 0 ? _arc(p[(i + n - 1) % n], p[i], p[(i + 1) % n], r[i]) : [p[i]])];

pitch_y = plate_d - plate_trim;                     // cell pitch when joined by dovetails
// Long frame span adds the 100 mm bin length per cell; adjacent single frames still join at pitch_y.
function span(n) = plate_d + (n - 1) * bin_size.x;
function bin_len(n) = bin_size.x * n;
module sym_y(d = plate_d) { children(); translate([0, d, 0]) mirror([0, 1, 0]) children(); }
module rrect(a, b, r) { translate(a + [r, r]) offset(r = r, $fn = fn) square(b - a - [2 * r, 2 * r]); }
module halfspace(n, d, L = 1000) {
    u = _u(n);
    translate(u * d / norm(n)) rotate([0, acos(u.z), atan2(u.y, u.x)]) translate([-L / 2, -L / 2, -L]) cube(L);
}
// 2D (u,v) profile extruded along w: map (u,v,w) -> world via m
module prism(m, h) { multmatrix(m) linear_extrude(h) children(); }
XZ = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]];   // u->x, v->z, w->y
YZ = [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]];   // u->y, v->z, w->x

// ---------- plate ----------
module footprint(y0, y1) {
    polygon(rounded([[0, y0], [plate_w, y0], [plate_w, y1], [0, y1]], [0, plate_corner_r, plate_corner_r, 0]));
}
module stand_mask(inset, L) {
    if (inset == 0) footprint(plate_trim, L);
    else intersection() {
        footprint(inset, L - inset);
        translate([inset, inset]) square([plate_w - 2 * inset, L - 2 * inset]);
    }
}
module window2d(L = plate_d) {  // one window stretched over the whole plate length
    w = (win_size + [0, L - plate_d]) / 2;
    c = win_corner;
    translate([win_center.x, win_center.y + (L - plate_d) / 2]) polygon(rounded(
        [[-w.x + c, -w.y], [w.x - c, -w.y], [w.x, -w.y + c], [w.x, w.y - c],
         [w.x - c, w.y], [-w.x + c, w.y], [-w.x, w.y - c], [-w.x, -w.y + c]], [for (i = [0:7]) win_fillet]));
}
module window(L = plate_d) {
    translate([0, 0, -eps]) linear_extrude(plate_t + 2 * eps) window2d(L);
    for (z = [0, plate_t]) hull() {
        translate([0, 0, z - eps]) linear_extrude(2 * eps) offset(r = win_chamfer + eps, $fn = fn) window2d(L);
        translate([0, 0, z > 0 ? z - win_chamfer : win_chamfer]) linear_extrude(eps) window2d(L);
    }
}
module loc2d(i, r) {
    if (i == 0) offset(r = r, $fn = fn) polygon([tri_vertex, tri_vertex - [tri_leg, 0], tri_vertex + [0, tri_leg]]);
    else hull() for (x = slot_ends) translate([x, slot_y]) circle(r, $fn = fn);
}
module sockets(d = plate_d) {  // mouth at z = 0, opening downward
    sym_y(d) for (i = [0, 1]) {
        hull() {
            translate([0, 0, -1]) linear_extrude(1) loc2d(i, socket_r + socket_chamfer);
            translate([0, 0, socket_chamfer]) linear_extrude(eps) loc2d(i, socket_r);
        }
        translate([0, 0, -eps]) linear_extrude(socket_depth + eps) loc2d(i, socket_r);
    }
}
module tips(d = plate_d, z = post_top) {
    sym_y(d) for (i = [0, 1]) translate([0, 0, z - eps]) {
        hull() {
            linear_extrude(eps) loc2d(i, tip_r + tip_flare);
            translate([0, 0, tip_flare]) linear_extrude(eps) loc2d(i, tip_r);
        }
        linear_extrude(tip_h - tip_chamfer + eps) loc2d(i, tip_r);
        hull() {
            translate([0, 0, tip_h - tip_chamfer]) linear_extrude(eps) loc2d(i, tip_r);
            translate([0, 0, tip_h]) linear_extrude(eps) loc2d(i, tip_r - tip_chamfer);
        }
    }
}

// INFERRED: printed sockets-up; flipped onto the post tips it caps a stack.
// n-long cap: INFERRED from the x2 frame plate (no x2 cap in the references).
module cap(n = 1) {
    L = span(n);
    difference() {
        linear_extrude(plate_t) footprint(0, L - plate_trim);
        window(L);
        translate([0, 0, plate_t]) mirror([0, 0, 1]) sockets(L);
    }
}

// ---------- frame ----------
module tab2d() {  // dovetail, tip at t = 0, mouth at t = dovetail_len
    L = dovetail_len;
    p = [[23.5, 0], [23.5, 1.4], [21.35, 3.55], [21.35, L], [24, L + 0.5], [24, L + 2]];  // root dips into plate: no coplanar seam
    polygon(rounded(concat(p, [for (i = [len(p) - 1:-1:0]) [-p[i].x, p[i].y]]),
                    [0.9, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0.9]));
}
module tab() {
    y0 = plate_trim - dovetail_len;
    a = atan((tab_top[1] - tab_top[0]) / dovetail_len);
    translate([dovetail_x, y0, 0]) intersection() {
        linear_extrude(plate_t) tab2d();
        translate([0, 0, tab_top[0]]) rotate([a, 0, 0]) translate([-50, -50, -100]) cube(100);
    }
}
module notch(d = plate_d) { translate([dovetail_x, d - dovetail_len, -eps]) linear_extrude(rail_top + 2 * eps) tab2d(); }

module rail2d(w) {
    c = rail_chamfer;
    polygon([[0, plate_t], [w, plate_t], [w, rail_top - c], [w - c, rail_top], [c, rail_top], [0, rail_top - c]]);
}
module gusset2d(a, dir) {  // in (along, z); post face at `a`, gusset grows toward dir
    translate([a, 0]) mirror([dir < 0 ? 1 : 0, 0]) intersection() {
        translate([0, plate_t]) square([gusset_leg + 2 * gusset_r, gusset_leg + 2 * gusset_r + rail_top]);
        offset(r = -gusset_r, $fn = fn) offset(delta = gusset_r) union() {
            translate([-2 * gusset_r, plate_t]) square([2 * gusset_r, rail_top + gusset_leg + gusset_r - plate_t]);
            translate([0, plate_t]) square([gusset_leg + 2 * gusset_r, rail_top - plate_t]);
            polygon([[0, rail_top - eps], [gusset_leg, rail_top - eps], [0, rail_top + gusset_leg]]);
        }
    }
}
// ponytail: rail edge chamfer carried up the gusset as gusset_steps layers (error <= rail_chamfer / (2 * steps));
// a true swept chamfer needs minkowski, which falls back to CGAL here and discards facets.
gusset_steps = 4;
module gusset(a, dir, w) {
    c = rail_chamfer;
    n = gusset_steps;
    intersection() {
        union() {
            translate([0, 0, c - eps]) linear_extrude(w - 2 * c + 2 * eps) gusset2d(a, dir);
            for (i = [0:n - 1], z = [c * i / n, w - c * (i + 1) / n])
                translate([0, 0, z - eps]) linear_extrude(c / n + 2 * eps) offset(delta = -c * (1 - (i + 0.5) / n)) gusset2d(a, dir);
        }
        translate([-500, -500, 0]) cube([1000, 1000, w]);
    }
}
function scoop_d(z) = let(D = scoop_leg / sqrt(2))
    z < scoop_flat[0] ? D - (scoop_r[0] - sqrt(max(0, scoop_r[0]^2 - (scoop_flat[0] - z)^2))) :
    z > scoop_flat[1] ? D - (scoop_r[1] - sqrt(max(0, scoop_r[1]^2 - (z - scoop_flat[1])^2))) : D;
module scoop() {
    D = scoop_leg / sqrt(2);
    z0 = scoop_flat[0] - sqrt(2 * scoop_r[0] * D - D * D);
    z1 = scoop_flat[1] + sqrt(2 * scoop_r[1] * D - D * D);
    zs = [for (i = [0:60]) z0 + (z1 - z0) * i / 60];
    translate([plate_w, 0, 0]) rotate([0, 0, 135]) rotate([90, 0, 0])
        linear_extrude(4 * scoop_leg, center = true) polygon(concat([[-5, z0]], [for (z = zs) [scoop_d(z), z]], [[-5, z1]]));
}
module xpost2d() {
    c = arm_chamfer;
    polygon([[0, 0], [xpost_len - c, 0], [xpost_len, c], [xpost_len, rail_w - c], [xpost_len - c, rail_w], [0, rail_w]]);
}
module ppost2d() {
    c = arm_chamfer;
    x0 = plate_w - arm_len.x;
    x1 = plate_w - side_rail_w;
    polygon([[x0 + c, 0], [plate_w, 0], [plate_w, arm_len.y - c], [plate_w - c, arm_len.y], [x1 + c, arm_len.y],
             [x1, arm_len.y - c], [x1, rail_w + web_leg], [x1 - web_leg, rail_w], [x0 + c, rail_w], [x0, rail_w - c], [x0, c]]);
}
module frame_half(d = plate_d) {  // front half; back via sym_y
    prism(YZ, plate_w) rail2d(rail_w);                                     // front rail
    translate([0, rail_w, plate_t]) cube([plate_w - side_rail_w, ledge[0], ledge[1]]);
    translate([0, 0, plate_t]) linear_extrude(post_top - plate_t) { xpost2d(); ppost2d(); }
    multmatrix(XZ) { gusset(xpost_len, 1, rail_w); gusset(plate_w - arm_len.x, -1, rail_w); }
    translate([plate_w - side_rail_w, 0, 0]) multmatrix(YZ) gusset(arm_len.y, 1, side_rail_w);
}
// Shared frame shell before locator sockets and male tips are applied.
module frame_body(n = 1) {
    L = span(n);
    difference() {
        intersection() {
            union() {
                cube([plate_w, L, plate_t]);
                sym_y(L) frame_half(L);
                // One full rail avoids a coincident mid-row seam between mirrored halves.
                translate([plate_w - side_rail_w, 0, 0]) prism(XZ, L) rail2d(side_rail_w);
            }
            translate([0, 0, -1]) linear_extrude(post_top + 2) footprint(plate_trim, L);
        }
        window(L);
        notch(L);
        sym_y(L) scoop();
    }
    tab();
}
// n-long frame (MEASURED x2): corner posts only, one stretched window, rails run full length.
module frame(n = 1) {
    L = span(n);
    difference() { frame_body(n); sockets(L); }
    tips(L);
}

// Four feet follow the frame corner profiles and are placed in the selected footprint.
module stand_legs(n = 1, z0 = -foot_h, z1 = 0, inset = 0) {
    L = span(n);
    // The positive overlap above z1's plate underside makes a solid joint.
    intersection() {
        stand_leg_geometry(n, z0, z1, inset);
        translate([0, 0, z0 - 1])
            linear_extrude(z1 - z0 + 2) stand_mask(inset, L);
    }
}
module stand_leg_geometry(n, z0, z1, inset = 0) {
    L = span(n);
    c = foot_chamfer;
    // A 0.01 mm X overlap avoids zero-area union facets at full-width plate edges.
    edge_eps = inset == 0 ? eps : 0;
    union() {
        // Move each inherited corner profile to the selected plate perimeter.
        // The floor bevel, rather than a XY setback, keeps the floor contact inset.
        sym_y(L) translate([0, inset, z0 + c]) {
            translate([inset + edge_eps, 0, 0]) linear_extrude(z1 - z0 - c) xpost2d();
            translate([-inset - edge_eps, 0, 0]) linear_extrude(z1 - z0 - c) ppost2d();
        }
        stand_bevels(n, z0, inset);
        stand_braces(n, z1, inset);
    }
}
module stand_bevels(n, z0, inset = 0) {
    L = span(n);
    c = foot_chamfer;
    edge_eps = inset == 0 ? eps : 0;
    // Extrude from the exact post profile toward the floor. The top vertices
    // are shared with the straight post; a 3D hull introduced sliver seams.
    sym_y(L) translate([0, inset, 0]) for (i = [0, 1])
        let(w = i == 0 ? xpost_len : arm_len.x,
            h = i == 0 ? rail_w : arm_len.y,
            base_cx = i == 0 ? w / 2 : plate_w - w / 2,
            cx = i == 0 ? base_cx + inset + edge_eps : base_cx - inset - edge_eps)
        translate([cx, h / 2, z0 + c]) mirror([0, 0, 1])
            linear_extrude(c, scale = [(w - 2 * c) / w, (h - 2 * c) / h])
                translate([-base_cx, -h / 2])
                    if (i == 0) xpost2d(); else ppost2d();
}
module stand_braces(n, z1, inset = 0) {
    L = span(n);
    g = gusset_leg;
    brace_w = min(rail_w, side_rail_w) - 2 * eps;
    sym_y(L) translate([0, inset, 0])
        translate([plate_w - side_rail_w - inset, 0, 0]) prism(YZ, brace_w)
            polygon([[arm_len.y, z1 - g], [arm_len.y, z1], [arm_len.y + g, z1]]);
}
module stand(n = 1) {
    L = span(n);
    union() {
        translate([0, 0, -plate_t]) difference() {
            linear_extrude(plate_t) footprint(plate_trim, L);
            window(L);
        }
        stand_legs(n, -foot_h - plate_t, -plate_t + foot_chamfer);
        tips(L, 0);
    }
}

// Inner frame support for the bin, with four integral feet.
module stand_bin(n = 1) {
    L = span(n);
    union() {
        difference() {
            linear_extrude(plate_t) stand_mask(stand_inset, L);
            window(L);
        }
        intersection() {
            union() {
                sym_y(L) prism(YZ, plate_w) rail2d(rail_w);
                translate([plate_w - side_rail_w, 0, 0]) prism(XZ, L) rail2d(side_rail_w);
                sym_y(L) translate([0, rail_w, plate_t]) cube([plate_w - side_rail_w, ledge[0], ledge[1]]);
            }
            linear_extrude(rail_top) stand_mask(stand_inset, L);
        }
        stand_legs(n, -foot_h, foot_chamfer, stand_inset);
    }
}

// ---------- bin (open front +Y and open top behind the roof lip) ----------
// Local bin dimensions: X = 100*len, Y = 80*hgt, Z = 100*wid + 35 mm fixed nose. Other features keep source sizes.
module bin(n = 1) { bin_cell(bin_len(n), bin_size.y + dz, bin_size.z + dx); } // bin height = 100*wid_n + 35 mm
module bin_cell(W, D, H) {
    t = bin_wall;
    k = 1 / shoulder_taper;
    Ht = H + 15;
    c = inner_chamfer;
    shoulder_z = H - shoulder_drop;
    roof_z = H - roof_drop;
    facet_d = H + facet_offset + facet_n.x * (W - bin_size.x);  // plane stays on the +X end
    nm = [-facet_n.x, facet_n.y, facet_n.z];
    dm = facet_d - facet_n.x * W;
    inset = t * norm(facet_n);
    hs = max(1000, 4 * max(W, D, H));  // cutter size must cover the bin
    difference() {
        intersection() {
            translate([0, -1, 0]) prism(XZ, D + 2) polygon(rounded(
                [[bin_chamfer, 0], [W - bin_chamfer, 0], [W, bin_chamfer], [W, shoulder_z],
                 [W - k * (H - shoulder_z), H], [k * (H - shoulder_z), H], [0, shoulder_z], [0, bin_chamfer]],
                [0, 0, bin_chamfer_r, 0, 0, 0, 0, bin_chamfer_r]));
            translate([-1, 0, 0]) prism(YZ, W + 2) polygon(
                [[heel[0], 0], [D, 0], [D, shoulder_z], [D - (H - shoulder_z) / front_slope, H],
                 [H - roof_z, H], [0, roof_z], [0, heel[0] + heel[1]], [heel[0], heel[1]]]);
            translate([0, 0, -1]) linear_extrude(H + 2) polygon(
                [[corner_notch.x, 0], [W - corner_notch.x, 0], [W - corner_notch.x, corner_notch.y], [W, corner_notch.y],
                 [W, D], [0, D], [0, corner_notch.y], [corner_notch.x, corner_notch.y]]);
            halfspace(facet_n, facet_d, hs);
            halfspace(nm, dm, hs);
        }
        intersection() {  // cavity
            translate([0, -1, 0]) prism(XZ, D + 3) polygon(
                [[t + c, bin_floor], [W - t - c, bin_floor], [W - t, bin_floor + c], [W - t, shoulder_z],
                 [W - t - k * (Ht - shoulder_z), Ht], [t + k * (Ht - shoulder_z), Ht], [t, shoulder_z], [t, bin_floor + c]]);
            translate([-1, 0, 0]) prism(YZ, W + 2) polygon(
                [[t, bin_floor + c], [t + c, bin_floor], [D + 1, bin_floor], [D + 1, roof_z - t * sqrt(2) + D + 1],
                 [t, roof_z - t * sqrt(2) + t]]);
            translate([0, 0, -1]) linear_extrude(Ht) polygon(
                [[t, t + inner_plan_chamfer], [t + inner_plan_chamfer, t], [W - t - inner_plan_chamfer, t],
                 [W - t, t + inner_plan_chamfer], [W - t, D + 1], [t, D + 1]]);
            halfspace(facet_n, facet_d - inset, hs);
            halfspace(nm, dm - inset, hs);
        }
        floor_panels(W, D);
        back_panels(W, H);
        side_panels(W, D, H);
    }
}
module recess(depth, k) {  // surface at z = 0, cuts toward +z
    hull() {
        translate([0, 0, -1]) linear_extrude(1 + eps) children();
        translate([0, 0, depth - eps]) linear_extrude(eps) offset(delta = -k * depth) children();
    }
}
module mirror_x_bin(W) { children(); translate([W, 0, 0]) mirror([1, 0, 0]) children(); }
// Floor/back panels: one pair per bin, outer margins fixed, centre gap panel_gap, far edge follows the stretched axis.
panel_gap = bin_size.x - 2 * floor_panel[1].x;   // 10, same for floor and back panels
module floor_panels(W, D) {
    p = floor_panel;
    mirror_x_bin(W) translate([0, 0, bin_floor]) mirror([0, 0, 1]) recess(panel_depth, panel_slope)
        rrect(p[0], [W / 2 - panel_gap / 2, p[1].y + D - bin_size.y], p[2]);
}
module back_panels(W, H) {
    p = back_panel;
    mirror_x_bin(W) multmatrix(XZ) recess(panel_depth, panel_slope)
        rrect(p[0], [W / 2 - panel_gap / 2, p[1].y + H - bin_size.z], p[2]);
}
// End-wall "Y" panels, measured in (y, z) of the 1-cell bin. Stretch is piecewise so the Y junction keeps its shape:
// points beyond side_split.x move by the extra depth; the bars grow at their outer edges by half the extra height each.
side_zc = 58.95;            // mirror line of the two bars
side_split = [30, 20];      // [y inside the straight run of the bars, z between the bar edge (17.94) and the Y (22.0)]
function side_panel_pts(dy = 0, dh = 0) = let(m = -1.2649, zc = side_zc, y0 = 10.035, y1 = 66.435, z0 = 17.94, z1 = 56.41,
        q1 = [[y0, z0], [y1, z0], [y1, 54.53 + m * (y1 - 42.765)], [42.765 + (z1 - 54.53) / m, z1], [y0, z1]],
        q3 = [[45.76, zc], [74.965, 22.016], [74.965, 2 * zc - 22.016]],
        mv = function(p) [p.x + (p.x > side_split.x ? dy : 0),
                          p.y + (p.y > side_split.y ? dh / 2 : 0) + (p.y > 2 * zc - side_split.y ? dh / 2 : 0)])
    [[for (p = q1) mv(p)], [for (p = q1) mv([p.x, 2 * zc - p.y])], [for (p = q3) mv(p)]];
module side_panels(W, D, H) {  // MEASURED at 0.2 mm depth; 45? walls
    mirror_x_bin(W) multmatrix(YZ) for (q = side_panel_pts(D - bin_size.y, H - bin_size.z))
        recess(panel_depth, 1) offset(r = 0.2, $fn = fn) offset(r = side_r, $fn = fn) offset(delta = -side_r) polygon(q);
}

// ---------- assembly (INFERRED from the MakerWorld cover photo) ----------
// Bin lies on its back face, mouth toward -X; its back-corner notches ride the ledges.
module bin_in_frame(n = 1) {
    multmatrix([[0, 0, -1, plate_w - side_rail_w - bin_gap],
                [-1, 0, 0, (span(n) + bin_len(n)) / 2],
                [0, 1, 0, plate_t]]) bin(n);
}
// One entry per printed part: [kind, length, offset]. Iterated at top level so that
// --enable=lazy-union keeps every part a separate object (3MF). Each item's back edge sits on its first cell's back edge.
function _pack_cum(row, i) = i == 0 ? 0 : _pack_cum(row, i - 1) + span(row[i - 1]) - plate_trim;
function _row_span(row) = _pack_cum(row, len(row)) + plate_trim;
assert(len(asm_spec) > 0 && len([for (row = asm_spec) if (len(row) == 0) 1]) == 0,
       "asm_spec must contain nonempty rows");
assert(len([for (row = asm_spec, n = row) if (n < 1 || n != round(n)) 1]) == 0,
       "asm_spec cells must be positive whole numbers");
assert(len([for (row = asm_spec) if (row != asm_spec[0]) 1]) == 0,
       "every asm_spec row must use the same part partition");
assert(len([for (row = asm_spec) if (abs(_row_span(row) - _row_span(asm_spec[0])) > eps) 1]) == 0,
       "every asm_spec row must have the same physical span");
function _y(row, i) = _row_span(row) - span(row[i]) - _pack_cum(row, i);
function asm_items() = let(rs = asm_spec, top = len(rs)) concat(
    [for (r = [0:top - 1], i = [0:len(rs[r]) - 1], kind = asm_bins ? ["frame", "bin"] : ["frame"])
        [kind, rs[r][i], [0, _y(rs[r], i), r * post_top]]],
    [for (i = [0:len(rs[top - 1]) - 1]) ["cap", rs[top - 1][i], [0, _y(rs[top - 1], i), top * post_top]]],
    asm_stand ? [for (i = [0:len(rs[0]) - 1]) ["stand", rs[0][i], [0, _y(rs[0], i), 0]]] : []);
module asm_part(kind, n) {
    if (kind == "frame") color("SlateGray") frame(n);
    else if (kind == "bin") color("DimGray") bin_in_frame(n);
    else if (kind == "stand") color("DarkSlateGray") stand(n);
    else color("LightSlateGray") translate([0, span(n), plate_t]) rotate([180, 0, 0]) cap(n);
}

// ---------- output ----------
if (part == "cap") cap(size[0]);
else if (part == "frame") frame(size[0]);
else if (part == "bin") bin(size[0]);
else if (part == "stand") translate([0, 0, foot_h + plate_t]) stand(size[0]);  // feet on the bed, tips up
else if (part == "stand_bin") translate([0, 0, foot_h]) stand_bin(size[0]);
else if (part == "assembly") for (it = asm_items()) translate(it[2]) asm_part(it[0], it[1]);
else if (part == "assembly_bin") {
    color("DarkSlateGray") stand_bin(size[0]);
    color("DimGray") bin_in_frame(size[0]);
}
else if (part == "layout") {  // print layout of the reference STL at size [1,1,1]; positions follow size
    fx = 3 + plate_w + 2;
    translate([3, 65.179, 0]) cap(size[0]);
    translate([fx, 29.465, 0]) frame(size[0]);
    translate([fx + plate_w + 4, 29.465, foot_h + plate_t]) stand(size[0]);
    translate([fx + 24, 29.465 + span(size[0]) + 2, 0]) bin(size[0]);
    translate([3 * plate_w + 13, 29.465, foot_h]) stand_bin(size[0]);
}
