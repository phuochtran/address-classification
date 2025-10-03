import re
import unicodedata
from unidecode import unidecode

class Solution:
    def __init__(self):
        # Load Data Set
        self.province_path = 'list_province.txt'
        self.district_path = 'list_district.txt'
        self.ward_path = 'list_ward.txt'
        # Build BK-Tree
        self.province_bktree, self.province_map = self._build_bktree(self._load_data(self.province_path))
        self.district_bktree, self.district_map = self._build_bktree(self._load_data(self.district_path))
        self.ward_bktree, self.ward_map = self._build_bktree(self._load_data(self.ward_path))
        # Build Reference
        self.ref = self._build_reference("reference.txt")
        # Set up prefixes
        self.prefix_map = {
            "p": "ward",
            "q": "district",
            "t": "province",
            "x": "ward",
            "h": "district",
            "tt": "ward",
            "tx": "district",
            "tp": "province", # "district"
            "p.": "ward",
            "q.": "district",
            "t.": "province",
            "x.": "ward",
            "h.": "district",
            "tp.": "province", # "district"
            "xa": "ward",
            "tx.": "district",
            "tt.": "ward",
            "quan": "district",
            "tinh": "province",
            "huyen": "district",
            "phuong": "ward",
            "thi xa": "district",
            "thi tran": "ward",
            "thanh pho": "province" # "district"
        }


    def _load_data(self, file_path: str):
        names = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    names.append(name)
        return names

    def _build_reference(self, file_path: str):
        ref = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = [self._normalize(p) for p in line.split(",")]
                if len(parts) != 3:
                    continue
                ward, district, province = parts
                if province not in ref:
                    ref[province] = {}
                if district not in ref[province]:
                    ref[province][district] = set()
                ref[province][district].add(ward)
        return ref

    def _normalize(self, s: str) -> str:
        s = s.lower()
        s = unidecode(s)
        s = re.sub(r'[\W_]+', ' ', s)
        return s.strip()

    def _levenshtein(self, a: str, b: str) -> int:
        if a == b:
            return 0
        if len(a) < len(b):
            a, b = b, a
        previous = list(range(len(b) + 1))
        for i, ca in enumerate(a, start=1):
            current = [i]
            for j, cb in enumerate(b, start=1):
                ins = previous[j] + 1
                dele = current[j-1] + 1
                rep = previous[j-1] + (0 if ca == cb else 1)
                current.append(min(ins, dele, rep))
            previous = current
        return previous[-1]

    class BKTree:
        def __init__(self, distfn):
            self.distfn = distfn
            self.tree = None  # (word, {distance: child_node})

        def add(self, word):
            if self.tree is None:
                self.tree = (word, {})
                return
            node = self.tree
            while True:
                w, children = node
                d = self.distfn(word, w)
                if d in children:
                    node = children[d]
                else:
                    children[d] = (word, {})
                    return

        def search(self, word, maxdist):
            if self.tree is None:
                return []
            results = []
            stack = [self.tree]
            while stack:
                w, children = stack.pop()
                d = self.distfn(word, w)
                if d <= maxdist:
                    results.append((w, 1.0 - d/max(len(word), len(w))))
                low = d - maxdist
                high = d + maxdist
                for k in children:
                    if low <= k <= high:
                        stack.append(children[k])
            return results

    def _build_bktree(self, names):
        norm_to_orig = {}
        for name in names:
            n = self._normalize(name)
            # if duplicate normalized keys, keep the first (or could store list)
            if n not in norm_to_orig:
                norm_to_orig[n] = name
        bk = self.BKTree(self._levenshtein)
        for n in norm_to_orig:
            bk.add(n)
        return bk, norm_to_orig

    def _max_distance(self, L: int) -> int:
        if L <= 2:
            return 0
        if L <= 5:
            return 1
        # allow up to ~20% of length as edits (rounded)
        return max(1, int(L * 0.20))

    def _detect_level(self, substr: str) -> tuple[str | None, str | None]:
        prefix, level = None, None
        for pfx, lvl in self.prefix_map.items():
            if substr.startswith(pfx):
                prefix, level = pfx, lvl
        return prefix, level

    def process(self, input: str) -> dict:
        norm_text = self._normalize(input)
        print(f"norm: {norm_text}\n")
        tokens = norm_text.split()
        n = len(tokens)

        # Build candidates
        max_window = 5
        '''
        candidates = []
        for i in range(n):
            for j in range(i+1, min(n, i+max_window) + 1):
                substr = ' '.join(tokens[i:j])
                candidates.append((i, j, substr))
        '''
        candidates = []
        for i in reversed(range(n)):  # start from the last token
            for j in range(max(0, i-max_window+1), i+1):  # window backward
                substr = ' '.join(tokens[j:i+1])
                candidates.append((j, i+1, substr))
        print(f"candidates: {candidates}\n")
        output = {
            "province": {"orig": "", "norm": "", "score": 0},
            "district": {"orig": "", "norm": "", "score": 0},
            "ward": {"orig": "", "norm": "", "score": 0}
        }
        for (i,j,substr) in candidates:
            maxdist = self._max_distance(max(1, len(substr.replace(' ', ''))))
            bias = 0.7
            prefix, level = self._detect_level(substr)
            match level:
                case "province":
                    substr = substr[len(prefix):].strip()
                    if not substr: continue
                    results = self.province_bktree.search(substr, maxdist) if self.province_bktree is not None else []
                    print(f"({i}, {j}) level: {level} - r: {results}")
                    if results:
                        norm, score = max(results, key=lambda x: x[1])
                        if score+bias > output["province"]["score"] or (score+bias == output["province"]["score"] and len(norm) > len(output["province"]["norm"])):
                            orig = self.province_map.get(norm, "")
                            output["province"] = {'orig': orig, 'norm': norm, 'score': score+bias}
                            if output["district"]["orig"] and output["district"]["norm"] not in self.ref[output["province"]["norm"]]:
                                output["district"] = {'orig': '', 'norm': '', 'score': 0}
                    print(f"output: {output}\n")
                case "district":
                    substr = substr[len(prefix):].strip()
                    if not substr: continue
                    results = self.district_bktree.search(substr, maxdist) if self.district_bktree is not None else []
                    print(f"({i}, {j}) level: {level} - r: {results}")
                    if results:
                        for res in sorted(results, key=lambda x: x[1], reverse=True):
                            norm, score = res
                            if output["province"]["orig"] and norm not in self.ref[output["province"]["norm"]]: continue
                            if score+bias > output["district"]["score"] or (score+bias == output["district"]["score"] and len(norm) > len(output["district"]["norm"])):
                                orig = self.district_map.get(norm, "")
                                output["district"] = {'orig':orig,'norm':norm,'score':score+bias}
                                if output["ward"]["orig"] and all(output["ward"]["norm"] not in ws for ws in [province[output["district"]["norm"]] for province in self.ref.values() if output["district"]["norm"] in province]):
                                    output["ward"] = {'orig':'','norm':'','score':0}
                                break
                            break
                    print(f"output: {output}\n")
                case "ward":
                    substr = substr[len(prefix):].strip()
                    if not substr: continue
                    results = self.ward_bktree.search(substr, maxdist) if self.ward_bktree is not None else []
                    print(f"({i}, {j}) level: {level} - r: {results}")
                    if results:
                        for res in sorted(results, key=lambda x: x[1], reverse=True):
                            norm, score = res
                            if output["province"]["orig"]:
                                if output["district"]["orig"]:
                                    if norm not in self.ref[output["province"]["norm"]][output["district"]["norm"]]:
                                        continue
                                else:
                                    if all(norm not in wards for wards in self.ref[output["province"]["norm"]].values()):
                                        continue
                            else:
                                if output["district"]["orig"]:
                                    if all(norm not in province[output["district"]["norm"]] for province in self.ref.values() if output["district"]["norm"] in province):
                                        continue
                            if score+bias > output["ward"]["score"] or (score+bias == output["ward"]["score"] and len(norm) > len(output["ward"]["norm"])):
                                orig = self.ward_map.get(norm, "")
                                output["ward"] = {'orig':orig,'norm':norm,'score':score+bias}
                                break
                    print(f"output: {output}\n")
                case _:
                    # province
                    if not output["province"]["orig"]:
                        results = self.province_bktree.search(substr, maxdist) if self.province_bktree is not None else []
                        print(f"({i}, {j}) level: {level} >> province - r: {results}")
                        if results:
                            norm, score = max(results, key=lambda x: x[1])
                            orig = self.province_map.get(norm, "")
                            output["province"] = {'orig':orig,'norm':norm,'score':score}
                            if output["district"]["orig"] and output["district"]["norm"] not in self.ref[output["province"]["norm"]]:
                                output["district"] = {'orig': '', 'norm': '', 'score': 0}
                        print(f"output: {output}\n")
                    # district
                    elif not output["district"]["orig"]:
                        results = self.district_bktree.search(substr, maxdist) if self.district_bktree is not None else []
                        print(f"({i}, {j}) level: {level} >> district - r: {results}")
                        if results:
                            for res in sorted(results, key=lambda x: x[1], reverse=True):
                                norm, score = res
                                print(f"ref: {self.ref[output["province"]["norm"]]}")
                                if norm in self.ref[output["province"]["norm"]]:
                                    orig = self.district_map.get(norm, "")
                                    output["district"] = {'orig':orig,'norm':norm,'score':score}
                                    if output["ward"]["orig"] and all(output["ward"]["norm"] not in ws for ws in [province[output["district"]["norm"]] for province in self.ref.values() if output["district"]["norm"] in province]):
                                        output["ward"] = {'orig':'','norm':'','score':0}
                                    break
                        print(f"output: {output}\n")
                    # ward
                    elif not output["ward"]["orig"]:
                        results = self.ward_bktree.search(substr, maxdist) if self.ward_bktree is not None else []
                        print(f"({i}, {j}) level: {level} >> ward - r: {results}")
                        if results:
                            for res in sorted(results, key=lambda x: x[1], reverse=True):
                                norm, score = res
                                print(f"ref: {self.ref[output["province"]["norm"]][output["district"]["norm"]]}")
                                if norm in self.ref[output["province"]["norm"]][output["district"]["norm"]]:
                                    orig = self.ward_map.get(norm, "")
                                    output["ward"] = {'orig':orig,'norm':norm,'score':score}
                                    break
                        print(f"output: {output}\n")
        return [output[level]["orig"] for level in ["ward", "district", "province"]]

if __name__ == "__main__":
    sol = Solution()
    print(sol.process("tHỊ trN TRà lâN - HUYeN CON cUOG"))
