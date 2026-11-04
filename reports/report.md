# Soletta CAD build report (full quality)

Elapsed: 504.1 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 3,848,662 | True | True | 1 | 822.6 | 298.4 x 126.1 x 106.9 | 17.8% |
| outsole | 2,441,034 | True | True | 1 | 114.6 | 291.8 x 106.4 x 22.8 | 23.8% |
| laces | 660,612 | True | True | 1 | 14.9 | 101.1 x 49.1 x 41.2 | 14.6% |
| tongue as fitted (separate part) | 823,044 | True | True | 1 | 23.3 | 133.0 x 44.0 x 55.2 | 30.7% |
| tongue, flat print | 466 | True | True | 1 | 15.3 | 172.4 x 34.0 x 5.0 | 0.0% |
| medial straps as fitted (display) | 445,814 | True | True | 3 | 6.8 | 156.4 x 27.8 x 86.4 | 6.2% |
| dial housing (each) | 8,790 | True | True | 1 | 3.0 | 30.6 x 33.4 x 13.4 | 0.3% |
| dial spool (each) | 6,560 | True | True | 1 | 1.9 | 21.6 x 21.6 x 12.6 | 4.3% |
| dial knob (each) | 14,088 | True | True | 1 | 3.7 | 26.0 x 26.0 x 8.0 | 5.3% |
| strap buckle (each) | 1,764 | True | True | 1 | 0.8 | 14.4 x 23.2 x 9.2 | 18.0% |
| printable shoe (body+outsole), reloaded STL | 847,928 | True | True | 1 | 932.8 | 298.4 x 126.1 x 114.7 | 21.0% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 3678 | 1.65 | 2.15 | 5.45 | 26.29% |

Thin samples are expected on the cable channel sheaths (4 mm tube, 1.6 mm bore), the inner tongue, guide clips and eyelet rims, which are features rather than walls.

## Function checks on the printable STL

| check | value |
|---|---|
| channel L1 open, min clearance from centre line mm | 1.1 |
| channel L1 length mm | 83.9 |
| channel L2 open, min clearance from centre line mm | 1.1 |
| channel L2 length mm | 98.0 |
| channel L3 open, min clearance from centre line mm | 1.1 |
| channel L3 length mm | 89.8 |
| throat slot open from footbed to top, min clearance mm | 1.44 |
| tongue (sliding part) vs shoe min clearance mm | 1.0 |
| tongue glue flap distance to vamp, max mm | 0.0 |
| strap 1 buckle vs shoe min clearance mm | -0.0 |
| strap 1 webbing passage under buckle clear, min mm | 1.04 |
| strap 1 wall behind buckle seat, min mm | 11.9 |
| strap 1 top loop clear, min mm | 1.3 |
| strap 2 buckle vs shoe min clearance mm | -0.0 |
| strap 2 webbing passage under buckle clear, min mm | 0.7 |
| strap 2 wall behind buckle seat, min mm | 11.9 |
| strap 2 top loop clear, min mm | 1.3 |
| strap 3 buckle vs shoe min clearance mm | -0.04 |
| strap 3 webbing passage under buckle clear, min mm | 0.7 |
| strap 3 wall behind buckle seat, min mm | 11.9 |
| strap 3 top loop clear, min mm | 1.3 |

## Dial mechanism checks (exact B-rep)

| check | value |
|---|---|
| spool_vs_knob_mm3 | 0.0 |
| engaged_rest_spool_vs_housing_mm3 | 0.0 |
| engaged_knob_vs_housing_mm3 | 0.0 |
| released_spin_max_interference_mm3 | 0.0 |
| engaged_turning_pawl_flex_overlap_mm3 | 1.255 |
| tooth_engagement_mm | 0.8 |
| clicks_per_turn | 24 |
| cable_per_turn_mm_each_end | 45.9 |
| release_lift_mm | 3.2 |
| stack_height_mm | 19.6 |

## Dial frames

| Dial | Origin (mm) | Axis | Seat height |
|---|---|---|---|
| L1 | [175.73, 70.01, 35.11] | [-0.055, 0.995, -0.082] | 6.99 |
| L2 | [127.96, 63.28, 40.98] | [-0.002, 1.0, -0.001] | 3.9 |
| L3 | [57.73, 62.2, 52.05] | [-0.012, 0.996, -0.085] | 7.0 |

## Warnings

- body: removed 2 floating fragment(s)
- outsole: removed 7 floating fragment(s)
- laces: removed 7 floating fragment(s)
- webbing: removed 3 floating fragment(s)
