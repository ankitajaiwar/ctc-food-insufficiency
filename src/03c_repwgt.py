# replicate weight SEs for the main DiD
# Var = 4/80 * sum_r (b_r - b)^2  (census successive difference replication)
# pyfixest kept running out of memory refitting 80x, so just do WLS with dummies in numpy
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from config import CLEAN, OUT, load_clean

RW = CLEAN / "repwgt.parquet"
TERMS = ["has_kids:during", "has_kids:post"]


def make_X(d):
    X = pd.DataFrame({
        "const": 1.0, "has_kids": d.has_kids,
        "has_kids:during": d.has_kids * d.during, "has_kids:post": d.has_kids * d.post,
        "age": d.age, "age2": d.age ** 2, "female": d.female, "hisp": d.hisp,
        "married": d.married, "numper": d.numper,
    })
    fe = [pd.get_dummies(d[c].astype(int), prefix=c, drop_first=True, dtype=float)
          for c in ["race", "educ", "week", "state"]]
    return pd.concat([X] + fe, axis=1)


def wls(X, y, w):
    Xw = X * w[:, None]
    return np.linalg.solve(Xw.T @ X, Xw.T @ y)


def repwgt_se(d, label):
    ids = pq.read_table(RW, columns=["SCRAM", "week"]).to_pandas()
    ids["row"] = np.arange(len(ids))
    d = d.merge(ids, left_on=["scram", "week"], right_on=["SCRAM", "week"])
    Xdf = make_X(d)
    idx = [Xdf.columns.get_loc(t) for t in TERMS]
    X, y = Xdf.to_numpy(float), d.food_insuf.to_numpy(float)
    b = wls(X, y, d.pweight.to_numpy(float))[idx]  # should match 03_did
    bs = []
    for r in range(1, 81):
        w = pq.read_table(RW, columns=[f"PWEIGHT{r}"]).column(0).to_numpy()[d.row.values]
        bs.append(wls(X, y, w.astype(float))[idx])
    se = np.sqrt(4 / 80 * ((np.array(bs) - b) ** 2).sum(axis=0))
    return pd.DataFrame({"sample": label, "term": TERMS, "estimate": b, "se_repwgt": se,
                         "lo": b - 1.96 * se, "hi": b + 1.96 * se, "n": len(d)})


df = load_clean()
res = pd.concat([repwgt_se(df[df.inc_lt150 == 1], "<150K"), repwgt_se(df[df.inc_lt75 == 1], "<75K")])
res.to_csv(OUT / "did_repwgt_se.csv", index=False)
print(res)
