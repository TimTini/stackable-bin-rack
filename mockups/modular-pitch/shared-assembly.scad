// Shared outer frame prototype: F5 only, not a print-ready design.
case = "all"; // [all, frame2, frame3, support2, support3]
show_bins = true;
include <model.scad>
// One 4 mm divider and 1 mm clearance on either side at each boundary.
shared_wall = 4;
shared_gap = 1;
shared_step = 100 + shared_wall + 2*shared_gap;
function span(n) = plate_d + (n-1)*shared_step;
function bin_len(n) = 100*n + (n-1)*(shared_wall+2*shared_gap);

module caption(s) {
    color("Black") translate([-30,0,0]) rotate([0,0,90])
        linear_extrude(0.6) text(s,size=10);
}
module positioned_bin(n=1) {
    multmatrix([[0,0,-1,plate_w-side_rail_w],
                [-1,0,0,(span(n)+bin_len(n))/2],
                [0,1,0,plate_t]]) bin(n);
}
module small_bins(n) {
    for(i=[0:n-1]) translate([0,i*shared_step,0])
        color(i%2==0 ? "Silver" : "LightSteelBlue") positioned_bin(1);
}
module shared_dividers(n, tall=true) {
    for(i=[1:n-1]) {
        y = 10+i*shared_step-shared_gap-shared_wall;
        // Walls are joined to the perimeter by their ends; ledges support bin edges.
        color("Goldenrod") translate([0,y,plate_t])
            cube([plate_w,shared_wall,(tall ? post_top : rail_top)-plate_t]);
        color("Goldenrod") translate([0,y-2,plate_t])
            cube([plate_w-side_rail_w,shared_wall+4,ledge[1]]);
    }
}
module shared_frame(n) {
    color("LightSteelBlue") frame(n);
    shared_dividers(n);
}
module framed(n) {
    caption(str("SHARED ",n," CELLS / LONG ",bin_len(n)," mm"));
    color("DarkSlateGray") stand(n);
    color("SteelBlue") frame(n);
    if(show_bins) color("Silver") positioned_bin(n);
    translate([0,0,post_top]) {
        shared_frame(n);
        if(show_bins) small_bins(n);
        color("SlateGray") translate([0,span(n),post_top+plate_t])
            rotate([180,0,0]) cap(n);
    }
}
module supported(n) {
    caption(str("SHARED BASE ",n," CELLS vs LONG BIN"));
    translate([0,0,foot_h]) {
        color("SlateGray") stand_bin(n);
        shared_dividers(n,false);
        if(show_bins) small_bins(n);
    }
    translate([185,0,foot_h]) {
        color("SteelBlue") stand_bin(n);
        if(show_bins) color("Silver") positioned_bin(n);
    }
}
if(case=="all") {
    framed(2);
    translate([0,410,0]) framed(3);
    translate([260,0,0]) supported(2);
    translate([260,410,0]) supported(3);
} else if(case=="frame2") framed(2);
else if(case=="frame3") framed(3);
else if(case=="support2") supported(2);
else if(case=="support3") supported(3);
echo(shared_step=shared_step, frame_spans=[span(1),span(2),span(3)],
     large_bin_lengths=[bin_len(1),bin_len(2),bin_len(3)]);
