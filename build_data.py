"""
build_data.py

Reads seoul-apt-latest.csv (Seoul-wide apartment transaction data) and writes
data/yangcheon.json — a compact, index-referenced dataset scoped to Yangcheon-gu
(양천구), covering 매매 (sale) and 전세 (jeonse) transactions only.

Python standard library only (course project constraint: no pandas / third-party
packages).

See PRD.md sections 4.2 (data contract) and 4.4 (calculation rules).
"""

import csv
import json
import os

SRC_CSV = "seoul-apt-latest.csv"
OUT_DIR = "data"
OUT_PATH = os.path.join(OUT_DIR, "yangcheon.json")

TARGET_GU = "양천구"
GENERATED_DATE = "2026-08-12"
SOURCE_LABEL = "서울열린데이터광장 서울시 부동산 실거래가 정보(OA-21275)"


def parse_float(value):
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int_amount(value):
    """Amounts are integers stored as strings (may contain no decimals)."""
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def main():
    dongs_set = set()
    months_set = set()

    # Raw rows kept for a second pass, since we need the full dong/month
    # index sets built first (indices must be stable and sorted).
    sale_rows = []   # (dong, complex, month, area, floor, price)
    jeonse_rows = []  # (dong, complex, month, area, floor, deposit)

    with open(SRC_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("gu") != TARGET_GU:
                continue

            deal_type = row.get("deal_type")
            if deal_type not in ("매매", "전세"):
                continue  # drop 월세 entirely (and any unexpected values)

            area = parse_float(row.get("area_m2"))
            floor = parse_float(row.get("floor"))
            if area is None or floor is None:
                continue  # skip rows where area_m2 / floor fail to parse

            dong = row.get("dong")
            complex_name = row.get("complex")
            month = row.get("contract_ym")

            if deal_type == "매매":
                price = parse_int_amount(row.get("price"))
                if price is None:
                    continue
                sale_rows.append((dong, complex_name, month, area, floor, price))
                dongs_set.add(dong)
                months_set.add(month)
            else:  # 전세
                deposit = parse_int_amount(row.get("deposit"))
                if deposit is None:
                    continue
                jeonse_rows.append((dong, complex_name, month, area, floor, deposit))
                dongs_set.add(dong)
                months_set.add(month)

    dongs = sorted(dongs_set)
    months = sorted(months_set)
    dong_idx = {d: i for i, d in enumerate(dongs)}
    month_idx = {m: i for i, m in enumerate(months)}

    # complex identity = (dong, complex_name) pair, since a complex name can
    # repeat across dongs.
    complex_key_to_idx = {}
    complexes = []  # [dongIdx, complexName]

    def get_complex_idx(dong, complex_name):
        key = (dong, complex_name)
        idx = complex_key_to_idx.get(key)
        if idx is None:
            idx = len(complexes)
            complex_key_to_idx[key] = idx
            complexes.append([dong_idx[dong], complex_name])
        return idx

    sales = []
    for dong, complex_name, month, area, floor, price in sale_rows:
        cx = get_complex_idx(dong, complex_name)
        m = month_idx[month]
        sales.append([cx, m, round(area, 1), int(floor), int(price)])

    jeonse = []
    for dong, complex_name, month, area, floor, deposit in jeonse_rows:
        cx = get_complex_idx(dong, complex_name)
        m = month_idx[month]
        jeonse.append([cx, m, round(area, 1), int(floor), int(deposit)])

    data = {
        "meta": {
            "gu": TARGET_GU,
            "period": {"from": months[0], "to": months[-1]},
            "source": SOURCE_LABEL,
            "generated": GENERATED_DATE,
            "counts": {"sale": len(sales), "jeonse": len(jeonse)},
        },
        "dongs": dongs,
        "months": months,
        "complexes": complexes,
        "sales": sales,
        "jeonse": jeonse,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_PATH) / 1024

    print("=== build_data.py summary ===")
    print(f"sales rows:   {len(sales)}")
    print(f"jeonse rows:  {len(jeonse)}")
    print(f"complexes:    {len(complexes)}")
    print(f"months:       {len(months)}")
    print(f"dongs:        {dongs}")
    print(f"output file:  {OUT_PATH}")
    print(f"output size:  {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
