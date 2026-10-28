# Modular pitch mockup - 2026-10-28

Open assembly.scad and press F5. Select `case` in Customizer; `show_bins=false` exposes the frame bridges.

- frame2/frame3: singles above a continuous long frame.
- support2/support3: singles on direct bin supports beside a long supported bin. These are side-by-side comparisons, not a claim of frameless vertical stacking.
- bare2/bare3: bins alone, 100*n mm, touching end-to-end.

Trial choice: retain original single-frame pitch 119.93 mm, extend longer frames by that pitch. Keep bin lengths 100/200/300 mm. Long frames therefore have extra space around the bins. Amber ledges and top bridges are provisional support geometry for visual review; not production mating features. Changing only span does not establish universal socket compatibility.

The copied model.scad is an isolated snapshot. Main SCAD, canonical exports and Fusion are unchanged. No STL for printing, physical fit, load, collision or slicer approval is implied.
