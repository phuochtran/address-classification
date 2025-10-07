import time
import re
import json
from functools import lru_cache

THRESHOLD = 0.83
MAX_DISTANCE = 3
_WARD_FALLBACK_TIME_LIMIT_SEC = 0.03
_MAPPING = [
    # oa: o + (a có dấu) -> (o có dấu) + a
    ("oà", "òa"), ("oá", "óa"), ("oả", "ỏa"), ("oã", "õa"), ("oạ", "ọa"),
    ("Oà", "Òa"), ("Oá", "Óa"), ("Oả", "Ỏa"), ("Oã", "Õa"), ("Oạ", "Ọa"),
    ("oÀ", "òa"), ("oÁ", "óa"), ("oẢ", "ỏa"), ("oÃ", "õa"), ("oẠ", "ọa"),
    ("OÀ", "ÒA"), ("OÁ", "ÓA"), ("OẢ", "ỎA"), ("OÃ", "ÕA"), ("OẠ", "ỌA"),

    # oe: o + (e có dấu) -> (o có dấu) + e
    ("oè", "òe"), ("oé", "óe"), ("oẻ", "ỏe"), ("oẽ", "õe"), ("oẹ", "ọe"),
    ("Oè", "Òe"), ("Oé", "Óe"), ("Oẻ", "Ỏe"), ("Oẽ", "Õe"), ("Oẹ", "Ọe"),
    ("oÈ", "òe"), ("oÉ", "óe"), ("oẺ", "ỏe"), ("oẼ", "õe"), ("oẸ", "ọe"),
    ("OÈ", "ÒE"), ("OÉ", "ÓE"), ("OẺ", "ỎE"), ("OẼ", "ÕE"), ("OẸ", "ỌE"),

    # uy: u + (y có dấu) -> (u có dấu) + y
    ("uỳ", "ùy"), ("uý", "úy"), ("uỷ", "ủy"), ("uỹ", "ũy"), ("uỵ", "ụy"),
    ("Uỳ", "Ùy"), ("Uý", "Úy"), ("Uỷ", "Ủy"), ("Uỹ", "Ũy"), ("Uỵ", "Ụy"),
    ("uỲ", "ùy"), ("uÝ", "úy"), ("uỶ", "ủy"), ("uỸ", "ũy"), ("uỴ", "ụy"),
    ("UỲ", "ÙY"), ("UÝ", "ÚY"), ("UỶ", "ỦY"), ("UỸ", "ŨY"), ("UỴ", "ỤY"),
]
_REMOVE_DATA_BY_TEAMPLTE_FILE = False
class Solution:
    def __init__(self):
        self.province_path = 'list_province.txt'
        self.district_path = 'list_district.txt'
        self.ward_path = 'list_ward.txt'

        # address data
        self.address_path = 'list_address.json'
        self.abbreviate_path = 'abbreviations.json'
        self.province_data = self.TrieNode()
        self.district_data = {}
        self.ward_data = {}
        self.all_districts_data = self.TrieNode()
        self.province_wards_data = {}

        # Load data
        self.load_hierarchical_data()

    class TrieNode():
        def __init__(self):
            self.childs = {}
            self.exact_word = None
            self.key_word = None

    def remove_prefixes(self, text, level):
        text = text.strip().lower()

        if level == 'province':
            text = re.sub(r'\b(tỉnh|tp|tnh|tỉnhc|tỉnhv|tpho|thanhpho|thànhphô|thànhphố|thphố|tphố|thpho|tp\.)\s*', '', text)
        elif level == 'district':
            text = re.sub(r'\b(huyện|hyen|huyen|quận|quan|qận|qan|qun|tp|tpho|thanhpho|thànhphô|thànhphố|thphố|tphố|thpho|q\.)\s*', '', text)
        elif level == 'ward':
            text = re.sub(r'\b(xã|thịxã|thxã|phường|phưòng|phung|tt|tx|p|Thi trấ|F\.)\s*', '', text)

        return text

    def insert(self, root_node, key, word, level):
        # Remove prefixes
        cleaned_key = self.remove_prefixes(key, level)
        cleaned_key = cleaned_key.replace(" ", "").strip().lower()

        node = root_node
        for char in cleaned_key:
            if char not in node.childs:
                node.childs[char] = self.TrieNode()
            node = node.childs[char]
        node.exact_word = word.strip()
        node.key_word = cleaned_key

    def load_hierarchical_data(self):
        """Load data from the hierarchical JSON file"""
        def remove_prefix(name):
            if not name:
                return ""
            name = re.sub(r'^(tỉnh|thành phố|huyện|quận|thị xã|xã|phường|thị trấn)\s+', '', name, flags=re.IGNORECASE)
            return name.strip()

        with open(self.province_path, 'r', encoding='utf-8') as f:
            flat_provinces = [line.strip() for line in f if line.strip()]

        with open(self.district_path, 'r', encoding='utf-8') as f:
            flat_districts = [line.strip() for line in f if line.strip()]

        with open(self.ward_path, 'r', encoding='utf-8') as f:
            flat_wards = [line.strip() for line in f if line.strip()]

        with open(self.address_path, "r", encoding='utf-8') as file:
            data = json.load(file)

        try:
            with open(self.abbreviate_path, 'r', encoding='utf-8') as f:
                self.abbreviations = json.load(f)
        except FileNotFoundError:
            self.abbreviations = {"province": {}, "district": {}, "ward": {}}

        # Load provinces
        for province_name in data.keys():
            province_name = remove_prefix(province_name)
            if _REMOVE_DATA_BY_TEAMPLTE_FILE and province_name not in flat_provinces:
                continue
            self.insert(self.province_data, province_name, province_name, 'province')
            for abbreviation in self.abbreviations.get("province", {}).get(province_name, []):
                self.insert(self.province_data, abbreviation, province_name, 'province')

        # Load districts and wards
        for province_name, districts in data.items():
            province_name = remove_prefix(province_name)
            if _REMOVE_DATA_BY_TEAMPLTE_FILE and province_name not in flat_provinces:
                continue
            # Create a trie for districts in province
            self.district_data[province_name] = self.TrieNode()

            # Create a trie for wards in this province (skip district level)
            self.province_wards_data[province_name] = self.TrieNode()

            for district_name, wards in districts.items():
                district_name = remove_prefix(district_name)
                if _REMOVE_DATA_BY_TEAMPLTE_FILE and district_name not in flat_districts:
                    continue
                # Insert district into province's district trie
                self.insert(self.district_data[province_name], district_name, district_name, 'district')
                # Insert district into all districts trie (for skip province)
                self.insert(self.all_districts_data, district_name, district_name, 'district')

                for abbreviation in self.abbreviations.get("district", {}).get(district_name, []):
                    self.insert(self.province_data, abbreviation, district_name, 'district')

                # Create a trie for wards in this district
                ward_key = (province_name, district_name)
                self.ward_data[ward_key] = self.TrieNode()

                # Insert wards into district's ward trie
                for ward_name in wards:
                    ward_name = remove_prefix(ward_name)
                    if _REMOVE_DATA_BY_TEAMPLTE_FILE and ward_name not in flat_wards:
                        continue
                    self.insert(self.ward_data[ward_key], ward_name, ward_name, 'ward')
                    # Insert ward into province's ward trie (skip district level)
                    self.insert(self.province_wards_data[province_name], ward_name, ward_name, 'ward')

                    for abbreviation in self.abbreviations.get("ward", {}).get(ward_name, []):
                        self.insert(self.province_data, abbreviation, ward_name, 'ward')

    def find_closest_string(self, root_node, word, level, deadline=None):
        # Remove prefixes from search word
        word = self.remove_prefixes(word, level).strip().lower()

        results = []
        max_distance = MAX_DISTANCE
        initial_row = list(range(len(word) + 1))

        def search_recursive(node, prefix, previous_row):
            nonlocal max_distance

            # early stop when timeout
            if deadline is not None and time.perf_counter() > deadline:
                return

            current_word = prefix

            if node.key_word and previous_row[-1] <= max_distance:
                results.append((node.key_word, node.exact_word, previous_row[-1]))
                max_distance = previous_row[-1]

            for char, child_node in node.childs.items():
                current_row = [previous_row[0] + 1]

                for i in range(1, len(word) + 1):
                    insert_cost = current_row[i - 1] + 1
                    delete_cost = previous_row[i] + 1
                    replace_cost = previous_row[i - 1] + (0 if word[i - 1] == char else 1)
                    current_row.append(min(insert_cost, delete_cost, replace_cost))

                if min(current_row) <= max_distance:
                    search_recursive(child_node, current_word + char, current_row)

        search_recursive(root_node, "", initial_row)
        results.sort(key=lambda x: x[2])

        dynamic_threshold = THRESHOLD - (len(word) / 100)
        if results:
            return results[0][1] if dynamic_threshold <= 1 - (results[0][2]/max(len(word), len(results[0][0]))) else ""
        return ""

    def normalize_vn_legacy_to_modern(self, text: str) -> str:
        if not text:
            return text
        for old, new in _MAPPING:
            text = text.replace(old, new)
        return text

    def sanitize_string(self, input_word):
        input_word = input_word.strip().lower()
        input_word = self.normalize_vn_legacy_to_modern(input_word)
        input_word = re.sub(r'[\s,.~-]', ' ', input_word)
        return input_word.strip()

    def slide_and_combine_with_indices(self, words):
        n = len(words)
        results = []

        for i in range(n - 1, -1, -1):
            window = words[max(0, i - 2):i + 1]

            if len(window) == 3:
                w1, w2, w3 = window
                results.extend([(f"{w2}{w3}", i - 1), (f"{w1}{w2}", i - 2), (w3, i), (f"{w1}{w2}{w3}", i - 2)])
            elif len(window) == 2:
                w1, w2 = window
                results.extend([(f"{w1}{w2}", i - 1), (w2, i)])
            elif len(window) == 1:
                results.append((window[0], i))

        return results

    def process(self, s: str):
        # write your process string here
        result = {
            "province": "",
            "district": "",
            "ward": ""
        }

        start_time = time.perf_counter()
        cleaned_input = self.sanitize_string(s).split()

        # Step 1: Find province
        province_candidates = self.slide_and_combine_with_indices(cleaned_input)
        matched_start_index = -1
        processed_province_candidates = set()

        for i, (candidate, start_index) in enumerate(province_candidates):
            if candidate in processed_province_candidates:
                continue
            processed_province_candidates.add(candidate)

            result["province"] = self.find_closest_string(self.province_data, candidate, 'province')
            if result["province"]:
                matched_start_index = start_index
                cleaned_input = cleaned_input[:matched_start_index]
                break

        # Step 2: Find district
        district_found = False
        if result["province"] and result["province"] in self.district_data:
            district_candidates = self.slide_and_combine_with_indices(cleaned_input)
            matched_start_index = -1
            processed_district_candidates = set()

            for i, (candidate, start_index) in enumerate(district_candidates):
                if candidate in processed_district_candidates:
                    continue
                processed_district_candidates.add(candidate)

                result["district"] = self.find_closest_string(
                    self.district_data[result["province"]],
                    candidate,
                    'district'
                )
                if result["district"]:
                    matched_start_index = start_index
                    cleaned_input = cleaned_input[:matched_start_index]
                    district_found = True
                    break

        if not result["province"]:
            district_candidates = self.slide_and_combine_with_indices(cleaned_input)
            matched_start_index = -1
            processed_district_candidates = set()
            deadline = time.perf_counter() + _WARD_FALLBACK_TIME_LIMIT_SEC

            for i, (candidate, start_index) in enumerate(district_candidates):
                if time.perf_counter() > deadline:
                    break
                if candidate in processed_district_candidates:
                    continue
                processed_district_candidates.add(candidate)

                result["district"] = self.find_closest_string(
                    self.all_districts_data,
                    candidate,
                    'district',
                    deadline=deadline
                )
                if result["district"]:
                    matched_start_index = start_index
                    cleaned_input = cleaned_input[:matched_start_index]
                    district_found = True
                    break

        # Step 3: Find ward
        if result["province"] and result["district"]:
            ward_key = (result["province"], result["district"])
            if ward_key in self.ward_data:
                ward_candidates = self.slide_and_combine_with_indices(cleaned_input)
                processed_ward_candidates = set()

                for i, (candidate, start_index) in enumerate(ward_candidates):
                    if candidate in processed_ward_candidates:
                        continue
                    processed_ward_candidates.add(candidate)

                    result["ward"] = self.find_closest_string(
                        self.ward_data[ward_key],
                        candidate,
                        'ward'
                    )
                    if result["ward"]:
                        break

        elif result["province"] and not result["district"]:
            if result["province"] in self.province_wards_data:
                ward_candidates = self.slide_and_combine_with_indices(cleaned_input)
                processed_ward_candidates = set()
                deadline = time.perf_counter() + _WARD_FALLBACK_TIME_LIMIT_SEC

                for i, (candidate, start_index) in enumerate(ward_candidates):
                    if time.perf_counter() > deadline:
                        break
                    if candidate in processed_ward_candidates:
                        continue
                    processed_ward_candidates.add(candidate)

                    result["ward"] = self.find_closest_string(
                        self.province_wards_data[result["province"]],
                        candidate,
                        'ward',
                        deadline=deadline
                    )
                    if result["ward"]:
                        break

        return result
