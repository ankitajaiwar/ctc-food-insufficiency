# download HPS PUF zips (csv + repwgt + dictionary) into data/raw
# python src/01_download.py 22 45
import sys
import time
import zipfile
import requests
from config import RAW, WEEKS

URL = "https://www2.census.gov/programs-surveys/demo/datasets/hhp/{yr}/wk{wk}/HPS_Week{wk}_PUF_CSV.zip"

first, last = (int(x) for x in sys.argv[1:3]) if len(sys.argv) > 2 else (22, 45)
RAW.mkdir(parents=True, exist_ok=True)

for wk in range(first, last + 1):
    if wk not in WEEKS:
        continue
    dest = RAW / f"HPS_Week{wk}_PUF_CSV.zip"
    if dest.exists() and zipfile.is_zipfile(dest):
        continue
    # census puts wk40 under 2021 and wk41+ under 2022
    yr = 2021 if wk <= 40 else 2022
    r = requests.get(URL.format(yr=yr, wk=wk), timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(wk, f"{len(r.content) / 1e6:.0f}MB")
    time.sleep(1)
