# subgroup DiD dot plot (from 04 output). python src/05b_subgroups_fig.py [brief]
import sys
import matplotlib.pyplot as plt
import pandas as pd
from config import OUT

sg = pd.read_csv(OUT / "subgroup_did.csv")
sg = sg[sg.baseline == "wk22-26"].copy()
brief = len(sys.argv) > 1 and sys.argv[1] == "brief"
if brief:  # shorter version for the policy brief
    sg = sg[sg.dimension.isin(["Income", "Race/ethnicity", "Number of children", "Education"])]
sg[["estimate", "lo", "hi", "pre_rate_kids"]] *= 100
overall = -3.14  # full-sample DiD, same baseline/weeks (see 04 notes)

bg, ink, gray, grid, blue = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})

# y positions with a gap + header between dimensions
ypos, labels, headers, y = [], [], [], 0
for dim, g in sg.groupby("dimension", sort=False):
    headers.append((y, dim))
    y += 1
    for _, r in g.iterrows():
        ypos.append(y)
        labels.append(f"{r.group}  ({r.pre_rate_kids:.0f}%)")
        y += 1
    y += 0.6

fig, ax = plt.subplots(figsize=(8, 6.2 if brief else 8.4), dpi=200, facecolor=bg)
ax.set_facecolor(bg)
ax.axvline(0, color=gray, lw=1)
ax.axvline(overall, color=gray, lw=1, ls=(0, (3, 3)))
ax.text(overall - 0.15, -1.0, f"all families {overall:.1f} pp", ha="right", va="center", color=gray, fontsize=8)
ax.grid(axis="x", color=grid, lw=0.8, zorder=0)
ax.hlines(ypos, sg.lo, sg.hi, color=blue, lw=2, alpha=0.5, zorder=2)
ax.scatter(sg.estimate, ypos, s=46, color=blue, edgecolor=bg, linewidth=1.5, zorder=3)
for (yy, dim) in headers:
    ax.text(-10.3, yy, dim, fontweight="bold", color=ink, va="center", fontsize=9.5)
ax.set_yticks(ypos)
ax.set_yticklabels(labels, color=ink)
ax.set_xlim(-10.5, 2)
ax.set_ylim(y, -1.6)
ax.tick_params(axis="y", length=0, pad=6)
ax.tick_params(axis="x", colors=gray, length=0)
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(gray)
ax.set_xlabel("Change in food insufficiency gap during payments (percentage points, 95% CI)", color=gray)

fig.text(0.02, 0.97, "The largest drops were among families with the least to begin with", fontsize=12,
         fontweight="bold", color=ink)
sub = ("DiD by subgroup, households with vs. without children, income under $150K. "
       "Baseline Jan–Mar 2021, payment weeks Jul–Dec 2021.\n")
if brief:
    sub = ("Drop in food insufficiency for families with children during the payment months, beyond the change\n"
           "for families without children (income under $150K; Jan–Mar 2021 vs. Jul–Dec 2021).\n")
fig.text(0.02, 0.935 if brief else 0.948, sub +
         "In parentheses: share of families with children food-insufficient at baseline. Black, White, Asian = non-Hispanic.",
         fontsize=8.5, color=gray, va="top")
fig.text(0.02, 0.01, "Source: U.S. Census Bureau, Household Pulse Survey public use files.", fontsize=8, color=gray)
fig.subplots_adjust(left=0.27, right=0.97, top=0.83 if brief else 0.89, bottom=0.09 if brief else 0.07)
fig.savefig(OUT / ("subgroups_brief.png" if brief else "subgroups_150K.png"), facecolor=bg)
