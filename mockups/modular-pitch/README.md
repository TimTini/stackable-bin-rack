# Modular pitch mockup - 2026-10-28

Open assembly.scad and press F5. Select `case` in Customizer; `show_bins=false` exposes the frame bridges.

- frame2/frame3: singles above a continuous long frame.
- support2/support3: singles on direct bin supports beside a long supported bin. These are side-by-side comparisons, not a claim of frameless vertical stacking.
- bare2/bare3: bins alone, 100*n mm, touching end-to-end.

Trial choice: retain original single-frame pitch 119.93 mm, extend longer frames by that pitch. Keep bin lengths 100/200/300 mm. Long frames therefore have extra space around the bins. Amber ledges and top bridges are provisional support geometry for visual review; not production mating features. Changing only span does not establish universal socket compatibility.

The copied model.scad is an isolated snapshot. Main SCAD, canonical exports and Fusion are unchanged. No STL for printing, physical fit, load, collision or slicer approval is implied.

## Shared outer frame option

Open shared-assembly.scad. Four scenes: frame2/frame3 stack [1|1] or [1|1|1] over a continuous long bin; support2/support3 compare a shared divided base against a long bin on the same size base. show_bins=false reveals the shared walls. The original assembly.scad is retained for comparison.

Trial dimensions: 100 mm small bins, 4 mm divider, 1 mm clearance per side; cell pitch106 mm. Nominal frame spans120/226/332 mm; large bins100/206/312 mm. Caps and outer locators are common to the divided/open frame of each size. The shared divider uses the existing rounded corner-cut window and chamfered rail profiles, with colors matching the frame/support. Walls/ledges are provisional; no fit, collision, strength or print validation. A supported case is not a bare one-piece divided bin, and no unsupported vertical stacking is implied.
