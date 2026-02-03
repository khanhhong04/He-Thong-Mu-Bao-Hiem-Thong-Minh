#pragma once
#include <Arduino.h>

void imu_begin();
uint8_t imu_whoami();
int16_t imu_read16(uint8_t regH);
void   imu_read_accel_raw(int16_t& ax, int16_t& ay, int16_t& az);
void   imu_read_gyro_raw (int16_t& gx, int16_t& gy, int16_t& gz);

// (tùy chọn) tính góc nghiêng nếu bạn còn dùng JSON nền
void   imu_compute_tilt(float ax, float ay, float az, float& pitchDeg, float& rollDeg);

// Khởi tạo IMU
void imu_init();

// Đọc 1 mẫu IMU (gia tốc + gyro), đơn vị: raw
void imu_read(float &ax_raw, float &ay_raw, float &az_raw,
              float &gx_raw, float &gy_raw, float &gz_raw);