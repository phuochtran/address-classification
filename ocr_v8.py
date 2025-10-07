import re
import json
from rapidfuzz.distance import Levenshtein

class Solution:
    def __init__(self):
        self.province_path = 'list_province.txt'
        self.district_path = 'list_district.txt'
        self.ward_path = 'list_ward.txt'
        self.province_bktree, self.province_map = self._build_bktree(self._load_data(self.province_path))
        self.district_bktree, self.district_map = self._build_bktree(self._load_data(self.district_path))
        self.ward_bktree, self.ward_map = self._build_bktree(self._load_data(self.ward_path))
        self.ref = self._build_reference('reference.txt')
        self.prefix_map = self._build_prefix('prefix.json')

    def _load_data(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def _build_reference(self, file_path: str):
        ref = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = [self._normalize(p) for p in line.split(',')]
                if len(parts) != 3:
                    continue
                ward, district, province = parts
                if province not in ref:
                    ref[province] = {}
                if district not in ref[province]:
                    ref[province][district] = set()
                ref[province][district].add(ward)
        return ref
    
    def _build_prefix(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _normalize(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r'[\W_]+', ' ', s)
        return s.strip()

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
            if n not in norm_to_orig:
                norm_to_orig[n] = name
        bk = self.BKTree(Levenshtein.distance)
        for n in norm_to_orig:
            bk.add(n)
        return bk, norm_to_orig

    def _max_distance(self, L: int) -> int:
        if L <= 2:
            return 0
        if L <= 5:
            return 1
        return max(1, int(L * 0.25))

    def _detect_level(self, substr: str) -> tuple:
        prefix, level, num = None, None, None
        matches = []
        for pfx, lvl in self.prefix_map.items():
            candidate = self._normalize(substr[:len(pfx)])
            num = Solution._lcs(pfx, candidate)
            score = num/max(len(pfx), len(candidate))
            matches.append((pfx, lvl, num, score))
        prefix, level, num, _ = max(matches, key=lambda x: (x[3], x[2]))
        return prefix, level, num

    def _classify(self, substr: str) -> bool:
        maxdist = self._max_distance(max(1, len(substr.replace(' ', ''))))
        bias = 0.2
        prefix, level, num = self._detect_level(substr)
        match level:
            case 'province':
                sub = substr[num:].strip()
                if not sub: return False
                results = self.province_bktree.search(sub, maxdist) if self.province_bktree is not None else []
                if results:
                    norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                    if score+bias > self.output['province']['score'] or (score+bias == self.output['province']['score'] and num > self.output['province']['num']):
                        orig = self.province_map.get(norm, '')
                        self.output['province'] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                        if self.output['district']['orig'] and self.output['district']['norm'] not in self.ref[self.output['province']['norm']]:
                            self.output['district'] = {'orig':'','norm':'','num':0,'score':0}
                        return True
            case 'district':
                sub = substr[num:].strip()
                if not sub: return False
                results = self.district_bktree.search(sub, maxdist) if self.district_bktree is not None else []
                if results:
                    for res in sorted(results, key=lambda x: (x[2], x[1]), reverse=True):
                        norm, num, score = res
                        if self.output['province']['orig'] and norm not in self.ref[self.output['province']['norm']]: continue
                        if score+bias > self.output['district']['score'] or (score+bias == self.output['district']['score'] and num > self.output['district']['num']):
                            orig = self.district_map.get(norm, '')
                            self.output['district'] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                            if self.output['ward']['orig'] and all(self.output['ward']['norm'] not in ws for ws in [province[self.output['district']['norm']] for province in self.ref.values() if self.output['district']['norm'] in province]):
                                self.output['ward'] = {'orig':'','norm':'','num':0,'score':0}
                            return True
            case 'ward':
                sub = substr[num:].strip()
                if not sub: return False
                results = self.ward_bktree.search(sub, maxdist) if self.ward_bktree is not None else []
                if results:
                    for res in sorted(results, key=lambda x: (x[2], x[1]), reverse=True):
                        norm, num, score = res
                        if self.output['province']['orig']:
                            if self.output['district']['orig']:
                                if norm not in self.ref[self.output['province']['norm']][self.output['district']['norm']]:
                                    continue
                            else:
                                if all(norm not in wards for wards in self.ref[self.output['province']['norm']].values()):
                                    continue
                        else:
                            if self.output['district']['orig']:
                                if all(norm not in province[self.output['district']['norm']] for province in self.ref.values() if self.output['district']['norm'] in province):
                                    continue
                        if score+bias > self.output['ward']['score'] or (score+bias == self.output['ward']['score'] and num > self.output['ward']['num']):
                            orig = self.ward_map.get(norm, '')
                            self.output['ward'] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                            return True
        bias = 0
        # province
        results = self.province_bktree.search(substr, maxdist) if self.province_bktree is not None else []
        if results:
            norm, num, score = max(results, key=lambda x: (x[2], x[1]))
            if score+bias > self.output['province']['score'] or (score+bias == self.output['province']['score'] and num > self.output['province']['num']):
                orig = self.province_map.get(norm, '')
                self.output['province'] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                if self.output['district']['orig'] and self.output['district']['norm'] not in self.ref[self.output['province']['norm']]:
                    self.output['district'] = {'orig':'','norm':'','num':0,'score':0}
                return True
        # district
        results = self.district_bktree.search(substr, maxdist) if self.district_bktree is not None else []
        if results:
            for res in sorted(results, key=lambda x: (x[2], x[1]), reverse=True):
                norm, num, score = res
                if self.output['province']['orig'] and norm not in self.ref[self.output['province']['norm']]: continue
                if score+bias > self.output['district']['score'] or (score+bias == self.output['district']['score'] and num > self.output['district']['num']):
                    orig = self.district_map.get(norm, '')
                    self.output['district'] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                    if self.output['ward']['orig'] and all(self.output['ward']['norm'] not in ws for ws in [province[self.output['district']['norm']] for province in self.ref.values() if self.output['district']['norm'] in province]):
                        self.output['ward'] = {'orig':'','norm':'','num':0,'score':0}
                    return True
        # ward
        results = self.ward_bktree.search(substr, maxdist) if self.ward_bktree is not None else []
        if results:
            for res in sorted(results, key=lambda x: (x[2], x[1]), reverse=True):
                norm, num, score = res
                if self.output['province']['orig']:
                    if self.output['district']['orig']:
                        if norm not in self.ref[self.output['province']['norm']][self.output['district']['norm']]:
                            continue
                    else:
                        if all(norm not in wards for wards in self.ref[self.output['province']['norm']].values()):
                            continue
                else:
                    if self.output['district']['orig']:
                        if all(norm not in province[self.output['district']['norm']] for province in self.ref.values() if self.output['district']['norm'] in province):
                            continue
                if score+bias > self.output['ward']['score'] or (score+bias == self.output['ward']['score'] and num > self.output['ward']['num']):
                    orig = self.ward_map.get(norm, '')
                    self.output['ward'] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                    return True
        return False

    def process(self, input: str) -> dict:
        self.output = {
            'province':{'orig':'','norm':'','num':0,'score':0},
            'district':{'orig':'','norm':'','num':0,'score':0},
            'ward':{'orig':'','norm':'','num':0,'score':0}
        }
        parts = [part for part in reversed(input.split(','))]
        for part in parts:
            norm_text = self._normalize(part)
            tokens = norm_text.split()
            max_window = 4
            for i in reversed(range(len(tokens))):
                for j in range(max(0, i-max_window+1), i+1):
                    substr = ' '.join(tokens[j:i+1])
                    if (self._classify(substr)): break
        return [self.output[level]['orig'] for level in ['ward', 'district', 'province']]

if __name__ == '__main__':
    sol = Solution()
    print(sol.process('X.Nga Thanh hyện Nga son TỉnhThanhQ Hóa'))
