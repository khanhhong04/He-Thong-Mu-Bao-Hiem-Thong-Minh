// src/fft_features.cpp
#include "fft_features.h"
#include <arduinoFFT.h>
#include <math.h>

// =======================
// CẤU HÌNH FFT
// =======================

// FFT length dùng trên ESP32
static const uint16_t N_FFT = 512;      // 512 mẫu ~ 0.512s @ 1000 Hz
static const double   FS    = 1000.0;   // Hz

// Buffer cho arduinoFFT (dùng double theo yêu cầu lib)
static double vReal[N_FFT];
static double vImag[N_FFT];

// Đối tượng FFT
static arduinoFFT FFT(vReal, vImag, N_FFT, FS);

// =======================
// HÀM TÍNH FEATURE FFT
// =======================

void compute_fft_features(const float* samples, int N, float* outFeat)
{
    if (N > N_FFT) {
        N = N_FFT;
    }

    // 1) Copy dữ liệu vào vReal, zero-padding phần còn lại
    for (int i = 0; i < N; ++i) {
        vReal[i] = (double)samples[i];
        vImag[i] = 0.0;
    }
    for (int i = N; i < N_FFT; ++i) {
        vReal[i] = 0.0;
        vImag[i] = 0.0;
    }

    // 2) Bỏ DC: trừ mean
    double mean = 0.0;
    for (int i = 0; i < N_FFT; ++i) {
        mean += vReal[i];
    }
    mean /= (double)N_FFT;
    for (int i = 0; i < N_FFT; ++i) {
        vReal[i] -= mean;
    }

    // 3) FFT: Hamming + Compute + Magnitude
    FFT.Windowing(FFT_WIN_TYP_HAMMING, FFT_FORWARD);
    FFT.Compute(FFT_FORWARD);
    FFT.ComplexToMagnitude();   // vReal[k] = |X[k]|

    // 4) Tính năng lượng theo 5 dải tần
    //
    //   df = FS / N_FFT ~ 1.95 Hz
    //   f_k = k * df
    //
    //   Band 0:  0.5–  4 Hz  (1.5 / 3 Hz)
    //   Band 1:  4 –  8 Hz  (5–7 Hz)
    //   Band 2: 12 – 20 Hz  (13–20 Hz)
    //   Band 3: 20 – 40 Hz
    //   Band 4: 40 – 80 Hz
    //
    float bandEnergy[5] = {0, 0, 0, 0, 0};

    const float df = (float)(FS / (double)N_FFT);

    // chỉ cần 1..N_FFT/2 (phổ 1 phía)
    for (uint16_t k = 1; k < N_FFT / 2; ++k) {
        float f   = df * (float)k;
        float mag = (float)vReal[k];
        float e   = mag * mag;      // năng lượng tạm coi = |X|^2

        if (f >= 0.5f && f < 4.0f) {
            bandEnergy[0] += e;
        } else if (f >= 4.0f && f < 8.0f) {
            bandEnergy[1] += e;
        } else if (f >= 12.0f && f < 20.0f) {
            bandEnergy[2] += e;
        } else if (f >= 20.0f && f < 40.0f) {
            bandEnergy[3] += e;
        } else if (f >= 40.0f && f < 80.0f) {
            bandEnergy[4] += e;
        }
    }

    // 5) Gán ra outFeat (lấy sqrt để scale về giống "magnitute")
    for (int i = 0; i < 5; ++i) {
        outFeat[i] = sqrtf(bandEnergy[i]);
    }
}
