# shared settings for the CTC analysis
import os
from pathlib import Path
import pandas as pd

# override with env vars to run on the synthetic test data
RAW = Path(os.environ.get("HPS_RAW", "data/raw"))
CLEAN = Path(os.environ.get("HPS_CLEAN", "data/clean"))
OUT = Path(os.environ.get("HPS_OUT", "output"))

# HPS week -> (phase, start, end, period)
# dates from the Census week pages / Phase 3.x source & accuracy statements
# CTC advance payments: 7/15, 8/13, 9/15, 10/15, 11/15, 12/15/2021
# 22-27 only used for the extended baseline (EIP3 checks landed ~3/12-3/17)
WEEKS = {
    22: ("3.0", "2021-01-06", "2021-01-18", "pre_ext"),
    23: ("3.0", "2021-01-20", "2021-02-01", "pre_ext"),
    24: ("3.0", "2021-02-03", "2021-02-15", "pre_ext"),
    25: ("3.0", "2021-02-17", "2021-03-01", "pre_ext"),
    26: ("3.0", "2021-03-03", "2021-03-15", "pre_ext"),
    27: ("3.0", "2021-03-17", "2021-03-29", "pre_ext"),
    28: ("3.1", "2021-04-14", "2021-04-26", "pre"),
    29: ("3.1", "2021-04-28", "2021-05-10", "pre"),
    30: ("3.1", "2021-05-12", "2021-05-24", "pre"),
    31: ("3.1", "2021-05-26", "2021-06-07", "pre"),
    32: ("3.1", "2021-06-09", "2021-06-21", "pre"),
    33: ("3.1", "2021-06-23", "2021-07-05", "pre"),
    34: ("3.2", "2021-07-21", "2021-08-02", "during"),
    35: ("3.2", "2021-08-04", "2021-08-16", "during"),
    36: ("3.2", "2021-08-18", "2021-08-30", "during"),
    37: ("3.2", "2021-09-01", "2021-09-13", "during"),
    38: ("3.2", "2021-09-15", "2021-09-27", "during"),
    39: ("3.2", "2021-09-29", "2021-10-11", "during"),
    # no collection 10/12 - 11/30
    40: ("3.3", "2021-12-01", "2021-12-13", "during"),  # before the 12/15 payment
    41: ("3.3", "2021-12-29", "2022-01-10", "post"),
    42: ("3.3", "2022-01-26", "2022-02-07", "post"),
    43: ("3.4", "2022-03-02", "2022-03-14", "post"),
    44: ("3.4", "2022-03-30", "2022-04-11", "post"),
    45: ("3.4", "2022-04-27", "2022-05-09", "post"),
}

REF_WEEK = 33      # last full week before first payment
PLACEBO_WEEK = 31

CONTROLS = "age + I(age**2) + female + hisp + C(race) + C(educ) + married + numper"


def load_clean(include_ext=False):
    df = pd.read_parquet(CLEAN / "hps_ctc.parquet")
    if not include_ext:
        df = df[df.period != "pre_ext"]
    return df.dropna(subset=["food_insuf", "has_kids", "pweight", "state", "age", "female",
                             "hisp", "race", "educ", "married", "numper", "income"])
