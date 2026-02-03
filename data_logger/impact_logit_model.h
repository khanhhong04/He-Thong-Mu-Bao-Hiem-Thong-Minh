// Auto-generated from export_logit_to_c.py
#pragma once

#define IMPACT_FEAT_DIM 28

static const float IMPACT_W[IMPACT_FEAT_DIM] = {
  0.66040257,
  0.64202067,
  0.17853855,
  1.06994270,
  0.02271676,
  0.39673521,
  0.05700095,
  -0.53330185,
  0.33482147,
  -0.44465263,
  -0.52614003,
  0.15739582,
  0.37273215,
  -0.14744698,
  0.26285334,
  -0.29570362,
  0.07019740,
  0.59619750,
  -0.89209863,
  0.76168157,
  -0.60550681,
  0.88770674,
  0.39991574,
  0.07955958,
  0.41005496,
  -1.29321691,
  0.09841438,
  -0.92841542
};

static const float IMPACT_SCALE[IMPACT_FEAT_DIM] = {
  0.43608283,
  0.50782874,
  2.33167551,
  0.33334872,
  2.62493091,
  30.27159072,
  123.80521029,
  217.62611624,
  212.07396013,
  420.70441988,
  27.05796444,
  106.58379072,
  215.36438445,
  218.51438681,
  427.96686035,
  20.41775949,
  74.02185753,
  188.76033529,
  203.50466950,
  386.09924170,
  155.44695034,
  86.30783190,
  344.94195236,
  18.18322379,
  332.88481225,
  0.38582606,
  0.31248479,
  0.32710672
};

static const float IMPACT_BIAS = -2.55471058;

/* Feature order (must match firmware):
00: a_mag_mean
01: a_mag_std
02: a_mag_max
03: a_mag_min
04: a_mag_ptp
05: gx_mean
06: gx_std
07: gx_max
08: gx_min
09: gx_ptp
10: gy_mean
11: gy_std
12: gy_max
13: gy_min
14: gy_ptp
15: gz_mean
16: gz_std
17: gz_max
18: gz_min
19: gz_ptp
20: g_mag_mean
21: g_mag_std
22: g_mag_max
23: g_mag_min
24: g_mag_ptp
25: az_mean
26: ax_abs_mean
27: ay_abs_mean
*/
