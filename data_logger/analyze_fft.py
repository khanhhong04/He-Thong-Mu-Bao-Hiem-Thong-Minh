import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path(r"E:\smart-helmet\data_logger")
LABELED_FILE = DATA_DIR / "labeled_windows_512.csv"

FS = 1000.0
WIN = 512
ACCEL_SENS = 8192.0

K_IMPACT  = 10   # số window impact dùng để vẽ / trung bình
K_NOIMPACT = 10  # số window no-impact “vừa phải” dùng để vẽ / trung bình

# -----------------------------
# Hàm đọc 1 window từ file gốc
# -----------------------------
def extract_g_window(row):
    csv_path = DATA_DIR / row["file"]
    df_raw = pd.read_csv(csv_path)

    start = int(row["start_sample"])
    end   = start + WIN

    ax = df_raw["ax_raw"].values[start:end] / ACCEL_SENS
    ay = df_raw["ay_raw"].values[start:end] / ACCEL_SENS
    az = df_raw["az_raw"].values[start:end] / ACCEL_SENS

    g = np.sqrt(ax*ax + ay*ay + az*az)
    return g

# -----------------------------
# FFT 1 window
# -----------------------------
def fft_mag(g):
    N = len(g)
    g_dc = g - np.mean(g)
    w = np.hamming(N)
    x = g_dc * w

    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(N, d=1.0/FS)
    mag = np.abs(X)
    return freqs, mag

# -----------------------------
# Hàm tìm top K peak tần số
# -----------------------------
def top_peaks(freqs, mag, k=5, fmin=0.5, fmax=120.0):
    mask = (freqs >= fmin) & (freqs <= fmax)
    f = freqs[mask]
    m = mag[mask]

    idx = np.arange(len(m))
    if len(m) < 3:
        return []

    # local maxima đơn giản
    is_peak = (m[1:-1] > m[:-2]) & (m[1:-1] > m[2:])
    peak_idx = idx[1:-1][is_peak]

    peaks = [(float(f[i]), float(m[i])) for i in peak_idx]
    # sort theo biên độ giảm dần
    peaks.sort(key=lambda x: x[1], reverse=True)
    return peaks[:k]

# -----------------------------
# MAIN
# -----------------------------
df = pd.read_csv(LABELED_FILE)
print("Tổng window:", len(df))
print(df["label"].value_counts())

# ----- chọn IMPACT: top K theo g_max -----
imp_df = df[df["label"] == 1].copy()
imp_df = imp_df.sort_values("g_max", ascending=False).head(K_IMPACT)

# ----- chọn NO-IMPACT: các window “vừa phải” -----
no_df = df[df["label"] == 0].copy().sort_values("g_max")

# bỏ bớt cực trị (rất nhỏ & rất lớn)
q30 = no_df["g_max"].quantile(0.30)
q80 = no_df["g_max"].quantile(0.80)
cand_no = no_df[(no_df["g_max"] >= q30) & (no_df["g_max"] <= q80)]

if len(cand_no) >= K_NOIMPACT:
    no_sel = cand_no.sample(K_NOIMPACT, random_state=0)
else:
    no_sel = no_df.sample(min(K_NOIMPACT, len(no_df)), random_state=0)

print("Số impact chọn:", len(imp_df))
print("Số no-impact chọn:", len(no_sel))

impact_mags = []
no_mags = []

# ----- FFT impact -----
for _, row in imp_df.iterrows():
    g = extract_g_window(row)
    freqs, mag = fft_mag(g)
    impact_mags.append(mag)

# ----- FFT no-impact -----
for _, row in no_sel.iterrows():
    g = extract_g_window(row)
    freqs2, mag2 = fft_mag(g)   # freqs2 ~= freqs, nên dùng freqs là đủ
    no_mags.append(mag2)
# =============================
# 1B) TẠO BẢNG PEAK 10×10 (CSV)
# =============================
peak_rows = []

# Impact → class = "impact"
for idx, mag in enumerate(impact_mags):
    peaks = top_peaks(freqs, mag, k=5, fmin=0.5, fmax=120.0)
    for rank, (f0, m0) in enumerate(peaks, start=1):
        peak_rows.append({
            "class": "impact",
            "window_id": idx,        # index trong 10 cửa sổ đã chọn
            "peak_rank": rank,       # 1..5
            "freq_hz": round(f0, 2),
            "magnitude": round(m0, 2),
        })

# No-impact → class = "no-impact"
for idx, mag in enumerate(no_mags):
    peaks = top_peaks(freqs, mag, k=5, fmin=0.5, fmax=120.0)
    for rank, (f0, m0) in enumerate(peaks, start=1):
        peak_rows.append({
            "class": "no-impact",
            "window_id": idx,
            "peak_rank": rank,
            "freq_hz": round(f0, 2),
            "magnitude": round(m0, 2),
        })

