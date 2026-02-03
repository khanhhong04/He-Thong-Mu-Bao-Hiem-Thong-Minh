#include <Arduino.h>
#include <math.h>

#include "config.h"
#include "imu.h"
#include "fft_features.h"
#include "ml_model.h"
#include "train_on_device.h"
#include "ble.h" 

// =========================
// CẤU HÌNH DETECTION
// =========================

// Số mẫu cho FFT (phải KHỚP với N_FFT trong fft_features.cpp)
static const int WIN_N  = 512;
static const int STEP   = WIN_N / 2;          // overlap 50%
static const float ACCEL_SENS = ACCEL_SENS_4G; // từ config.h (8192.0f)

// Ngưỡng xác suất để coi là impact
static const float IMPACT_THRESH = 0.90f;

static const float PEAK_G_MIN = 1.8f;

// Thời gian chống dính (debounce) cho impact, ms
static const uint32_t IMPACT_DEBOUNCE_MS = 1500;

// =========================
// BIẾN TOÀN CỤC
// =========================

static LogisticModel gModel;

// buffer trượt chứa độ lớn gia tốc |a| (g)
static float gBuf[WIN_N];
static int   gBufIdx = 0;

// lưu accel raw / g mới nhất (cho 3 feature cuối)
static float last_ax_g = 0.0f;
static float last_ay_g = 0.0f;
static float last_az_g = 0.0f;

static uint32_t lastSampleUs     = 0;
static uint32_t lastImpactMs     = 0;

// =========================
// HÀM HỖ TRỢ
// =========================

// Lấy 1 mẫu IMU, cập nhật gBuf với |a| (đơn vị g)
static void sampleImuAndUpdateBuffer() {
    float ax_raw, ay_raw, az_raw;
    float gx_raw, gy_raw, gz_raw;

    imu_read(ax_raw, ay_raw, az_raw, gx_raw, gy_raw, gz_raw);

    // scale về g
    last_ax_g = ax_raw / ACCEL_SENS;
    last_ay_g = ay_raw / ACCEL_SENS;
    last_az_g = az_raw / ACCEL_SENS;

    float gmag = sqrtf(last_ax_g * last_ax_g +
                       last_ay_g * last_ay_g +
                       last_az_g * last_az_g);

    // cho vào buffer
    if (gBufIdx < WIN_N) {
        gBuf[gBufIdx++] = gmag;
    }
}

static void run_detection_window() {
    if (gBufIdx < WIN_N) return;

    // ===== 0) TÍNH GIA TỐC ĐỈNH TRONG CỬA SỔ =====
    float g_peak = 0.0f;
    for (int i = 0; i < WIN_N; ++i) {
        if (gBuf[i] > g_peak) g_peak = gBuf[i];
    }
    bool strong_motion = (g_peak > PEAK_G_MIN);

    // ===== 1) FFT feature 5 dải tần =====
    float fft_feat[5];
    compute_fft_features(gBuf, WIN_N, fft_feat);

    // ===== 2) 3 feature cuối = accel (g) tại sample mới nhất =====
    float feat[FEAT_DIM]; // FEAT_DIM = 8: 5 FFT + 3 accel
    feat[0] = fft_feat[0];
    feat[1] = fft_feat[1];
    feat[2] = fft_feat[2];
    feat[3] = fft_feat[3];
    feat[4] = fft_feat[4];
    feat[5] = last_ax_g;
    feat[6] = last_ay_g;
    feat[7] = last_az_g;

    // ===== 3) Dự đoán xác suất impact =====
    float p = logistic_predict(gModel, feat);

    Serial.print("p(impact) = ");
    Serial.print(p, 3);
    Serial.print("  | g_peak = ");
    Serial.println(g_peak, 3);

    uint32_t nowMs = millis();
    bool inCooldown = (nowMs - lastImpactMs) < IMPACT_DEBOUNCE_MS;

    // ===== 4) Quyết định impact_flag =====
    int impact_flag = 0;

    // Chỉ cho phép impact nếu:
    //  - g_peak đủ lớn (strong_motion)
    //  - Xác suất p vượt ngưỡng
    //  - Không nằm trong thời gian cooldown
    if (strong_motion && (p > IMPACT_THRESH) && !inCooldown) {
        impact_flag = 1;
        lastImpactMs = nowMs;
        Serial.println(">>> IMPACT DETECTED! <<<");
    }

    // ===== 5) Gửi JSON ML qua BLE mỗi cửa sổ 512ms =====
    char json[128];
    snprintf(json, sizeof(json),
             "{\"type\":\"ai\",\"impact\":%d,\"p\":%.3f,"
             "\"ax\":%.2f,\"ay\":%.2f,\"az\":%.2f}",
             impact_flag, p, last_ax_g, last_ay_g, last_az_g);

    ble_send_text(json);

    // ===== 6) Trượt cửa sổ: giữ lại 256 mẫu cuối =====
    const int HALF = WIN_N / 2;
    for (int i = 0; i < HALF; ++i) {
        gBuf[i] = gBuf[i + HALF];
    }
    gBufIdx = HALF;
}


// =========================
// SETUP & LOOP CHÍNH
// =========================

void setup() {
    Serial.begin(115200);
    delay(800);
    Serial.println();
    Serial.println("=== Smart Helmet – ML MODE (train + detect) ===");

    // Khởi tạo IMU
    imu_init();
    Serial.println("IMU ready.");

    // (Tuỳ chọn) khởi tạo BLE nếu bạn muốn gửi cảnh báo, còn không thì bỏ:
     ble_init();

    // Khởi tạo model logistic
    model_init(gModel);

    // Train offline trên dữ liệu trong training_data.cpp
    run_offline_training(gModel);

    Serial.println("Thong so model sau khi train:");
    Serial.print("b = ");
    Serial.println(gModel.b, 6);
    for (int i = 0; i < FEAT_DIM; ++i) {
        Serial.print("w[");
        Serial.print(i);
        Serial.print("] = ");
        Serial.println(gModel.w[i], 6);
    }

    // Chuẩn bị cho sampling realtime
    lastSampleUs = micros();
    gBufIdx      = 0;
    lastImpactMs = 0;

    Serial.println("Bat dau detect impact realtime...");
}

void loop() {
    uint32_t nowUs = micros();

    // Lấy mẫu đúng tần số SAMPLE_RATE_HZ (ở config.h bạn set = 1000)
    if (nowUs - lastSampleUs >= PERIOD_US) {
        lastSampleUs += PERIOD_US;

        sampleImuAndUpdateBuffer();
        run_detection_window();
    }

     // 🔴 XỬ LÝ SOS TỪ APP
    if (ble_take_sos()) {
        Serial.println("[FW] Received SOS from phone → bật còi / LED / giữ trạng thái incident");
    }
}
