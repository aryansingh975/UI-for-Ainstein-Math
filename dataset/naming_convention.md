# Dataset Naming Convention

The files in the **`dataset/`** directory follow a simple naming schema that encodes the grade, source textbook, and chapter identifier.

## Pattern
```
<class><grade>-<source><id>.validation.json
```

| Component | Example | Meaning |
|-----------|---------|---------|
| **class** | `class08` | Grade 8 (the school class). |
| **source** | `hegp` | Abbreviation for **Higher Elementary Granth Prakash**, the NCERT *Ganita Prakash* textbook used for Grade 8 mathematics. |
| **id** | `107` | Internal textbook/chapter identifier used by NCERT. In this case it corresponds to *Chapter 7 – Proportional Reasoning*. |
| **extension** | `.validation.json` | The file is a JSON‑formatted validation dataset containing the problem statement, givens, solution steps, hints, and expected answers. |

### Example
- **File**: `class08-hegp107.validation.json`
- **Interpretation**: A Grade 8 problem taken from the *Higher Elementary Granth Prakash* textbook, chapter 107 (chapter 7), representing a validation dataset.

## Adding new files
1. Determine the grade and textbook source (e.g., `hegp` for Ganita Prakash).
2. Identify the NCERT chapter/ID number (e.g., `107`).
3. Name the file using the pattern above and place it under `dataset/` (or a sub‑folder for the specific grade).
4. Update this README if you introduce a new source abbreviation or naming rule.

---
*Consistent naming makes the dataset easier to explore, query, and extend.*