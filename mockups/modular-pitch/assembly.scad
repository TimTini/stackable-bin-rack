// Visual prototype only. F5 preview; not approved for printing.
// Pick one case in Customizer or use "all" for the comparison gallery.
case = "all"; // [all, frame2, frame3, support2, support3, bare2, bare3]
show_bins = true;
include <model.scad>

module label(s) {
    color("Black") translate([-30, 0, 0]) rotate([0, 0, 90])
        linear_extrude(0.6) text(s, size=10);
}
// Amber = provisional added support. Bin length remains 100*n.
module bearing(n) {
    L = span(n);
    reach = (L - bin_len(n))/2 + 1;
    if (n > 1) color("Goldenrod") sym_y(L)
        translate([0, rail_w, plate_t])
            cube([plate_w - side_rail_w, reach - rail_w, ledge[1]]);
}
module bridge(n) {
    if (n > 1) color("Goldenrod") for (i=[1:n-1]) {
        // Preview-only top bridge above the bin envelope; not a load/fit proof.
        translate([0, i*pitch_y-16, post_top-3]) cube([plate_w, 32, 3]);
        intersection() {
            translate([0, (i-1)*pitch_y, 0]) tips(plate_d);
            translate([-1, i*pitch_y-18, post_top]) cube([plate_w+2, 36, tip_h+1]);
        }
        intersection() {
            translate([0, i*pitch_y, 0]) tips(plate_d);
            translate([-1, i*pitch_y-18, post_top]) cube([plate_w+2, 36, tip_h+1]);
        }
    }
}
module placed_bin(n) {
    multmatrix([[0,0,-1,plate_w-side_rail_w],
                [-1,0,0,(span(n)+bin_len(n))/2],
                [0,1,0,plate_t]]) bin(n);
}
module framed(n) {
    label(str("FRAME: ", n, " x [1] / [", n, "]"));
    color("DarkSlateGray") stand(n);
    color("SteelBlue") frame(n);
    bearing(n);
    bridge(n);
    if (show_bins) color([0.65,0.68,0.7,0.8]) placed_bin(n);
    for (i=[0:n-1]) translate([0,i*pitch_y,post_top]) {
        color("LightSteelBlue") frame(1);
        if (show_bins) color([0.75,0.78,0.8,0.8]) placed_bin(1);
        color("SlateGray") translate([0,plate_d,post_top+plate_t])
            rotate([180,0,0]) cap(1);
    }
}
module supported(n) {
    label(str("SUPPORT: ", n, " x [1] vs [", n, "]"));
    for (i=[0:n-1]) translate([0,i*pitch_y,foot_h]) {
        color("SlateGray") stand_bin(1);
        if (show_bins) color("Silver") placed_bin(1);
    }
    translate([185,0,foot_h]) {
        color("SteelBlue") stand_bin(n);
        bearing(n);
        if (show_bins) color("Silver") placed_bin(n);
    }
}
module bare(n) {
    label(str("BARE: ", n, " x 100 = ", 100*n, " mm"));
    for (i=[0:n-1]) translate([0,i*100,0])
        color(i%2 == 0 ? "Silver" : "LightSteelBlue")
            multmatrix([[0,0,-1,135],[-1,0,0,100],[0,1,0,0]]) bin(1);
    translate([185,0,0]) color("Silver")
        multmatrix([[0,0,-1,135],[-1,0,0,100*n],[0,1,0,0]]) bin(n);
}
if (case == "all") {
    framed(2);
    translate([0,450,0]) framed(3);
    translate([250,0,0]) supported(2);
    translate([250,450,0]) supported(3);
    translate([700,0,0]) bare(2);
    translate([700,450,0]) bare(3);
} else if (case == "frame2") framed(2);
else if (case == "frame3") framed(3);
else if (case == "support2") supported(2);
else if (case == "support3") supported(3);
else if (case == "bare2") bare(2);
else if (case == "bare3") bare(3);
echo(mockup_pitch=pitch_y, bin_lengths=[100,200,300], frame_spans=[span(1),span(2),span(3)]);