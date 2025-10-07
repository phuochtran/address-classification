import re

def _levenshtein(a: str, b: str) -> int:
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

def _normalize(s: str) -> str:
    s = s.lower()
    #s = unidecode(s)
    #s = re.sub(r'[\W_]+', ' ', s)
    return s.strip()
input = "xA hoa TinH, huYEN MaNg thiT, Tinh viN Long"
pinput = [part for part in reversed(input.split(','))]
print(pinput)
