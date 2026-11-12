# main DiD + event study + robustness
# weighted LPM, week & state FE, controls, SE clustered by state
import pandas as pd
import pyfixest as pf
from config import OUT, REF_WEEK, PLACEBO_WEEK, CONTROLS, load_clean

df = load_clean()
s150 = df[df.inc_lt150 == 1]
s75 = df[df.inc_lt75 == 1]
OUT.mkdir(exist_ok=True)

DID = "{y} ~ has_kids + has_kids:during + has_kids:post + " + CONTROLS + " | week + state"


def fit(formula, data):
    return pf.feols(formula, data=data, weights="pweight", vcov={"CRV1": "state"})


def grab(model, name, terms):
    t = model.tidy().reset_index()
    t = t[t.Coefficient.isin(terms)]
    t.insert(0, "model", name)
    t["nobs"] = model._N
    return t[["model", "Coefficient", "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%", "nobs"]]


keys = ["has_kids:during", "has_kids:post"]
res = [
    grab(fit(DID.format(y="food_insuf"), s150), "main_<150K", keys),
    grab(fit(DID.format(y="food_insuf"), s75), "main_<75K", keys),
    grab(fit(DID.format(y="expense_dif"), s150.dropna(subset=["expense_dif"])), "alt_outcome_expenses_<150K", keys),
    grab(fit(DID.format(y="food_insuf"), df), "all_incomes", keys),
]

# placebo: pretend treatment starts at wk31, pre weeks only
pre = s150[s150.week <= REF_WEEK].copy()
pre["fake"] = (pre.week >= PLACEBO_WEEK).astype(float)
res.append(grab(fit("food_insuf ~ has_kids + has_kids:fake + " + CONTROLS + " | week + state", pre),
                f"placebo_wk{PLACEBO_WEEK}", ["has_kids:fake"]))

# triple diff: low income (<35k) x kids x period
ddd = fit("food_insuf ~ has_kids*inc_lt35 + has_kids:during + has_kids:post + inc_lt35:during"
          " + inc_lt35:post + has_kids:inc_lt35:during + has_kids:inc_lt35:post + "
          + CONTROLS + " | week + state", s150)
res.append(grab(ddd, "ddd_lowinc_<150K", ["has_kids:inc_lt35:during", "has_kids:inc_lt35:post"]))

res = pd.concat(res, ignore_index=True)
res.to_csv(OUT / "did_results.csv", index=False)
print(res.to_string(index=False))

# event study, ref = wk33
es = fit(f"food_insuf ~ i(week, has_kids, ref={REF_WEEK}) + has_kids + " + CONTROLS + " | week + state", s150)
es = es.tidy().reset_index()
es = es[es.Coefficient.str.contains("week::")]
es["week"] = es.Coefficient.str.extract(r"week::(\d+)")[0].astype(int)
es = pd.concat([es, pd.DataFrame([{"week": REF_WEEK, "Estimate": 0.0, "2.5%": 0.0, "97.5%": 0.0}])])
es = es.sort_values("week")[["week", "Estimate", "Std. Error", "2.5%", "97.5%"]]
es.to_csv(OUT / "event_study.csv", index=False)
print(es.to_string(index=False))

# N is respondents (adults), not households
pd.DataFrame({"sample": ["<150K", "<75K", "all"],
              "respondents": [len(s150), len(s75), len(df)]}).to_csv(OUT / "sample_sizes.csv", index=False)
