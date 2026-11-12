# who benefited most?
# 1) plain subgroup DiDs  2) causal forests, validated on a held-out half (BLP + sorted groups)
#
# uses the clean baseline (wk22-26, before the march stimulus) vs payment weeks (34-40),
# income < 150k. subgroup DiDs are repeated with the wk28-33 baseline as a check.
#
# forest setup: the kids-vs-no-kids gap isn't causal by itself, but its change from
# pre to during is the DiD. so fit one forest per period for the "effect" of having kids,
# predict both on the same people, and take the difference.
import numpy as np
import pandas as pd
import pyfixest as pf
from econml.dml import CausalForestDML
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from config import OUT, CONTROLS, load_clean

SEED = 2021
full = load_clean(include_ext=True)
full = full[full.inc_lt150 == 1]
full["adults"] = full.numper - full.numkid.fillna(0)
full["ba_plus"] = (full.educ >= 6).astype(float)
full["black"] = ((full.race == 2) & (full.hisp == 0)).astype(float)
full["asian"] = ((full.race == 3) & (full.hisp == 0)).astype(float)
full["white"] = ((full.race == 1) & (full.hisp == 0)).astype(float)

clean = full[full.week.between(22, 26) | full.week.between(34, 40)].copy()
alt = full[full.week.between(28, 40)].copy()  # usual baseline


def did(d):
    m = pf.feols(f"food_insuf ~ has_kids + has_kids:during + {CONTROLS} | week + state",
                 data=d, weights="pweight", vcov={"CRV1": "state"})
    r = m.tidy().loc["has_kids:during"]
    return r.Estimate, r["2.5%"], r["97.5%"], r["Pr(>|t|)"]


def pre_rate(d):
    k = d[(d.has_kids == 1) & (d.during == 0)]
    return np.average(k.food_insuf, weights=k.pweight)


# ---- 1) subgroup DiDs ----
groups = {
    "Income": {"Under $35K": lambda d: d.income <= 2, "$35-75K": lambda d: d.income.between(3, 4),
               "$75-150K": lambda d: d.income.between(5, 6)},
    "Race/ethnicity": {"Hispanic": lambda d: d.hisp == 1, "Black": lambda d: d.black == 1,
                       "White": lambda d: d.white == 1, "Asian": lambda d: d.asian == 1},
    "Adults in household": {"One adult": lambda d: d.adults == 1, "Two or more": lambda d: d.adults >= 2},
    "Education": {"No bachelor's": lambda d: d.ba_plus == 0, "Bachelor's+": lambda d: d.ba_plus == 1},
    "Respondent age": {"18-34": lambda d: d.age < 35, "35-49": lambda d: d.age.between(35, 49),
                       "50+": lambda d: d.age >= 50},
}
# number of kids: treated = households with exactly k kids, control = no kids
kid_groups = {"1 child": lambda d: d.numkid == 1, "2 children": lambda d: d.numkid == 2,
              "3+ children": lambda d: d.numkid >= 3}

rows = []
for dim, gs in list(groups.items()) + [("Number of children", kid_groups)]:
    for name, f in gs.items():
        for base, d in [("wk22-26", clean), ("wk28-33", alt)]:
            if dim == "Number of children":
                sub = d[(d.has_kids == 0) | f(d)]
            else:
                sub = d[f(d)]
            est, lo, hi, p = did(sub)
            rows.append(dict(dimension=dim, group=name, baseline=base, estimate=est, lo=lo, hi=hi, p=p,
                             pre_rate_kids=pre_rate(sub), n=len(sub)))
sg = pd.DataFrame(rows)
sg.to_csv(OUT / "subgroup_did.csv", index=False)
show = sg[sg.baseline == "wk22-26"].copy()
show[["estimate", "lo", "hi", "pre_rate_kids"]] = (show[["estimate", "lo", "hi", "pre_rate_kids"]] * 100).round(2)
print(show.drop(columns="baseline").to_string(index=False))

# ---- 2) causal forests ----
X_COLS = ["income", "age", "female", "hisp", "black", "asian", "white", "educ", "married", "adults"]

