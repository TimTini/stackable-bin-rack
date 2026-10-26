// Interference checks for the assembly; each case should render empty.
include <stackable-bin-rack.scad>
part = "none";

case = 0;
pitch_y = plate_d - plate_trim;
// two singles sitting on top of one x2, same placement as asm_spec [[2], [1, 1]]
module singles_on_x2(kind = "frame") for (k = [0, 1]) translate([0, span(2) - plate_d - k * pitch_y, post_top])
    if (kind == "frame") frame(); else bin_in_frame();

if (case == 0) intersection() { frame(); bin_in_frame(); }                                       // bin vs own frame
if (case == 1) intersection() { translate([0, 0, post_top]) frame(); bin_in_frame(); }           // bin vs frame above
if (case == 2) intersection() { frame(); translate([0, 0, post_top]) frame(); }                  // stacked frames
if (case == 3) intersection() { frame(); translate([0, -pitch_y, 0]) frame(); }                  // dovetail neighbours
if (case == 4) intersection() { frame(); translate([0, plate_d, post_top + plate_t]) rotate([180, 0, 0]) cap(); }
if (case == 5) intersection() { bin_in_frame(); translate([0, -pitch_y, 0]) bin_in_frame(); }    // neighbouring bins
if (case == 6) intersection() { frame(2); bin_in_frame(2); }                                     // x2 bin vs x2 frame
if (case == 7) intersection() { bin_in_frame(2); singles_on_x2(); }                              // x2 bin vs two frames above
if (case == 8) intersection() { frame(2); singles_on_x2(); }                                     // x2 frame vs two frames above
if (case == 9) intersection() { frame(2); translate([0, -pitch_y, 0]) frame(); }                 // x2 next to x1
if (case == 10) intersection() { frame(2); translate([0, span(2), post_top + plate_t]) rotate([180, 0, 0]) cap(2); }
if (case == 11) intersection() { bin_in_frame(2); singles_on_x2("bin"); }                        // x2 bin vs bins above
