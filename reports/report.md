# Soletta CAD build report (draft quality)

Elapsed: 120.9 s. Grid resolution (mm): {'body': 0.8, 'outsole': 0.5, 'laces': 0.45}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 546,248 | True | True | 1 | 1255.3 | 298.2 x 133.8 x 106.9 | 12.9% |
| outsole | 589,180 | True | True | 1 | 106.5 | 291.9 x 112.8 x 22.8 | 26.3% |
| laces | 222,258 | True | True | 1 | 19.7 | 96.3 x 80.1 x 55.0 | 15.4% |
| dial (each) | 18,948 | True | True | 1 | 5.6 | 32.0 x 32.0 x 8.0 | 16.6% |
| printable shoe (body+outsole) | 674,650 | True | True | 1 | 1361.9 | 298.2 x 133.8 x 114.9 | 19.6% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 2402 | 2.65 | 3.95 | 10.25 | 0.79% |

Thin samples are expected on the 1.5 mm cables, guide sleeves and eyelet rims, which are features rather than walls.

## Dial frames

| Dial | Origin (mm) | Axis | Seat height |
|---|---|---|---|
| L1 | [185.86, 54.75, 45.74] | [-0.015, 0.864, 0.504] | 9.0 |
| L2 | [132.03, 45.21, 51.76] | [0.003, 0.991, -0.132] | 9.0 |
| L3 | [69.02, 42.66, 63.87] | [0.004, 1.0, -0.029] | 3.99 |
| R1 | [185.66, -52.43, 45.73] | [-0.036, -0.863, 0.504] | 9.0 |
| R2 | [132.02, -39.21, 51.76] | [0.002, -0.991, -0.132] | 9.0 |
| R3 | [69.1, -41.24, 63.87] | [0.023, -0.999, -0.029] | 3.98 |

## Warnings

- outsole: removed 3 floating fragment(s)
