# Who benefited from the 2021 expanded Child Tax Credit?

**Status: work in progress.** The pipeline is built and tested on synthetic data. No results on real Household Pulse data yet.

<!-- Event-study chart goes here once estimated on real data -->

## Question

Did the 2021 advance Child Tax Credit (CTC) payments reduce food insufficiency among families with children? Which families benefited most?

The American Rescue Plan Act made the 2021 CTC larger and fully refundable. The IRS paid half of it in advance, in six monthly payments (Jul 15, Aug 13, Sep 15, Oct 15, Nov 15 and Dec 15, 2021). No payment followed in January 2022.

## Data

The data are the Census Bureau's Household Pulse Survey (HPS) public use files for weeks 28–45, which are repeated cross-sections of adults.

| Period | HPS weeks | Collection dates |
|---|---|---|
| Pre | 28–33 (Phase 3.1) | Apr 14 – Jul 5, 2021 |
| During | 34–39 (Phase 3.2), 40 (Phase 3.3) | Jul 21 – Oct 11, 2021; Dec 1–13, 2021 |
| Post | 41–42 (Phase 3.3), 43–45 (Phase 3.4) | Dec 29, 2021 – May 9, 2022 |

HPS did not collect data from Oct 12 to Nov 30, 2021.

The outcome is `CURFOODSUF`, coded 1 if the household sometimes or often did not have enough to eat in the last 7 days. The treated group is respondents with children in the household (`THHLD_NUMKID > 0`). The comparison group is respondents without children. The main sample is limited to 2020 household income under $150K, with an additional version under $75K.

## Method

- **Difference-in-differences:** a weighted linear probability model (`PWEIGHT`) with week and state fixed effects and demographic covariates. The key terms are kids × during and kids × post. Standard errors are clustered by state, and also computed with Census successive-difference replicate weights (80 replicates).
- **Event study:** kids × week interactions, with week 33 (Jun 23 – Jul 5, 2021) as the reference week.
- **Robustness checks:** a placebo start at week 31, a triple difference (kids × income under $35K × period), difficulty paying usual household expenses (`EXPNS_DIF`) as an alternative outcome, and an all-incomes sample.
- **Heterogeneity:** causal forests, validated with subgroup DiD regressions (in progress).

## Reproduce

```bash
pip install -r requirements.txt
python src/01_download.py 22 45          # 24 zips from www2.census.gov into data/raw/
python src/02_clean.py                    # writes data/clean/ and a variable audit
python src/03_did.py                      # main DiD, event study, placebo, robustness
python src/03b_pretrend.py                # extended event study + pre-trend checks
python src/03c_repwgt.py                  # replicate-weight SEs (PWEIGHT1-80)
python src/05_figures.py                  # event-study chart
```

To test without downloading anything, see `tests/make_synthetic.py` (fake data; paths are set with `HPS_RAW` / `HPS_CLEAN` / `HPS_OUT`). Week dates and shared settings live in `src/config.py`.

## Limitations

- Parallel trends may fail, because COVID-era shocks hit households with and without children differently.
- The data are repeated cross-sections, not a panel.
- Answers are self-reported, and response rates are low (about 5–7%).
- Other policies changed at the same time: SNAP emergency allotments, universal free school meals in 2021–22, and the end of federal pandemic unemployment benefits in September 2021.
- The unit is the adult respondent, not the household.
