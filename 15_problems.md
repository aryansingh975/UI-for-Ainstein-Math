# 15 Problems — Solution Graph Generation Plan

> See also: [core_structure_idea.md](./core_structure_idea.md) for unified JSON schema and pedagogical architecture.

---

## Chapter Mapping

| Chapter Folder | Source PDF | Topic |
|---|---|---|
| `chapter-1/squares-and-cubes/` | `hegp101.pdf` (Part 1, Ch 1) | A Square and A Cube |
| `chapter-2/power-play/` | `hegp102.pdf` (Part 1, Ch 2) | Power Play (Exponents) |
| `chapter-8/inverse-proportion/` | `hegp203.pdf` (Part 2, Ch 3) | Proportional Reasoning - 2 |
| `chapter-9/percentages/` | `hegp201.pdf` (Part 2, Ch 1) | Fractions in Disguise (%) |
| `chapter-10/quadratic-equation/` | Existing — renamed from `chapter-1` | Quadratic Equations (Gr 10) |
| `chapter-11/algebra-play/` | `hegp206.pdf` (Part 2, Ch 6) | Algebra Play |

---

## Chapter 8: Proportional Reasoning - 2 (Inverse Proportion)

Source: `dataset/class8_NCERT_part2/hegp203.pdf`
Folder: `solution_graph/chapter-8/inverse-proportion/`

| # | UUID | Difficulty | Problem | Key Answer |
|---|---|---|---|---|
| 1 | `g08-hegp203-ex003` | **Easy** | 20 workers take 4 days to lay a road. How many days will 10 workers take? | 8 days (20×4=80 worker-days ÷ 10 = 8) |
| 2 | `g08-hegp203-ex005` | **Moderate** | A school has provisions to feed 80 students for 15 days. If 20 more students join, for how many days will provisions last? | 12 days (80×15=1200 ÷ 100 = 12) |
| 3 | `g08-hegp203-ex006` | **Hard** | Ram takes 1 hr, Shyam takes 1.5 hrs to cut vegetables. How long do they take together? | 36 minutes (combined rate = 1+2/3 = 5/3 per hr → 3/5 hr = 36 min) |

---

## Chapter 1: A Square and A Cube (Square Roots & Cube Roots)

Source: `dataset/class8_NCERT_part1/hegp101.pdf`
Folder: `solution_graph/chapter-1/squares-and-cubes/`

| # | UUID | Difficulty | Problem | Key Answer |
|---|---|---|---|---|
| 4 | `g08-hegp101-sqrt-324` | **Easy** | Find √324 using prime factorisation. | 18 (324 = 2² × 3⁴ = 18²) |
| 5 | `g08-hegp101-cbrt-3375` | **Moderate** | Find ∛3375 using prime factorisation. | 15 (3375 = 3³ × 5³ = 15³) |
| 6 | `g08-hegp101-ex-p10-q6` | **Hard** | What is the smallest number to multiply 9408 by to make it a perfect square? | 3 (9408 = 2⁶ × 3 × 7² → multiply by 3 → √28224 = 168) |

---

## Chapter 2: Power Play (Exponents & Powers)

Source: `dataset/class8_NCERT_part1/hegp102.pdf`
Folder: `solution_graph/chapter-2/power-play/`

| # | UUID | Difficulty | Problem | Key Answer |
|---|---|---|---|---|
| 7 | `g08-hegp102-ex-p11-q1` | **Easy** | Simplify 2⁻⁴ × 2⁷ in exponential form. | 2³ = 8 (product rule: 2^(-4+7) = 2³) |
| 8 | `g08-hegp102-ex-p26-q5v` | **Moderate** | Simplify m⁵n¹²/(mn)⁹ in exponential form. | n³/m⁴ (expand: m⁵n¹²/m⁹n⁹ = m⁻⁴n³) |
| 9 | `g08-hegp102-ex-p26-q1` | **Hard** | Find units digit in 2²²⁴ ÷ 4³². | 6 (4³²=2⁶⁴, quotient=2¹⁶⁰, cycle [2,4,8,6] period 4, 160÷4=0 → units digit=6) |

---

## Chapter 9: Fractions in Disguise (Percentages — Profit/Loss, SI/CI)

Source: `dataset/class8_NCERT_part2/hegp201.pdf`
Folder: `solution_graph/chapter-9/percentages/`

