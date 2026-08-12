import csv

FILE_NAME = "seoul-apt-latest.csv"
TARGET_GU = "양천구"

count = 0
total_price = 0

with open(FILE_NAME, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["gu"] != TARGET_GU:
            continue
        if not row["price"]:
            continue
        count += 1
        total_price += int(row["price"])

if count == 0:
    print(f"{TARGET_GU} 데이터가 없습니다.")
else:
    avg_price_man = total_price / count
    avg_price_eok = round(avg_price_man / 10000, 2)
    print(f"{TARGET_GU} 거래 건수: {count}건")
    print(f"{TARGET_GU} 평균 물건금액: {avg_price_eok}억 원")
