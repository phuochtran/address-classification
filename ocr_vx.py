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
        # Set up Prefix Map
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
            "xã": "ward",
            "tx.": "district",
            "tt.": "ward",
            "quan": "district",
            "quận": "district",
            "tinh": "province",
            "tỉnh": "province",
            "huyen": "district",
            "huyện": "district",
            "phuong": "ward",
            "phường": "ward",
            "thi xa": "district",
            "thị xã": "district",
            "thi tran": "ward",
            "thị trấn": "ward",
            "thanh pho": "province", # "district"
            "thành phố": "province" # "district"
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
        #s = unidecode(s)
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
                    num = Solution._lcs(word, w)
                    results.append((w, num, 1.0 - d/max(len(word), len(w))))
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
        return max(1, int(L * 0.20))

    @staticmethod
    def _lcs(s1, s2):
        N, M = len(s1)+1, len(s2)+1
        vec = [0]*M
        for i in range(N-2, -1, -1):
            tmp = [0]*M
            for j in range(M-2, -1, -1):
                tmp[j] = 1 + vec[j + 1] if s1[i] == s2[j] else max(vec[j], tmp[j + 1])
            vec = tmp
        return vec[0]

    def _detect_level(self, substr: str) -> tuple:
        prefix, level, num = None, None, None
        matches = []
        for pfx, lvl in self.prefix_map.items():
            candidate = self._normalize(substr[:len(pfx)])
            num = Solution._lcs(pfx, candidate)
            score = num/max(len(pfx), len(candidate))
            matches.append((pfx, lvl, num, score))
        prefix, level, num, _ = max(matches, key=lambda x: (x[3], x[2]))
        print(f"prefix matched: {prefix}")
        return prefix, level, num

    def process(self, input: str) -> dict:
        norm_text = self._normalize(input)
        print(f"norm: {norm_text}\n")
        tokens = norm_text.split()
        n = len(tokens)

        # Build candidates
        max_window = 5
        candidates = []
        for i in reversed(range(n)):  # start from the last token
            for j in range(max(0, i-max_window+1), i+1):  # window backward
                substr = ' '.join(tokens[j:i+1])
                candidates.append((j, i+1, substr))
        print(f"candidates: {candidates}\n")
        output = {
            "province": {"orig": "", "norm": "", "num": 0, "score": 0},
            "district": {"orig": "", "norm": "", "num": 0, "score": 0},
            "ward": {"orig": "", "norm": "", "num": 0, "score": 0}
        }
        for (i,j,substr) in candidates:
            maxdist = self._max_distance(max(1, len(substr.replace(' ', ''))))
            bias = 0.2
            prefix, level, num = self._detect_level(substr)
            match level:
                case "province":
                    sub = substr[num:].strip()
                    if not sub: continue
                    print(f"sub: {sub}")
                    results = self.province_bktree.search(sub, maxdist) if self.province_bktree is not None else []
                    print(f"({i}, {j}) level: {level} - r: {results}")
                    if results:
                        norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                        print(f"best matched - norm: {norm}, num: {num}, score: {score}")
                        if score+bias > output["province"]["score"] or (score+bias == output["province"]["score"] and num > output["province"]["num"]):
                            orig = self.province_map.get(norm, "")
                            output["province"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                            if output["district"]["orig"] and output["district"]["norm"] not in self.ref[output["province"]["norm"]]:
                                output["district"] = {'orig':'','norm':'','num':0,'score':0}
                        print(f"output: {output}\n")
                case "district":
                    sub = substr[num:].strip()
                    if not sub: continue
                    print(f"sub: {sub}")
                    results = self.district_bktree.search(sub, maxdist) if self.district_bktree is not None else []
                    print(f"({i}, {j}) level: {level} - r: {results}")
                    if results:
                        norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                        print(f"best matched - norm: {norm}, num: {num}, score: {score}")
                        if output["province"]["orig"] and norm not in self.ref[output["province"]["norm"]]: continue
                        if score+bias > output["district"]["score"] or (score+bias == output["district"]["score"] and num > output["district"]["num"]):
                            orig = self.district_map.get(norm, "")
                            output["district"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                            if output["ward"]["orig"] and all(output["ward"]["norm"] not in ws for ws in [province[output["district"]["norm"]] for province in self.ref.values() if output["district"]["norm"] in province]):
                                output["ward"] = {'orig':'','norm':'','num':0,'score':0}
                        print(f"output: {output}\n")
                case "ward":
                    sub = substr[num:].strip()
                    if not sub: continue
                    print(f"sub: {sub}")
                    results = self.ward_bktree.search(sub, maxdist) if self.ward_bktree is not None else []
                    print(f"({i}, {j}) level: {level} - r: {results}")
                    if results:
                        norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                        print(f"best matched - norm: {norm}, num: {num}, score: {score}")
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
                        if score+bias > output["ward"]["score"] or (score+bias == output["ward"]["score"] and num > output["ward"]["num"]):
                            orig = self.ward_map.get(norm, "")
                            output["ward"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                        print(f"output: {output}\n")
            bias = 0
            # province
            results = self.province_bktree.search(substr, maxdist) if self.province_bktree is not None else []
            print(f"({i}, {j}) - r: {results}")
            if results:
                norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                print(f"best matched - norm: {norm}, num: {num}, score: {score}")
                if score+bias > output["province"]["score"] or (score+bias == output["province"]["score"] and num > output["province"]["num"]):
                    orig = self.province_map.get(norm, "")
                    output["province"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                    if output["district"]["orig"] and output["district"]["norm"] not in self.ref[output["province"]["norm"]]:
                        output["district"] = {'orig':'','norm':'','num':0,'score':0}
                print(f"output: {output}\n")
            # district
            results = self.district_bktree.search(substr, maxdist) if self.district_bktree is not None else []
            print(f"({i}, {j}) - r: {results}")
            if results:
                norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                print(f"best matched - norm: {norm}, num: {num}, score: {score}")
                if output["province"]["orig"] and norm not in self.ref[output["province"]["norm"]]: continue
                if score+bias > output["district"]["score"] or (score+bias == output["district"]["score"] and num > output["district"]["num"]):
                    orig = self.district_map.get(norm, "")
                    output["district"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                    if output["ward"]["orig"] and all(output["ward"]["norm"] not in ws for ws in [province[output["district"]["norm"]] for province in self.ref.values() if output["district"]["norm"] in province]):
                        output["ward"] = {'orig':'','norm':'','num':0,'score':0}
                print(f"output: {output}\n")
            # ward
            results = self.ward_bktree.search(substr, maxdist) if self.ward_bktree is not None else []
            print(f"({i}, {j}) - r: {results}")
            if results:
                norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                print(f"best matched - norm: {norm}, num: {num}, score: {score}")
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
                if score+bias > output["ward"]["score"] or (score+bias == output["ward"]["score"] and num > output["ward"]["num"]):
                    orig = self.ward_map.get(norm, "")
                    output["ward"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                print(f"output: {output}\n")
        return [output[level]["orig"] for level in ["ward", "district", "province"]]

if __name__ == "__main__":
    sol = Solution()
    print(sol.process("Phường Phú Mỹ, Thà6nh phố Thủ Dầu Một, TBình Dương"))
#OA: 51.33%
