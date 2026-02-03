// src/ml_model.h
#pragma once

// Số chiều feature:
// ví dụ: 5 FFT peaks + 3 giá trị ax, ay, az cuối cửa sổ = 8
#define FEAT_DIM 8

struct LogisticModel {
    float w[FEAT_DIM];
    float b;
};

// Khởi tạo trọng số ban đầu (w = 0, b = 0)
void model_init(LogisticModel& m);

// Tính xác suất p = P(impact | x)
float logistic_predict(const LogisticModel& m, const float* x);

// Cập nhật model với 1 mẫu (x, y) – training trực tiếp trên ESP32
// y ∈ {0,1}
void logistic_train_step(LogisticModel& m, const float* x, int y);