df_peaks = pd.DataFrame(peak_rows)
peaks_path = DATA_DIR / "fft_peaks_10x10.csv"
df_peaks.to_csv(peaks_path, index=False, encoding="utf-8-sig")

print("\nĐÃ LƯU BẢNG PEAK 10×10 →", peaks_path)
print(df_peaks.head(20))

# =============================
# 1C) BẢNG TẦN SỐ ĐẶC TRƯNG (GROUP THEO freq)
# =============================
df_peaks["freq_bin"] = df_peaks["freq_hz"]  # ở đây freq đã là 3.91, 5.86,… nên giữ nguyên

summary = (
    df_peaks
    .groupby(["freq_bin", "class"])
    .agg(
        count=("magnitude", "count"),
        mean_mag=("magnitude", "mean"),
    )
    .reset_index()
)

# Pivot số lần xuất hiện theo từng lớp
pivot_count = summary.pivot(index="freq_bin", columns="class", values="count").fillna(0)

summary_path = DATA_DIR / "fft_peaks_summary.csv"
pivot_count.to_csv(summary_path, encoding="utf-8-sig")

print("\n===== BẢNG TẦN SỐ ĐẶC TRƯNG – SỐ LẦN XUẤT HIỆN PEAK =====")
print(pivot_count.sort_index().head(30))
print("\n(ĐÃ LƯU pivot_count →", summary_path, ")")

# =============================
# 2) TRUNG BÌNH FFT & VẼ
# =============================
impact_avg = np.mean(np.vstack(impact_mags), axis=0)
no_avg     = np.mean(np.vstack(no_mags), axis=0)

# ----- vẽ 0–120 Hz -----
mask = (freqs >= 0) & (freqs <= 120)
f_plot    = freqs[mask]
imp_plot  = impact_avg[mask]
no_plot   = no_avg[mask]

plt.figure(figsize=(10, 6))
plt.plot(f_plot, imp_plot, label="Impact (average)", color="red")
plt.plot(f_plot, no_plot, label="No-impact (average, moving)", color="blue")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.title("So sánh FFT trung bình giữa Impact và No-impact (nhiều cửa sổ, chuyển động thật)")
plt.legend()
plt.grid(True)
out_path_avg = DATA_DIR / "fft_compare_avg_multi.png"
plt.savefig(out_path_avg, dpi=200)
plt.close()

print("Đã lưu hình trung bình:", out_path_avg)

# (tuỳ chọn) thêm phiên bản log-scale cho dễ nhìn các dải nhỏ
plt.figure(figsize=(10, 6))
plt.plot(f_plot, imp_plot, label="Impact (average)", color="red")
plt.plot(f_plot, no_plot, label="No-impact (average, moving)", color="blue")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (log scale)")
plt.yscale("log")
plt.title("So sánh FFT trung bình (log-scale) giữa Impact và No-impact")
plt.legend()
plt.grid(True, which="both")
out_path_avg_log = DATA_DIR / "fft_compare_avg_multi_log.png"
plt.savefig(out_path_avg_log, dpi=200)
plt.close()

print("Đã lưu hình log-scale:", out_path_avg_log)

# =============================
# 3) IN CÁC TẦN SỐ ĐỈNH ĐẶC TRƯNG CỦA TRUNG BÌNH
# =============================
print("\n===== Các tần số đỉnh (peaks) của FFT trung bình =====")

imp_peaks = top_peaks(f_plot, imp_plot, k=5, fmin=0.5, fmax=120.0)
no_peaks  = top_peaks(f_plot, no_plot,  k=5, fmin=0.5, fmax=120.0)

print("Impact peaks (freq Hz | magnitude):")
for f0, m0 in imp_peaks:
    print(f"  {f0:6.2f} Hz | {m0:6.2f}")

print("\nNo-impact peaks (freq Hz | magnitude):")
for f0, m0 in no_peaks:
    print(f"  {f0:6.2f} Hz | {m0:6.2f}")

# =============================
# 4) NĂNG LƯỢNG TRUNG BÌNH THEO BAND
# =============================
print("\n===== Năng lượng trung bình từng band (từ labeled_windows_512.csv) =====")
band_cols = ["band_0_4", "band_4_8", "band_12_20", "band_20_40", "band_40_80"]

impact_rows = df[df.label == 1]
noimpact_rows = df[df.label == 0]

for col in band_cols:
    print(f"{col}: impact={impact_rows[col].mean():.2f}   no-impact={noimpact_rows[col].mean():.2f}")
