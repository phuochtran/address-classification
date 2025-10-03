import json

def load_test_cases(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = []
    for item in data:
        text = item["text"]
        ward = item["result"].get("ward", "")
        district = item["result"].get("district", "")
        province = item["result"].get("province", "")
        cases.append((text, [ward, district, province]))
    return cases
