# the wk28-33 pre-period isn't flat. checking whether that's the march 2021 stimulus
# (EIP3, $1400/person incl. kids) wearing off, plus a few other pre-trend checks
import numpy as np
import pandas as pd
import pyfixest as pf
from config import OUT, WEEKS, CONTROLS, load_clean


def fit(formula, data):
    return pf.feols(formula, data=data, weights="pweight", vcov={"CRV1": "state"})


def event_study(data, ref):
    m = fit(f"food_insuf ~ i(week, has_kids, ref={ref}) + has_kids + {CONTROLS} | week + state", data)
    t = m.tidy().reset_index()
    t = t[t.Coefficient.str.contains("week::")]
    t["week"] = t.Coefficient.str.extract(r"week::(\d+)")[0].astype(int)
    t = pd.concat([t, pd.DataFrame([{"week": ref, "Estimate": 0.0, "Std. Error": 0.0}])])
    t = t.sort_values("week")[["week", "Estimate", "Std. Error"]].reset_index(drop=True)
    t["lo"] = t.Estimate - 1.96 * t["Std. Error"]
    t["hi"] = t.Estimate + 1.96 * t["Std. Error"]
    t["period"] = t.week.map(lambda w: WEEKS[w][3])
    t["start"] = t.week.map(lambda w: WEEKS[w][1])
    return t


def row(m, term, label, **extra):
    r = m.tidy().loc[term]
    return dict(check=label, estimate=r.Estimate, lo=r["2.5%"], hi=r["97.5%"], p=r["Pr(>|t|)"], **extra)


full = load_clean(include_ext=True)
main = full[full.period != "pre_ext"]
s150 = main[main.inc_lt150 == 1]
out = []

# 1) event study back to jan 2021, ref = wk26 (last week before EIP3)
for tag, d in [("150K", full[full.inc_lt150 == 1]), ("all", full)]:
    es = event_study(d, ref=26)
    es.to_csv(OUT / f"event_study_ext_{tag}.csv", index=False)
    print(tag, (es.set_index("week")[["Estimate", "lo", "hi"]] * 100).round(2).T, sep="\n")

# 2) recenter on the pre-period mean, 3) subtract a linear fit to the pre coefs
es = event_study(s150, ref=33)
pre_mean = es.loc[es.period == "pre", "Estimate"].mean()
es["Estimate_vs_premean"] = es.Estimate - pre_mean
pre = es[es.period == "pre"]
slope, b0 = np.polyfit(pre.week, pre.Estimate, 1)
es["Estimate_detrended"] = es.Estimate - (b0 + slope * es.week)
es.to_csv(OUT / "event_study_main_diagnostics.csv", index=False)
for p in ["during", "post"]:
    out.append(dict(check=f"pre-mean reference: mean {p} coef", estimate=es.loc[es.period == p, "Estimate_vs_premean"].mean()))
    out.append(dict(check=f"linear pre-trend removed: mean {p} coef", estimate=es.loc[es.period == p, "Estimate_detrended"].mean()))
out.append(dict(check="pre-trend slope per HPS week (wk 28-33)", estimate=slope))

# 4) kids x linear trend in the DiD (trend in 2-wk units)
d = s150.copy()
t0 = pd.Timestamp(WEEKS[28][1])
d["trend"] = d.week.map(lambda w: (pd.Timestamp(WEEKS[w][1]) - t0).days / 14)
m = fit(f"food_insuf ~ has_kids + has_kids:trend + has_kids:during + has_kids:post + {CONTROLS} | week + state", d)
for term in ["has_kids:during", "has_kids:post", "has_kids:trend"]:
    out.append(row(m, term, f"DiD + kids x trend: {term}"))

# 5) tight windows around the first payment
for tag, base in [("<150K", s150), ("all", main)]:
    for wks in [(33, 34), (32, 33, 34, 35)]:
        m = fit(f"food_insuf ~ has_kids + has_kids:during + {CONTROLS} | week + state", base[base.week.isin(wks)])
        out.append(row(m, "has_kids:during", f"short window {wks} {tag}", n=m._N))

# 6) did EIP3 itself move the gap? wk25-26 vs wk27-28
for tag, base in [("<150K", full[full.inc_lt150 == 1]), ("all", full)]:
    d = base[base.week.isin([25, 26, 27, 28])].copy()
    d["after_eip3"] = (d.week >= 27).astype(float)
    m = fit(f"food_insuf ~ has_kids + has_kids:after_eip3 + {CONTROLS} | week + state", d)
    out.append(row(m, "has_kids:after_eip3", f"EIP3 effect, weeks 25-26 vs 27-28 {tag}"))

# 7) same DiD but with the clean jan-mar baseline (drop wk27-33)
clean = full[(full.week <= 26) | (full.week >= 34)]
for tag, d in [("<150K", clean[clean.inc_lt150 == 1]), ("<75K", clean[clean.inc_lt75 == 1]),
               ("<35K", clean[clean.inc_lt35 == 1]), ("all", clean)]:
    m = fit(f"food_insuf ~ has_kids + has_kids:during + has_kids:post + {CONTROLS} | week + state", d)
    for term in ["has_kids:during", "has_kids:post"]:
        out.append(row(m, term, f"baseline wk22-26 {tag}: {term}", n=len(d)))

out = pd.DataFrame(out)
out.to_csv(OUT / "pretrend_checks.csv", index=False)
show = out.copy()
show[["estimate", "lo", "hi"]] = (show[["estimate", "lo", "hi"]] * 100).round(2)
print(show.to_string(index=False))
