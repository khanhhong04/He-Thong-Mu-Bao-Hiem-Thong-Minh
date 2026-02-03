#pragma once
#include <stdint.h>

extern const int TRAIN_SAMPLES;

// raw int16 từ IMU (±4g)
extern const int16_t train_ax[];
extern const int16_t train_ay[];
extern const int16_t train_az[];
extern const uint8_t train_label[];  // 0 = noimpact, 1 = impact
