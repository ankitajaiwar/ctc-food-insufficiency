# fake HPS-shaped zips to test the pipeline without downloading anything.
# numbers are made up -- don't use anything from this for results.
#   python tests/make_synthetic.py
#   HPS_RAW=data/synthetic HPS_CLEAN=data/synthetic_clean HPS_OUT=output_synthetic python src/02_clean.py
import sys
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from config import WEEKS

rng = np.random.default_rng(0)
out = Path("data/synthetic")
out.mkdir(parents=True, exist_ok=True)

for wk, (phase, _, _, period) in WEEKS.items():
    n = 4000
    kids = rng.poisson(0.7, n)
    inc = rng.integers(1, 9, n)
    effect = {"pre_ext": 0, "pre": 0, "during": -0.03, "post": -0.005}[period] * (kids > 0)
    p = np.clip(0.12 - 0.012 * inc + 0.02 * (kids > 0) + effect, 0.01, 1)
    df = pd.DataFrame({
        "SCRAM": [f"V{wk}_{i}" for i in range(n)], "WEEK": wk,
        "EST_ST": rng.choice([1, 6, 12, 34, 36, 48], n),
        "PWEIGHT": rng.uniform(500, 5000, n), "HWEIGHT": rng.uniform(500, 5000, n),
        "CURFOODSUF": np.where(rng.random(n) < p, rng.choice([3, 4], n), rng.choice([1, 2], n)),
        "THHLD_NUMKID": kids, "THHLD_NUMPER": kids + rng.integers(1, 4, n), "INCOME": inc,
        "TBIRTH_YEAR": rng.integers(1940, 2003, n),
        ("EGENDER" if wk <= 33 else "EGENID_BIRTH"): rng.integers(1, 3, n),
        "RRACE": rng.integers(1, 5, n), "RHISPANIC": rng.integers(1, 3, n),
        "EEDUC": rng.integers(1, 8, n), "MS": rng.integers(1, 6, n), "EXPNS_DIF": rng.integers(1, 5, n),
    })
    if 34 <= wk <= 42:
        df["CTC_YN"] = rng.integers(1, 3, n)
    rw = pd.DataFrame({"SCRAM": df.SCRAM, "WEEK": wk,
                       **{f"PWEIGHT{r}": df.PWEIGHT * rng.uniform(0.8, 1.2, n) for r in range(1, 81)}})
    with zipfile.ZipFile(out / f"HPS_Week{wk}_PUF_CSV.zip", "w") as z:
        z.writestr(f"pulse_puf_{wk}.csv", df.to_csv(index=False))
        z.writestr(f"pulse_repwgt_puf_{wk}.csv", rw.to_csv(index=False))
print("wrote", out)
