import re
import unicodedata

class Solution:
    def __init__(self):
        # Load Data Set
        self.province_path = 'list_province.txt'
        self.district_path = 'list_district.txt'
        self.ward_path = 'list_ward.txt'
        PROVINCES = self._read_file(self.province_path)
        DISTRICTS = self._read_file(self.district_path)
        WARDS = self._read_file(self.ward_path)
        # Build BK-Tree
        self.bk_province, self.map_province = self._build_index(PROVINCES)
        self.bk_district, self.map_district = self._build_index(DISTRICTS)
        self.bk_ward, self.map_ward = self._build_index(WARDS)
        self.PREFIX_LEVELS = {
            "province": ["tinh", "t", "t.", "thanh pho", "tp", "tp."],
            "district": ["huyen", "h", "h.", "quan", "q", "q.", "thi xa", "tx", "tx.", "thanh pho", "tp", "tp."],
            "ward": ["xa", "x", "x.", "phuong", "p", "p.", "thi tran", "tt", "tt."],
        }

    def _read_file(self, path_txt: str):
        names = []
        with open(path_txt, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    names.append(name)
        return names

    def _strip_accents(self, s: str) -> str:
        s = unicodedata.normalize('NFD', s)
        s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
        return unicodedata.normalize('NFC', s)

    def _normalize(self, s: str) -> str:
        s = s.lower()
        # replace common punctuation with spaces
        s = re.sub(r'[\.,;/\\\(\)\[\]\-_:]', ' ', s)
        s = s.replace('\'', ' ')
        s = re.sub(r'\s+', ' ', s).strip()
        s = self._strip_accents(s)
        # remove any non-alphanumeric (keep spaces)
        s = re.sub(r'[^a-z0-9\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

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
                    results.append((w, d))
                low = d - maxdist
                high = d + maxdist
                for k in children:
                    if low <= k <= high:
                        stack.append(children[k])
            return results

    def _build_index(self, names):
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
        for level, prefixes in self.PREFIX_LEVELS.items():
            for prefix in prefixes:
                if substr.startswith(prefix + " "):
                    return level, prefix
        return None, None

    def process(self, input: str) -> dict:
        norm_text = self._normalize(input)
        tokens = norm_text.split()
        n = len(tokens)

        # Build candidates
        max_window = 3
        candidates = []
        for i in range(n):
            for j in range(i+1, min(n, i+max_window) + 1):
                substr = ' '.join(tokens[i:j])
                candidates.append((i, j, substr))

        # For each candidate, try match against wards, districts, provinces
        matches = []
        for (i,j,substr) in candidates:
            L = len(substr.replace(' ', ''))
            maxdist = self._max_distance(max(1, L))

            level, prefix = self._detect_level(substr)
            if level == "ward":
                substr = substr[len(prefix):].strip()
                r = self.bk_ward.search(substr, maxdist) if self.bk_ward is not None else []
                if r:
                    best = min(r, key=lambda x: x[1])
                    matched_norm, dist = best
                    score = 1.0 - dist / max(len(substr), len(matched_norm))
                    matches.append({'level':'ward','span':(i,j),'matched':matched_norm,'score':score})
            elif level == "district":
                substr = substr[len(prefix):].strip()
                r = self.bk_district.search(substr, maxdist) if self.bk_district is not None else []
                if r:
                    best = min(r, key=lambda x: x[1])
                    matched_norm, dist = best
                    score = 1.0 - dist / max(len(substr), len(matched_norm))
                    matches.append({'level':'district','span':(i,j),'matched':matched_norm,'score':score})
            elif level == "province":
                substr = substr[len(prefix):].strip()
                r = self.bk_province.search(substr, maxdist) if self.bk_province is not None else []
                if r:
                    best = min(r, key=lambda x: x[1])
                    matched_norm, dist = best
                    score = 1.0 - dist / max(len(substr), len(matched_norm))
                    matches.append({'level':'province','span':(i,j),'matched':matched_norm,'score':score})
            else:
                # ward
                r = self.bk_ward.search(substr, maxdist) if self.bk_ward is not None else []
                if r:
                    best = min(r, key=lambda x: x[1])
                    matched_norm, dist = best
                    score = 1.0 - dist / max(len(substr), len(matched_norm))
                    matches.append({'level':'ward','span':(i,j),'matched':matched_norm,'score':score})
                # district
                r = self.bk_district.search(substr, maxdist) if self.bk_district is not None else []
                if r:
                    best = min(r, key=lambda x: x[1])
                    matched_norm, dist = best
                    score = 1.0 - dist / max(len(substr), len(matched_norm))
                    matches.append({'level':'district','span':(i,j),'matched':matched_norm,'score':score})
                # province
                r = self.bk_province.search(substr, maxdist) if self.bk_province is not None else []
                if r:
                    best = min(r, key=lambda x: x[1])
                    matched_norm, dist = best
                    score = 1.0 - dist / max(len(substr), len(matched_norm))
                    matches.append({'level':'province','span':(i,j),'matched':matched_norm,'score':score})
        # pick best for each level (highest score; if tie longer span)
        output = {}
        for level in ('ward','district','province'):
            cand = [m for m in matches if m['level']==level]
            if not cand:
                output[level] = ""
                continue
            # sort by score desc, then span length desc
            cand.sort(key=lambda x: (x['score'], x['span'][1]-x['span'][0]), reverse=True)
            best = cand[0]
            # require a minimum score to accept (adjustable)
            if best['score'] >= 0.45:
                if level == 'ward':
                    output[level] = self.map_ward.get(best['matched'], None)
                elif level == 'district':
                    output[level] = self.map_district.get(best['matched'], None)
                elif level == 'province':
                    output[level] = self.map_province.get(best['matched'], None)
            else:
                output[level] = ""
        return output


