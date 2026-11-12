# stack HPS weeks into one file, harmonize names, build outcome/treatment
# check codes against pulse20XX_data.dictionary_CSV_<wk>.xlsx in each zip
import zipfile
import numpy as np
import pandas as pd
from config import RAW, CLEAN, WEEKS

# new name -> possible source names (first one found wins)
VARS = {
    "scram": ["SCRAM"], "state": ["EST_ST"], "pweight": ["PWEIGHT"], "hweight": ["HWEIGHT"],
    "foodsuf": ["CURFOODSUF"], "numkid": ["THHLD_NUMKID"], "numper": ["THHLD_NUMPER"],
    "income": ["INCOME"], "birth_year": ["TBIRTH_YEAR"],
    "sex": ["EGENID_BIRTH", "EGENDER"],  # EGENDER through 3.1
    "race": ["RRACE"], "hispanic": ["RHISPANIC"], "educ": ["EEDUC"], "marital": ["MS"],
    "expns_dif": ["EXPNS_DIF"],
    "ctc_recv": ["CTC_YN"],  # wk34-42 only
}
# NB: INCOME is 2019 income through wk33, 2020 income from wk34


def read_week(wk):
    z = zipfile.ZipFile(RAW / f"HPS_Week{wk}_PUF_CSV.zip")
    csvs = [n for n in z.namelist() if n.endswith(".csv")]
    puf = [n for n in csvs if "repwgt" not in n][0]
    rep = [n for n in csvs if "repwgt" in n][0]
    keep = {c for v in VARS.values() for c in v}
    df = pd.read_csv(z.open(puf), usecols=lambda c: c in keep)
    rw = pd.read_csv(z.open(rep), dtype={f"PWEIGHT{i}": "float32" for i in range(1, 81)})
    return df, rw


frames, reps, found = [], [], {}
for wk in WEEKS:
    raw, rw = read_week(wk)
    df = pd.DataFrame(index=raw.index)
    for new, olds in VARS.items():
        src = next((c for c in olds if c in raw.columns), None)
        found[(new, wk)] = src
        df[new] = raw[src] if src else np.nan
    df = df.replace([-99, -88], np.nan)
    df["week"] = wk

    # 1/2 = enough food, 3/4 = sometimes/often not enough
    df["food_insuf"] = df.foodsuf.map({1: 0, 2: 0, 3: 1, 4: 1})
    df["expense_dif"] = df.expns_dif.map({1: 0, 2: 0, 3: 1, 4: 1})
    df["has_kids"] = (df.numkid > 0).astype(float).where(df.numkid.notna())

    # income brackets: 1 <25k, 2 25-35, 3 35-50, 4 50-75, 5 75-100, 6 100-150, 7 150-200, 8 200+
    df["inc_lt150"] = (df.income <= 6).astype(float).where(df.income.notna())
    df["inc_lt75"] = (df.income <= 4).astype(float).where(df.income.notna())
    df["inc_lt35"] = (df.income <= 2).astype(float).where(df.income.notna())

    df["age"] = (2021 if wk <= 40 else 2022) - df.birth_year
    df["female"] = (df.sex == 2).astype(float)
    df["hisp"] = (df.hispanic == 2).astype(float)
    df["married"] = (df.marital == 1).astype(float)
    df["single_adult_hh"] = ((df.numper - df.numkid) == 1).astype(float)

    df["period"] = WEEKS[wk][3]
    df["during"] = float(df.period.iloc[0] == "during")
    df["post"] = float(df.period.iloc[0] == "post")
    frames.append(df)
    reps.append(rw.assign(week=wk))
    print(wk, len(df), sorted(df.foodsuf.dropna().unique()), sorted(df.income.dropna().unique()))

CLEAN.mkdir(parents=True, exist_ok=True)
data = pd.concat(frames, ignore_index=True)
data.to_parquet(CLEAN / "hps_ctc.parquet")
pd.concat(reps, ignore_index=True).to_parquet(CLEAN / "repwgt.parquet")

audit = pd.Series(found).unstack().fillna("MISSING")
audit.to_csv(CLEAN / "variable_audit.csv")
print(audit[(audit == "MISSING").any(axis=1)])
print("n =", len(data))

ok = data.dropna(subset=["food_insuf", "has_kids"])
print(ok.groupby(["period", "has_kids"]).apply(
    lambda g: np.average(g.food_insuf, weights=g.pweight), include_groups=False).unstack())