| # | UUID | Difficulty | Problem | Key Answer |
|---|---|---|---|---|
| 10 | `g08-hegp201-ex-p19-q1` | **Easy** | Shopkeeper buys geometry box for ₹75, sells for ₹110. Find profit and profit %. | Profit = ₹35, Profit% = 46.67% |
| 11 | `g08-hegp201-ex010` | **Moderate** | TV bought at ₹21,000 depreciates by 5% after 1 year. Find value after 1 year. | ₹19,950 (reduction = 21000 × 0.05 = 1050) |
| 12 | `g08-hegp201-ex-p22-q1` | **Hard** | ₹20,000 at 10% p.a. for 2 years: compare simple vs compound interest. | SI = ₹4000 (total ₹24,000); CI: Y1=₹22,000, Y2=₹24,200; Difference = ₹200 |

---

## Chapter 11: Algebra Play (Linear Equations in One Variable)

Source: `dataset/class8_NCERT_part2/hegp206.pdf`
Folder: `solution_graph/chapter-11/algebra-play/`

| # | UUID | Difficulty | Problem | Key Answer |
|---|---|---|---|---|
| 13 | `g08-hegp206-grid-eq` | **Easy** | 4a + 16 = 36, solve for a. What are the four consecutive numbers starting at a? | a = 5; numbers: 5, 6, 7, 8 |
| 14 | `g08-hegp206-age-q7` | **Moderate** | Mother is 5× daughter's age. In 6 years, she will be 3× daughter's age. How old is daughter now? | 6 years (5x+6 = 3(x+6) → 2x = 12 → x = 6) |
| 15 | `g08-hegp206-heads-legs` | **Hard** | 55 heads, 150 legs: how many horses and how many hens? | 20 horses, 35 hens (h+k=55, 4h+2k=150 → h=20, k=35) |

---

## Folder Structure

```
solution_graph/
  chapter-1/
    squares-and-cubes/
      g08-hegp101-sqrt-324/        → graph.json  graph.js  graph.svg
      g08-hegp101-cbrt-3375/       → graph.json  graph.js  graph.svg
      g08-hegp101-ex-p10-q6/       → graph.json  graph.js  graph.svg
  chapter-2/
    power-play/
      g08-hegp102-ex-p11-q1/       → graph.json  graph.js  graph.svg
      g08-hegp102-ex-p26-q5v/      → graph.json  graph.js  graph.svg
      g08-hegp102-ex-p26-q1/       → graph.json  graph.js  graph.svg
  chapter-8/
    inverse-proportion/
      g08-hegp203-ex003/           → graph.json  graph.js  graph.svg
      g08-hegp203-ex005/           → graph.json  graph.js  graph.svg
      g08-hegp203-ex006/           → graph.json  graph.js  graph.svg
  chapter-9/
    percentages/
      g08-hegp201-ex-p19-q1/       → graph.json  graph.js  graph.svg
      g08-hegp201-ex010/           → graph.json  graph.js  graph.svg
      g08-hegp201-ex-p22-q1/       → graph.json  graph.js  graph.svg
  chapter-10/
    quadratic-equation/
      g10-quad-ex001/              → graph.json  graph.js  graph.svg  (existing, renamed from chapter-1)
  chapter-11/
    algebra-play/
      g08-hegp206-grid-eq/         → graph.json  graph.js  graph.svg
      g08-hegp206-age-q7/          → graph.json  graph.js  graph.svg
      g08-hegp206-heads-legs/      → graph.json  graph.js  graph.svg
```

---

## Schema Reference

All graphs use the **unified schema** from `core_structure_idea.md`:

- `graph_meta` → id, problem_uuid, problem_text, navigation_label, graph_type, version, total_methods, total_nodes, total_edges
- `start_node` → `"start"`
- `conclusion_node` → `"conclusion"`
- `nodes[]` → each node: `id`, `type` (start/method/step/extraction/conclusion), `label`, `description`, `prompt`, `accept[]`, `hints[]`
- `edges[]` → `{ "from": "...", "to": "..." }`
- Word problems: include `extraction` nodes for givens and goal
- Direct calc problems: `extraction` nodes with `"optional": true` + direct leap edge from `start` to method node
- `graph.js` wraps JSON: `window.SOLUTION_GRAPHS = window.SOLUTION_GRAPHS || {}; window.SOLUTION_GRAPHS["<uuid>"] = { ... };`