# split by respondent so train and eval never share people
rng = np.random.default_rng(SEED)
clean["half"] = rng.random(len(clean)) < 0.5
train, test = clean[clean.half], clean[~clean.half].copy()


def fit_forest(d):
    W = pd.get_dummies(d.week.astype(int), prefix="wk", dtype=float)
    W["state"] = d.state.values
    cf = CausalForestDML(
        model_y=HistGradientBoostingRegressor(max_iter=200, random_state=SEED),
        model_t=HistGradientBoostingClassifier(max_iter=200, random_state=SEED),
        discrete_treatment=True, cv=3, n_estimators=600, min_samples_leaf=200,
        max_samples=0.3, random_state=SEED, n_jobs=-1)
    w = d.pweight / d.pweight.mean()
    cf.fit(d.food_insuf.values, d.has_kids.astype(int).values, X=d[X_COLS].values, W=W.values,
           sample_weight=w.values)
    return cf


cf_pre = fit_forest(train[train.during == 0])
cf_dur = fit_forest(train[train.during == 1])

Xt = test[X_COLS].values
test["tau_pre"] = cf_pre.effect(Xt)
test["tau_dur"] = cf_dur.effect(Xt)
test["S"] = test.tau_dur - test.tau_pre  # predicted DiD effect; negative = bigger drop

imp = pd.DataFrame({"feature": X_COLS, "importance_pre": cf_pre.feature_importances_,
                    "importance_during": cf_dur.feature_importances_})
imp.to_csv(OUT / "forest_importance.csv", index=False)
print(imp.sort_values("importance_during", ascending=False).to_string(index=False))

kids_test = test[test.has_kids == 1]
avg_S = np.average(kids_test.S, weights=kids_test.pweight)
print("avg predicted effect, kids hh in test half:", round(avg_S * 100, 2), "pp")

# BLP (Chernozhukov et al.): does the predicted effect line up with the realized DiD?
# slope on kids:during:S_c ~ 1 if well calibrated, > 0 and significant if heterogeneity is real
test["S_c"] = test.S - np.average(test.S, weights=test.pweight)
blp = pf.feols(f"food_insuf ~ has_kids + has_kids:during + has_kids:during:S_c + S_c + has_kids:S_c"
               f" + during:S_c + {CONTROLS} | week + state", data=test, weights="pweight",
               vcov={"CRV1": "state"}).tidy()
blp = blp.loc[["has_kids:during", "has_kids:during:S_c"]]
print(blp)

# sorted groups (GATES): DiD within quartiles of predicted effect, on the held-out half
test["q"] = pd.qcut(test.S, 4, labels=["Q1 (largest predicted drop)", "Q2", "Q3", "Q4 (smallest)"])
gates = []
for q, d in test.groupby("q", observed=True):
    est, lo, hi, p = did(d)
    k = d[d.has_kids == 1]
    gates.append(dict(quartile=q, did=est, lo=lo, hi=hi, p=p, mean_pred=np.average(d.S, weights=d.pweight),
                      n=len(d), pre_rate_kids=pre_rate(d),
                      **{f"kids_{c}": np.average(k[c], weights=k.pweight) for c in
                         ["income", "age", "hisp", "black", "white", "ba_plus", "married", "adults"]},
                      kids_under35k=np.average(k.income <= 2, weights=k.pweight),
                      kids_one_adult=np.average(k.adults == 1, weights=k.pweight)))
gates = pd.DataFrame(gates)
gates.to_csv(OUT / "forest_gates.csv", index=False)
print(gates.round(3).to_string(index=False))

pd.DataFrame([{"term": t, "estimate": r.Estimate, "se": r["Std. Error"], "p": r["Pr(>|t|)"],
               "lo": r["2.5%"], "hi": r["97.5%"]} for t, r in blp.iterrows()] +
             [{"term": "avg predicted effect (kids, test half)", "estimate": avg_S}]
             ).to_csv(OUT / "forest_blp.csv", index=False)
