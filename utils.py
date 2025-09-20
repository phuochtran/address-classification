import json

ADMIN_PREFIXES = [
    "Tỉnh", "Thành phố", "Thành Phố", "TP",
    "Quận", "Huyện", "Thị xã", "Thị Xã", "Thị trấn", "Thị Trấn",
    "Phường", "Xã"
]

def clean_name(name: str) -> str:
    for prefix in ADMIN_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):].strip()
    return name.strip()

def load_data(path_json: str):
    with open(path_json, 'r', encoding='utf-8') as f:
        return json.load(f)

def export_names(data, 
                 file_tinh: str="tinh.txt", 
                 file_huyen: str="huyen.txt", 
                 file_xa: str="xa.txt"):
    set_tinh = set()
    set_huyen = set()
    set_xa = set()

    for level1 in data.get("data", []):
        prov = level1.get("name", "").strip()
        if prov:
            set_tinh.add(prov)

        for level2 in level1.get("level2s", []):
            dist = level2.get("name", "").strip()
            if dist:
                set_huyen.add(dist)

            for level3 in level2.get("level3s", []):
                xa = level3.get("name", "").strip()
                if xa:
                    set_xa.add(xa)

    with open(file_tinh, 'w', encoding='utf-8') as f:
        for name in sorted(set_tinh):
            f.write(clean_name(name) + "\n")

    with open(file_huyen, 'w', encoding='utf-8') as f:
        for name in sorted(set_huyen):
            f.write(clean_name(name) + "\n")

    with open(file_xa, 'w', encoding='utf-8') as f:
        for name in sorted(set_xa):
            f.write(clean_name(name) + "\n")

if __name__ == "__main__":
    PATH_JSON = "dvhcvn.json"
    data = load_data(PATH_JSON)
    export_names(data, file_tinh="data_set/tinh.txt", file_huyen="data_set/huyen.txt", file_xa="data_set/xa.txt")
