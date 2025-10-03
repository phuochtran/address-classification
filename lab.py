import re
import unicodedata
from unidecode import unidecode

'''
def strip_accents(s: str) -> str:
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return unicodedata.normalize('NFC', s)
'''

def normalize(text: str) -> str:
    text = text.lower()
    text = unidecode(text)  # handles đ→d, ô→o, ă→a, etc.
    text = re.sub(r'[\W_]+', ' ', text)  # replace non-alnum with spaces
    return text.strip()

print(normalize("xA đon xA hUYEn BINH lU tiNH HA nAm tiNH HA nAm"))
