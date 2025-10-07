import re
import time
from functools import lru_cache
from collections import defaultdict

class TrieNode:
    __slots__ = ['children', 'is_end', 'original']
    
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.original = None

class FuzzyTrie:
    def __init__(self):
        self.root = TrieNode()
        self.norm_to_orig = {}
    
    def insert(self, word, original):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.original = original
        self.norm_to_orig[word] = original
    
    def search_fuzzy(self, word, max_dist):
        """DFS search with edit distance limit"""
        results = []
        
        def dfs(node, pos, current_word, dist):
            # Pruning: if distance exceeded, stop
            if dist > max_dist:
                return
            
            # If we've processed all characters and at end node
            if pos == len(word):
                if node.is_end:
                    num = Solution._lcs(word, current_word)
                    score = 1.0 - dist / max(len(word), len(current_word))
                    results.append((current_word, num, score))
                # Continue searching for insertions
                for char, child in node.children.items():
                    dfs(child, pos, current_word + char, dist + 1)
                return
            
            target_char = word[pos]
            
            # Exact match
            if target_char in node.children:
                dfs(node.children[target_char], pos + 1, current_word + target_char, dist)
            
            # Substitution, deletion, insertion (only if we have distance budget)
            if dist < max_dist:
                # Substitution: different character
                for char, child in node.children.items():
                    if char != target_char:
                        dfs(child, pos + 1, current_word + char, dist + 1)
                
                # Deletion: skip character in word
                dfs(node, pos + 1, current_word, dist + 1)
                
                # Insertion: add character from trie
                for char, child in node.children.items():
                    dfs(child, pos, current_word + char, dist + 1)
        
        dfs(self.root, 0, "", 0)
        return results

