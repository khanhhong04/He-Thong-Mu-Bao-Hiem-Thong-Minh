import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

# Load feature file
df = pd.read_csv(r"E:\smart-helmet\data_logger\imu_fft_features.csv")

# Chọn cột feature
feat_cols = [
    'band_0_10_energy',
    'band_10_20_energy',
    'band_20_40_energy',
    'band_40_60_energy',
    'band_60_80_energy',
    'band_80_120_energy',
    'band_120_200_energy'
]

X = df[feat_cols]
y = df['label']

# scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# train/test (70/30)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42, stratify=y
)

# train model
clf = LogisticRegression()
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_test, y_pred))

print("\n===== CLASSIFICATION REPORT =====")
print(classification_report(y_test, y_pred))

