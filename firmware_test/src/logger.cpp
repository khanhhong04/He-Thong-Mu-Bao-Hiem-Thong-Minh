#include <Arduino.h>
#include "imu.h"
#include "ble.h"

static const int SAMPLE_RATE_HZ = 1000;
static const int SAMPLE_PERIOD_US = 1000000 / SAMPLE_RATE_HZ;

static uint32_t last_us = 0;

void logger_loop() {
    uint32_t now = micros();
    if (now - last_us < SAMPLE_PERIOD_US) return;
    last_us = now;

    float ax, ay, az, gx, gy, gz;
    imu_read(ax, ay, az, gx, gy, gz);

    // Đóng gói 1 sample (giống file Python decode)
    uint8_t packet[13];
    int16_t* i16 = (int16_t*)packet;
    i16[0] = (int16_t)ax;
    i16[1] = (int16_t)ay;
    i16[2] = (int16_t)az;
    i16[3] = (int16_t)gx;
    i16[4] = (int16_t)gy;
    i16[5] = (int16_t)gz;
    packet[12] = 0; // marker

    ble_send_bytes(packet, 13);
}
