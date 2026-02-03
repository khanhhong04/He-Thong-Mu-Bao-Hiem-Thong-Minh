import numpy as np
import pandas as pd
from pathlib import Path

# =========================
# CONFIG
# =========================
DATA_DIR = Path(r"E:\smart-helmet\data_logger")

SESSIONS = [
    "session_mix_1.csv",
    "session_mix_2.csv",
]

FS = 1000.0          # Hz
WIN = 512            # 512 mẫu ~ 0.512s
STEP = 256           # trượt 50%
ACCEL_SENS = 8192.0  # ±4g → 8192 LSB/g

# --- Dải tần giống ESP (fft_features.cpp) ---
BANDS = [
    (0.5, 4.0),   # band_0_4
    (4.0, 8.0),   # band_4_8
    (12.0, 20.0), # band_12_20
    (20.0, 40.0), # band_20_40
    (40.0, 80.0), # band_40_80
]

# --- Ngưỡng AUTO-LABEL (tự chỉnh được) ---
GMAG_THRESH  = 1.6    # g_max (độ lớn gia tốc)
JERK_THRESH = 50.0    # jerk_max (|Δg/Δt|), đơn vị g/s


def compute_band_features(g_win, fs=FS):
    """
    g_win: array length WIN, đã là |a| theo đơn vị g
    Trả về: list 5 feature (sqrt năng lượng mỗi band)
    """
    N = len(g_win)

    # Bỏ DC
    g_dc = g_win - np.mean(g_win)

    # Cửa sổ Hamming
    w = np.hamming(N)
    x = g_dc * w

    # FFT 1 phía
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(N, d=1.0/fs)
    mag = np.abs(X)
    energy = mag ** 2

    feats = []
    for (fmin, fmax) in BANDS:
        mask = (freqs >= fmin) & (freqs < fmax)
        e = energy[mask].sum()
        feats.append(np.sqrt(e))   # giống ESP: sqrt(energy)
    return feats


def build_windows_for_session(csv_name: str):
    csv_path = DATA_DIR / csv_name

    print(f"\n===== Xử lý {csv_name} =====")
    df = pd.read_csv(csv_path)

    # kiểm tra cột
    for col in ["ax_raw", "ay_raw", "az_raw"]:
        if col not in df.columns:
            raise ValueError(f"{csv_name} thiếu cột {col}")

    n_samples = len(df)
    print("  Số sample trong CSV:", n_samples)

    # Scale về g
    ax = df["ax_raw"].values.astype(float) / ACCEL_SENS
    ay = df["ay_raw"].values.astype(float) / ACCEL_SENS
    az = df["az_raw"].values.astype(float) / ACCEL_SENS

    # |a|
    g = np.sqrt(ax * ax + ay * ay + az * az)

    # jerk (sai phân bậc 1, nhân FS)
    jerk = np.zeros_like(g)
    jerk[1:] = (g[1:] - g[:-1]) * FS

    rows = []
    for start in range(0, n_samples - WIN + 1, STEP):
        end = start + WIN
        t_start_sec = start / FS

        g_win     = g[start:end]
        jerk_win  = jerk[start:end]
        ax_last   = ax[end - 1]
        ay_last   = ay[end - 1]
        az_last   = az[end - 1]

        # Feature FFT 5 dải tần
        band_feats = compute_band_features(g_win, fs=FS)

        # Thêm vài feature tín hiệu (để đánh giá / có thể dùng hoặc không)
        g_rms     = np.sqrt(np.mean(g_win ** 2))
        g_max     = np.max(g_win)
        jerk_rms  = np.sqrt(np.mean(jerk_win ** 2))
        jerk_max  = np.max(np.abs(jerk_win))

        # ===== AUTO-LABEL: luật impact =====
        if (g_max >= GMAG_THRESH) and (jerk_max >= JERK_THRESH):
            y = 1
        else:
            y = 0

        rows.append({
            "file": csv_name,
            "start_sample": start,
            "t_start_sec": t_start_sec,
            "label": y,
            "band_0_4": band_feats[0],
            "band_4_8": band_feats[1],
            "band_12_20": band_feats[2],
            "band_20_40": band_feats[3],
            "band_40_80": band_feats[4],
            # thêm cho phân tích / mô hình mở rộng
            "g_rms": g_rms,
            "g_max": g_max,
            "jerk_rms": jerk_rms,
            "jerk_max": jerk_max,
            "ax_last": ax_last,
            "ay_last": ay_last,
            "az_last": az_last,
        })

    print("  Số window tạo ra:", len(rows))
    return rows


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    all_rows = []
    for csv_name in SESSIONS:
        rows = build_windows_for_session(csv_name)
        all_rows.extend(rows)

    out = pd.DataFrame(all_rows)
    out_path = DATA_DIR / "labeled_windows_512.csv"
    out.to_csv(out_path, index=False)

    print("\n==============================")
    print("ĐÃ TẠO FILE:", out_path)
    print("Tổng window:", len(out))
    if len(out) > 0:
        print("label")
        print(out["label"].value_counts())
