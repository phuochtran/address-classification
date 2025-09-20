import re
import unicodedata
import time

# -----------------------
# Utility: normalize (lowercase, remove diacritics, remove punctuation)
# -----------------------
def strip_accents(s: str) -> str:
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return unicodedata.normalize('NFC', s)

def normalize(s: str) -> str:
    s = s.lower()
    # replace common punctuation with spaces
    s = re.sub(r'[\.,;/\\\(\)\[\]\-_:]', ' ', s)
    s = s.replace('\'', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    s = strip_accents(s)
    # remove any non-alphanumeric (keep spaces)
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# -----------------------
# Levenshtein distance (space-optimized)
# -----------------------
def levenshtein(a: str, b: str) -> int:
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
            sub = previous[j-1] + (0 if ca == cb else 1)
            current.append(min(ins, dele, sub))
        previous = current
    return previous[-1]

# -----------------------
# BK-tree for fast approximate lookup
# -----------------------
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

# -----------------------
# Build BK-tree and maps from a list of names
# -----------------------
def build_index(names):
    norm_to_orig = {}
    for name in names:
        n = normalize(name)
        # if duplicate normalized keys, keep the first (or could store list)
        if n not in norm_to_orig:
            norm_to_orig[n] = name
    bk = BKTree(levenshtein)
    for n in norm_to_orig:
        bk.add(n)
    return bk, norm_to_orig

# -----------------------
# Helper: dynamic threshold for allowed edit distance
# -----------------------
def max_dist_for_length(L: int) -> int:
    if L <= 2:
        return 0
    if L <= 5:
        return 1
    # allow up to ~20% of length as edits (rounded)
    return max(1, int(L * 0.20) + 0)

# -----------------------
# Main: classify address string
# -----------------------
def classify_address(text: str, bk_commune, map_commune, bk_district, map_district, bk_province, map_province):
    norm_text = normalize(text)
    tokens = norm_text.split()
    n = len(tokens)
    results = []

    # build candidate substrings (window up to 4 tokens; addresses usually short)
    max_window = 4
    candidates = []
    for i in range(n):
        for j in range(i+1, min(n, i+max_window) + 1):
            sub = ' '.join(tokens[i:j])
            L = len(sub.replace(' ', ''))
            # skip very short numeric tokens
            if re.fullmatch(r'\d+', sub):
                continue
            candidates.append((i, j, sub))

    # For each candidate, try match against communes, districts, provinces
    matches = []
    for (i,j,sub) in candidates:
        L = len(sub.replace(' ', ''))
        # try commune
        md = max_dist_for_length(max(1, L))
        r = bk_commune.search(sub, md) if bk_commune is not None else []
        if r:
            best = min(r, key=lambda x: x[1])  # (matched_norm, dist)
            matched_norm, dist = best
            score = 1.0 - dist / max(len(sub), len(matched_norm))
            matches.append({'level':'commune','span':(i,j),'sub':sub,'matched':matched_norm,'dist':dist,'score':score})
        # district
        md = max_dist_for_length(max(1, L))
        r = bk_district.search(sub, md) if bk_district is not None else []
        if r:
            best = min(r, key=lambda x: x[1])
            matched_norm, dist = best
            score = 1.0 - dist / max(len(sub), len(matched_norm))
            matches.append({'level':'district','span':(i,j),'sub':sub,'matched':matched_norm,'dist':dist,'score':score})
        # province
        md = max_dist_for_length(max(1, L))
        r = bk_province.search(sub, md) if bk_province is not None else []
        if r:
            best = min(r, key=lambda x: x[1])
            matched_norm, dist = best
            score = 1.0 - dist / max(len(sub), len(matched_norm))
            matches.append({'level':'province','span':(i,j),'sub':sub,'matched':matched_norm,'dist':dist,'score':score})

    # pick best for each level (highest score; if tie longer span)
    chosen = {}
    for level in ('commune','district','province'):
        cand = [m for m in matches if m['level']==level]
        if not cand:
            chosen[level] = None
            continue
        # sort by score desc, then span length desc
        cand.sort(key=lambda x: (x['score'], x['span'][1]-x['span'][0]), reverse=True)
        best = cand[0]
        # require a minimum score to accept (adjustable)
        if best['score'] >= 0.45:
            # map normalized to original name where possible
            orig = None
            if level == 'commune':
                orig = map_commune.get(best['matched'], None)
            elif level == 'district':
                orig = map_district.get(best['matched'], None)
            elif level == 'province':
                orig = map_province.get(best['matched'], None)
            chosen[level] = {'matched_norm':best['matched'],'orig':orig,'score':best['score'],'span':best['span'],'sub':best['sub'],'dist':best['dist']}
        else:
            chosen[level] = None

    return chosen

# -----------------------
# Example small database (you should replace with full official lists)
# -----------------------
PROVINCES = ["Long An", "Ha Noi", "Ho Chi Minh", "Bac Ninh"]
DISTRICTS = ["Cần Giuộc", "Thuận Thành (huyện)", "Quan 1", "Long An District"]
COMMUNES = ["Thuận Thành", "An Phu", "Can Giuoc Town"]

# build indexes
bk_province, map_province = build_index(PROVINCES)
bk_district, map_district = build_index(DISTRICTS)
bk_commune, map_commune = build_index(COMMUNES)

# -----------------------
# Quick tests (variants from the PDF)
# -----------------------
examples = [
    "X. Thuận Thành, H. Cần Giuộc, T. Long An",
    "Thuận Thanh, HCần Giuộc, Tlong An",
    "Thuận Thành, H Cần Giuộc T. Long An",
    "X ThuanThanh H. Can Giuoc, Long An",
    "ThuanThanh H Can Giuoc Long An",
    "X ThuanThanh LongAn",
    "ThuanThanh H Long An Long An",
]

def run_tests():
    for ex in examples:
        start = time.time()
        out = classify_address(ex, bk_commune, map_commune, bk_district, map_district, bk_province, map_province)
        elapsed = (time.time() - start) * 1000
        print(f"Input : {ex}")
        print(f"Time  : {elapsed:.2f} ms")
        for lvl in ('commune','district','province'):
            v = out[lvl]
            if v:
                print(f"  {lvl:8}: {v['orig']}  (norm='{v['matched_norm']}', score={v['score']:.2f}, sub='{v['sub']}')")
            else:
                print(f"  {lvl:8}: <not found>")
        print('-'*60)

if __name__ == "__main__":
    run_tests()
