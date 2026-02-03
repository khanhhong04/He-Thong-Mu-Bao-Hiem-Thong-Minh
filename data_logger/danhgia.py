import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_auc_score,
    roc_curve,
)
from sklearn.utils import resample


# =========================
# CONFIG
# =========================
DATA_DIR = Path(r"E:\smart-helmet\data_logger")
CSV_PATH = DATA_DIR / "labeled_windows_512.csv"

# 8 feature giống ESP (5 band FFT + 3 accel cuối)
FEAT_COLS_ESP = [
    "band_0_4",
    "band_4_8",
    "band_12_20",
    "band_20_40",
    "band_40_80",
    "ax_last",
    "ay_last",
    "az_last",
]

# Nếu sau muốn thử mô hình 12–13 feature lớn hơn thì thêm các cột:
FEAT_COLS_EXTENDED = FEAT_COLS_ESP + [
    "g_rms",
    "g_max",
    "jerk_rms",
    "jerk_max",
]

def train_and_eval(use_extended=False):
    df = pd.read_csv(CSV_PATH)
    print("Tổng window:", len(df))
    print("label")
    print(df["label"].value_counts())
    print()

    feat_cols = FEAT_COLS_EXTENDED if use_extended else FEAT_COLS_ESP

    # Bỏ các dòng có NaN ở feature (nếu có)
    df = df.dropna(subset=feat_cols + ["label"]).reset_index(drop=True)

    X = df[feat_cols].values
    y = df["label"].values.astype(int)

    # train/test split stratified
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    print("=== Train/Test shape ===")
    print("X_train:", X_train.shape, " X_test:", X_test.shape)
    print("y_train label counts:", np.bincount(y_train))
    print("y_test  label counts:", np.bincount(y_test))
    print()

    # =========================
    # Oversample lớp impact để cân bằng (cho dễ train)
    # =========================
    neg_idx = np.where(y_train == 0)[0]
    pos_idx = np.where(y_train == 1)[0]

    n_neg = len(neg_idx)
    n_pos = len(pos_idx)
    print("Trước oversample: pos =", n_pos, ", neg =", n_neg)

    if n_pos > 0 and n_pos < n_neg:
        # oversample positive
        pos_upsampled_idx = resample(
            pos_idx,
            replace=True,
            n_samples=n_neg,
            random_state=42,
        )
        new_idx = np.concatenate([neg_idx, pos_upsampled_idx])
        np.random.shuffle(new_idx)

        X_train_bal = X_train[new_idx]
        y_train_bal = y_train[new_idx]
    else:
        X_train_bal = X_train
        y_train_bal = y_train

    print("Sau oversample: pos =", (y_train_bal == 1).sum(),
          ", neg =", (y_train_bal == 0).sum())
    print()

    # =========================
    # Train logistic
    # =========================
    clf = LogisticRegression(
        solver="lbfgs",
        max_iter=1000,
        class_weight=None,  # đã oversample rồi
    )
    clf.fit(X_train_bal, y_train_bal)

    # =========================
    # Đánh giá với threshold = 0.75
    # =========================
    prob = clf.predict_proba(X_test)[:, 1]
    y_pred = (prob >= 0.75).astype(int)

    cm = confusion_matrix(y_test, y_pred)
    print("===== CONFUSION MATRIX (thr=0.75) =====")
    print(cm)
    print()

    print("===== CLASSIFICATION REPORT =====")
    print(classification_report(y_test, y_pred))
    try:
        auc = roc_auc_score(y_test, prob)
        print("ROC-AUC:", round(auc, 3))
    except Exception as e:
        print("ROC-AUC không tính được:", e)
        auc = None
    print()

    # =========================
    # Sweep threshold (để chọn ngưỡng cho ESP)
    # =========================
    print("===== SWEEP THRESHOLD (cho ESP) =====")
    for thr in [0.9, 0.8, 0.75, 0.7, 0.6, 0.5, 0.4]:
        y_pred_thr = (prob >= thr).astype(int)
        cm_thr = confusion_matrix(y_test, y_pred_thr)
        if cm_thr.shape != (2, 2):
            continue
        tn, fp, fn, tp = cm_thr.ravel()
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # recall lớp 1
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        acc = (tp + tn) / (tp + tn + fp + fn)
        print(f"{thr:.2f}   TPR={tpr:.3f}   FPR={fpr:.3f}   acc={acc:.3f}")
    print()

    # In bias + weight để nếu muốn nhét thẳng lên ESP
    print(f"===== HỆ SỐ LOGISTIC sklearn ({len(feat_cols)} feature) =====")
    print("bias b:", clf.intercept_[0])
    print("w:", clf.coef_[0].tolist())
    print("\nThứ tự feature:")
    for i, name in enumerate(feat_cols):
        print(f"{i} : {name}")

    # =====================================================
    #  VẼ ẢNH ĐỂ ĐƯA VÀO BÁO CÁO
    # =====================================================
    FIG_DIR = DATA_DIR / "figures"
    FIG_DIR.mkdir(exist_ok=True)

    # ---------- 1) CONFUSION MATRIX ----------
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, cmap="Blues")
    plt.title("Confusion Matrix (thr = 0.75)")
    plt.colorbar()
    tick_marks = np.arange(2)
    classes = ["Non-impact", "Impact"]
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)

    # in số lên từng ô
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j, i, str(cm[i, j]),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black"
            )

    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "confusion_matrix.png", dpi=300)
    plt.close()

    # ---------- 2) ROC CURVE ----------
    try:
        fpr, tpr, _ = roc_curve(y_test, prob)
        plt.figure(figsize=(6, 5))
        plt.plot(fpr, tpr, label=f"AUC = {auc:.3f}" if auc is not None else "ROC")
        plt.plot([0, 1], [0, 1], "--", color="gray")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend()
        plt.tight_layout()
        plt.savefig(FIG_DIR / "roc_curve.png", dpi=300)
        plt.close()
    except Exception as e:
        print("Không vẽ ROC được:", e)

    # ---------- 3) Histogram: Probability distribution ----------
    plt.figure(figsize=(6, 5))
    plt.hist(prob[y_test == 0], bins=20, alpha=0.6, label="Non-impact")
    plt.hist(prob[y_test == 1], bins=20, alpha=0.6, label="Impact")
    plt.axvline(0.75, color="black", linestyle="--", label="Threshold 0.75")
    plt.xlabel("Predicted Probability (Impact)")
    plt.ylabel("Count")
    plt.title("Distribution of Predicted Probabilities")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "probability_histogram.png", dpi=300)
    plt.close()

    print("\nẢnh đã được lưu vào:", FIG_DIR)


if __name__ == "__main__":
    # Đánh giá với 8 feature giống ESP
    print("=== ĐÁNH GIÁ VỚI 8 FEATURE (ESP) ===")
    train_and_eval(use_extended=False)

    # Nếu muốn thử luôn bản extended (13 feature) thì bỏ comment:
    # print("\n=== ĐÁNH GIÁ VỚI 12/13 FEATURE (EXTENDED) ===")
    # train_and_eval(use_extended=True)
