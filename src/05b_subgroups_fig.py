# subgroup DiD dot plot (from 04 output)
import matplotlib.pyplot as plt
import pandas as pd
from config import OUT

sg = pd.read_csv(OUT / "subgroup_did.csv")
sg = sg[sg.baseline == "wk22-26"].copy()
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

fig, ax = plt.subplots(figsize=(8, 8.4), dpi=200, facecolor=bg)
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

fig.text(0.02, 0.975, "The largest drops were among families with the least to begin with", fontsize=12,
         fontweight="bold", color=ink)
fig.text(0.02, 0.948, "DiD by subgroup, households with vs. without children, income under $150K. "
         "Baseline Jan–Mar 2021, payment weeks Jul–Dec 2021.\n"
         "In parentheses: share of families with children food-insufficient at baseline. Black, White, Asian = non-Hispanic.",
         fontsize=8.5, color=gray, va="top")
fig.text(0.02, 0.01, "Source: U.S. Census Bureau, Household Pulse Survey public use files.", fontsize=8, color=gray)
fig.subplots_adjust(left=0.27, right=0.97, top=0.89, bottom=0.07)
fig.savefig(OUT / "subgroups_150K.png", facecolor=bg)
