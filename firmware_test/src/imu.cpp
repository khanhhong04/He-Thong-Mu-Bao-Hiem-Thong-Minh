#include "config.h"
#include "imu.h"
#include <Wire.h>

static void i2cWrite8(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

uint8_t imu_whoami() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(REG_WHO_AM_I);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, (uint8_t)1);
  return Wire.available() ? Wire.read() : 0xFF;
}

int16_t imu_read16(uint8_t regH) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(regH);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, (uint8_t)2);
  if (Wire.available() >= 2) {
    uint8_t hi = Wire.read();
    uint8_t lo = Wire.read();
    return (int16_t)((hi << 8) | lo);
  }
  return 0;
}

void imu_read_accel_raw(int16_t& ax, int16_t& ay, int16_t& az) {
  ax = imu_read16(REG_ACCEL_XOUT_H);
  ay = imu_read16(REG_ACCEL_XOUT_H + 2);
  az = imu_read16(REG_ACCEL_XOUT_H + 4);
}

void imu_read_gyro_raw(int16_t& gx, int16_t& gy, int16_t& gz) {
  gx = imu_read16(REG_GYRO_XOUT_H);
  gy = imu_read16(REG_GYRO_XOUT_H + 2);
  gz = imu_read16(REG_GYRO_XOUT_H + 4);
}

void imu_begin() {
  uint8_t who = imu_whoami();
  Serial.printf("MPU6500 WHO_AM_I = 0x%02X (expected 0x70)\r\n", who);
  if (who != 0x70) {
    Serial.println("MPU6500 not found! Check wiring.");
    while (1) delay(100);
  }
  i2cWrite8(REG_PWR_MGMT_1, 0x00); // wake
  delay(50);
  i2cWrite8(REG_ACCEL_CONFIG, 0x08); // ±4g
  i2cWrite8(REG_GYRO_CONFIG,  0x08); // ±500 dps
  delay(20);
  Serial.println("MPU6500 initialized");
}

void imu_compute_tilt(float ax, float ay, float az, float& pitchDeg, float& rollDeg) {
  float dp = sqrtf(ay*ay + az*az);
  float dr = sqrtf(ax*ax + az*az);
  pitchDeg = dp > 0.001f ? atan2f(ax, dp) * 180.0f / PI : 0.0f;
  rollDeg  = dr > 0.001f ? atan2f(ay, dr) * 180.0f / PI : 0.0f;
}

// ===============================
// ADD MISSING FUNCTIONS FOR MAIN
// ===============================

// Wrapper cho init
void imu_init() {
    Wire.begin();
    Wire.setClock(1000000);  // 1 MHz I2C
    imu_begin();             // gọi hàm cũ của bạn
}

// Wrapper cho đọc IMU
void imu_read(float &ax_raw, float &ay_raw, float &az_raw,
              float &gx_raw, float &gy_raw, float &gz_raw) 
{
    int16_t ax16, ay16, az16;
    int16_t gx16, gy16, gz16;

    imu_read_accel_raw(ax16, ay16, az16);
    imu_read_gyro_raw (gx16, gy16, gz16);

    ax_raw = (float)ax16;
    ay_raw = (float)ay16;
    az_raw = (float)az16;
    gx_raw = (float)gx16;
    gy_raw = (float)gy16;
    gz_raw = (float)gz16;
}
