# event study plot (from 03b output). python src/05_figures.py [150K|all]
import sys
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from config import OUT

sample = sys.argv[1] if len(sys.argv) > 1 else "150K"
es = pd.read_csv(OUT / f"event_study_ext_{sample}.csv", parse_dates=["start"])
es["mid"] = es.start + pd.Timedelta(days=6)
es[["Estimate", "lo", "hi"]] *= 100

bg, ink, gray, grid, blue, band = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6", "#f0efec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200, facecolor=bg)
ax.set_facecolor(bg)

ax.axvspan(pd.Timestamp("2021-07-15"), pd.Timestamp("2021-12-15"), color=band, zorder=0)
ax.text(pd.Timestamp("2021-09-29"), 3.45, "Monthly CTC payments\nJul 15 – Dec 15, 2021",
        ha="center", va="top", color=gray, fontsize=9)
ax.axvline(pd.Timestamp("2021-03-17"), color=gray, lw=1, ls=(0, (3, 3)))
ax.text(pd.Timestamp("2021-03-20"), 3.45, "$1,400 stimulus\nchecks arrive", va="top", color=gray, fontsize=9)
ax.axhline(0, color=gray, lw=1)
ax.grid(axis="y", color=grid, lw=0.8, zorder=0)

ax.vlines(es.mid, es.lo, es.hi, color=blue, lw=1.5, alpha=0.45, zorder=2)
# don't connect across the oct-nov survey gap
gap = pd.Timestamp("2021-11-01")
ax.plot(es.mid[es.mid < gap], es.Estimate[es.mid < gap], color=blue, lw=2, zorder=3)
ax.plot(es.mid[es.mid > gap], es.Estimate[es.mid > gap], color=blue, lw=2, zorder=3)
ax.scatter(es.mid, es.Estimate, s=40, color=blue, edgecolor=bg, linewidth=1.5, zorder=4)

ref = es[es.Estimate == 0].iloc[0]
ax.annotate("reference\n(Mar 3–15)", (ref.mid, 0), xytext=(-10, -42), textcoords="offset points",
            ha="right", color=gray, fontsize=8.5)
ax.text(pd.Timestamp("2021-11-06"), -5.6, "no survey\nOct 12 – Nov 30", ha="center", color=gray, fontsize=8)

ax.set_ylim(-6.2, 3.6)
ax.set_ylabel("Difference vs. reference (percentage points)", color=gray)
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 3, 5, 7, 9, 11]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(gray)
ax.tick_params(colors=gray, length=0)

inc = "under $150K" if sample == "150K" else "all levels"
fig.text(0.06, 0.965, "Food insufficiency fell for families with children while CTC payments were arriving",
         fontsize=12, fontweight="bold", color=ink)
fig.text(0.06, 0.885, "Gap in the share reporting sometimes/often not enough to eat, households with vs. without "
         f"children, income {inc}.\nWeighted event-study estimates with 95% CIs; week and state fixed effects, "
         "demographic controls, SEs clustered by state.", fontsize=8.5, color=gray)
fig.text(0.06, 0.015, "Source: U.S. Census Bureau, Household Pulse Survey public use files, weeks 22–45.",
         fontsize=8, color=gray)
fig.subplots_adjust(left=0.09, right=0.98, top=0.82, bottom=0.14)
fig.savefig(OUT / f"event_study_{sample}.png", facecolor=bg)
