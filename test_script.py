import time
from ocr import classify_address
from ocr import build_index
from test_generator import generate_test_cases

def read_file(path_txt: str):
    names = []
    with open(path_txt, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name:  # bỏ dòng trống
                names.append(name)
    return names

# Test data
'''
PROVINCES = ["Long An", "Hà Nội", "Hồ Chí Minh", "Bắc Ninh"]
DISTRICTS = ["Cần Giuộc", "Thuận Thành", "Quận 1", "Long An"]
COMMUNES = ["Tiến Thắng", "Thuận Thành", "An Phú", "Cần Giuộc"]
'''

PROVINCES = read_file("tinh.txt")
DISTRICTS = read_file("huyen.txt")
COMMUNES = read_file("xa.txt")

bk_province, map_province = build_index(PROVINCES)
bk_district, map_district = build_index(DISTRICTS)
bk_commune, map_commune = build_index(COMMUNES)

# Danh sách test cases: (input, expected)
'''
TEST_CASES = [
    ("X ThuanThanh H. Can Giuoc, Long An", ["Thuận Thành", "Cần Giuộc", "Long An"]),
    ("an phu, quAn 1, ho chiMInh", ["An Phu", "Quan 1", "Ho Chi Minh"]),
    ("huan Thanh  longAn", ["Thuận Thành", "", "Long An"]),
    ("ThuanThanh H Long An Long An", ["Thuận Thành", "Long An District", "Long An"]),
]
'''
TEST_CASES = generate_test_cases("dvhcvn.json", n = 100)

def run_tests(test_cases):
    results = []
    times = []

    for idx, (input, expected) in enumerate(test_cases, start=1):
        start = time.perf_counter()
        output = classify_address(input, bk_commune, map_commune, bk_district, map_district, bk_province, map_province)
        end = time.perf_counter()

        elapsed = end - start
        times.append(elapsed)

        actual = []
        [actual.append(output[lvl]["orig"] if output[lvl] else "") for lvl in ("commune", "district", "province")]
        equal = lambda str1, str2: str1 == str2
        results.append({
            "id": idx,
            "input": input,
            "expected": expected,
            "actual": actual,
            "pass": equal(actual, expected),
            "time": elapsed
        })

    all_passed = all(r["pass"] for r in results)
    avg_time = sum(times) / len(times) if times else 0
    max_time = max(times) if times else 0

    return results, all_passed, avg_time, max_time

def print_report(results, all_passed, avg_time, max_time):
    print("=" * 80)
    print("TEST REPORT")
    print("=" * 80)

    for r in results:
        status = "PASSED ✅" if r["pass"] else "FAILED ❌"
        print(f"Test {r['id']}: {status}")
        print(f"  Input   : {r['input']}")
        print(f"  Expected: {r['expected']}")
        print(f"  Actual  : {r['actual']}")
        print(f"  Time    : {r['time']:.6f} s")
        print("-" * 80)

    print(f"Overall Result: {'SUCCESSFUL' if all_passed else 'FAILURE'}")
    print(f"Average execution time: {avg_time:.6f}s")
    print(f"Maximum execution time: {max_time:.6f}s")
    print("=" * 80)

if __name__ == "__main__":
    results, all_passed, avg_time, max_time = run_tests(TEST_CASES)
    print_report(results, all_passed, avg_time, max_time)
