import re
from unidecode import unidecode

def normalize(s: str) -> str:
    s = s.lower()
    s = unidecode(s)  # handles đ→d, ô→o, ă→a, etc.
    s = re.sub(r'[\W_]+', ' ', s)  # replace non-alnum with spaces
    return s.strip()

def build_reference_dict(file_path: str):
    ref = {}

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Mỗi dòng: ward, district, province
            parts = [normalize(p) for p in line.split(",")]
            if len(parts) != 3:
                continue  # bỏ qua dòng sai định dạng

            ward, district, province = parts

            # Thêm vào dict
            if province not in ref:
                ref[province] = {}
            if district not in ref[province]:
                ref[province][district] = set()
            ref[province][district].add(ward)

    return ref


if __name__ == "__main__":
    file_path = "reference.txt"  # đường dẫn file của bạn
    ref = build_reference_dict(file_path)
    print(ref)
