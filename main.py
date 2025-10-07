import time
from ocr_v8 import Solution
#from generator import generate_test_cases
from generator_v1 import load_test_cases

#TEST_CASES = generate_test_cases("dvhcvn.json", n = 1000)
TEST_CASES = load_test_cases("test.json")

class Color:
    GREEN = '\033[32m'
    RED = '\033[91m'
    RESET = '\033[0m'

def run_tests(test_cases):
    solution = Solution()
    results = []
    times = []

    for idx, (input, expected) in enumerate(test_cases, start=1):
        start = time.perf_counter()
        actual = solution.process(input)
        end = time.perf_counter()

        elapsed = end - start
        times.append(elapsed)

        equal = lambda str1, str2: str1 == str2
        results.append({
            "id": idx,
            "input": input,
            "expected": expected,
            "actual": actual,
            "pass": equal(actual, expected),
            "time": elapsed
        })

    avg_time = sum(times) / len(times) if times else 0
    max_time = max(times) if times else 0

    return results, avg_time, max_time

def print_report(results, avg_time, max_time):
    print("=" * 80)
    print("TEST REPORT")
    print("=" * 80)

    pass_results = 0
    for r in results:
        pass_results += int(r["pass"])
        status = f"{Color.GREEN}✓ PASS{Color.RESET}" if r["pass"] else f"{Color.RED}✗ FAIL{Color.RESET}"
        print(f"Test {r['id']}: {status}")
        print(f"  Input   : {r['input']}")
        print(f"  Expected: {r['expected']}")
        print(f"  Actual  : {r['actual']}")
        print(f"  Time    : {r['time']:.6f} s")
        print("-" * 80)

    print(f"Overall Accuracy: {pass_results/len(results)*100:.2f}%")
    print(f"Average Time: {avg_time:.6f}s")
    print(f"Maximum Time: {max_time:.6f}s")
    print("=" * 80)

if __name__ == "__main__":
    results, avg_time, max_time = run_tests(TEST_CASES)
    print_report(results, avg_time, max_time)
