import pandas as pd
from pathlib import Path
import numpy as np

# =========================
# CẤU HÌNH
# =========================
DATA_DIR = Path(r"E:\smart-helmet\data_logger")

# Tên base của session (không có _manual_labels)
SESSIONS = [
    "session_mix_1",
    "session_mix_2",
]

FS = 1000              # Hz
WIN_SEC = 2.0
WIN_SAMPLES = int(FS * WIN_SEC)   # 2000 mẫu / cửa sổ

# Nếu muốn giảm mẫu cho đỡ nặng flash, set >1 (ví dụ 2 hoặc 4)
DECIMATE = 1


# =========================
# HÀM ĐỌC 1 SESSION
# =========================
def load_session(base_name: str):
    csv_path = DATA_DIR / f"{base_name}.csv"
    label_path = DATA_DIR / f"{base_name}_manual_labels.csv"

    print(f"\n===== Đang xử lý session: {base_name} =====")
    print("CSV   :", csv_path)
    print("Label :", label_path)

    df = pd.read_csv(csv_path)
    lab_df = pd.read_csv(label_path)

    n_samples = len(df)
    print("  Số sample trong CSV:", n_samples)

    # Khởi tạo mảng label = -1 (chưa gán)
    labels = np.full(n_samples, -1, dtype=int)

    # Duyệt từng cửa sổ trong file manual_labels
    for _, row in lab_df.iterrows():
        lbl = row["label"]
        # nếu label bị bỏ trống hoặc NaN (skip) thì bỏ qua
        if pd.isna(lbl):
            continue
        lbl = int(lbl)
        start = int(row["start_sample"])
        end = start + WIN_SAMPLES
        if start >= n_samples:
            continue
        if end > n_samples:
            end = n_samples

        labels[start:end] = lbl

    # Kiểm tra còn sample nào chưa được gán nhãn không
    unlabelled = np.sum(labels < 0)
    if unlabelled > 0:
        print(f"  ⚠ Còn {unlabelled} sample chưa có nhãn (sẽ bỏ qua).")

    # Lọc chỉ giữ các sample có nhãn 0/1
    mask = labels >= 0
    df = df.loc[mask].reset_index(drop=True)
    labels = labels[mask]

    print("  Sau khi bỏ sample không nhãn:", len(df))

    # Giảm mẫu nếu cần
    if DECIMATE > 1:
        before = len(df)
        df = df.iloc[::DECIMATE, :].reset_index(drop=True)
        labels = labels[::DECIMATE]
        after = len(df)
        print(f"  Giảm mẫu (decimate={DECIMATE}): {before} → {after}")

    return df, labels


# =========================
# GỘP TẤT CẢ SESSION
# =========================
ax_all, ay_all, az_all, label_all = [], [], [], []

for base in SESSIONS:
    df_sess, lbl_sess = load_session(base)

    # Lấy 3 trục accel thô (int16)
    ax_all.extend(df_sess["ax_raw"].astype(int).tolist())
    ay_all.extend(df_sess["ay_raw"].astype(int).tolist())
    az_all.extend(df_sess["az_raw"].astype(int).tolist())
    label_all.extend(lbl_sess.astype(int).tolist())

N = len(ax_all)
print("\n===== TỔNG KẾT TOÀN BỘ DATA =====")
print("Tổng số sample dùng train:", N)
print("  Impact (1):", sum(1 for v in label_all if v == 1))
print("  No-impact (0):", sum(1 for v in label_all if v == 0))


# =========================
# HÀM SINH MẢNG C CHO FIRMWARE
# =========================
def to_c_int16_array(name: str, data, n: int) -> str:
    items = ", ".join(str(int(v)) for v in data)
    return f"const int16_t {name}[{n}] = {{ {items} }};\n"


def to_c_uint8_array(name: str, data, n: int) -> str:
    items = ", ".join(str(int(v)) for v in data)
    return f"const uint8_t {name}[{n}] = {{ {items} }};\n"


# =========================
# GHI FILE training_data.cpp
# =========================
out_path = Path("training_data.cpp")
with open(out_path, "w", encoding="utf-8") as f:
    f.write('#include "training_data.h"\n\n')
    f.write(f"const int TRAIN_SAMPLES = {N};\n\n")
    f.write(to_c_int16_array("train_ax", ax_all, N))
    f.write("\n\n")
    f.write(to_c_int16_array("train_ay", ay_all, N))
    f.write("\n\n")
    f.write(to_c_int16_array("train_az", az_all, N))
    f.write("\n\n")
    f.write(to_c_uint8_array("train_label", label_all, N))

print("\n✅ Đã tạo xong training_data.cpp (int16) — copy file này vào src/ của firmware ESP32.")
