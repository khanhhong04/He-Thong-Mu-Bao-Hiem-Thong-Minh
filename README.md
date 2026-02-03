# 🪖 Hệ Thống Mũ Bảo Hiểm Thông Minh Ứng Dụng IoT & Machine Learning

## 📖 Giới thiệu
Dự án **Hệ thống Mũ Bảo Hiểm Thông Minh** được xây dựng nhằm nâng cao an toàn cho người tham gia giao thông.  
Hệ thống sử dụng **ESP32 + cảm biến MPU6050** để thu thập dữ liệu gia tốc, kết hợp **xử lý tín hiệu FFT** và **mô hình Logistic Regression** để phát hiện **va chạm (impact)** theo thời gian thực.  

Khi phát hiện va chạm nghiêm trọng, hệ thống sẽ:
- Gửi cảnh báo đến ứng dụng di động qua BLE
- Cho phép người dùng gửi tín hiệu SOS
- Lưu dữ liệu phục vụ phân tích và đánh giá tai nạn

---

## 🎯 Mục tiêu dự án
- Phát hiện va chạm giao thông dựa trên dữ liệu IMU
- Phân biệt **impact / non-impact** bằng Machine Learning nhẹ, chạy trực tiếp trên ESP32
- Kết nối với ứng dụng di động và backend để giám sát và xử lý sự cố
- Hướng tới ứng dụng thực tế trong các thiết bị bảo hộ thông minh

---

## 🧠 Kiến trúc tổng thể hệ thống

He-Thong-Mu-Bao-Hiem-Thong-Minh/
│
├── app/ # Ứng dụng di động (React Native)
│
├── backend/ # Backend server (Node.js / Express)
│
├── data_logger/ # Tool thu thập và lưu dữ liệu IMU
│
├── firmware_test/ # Firmware ESP32 (FFT + ML + BLE)
│
├── simulator/ # Mô phỏng, phân tích dữ liệu & FFT
│
├── smart-helmet.code-workspace



---

## ⚙️ Phần cứng sử dụng
- **ESP32**
- **MPU6050 (Accelerometer + Gyroscope)**
- Smartphone (Android)
- Máy chủ backend

---

## 📊 Xử lý tín hiệu & Machine Learning

### 🔹 Tiền xử lý dữ liệu
- Lấy gia tốc thô theo 3 trục: `ax, ay, az`
- Chuẩn hóa về đơn vị **g** (chia cho 8192 với ±4g)
- Tính độ lớn gia tốc:
  
\[
|a| = \sqrt{ax^2 + ay^2 + az^2}
\]

---

### 🔹 Phân tích FFT
- Cửa sổ trượt: **512 mẫu (~0.5s)**, overlap 50%
- FFT một phía
- Trích xuất năng lượng ở 5 dải tần:

| Band | Dải tần (Hz) | Ý nghĩa |
|----|------------|--------|
| 0 | 0.5 – 4 | Chuyển động nền |
| 1 | 4 – 8 | Rung mạnh |
| 2 | 12 – 20 | Bắt đầu va chạm |
| 3 | 20 – 40 | Va đập mạnh |
| 4 | 40 – 80 | Xung lực cao |

---

### 🔹 Feature dùng cho mô hình (8 chiều)
- **5 feature FFT**: năng lượng theo 5 band
- **3 feature thời gian**: `ax, ay, az` tại mẫu cuối cửa sổ

---

### 🔹 Mô hình phân loại
- **Logistic Regression**
- Huấn luyện trực tiếp trên ESP32 (offline training)
- Đầu ra: xác suất va chạm `p(impact)`

---

## 📱 Ứng dụng di động
- Nhận dữ liệu va chạm từ ESP32 qua BLE
- Hiển thị trạng thái impact / non-impact
- Gửi tín hiệu SOS trong trường hợp khẩn cấp

---

## 🌐 Backend
- Lưu trữ dữ liệu sự kiện va chạm
- Quản lý thông tin người dùng
- Phục vụ mở rộng hệ thống trong tương lai

---

## 🚀 Kết quả đạt được
- Phát hiện va chạm theo thời gian thực
- Phân biệt rõ impact và non-impact dựa trên phổ tần số
- Mô hình nhẹ, chạy ổn định trên vi điều khiển
- Hệ thống hoạt động đồng bộ firmware – app – backend

---

## 📌 Định hướng phát triển
- Tích hợp GPS để gửi vị trí tai nạn
- Phân loại mức độ va chạm (nhẹ / nặng)
- Kết nối mạng IoT (4G / MQTT)
- Nâng cấp mô hình ML (SVM / TinyML)

---

## 👨‍🎓 Tác giả
- Sinh viên: **[Tạ Long Khánh]**
- Ngành: Công nghệ Thông tin
- Trường: **Đại học Xây dựng Hà Nội**
- Đồ án tốt nghiệp
