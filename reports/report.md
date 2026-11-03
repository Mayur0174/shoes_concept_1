# Soletta CAD build report (full quality)

Elapsed: 407.4 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 3,902,192 | True | True | 1 | 847.7 | 298.2 x 121.4 x 106.9 | 18.6% |
| outsole | 2,416,464 | True | True | 1 | 113.6 | 291.8 x 106.4 x 22.8 | 23.5% |
| laces | 667,328 | True | True | 1 | 15.2 | 98.0 x 47.7 x 42.5 | 15.8% |
| medial straps as fitted (display) | 427,852 | True | True | 3 | 6.4 | 157.1 x 29.4 x 70.2 | 6.4% |
| dial housing (each) | 8,790 | True | True | 1 | 3.0 | 30.6 x 33.4 x 13.4 | 0.3% |
| dial spool (each) | 6,560 | True | True | 1 | 1.9 | 21.6 x 21.6 x 12.6 | 4.3% |
| dial knob (each) | 14,088 | True | True | 1 | 3.7 | 26.0 x 26.0 x 8.0 | 5.3% |
| printable shoe (body+outsole), reloaded STL | 1,277,120 | True | True | 1 | 957.0 | 298.2 x 121.4 x 114.7 | 21.4% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 3637 | 1.69 | 2.25 | 6.45 | 6.05% |

Thin samples are expected on the cable channel sheaths (4 mm tube, 1.6 mm bore), the inner tongue, guide clips and eyelet rims, which are features rather than walls.

## Function checks on the printable STL

| check | value |
|---|---|
| channel L1 open, min clearance from centre line mm | 0.8 |
| channel L1 length mm | 86.7 |
| channel L2 open, min clearance from centre line mm | 0.8 |
| channel L2 length mm | 102.9 |
| channel L3 open, min clearance from centre line mm | 0.8 |
| channel L3 length mm | 90.1 |
| tongue gap under the quarters, min mm | 1.0 |
| strap 1 buckle slots + webbing gap clear, min mm | 1.3 |
| strap 1 top loop clear, min mm | 1.3 |
| strap 2 buckle slots + webbing gap clear, min mm | 1.3 |
| strap 2 top loop clear, min mm | 1.3 |
| strap 3 buckle slots + webbing gap clear, min mm | 1.3 |
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
| L1 | [175.29, 67.43, 37.81] | [-0.074, 0.997, 0.035] | 7.0 |
| L2 | [128.17, 58.79, 44.16] | [0.008, 0.989, 0.15] | 5.0 |
| L3 | [57.77, 58.41, 52.07] | [-0.01, 0.996, -0.084] | 7.0 |

## Warnings

- body: removed 2 floating fragment(s)
- outsole: removed 7 floating fragment(s)
- laces: removed 3 floating fragment(s)
- webbing: removed 4 floating fragment(s)