class Solution:
    def __init__(self):
        # Load Data Set
        self.province_path = 'list_province.txt'
        self.district_path = 'list_district.txt'
        self.ward_path = 'list_ward.txt'
        
        # Build Tries
        self.province_trie, self.province_map = self._build_trie(self._load_data(self.province_path))
        self.district_trie, self.district_map = self._build_trie(self._load_data(self.district_path))
        self.ward_trie, self.ward_map = self._build_trie(self._load_data(self.ward_path))
        
        # Build Reference
        self.ref = self._build_reference("reference.txt")
        
        # Set up Prefix Map - sorted by length (longest first)
        prefix_list = [
            ("thanh pho", "province"), ("thành phố", "province"),
            ("thi tran", "ward"), ("thị trấn", "ward"),
            ("thi xa", "district"), ("thị xã", "district"),
            ("phuong", "ward"), ("phường", "ward"),
            ("huyen", "district"), ("huyện", "district"),
            ("quan", "district"), ("quận", "district"),
            ("tinh", "province"), ("tỉnh", "province"),
            ("tp.", "province"), ("tx.", "district"), ("tt.", "ward"),
            ("xa", "ward"), ("xã", "ward"),
            ("tp", "province"), ("tx", "district"), ("tt", "ward"),
            ("p.", "ward"), ("q.", "district"), ("t.", "province"),
            ("x.", "ward"), ("h.", "district"),
            ("p", "ward"), ("q", "district"), ("t", "province"),
            ("x", "ward"), ("h", "district"),
        ]
        # Pre-normalize prefixes
        self.prefix_map = [(self._normalize(pfx), lvl, len(pfx)) for pfx, lvl in prefix_list]

    def _load_data(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

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

    @lru_cache(maxsize=1024)
    def _normalize(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r'[\W_]+', ' ', s)
        return s.strip()

    @staticmethod
    @lru_cache(maxsize=2048)
    def _lcs(s1, s2):
        N, M = len(s1)+1, len(s2)+1
        vec = [0]*M
        for i in range(N-2, -1, -1):
            tmp = [0]*M
            for j in range(M-2, -1, -1):
                tmp[j] = 1 + vec[j + 1] if s1[i] == s2[j] else max(vec[j], tmp[j + 1])
            vec = tmp
        return vec[0]

    def _build_trie(self, names):
        norm_to_orig = {}
        trie = FuzzyTrie()
        
        for name in names:
            n = self._normalize(name)
            if n not in norm_to_orig:
                norm_to_orig[n] = name
                trie.insert(n, name)
        
        return trie, norm_to_orig

    def _max_distance(self, L: int) -> int:
        if L <= 2:
            return 0
        if L <= 5:
            return 1
        return max(1, int(L * 0.2))

    def _detect_level(self, substr: str) -> tuple:
        # Fast prefix matching - check if substring starts with any prefix
        for pfx_norm, lvl, orig_len in self.prefix_map:
            if substr.startswith(pfx_norm):
                return orig_len, lvl
        return 0, None

    def _worker(self, substr: str, debug=False) -> bool:
        maxdist = self._max_distance(max(1, len(substr.replace(' ', ''))))
        bias = 0.2
        
        # Try prefix detection first
        prefix_len, level = self._detect_level(substr)
        
        if level:
            sub = substr[prefix_len:].strip()
            if not sub:
                return False
            
            # Search based on detected level
            if level == "province":
                results = self.province_trie.search_fuzzy(sub, maxdist)
                if results:
                    norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                    if score+bias > self.output["province"]["score"]:
                        orig = self.province_map.get(norm, "")
                        self.output["province"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                        if self.output["district"]["orig"] and self.output["district"]["norm"] not in self.ref[norm]:
                            self.output["district"] = {'orig':'','norm':'','num':0,'score':0}
                        return True
                        
            elif level == "district":
                results = self.district_trie.search_fuzzy(sub, maxdist)
                if results:
                    norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                    if self.output["province"]["orig"] and norm not in self.ref[self.output["province"]["norm"]]:
                        return False
                    if score+bias > self.output["district"]["score"]:
                        orig = self.district_map.get(norm, "")
                        self.output["district"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                        return True
                        
            elif level == "ward":
                results = self.ward_trie.search_fuzzy(sub, maxdist)
                if results:
                    norm, num, score = max(results, key=lambda x: (x[2], x[1]))
                    # Validation checks
                    if self.output["province"]["orig"]:
                        if self.output["district"]["orig"]:
                            if norm not in self.ref[self.output["province"]["norm"]][self.output["district"]["norm"]]:
                                return False
                        else:
                            if all(norm not in wards for wards in self.ref[self.output["province"]["norm"]].values()):
                                return False
                    if score+bias > self.output["ward"]["score"]:
                        orig = self.ward_map.get(norm, "")
                        self.output["ward"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                        return True
        
        # If no prefix match, try direct matching (without bias)
        bias = 0
        
        # Province
        results = self.province_trie.search_fuzzy(substr, maxdist)
        if results:
            norm, num, score = max(results, key=lambda x: (x[2], x[1]))
            if score+bias > self.output["province"]["score"]:
                orig = self.province_map.get(norm, "")
                self.output["province"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                if self.output["district"]["orig"] and self.output["district"]["norm"] not in self.ref[norm]:
                    self.output["district"] = {'orig':'','norm':'','num':0,'score':0}
                return True
        
        # District
        results = self.district_trie.search_fuzzy(substr, maxdist)
        if results:
            norm, num, score = max(results, key=lambda x: (x[2], x[1]))
            if self.output["province"]["orig"] and norm not in self.ref[self.output["province"]["norm"]]:
                return False
            if score+bias > self.output["district"]["score"]:
                orig = self.district_map.get(norm, "")
                self.output["district"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                return True
        
        # Ward
        results = self.ward_trie.search_fuzzy(substr, maxdist)
        if results:
            norm, num, score = max(results, key=lambda x: (x[2], x[1]))
            if self.output["province"]["orig"]:
                if self.output["district"]["orig"]:
                    if norm not in self.ref[self.output["province"]["norm"]][self.output["district"]["norm"]]:
                        return False
                else:
                    if all(norm not in wards for wards in self.ref[self.output["province"]["norm"]].values()):
                        return False
            if score+bias > self.output["ward"]["score"]:
                orig = self.ward_map.get(norm, "")
                self.output["ward"] = {'orig':orig,'norm':norm,'num':num,'score':score+bias}
                return True
        
        return False

    def process(self, input: str, debug=False) -> dict:
        start = time.perf_counter()
        self.output = {
            "province": {"orig": "", "norm": "", "num": 0, "score": 0},
            "district": {"orig": "", "norm": "", "num": 0, "score": 0},
            "ward": {"orig": "", "norm": "", "num": 0, "score": 0}
        }
        
        parts = [part for part in reversed(input.split(','))]
        for part in parts:
            norm_text = self._normalize(part)
            tokens = norm_text.split()
            max_window = 4
            
            # Early exit if all fields filled
            if all(self.output[level]["orig"] for level in ["ward", "district", "province"]):
                break
                
            for i in reversed(range(len(tokens))):
                for j in range(max(0, i-max_window+1), i+1):
                    substr = ' '.join(tokens[j:i+1])
                    if self._worker(substr, debug):
                        break
                        
        end = time.perf_counter()
        if debug:
            print(f"Overall Exec Time: {end-start:.4f}s")
        return [self.output[level]["orig"] for level in ["ward", "district", "province"]]

if __name__ == "__main__":
    sol = Solution()
    result = sol.process("xa loNG BinH HUyEn Go cOng tAY, tinH iEn GIANG", debug=True)
    print(f"Result: {result}")
