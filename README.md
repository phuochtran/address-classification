## KEY FEATURES
- Parse province/district/ward from unstructured text.

- Auto-builds hierarchy from plain text files (no JSON or API).

- Handles abbreviations (Q.1, P05, TP.HCM, TX Dĩ An, etc.).

- OCR noise correction (0→o, 1→l/i, 5→s, 8→b).

- Context scoring ensures realistic order (ward → district → province).

- Fallback detection for missing labels or incomplete input.

## PARSING FLOW
1. Normalization & Preprocessing

- Input is cleaned and standardized for later matching: Convert to lowercase, remove accents, unify spaces.

- Expand abbreviations: Q.1 → quan 1, P05 → phuong 5, TX → thi xa, TP → thanh pho.

- Apply OCR correction for typical digit/letter swaps.

- Output three normalized variants for robustness

2. Province Detection

- A Trie built from all province names and aliases scans the normalized text.

- Each match is scored based on:

+ Token length and relative position in text.

+ Bonus if preceded by “tỉnh”, “tp”, “thành phố”.

+ The top-scoring candidate becomes the detected province.

3. District Detection (Contextual)

- Trie search limited to districts under the detected province.

- Context-aware scoring:

+ Bonus if preceded by district-related words (quan, huyen, thi xa, tp).

+ Penalty if preceded by lower-level labels (phuong, xa).

+ Filter out districts whose normalized name equals the province name.

+ The earliest and highest-confidence district is selected.

4. Ward Detection

Trie search restricted by (province, district) pair.

Prefers wards appearing before the detected district (as in Vietnamese order).

Anchor check: If “phường N” found but N not valid in that district → leave ward empty.

5. Hierarchical Fallback

When any level is missing, _hier_lookup() searches normalized text against known province–district–ward combinations to fill missing parts.
