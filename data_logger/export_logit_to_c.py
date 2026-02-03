import joblib, json
from pathlib import Path
import numpy as np

MODELS = Path("models")
bundle = joblib.load(MODELS / "impact_logit.joblib")
pipe  = bundle["model"]
feat_names = bundle["features"]

scaler = pipe.named_steps["standardscaler"]
logit  = pipe.named_steps["logisticregression"]

coef = logit.coef_.reshape(-1)        # shape (28,)
bias = float(logit.intercept_[0])     # scalar
scale = scaler.scale_.reshape(-1)     # shape (28,)
# LƯU Ý: bạn dùng StandardScaler(with_mean=False), nên on-device chỉ cần chia cho scale_

assert len(feat_names) == len(coef) == len(scale) == 28, "Feature mismatch!"

# Xuất ra .h
out_h = Path("impact_logit_model.h")
with out_h.open("w", encoding="utf-8") as f:
    f.write("// Auto-generated from export_logit_to_c.py\n")
    f.write("#pragma once\n\n")
    f.write(f"#define IMPACT_FEAT_DIM {len(coef)}\n\n")

    def arr(name, arr):
        f.write(f"static const float {name}[IMPACT_FEAT_DIM] = {{\n")
        for i, v in enumerate(arr):
            end = "," if i < len(arr)-1 else ""
            f.write(f"  {float(v):.8f}{end}\n")
        f.write("};\n\n")

    arr("IMPACT_W", coef)
    arr("IMPACT_SCALE", scale)
    f.write(f"static const float IMPACT_BIAS = {bias:.8f};\n\n")

    # Ghi kèm thứ tự feature để đồng bộ firmware
    f.write("/* Feature order (must match firmware):\n")
    for i, n in enumerate(feat_names):
        f.write(f"{i:02d}: {n}\n")
    f.write("*/\n")

print("Exported:", out_h.resolve())
print("Feature order:", feat_names)
