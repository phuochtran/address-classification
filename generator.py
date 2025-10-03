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

def join_parts_randomly(parts: list[str], levels: list[str] | None = None) -> str:
    if not parts:
        return ""
    if levels is None:
        levels = [None] * len(parts)
    out = parts[0]
    for i in range(len(parts) - 1):
        next_level = levels[i + 1] if i + 1 < len(levels) else None
        r = random.random()
        if next_level == 'province':
            if r < 0.75:
                sep = ', '
            elif r < 0.92:
                sep = ' '
            else:
                sep = ' - '
        else:
            if r < 0.55:
                sep = ', '
            elif r < 0.95:
                sep = ' '
            else:
                sep = ' - '
        out = out.rstrip() + sep + parts[i + 1].lstrip()
    return out

def generate_test_case_from_data(data):
    level1 = random.choice(data["data"])
    province = level1["name"]
    if not level1.get("level2s"):
        return None
    level2 = random.choice(level1["level2s"])
    district = level2["name"]
    if not level2.get("level3s"):
        return None
    ward = random.choice(level2["level3s"])["name"]
    ground_truth = ["", "", ""]
    levels = []
    parts = []
    if random.random() < 0.9:
        parts.append(corrupt(ward))
        levels.append("ward")
        ground_truth[0] = clean_name(ward)
    if random.random() < 0.9:
        parts.append(corrupt(district))
        levels.append("district")
        ground_truth[1] = clean_name(district)
    if random.random() < 0.9:
        parts.append(corrupt(province))
        levels.append("province")
        ground_truth[2] = clean_name(province)
    if not parts:
        parts.append(corrupt(province))
        levels.append("province")
        ground_truth[2] = clean_name(province)
    noisy = join_parts_randomly(parts, levels)
    return (noisy, ground_truth)

def generate_test_cases(path_json: str, n: int = 50):
    data = load_data(path_json)
    test_cases = []
    while len(test_cases) < n:
        tc = generate_test_case_from_data(data)
        if tc:
            test_cases.append(tc)
    return test_cases
