// src/ml_model.cpp
#include "ml_model.h"
#include <math.h>

// Learning rate – giảm xuống cho ổn định hơn
static const float LR = 0.002f;

void model_init(LogisticModel& m) {
    for (int i = 0; i < FEAT_DIM; i++) {
        m.w[i] = 0.0f;
    }
    m.b = 0.0f;
}

float logistic_predict(const LogisticModel& m, const float* x) {
    float z = m.b;
    for (int i = 0; i < FEAT_DIM; i++) {
        z += m.w[i] * x[i];
    }
    // sigmoid
    return 1.0f / (1.0f + expf(-z));
}

void logistic_train_step(LogisticModel& m, const float* x, int y) {
    // y = 0 hoặc 1
    float p   = logistic_predict(m, x);
    float err = (float)y - p;   // gradient ascent trên log-likelihood

    for (int i = 0; i < FEAT_DIM; i++) {
        m.w[i] += LR * err * x[i];
    }

    m.b += LR * err;
}
