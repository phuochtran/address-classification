import random
import unicodedata
import json

ADMIN_PREFIXES = [
    "Tỉnh", "Thành phố", "Thành Phố", "TP",
    "Quận", "Huyện", "Thị xã", "Thị Xã", "Thị trấn", "Thị Trấn",
    "Phường", "Xã"
]

def load_data(path_json: str):
    with open(path_json, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_name(name: str) -> str:
    for prefix in ADMIN_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):].strip()
    return name.strip()

def remove_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def random_case(text: str) -> str:
    return ''.join(c.upper() if random.random() < 0.5 else c.lower() for c in text)

def corrupt(text: str) -> str:
    t = text
    if random.random() < 0.7:
        t = remove_accents(t)
    t = random_case(t)
    if len(t) > 3 and random.random() < 0.3:
        i = random.randrange(len(t))
        t = t[:i] + t[i+1:]
    if random.random() < 0.2:
        t = t + " " + t
    return t

def generate_test_case_from_data(data):
    level1 = random.choice(data["data"])
    province = level1["name"]

    if not level1.get("level2s"):
        return None
    level2 = random.choice(level1["level2s"])
    district = level2["name"]

    if not level2.get("level3s"):
        return None
    commune = random.choice(level2["level3s"])["name"]

    ground_truth = [
        clean_name(commune),
        clean_name(district),
        clean_name(province)
    ]

    parts = []
    if random.random() < 0.9:
        parts.append(corrupt(commune))
    if random.random() < 0.9:
        parts.append(corrupt(district))
    if random.random() < 0.9:
        parts.append(corrupt(province))

    noisy = ", ".join(parts)
    return (noisy, ground_truth)

def generate_test_cases(path_json: str, n: int = 50):
    data = load_data(path_json)
    test_cases = []
    while len(test_cases) < n:
        tc = generate_test_case_from_data(data)
        if tc:
            test_cases.append(tc)
    return test_cases

if __name__ == "__main__":
    PATH = "dvhcvn.json"
    tcs = generate_test_cases(PATH, n=20)
    for t in tcs:
        print(t)
