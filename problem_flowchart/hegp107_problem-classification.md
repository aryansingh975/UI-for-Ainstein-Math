# NCERT Class 8 Mathematics (Chapter 7: Proportional Reasoning - 1)
## Problem Categorization by Proportional Solver (PS) Archetypes

This document classifies all **39 problems** from [`class08-hegp107-proportional-reasoning-1.validation.json`](./dataset/class08-hegp107-proportional-reasoning-1.validation.json) into the mathematical archetypes defined in the [PS Algorithm Flowchart](./ps_algorithm_flowchart.svg) and [PS Verification Document](./ps_algorithm_hegp107_verification.md).

---

### Executive Summary Table

| Category | Archetype Name | Governing Formula / Invariant | Count |
| :--- | :--- | :--- | :---: |
| **Type 1** | **Simplest Form & Ratio Equality** | $a \cdot d = b \cdot c$ or $\gcd(a, b)$ reduction | 9 |
| **Type 2** | **Rule of Three (*Trairāśika*)** | $x = \frac{b \cdot c}{a}$ | 14 |
| **Type 3** | **Sharing in a Ratio** | $u = \frac{T}{m+n}, S_1 = m \cdot u, S_2 = n \cdot u$ | 9 |
| **Type 4** | **Unit Rate & Density Comparison** | $R_1 = \frac{b_1}{a_1} \text{ vs } R_2 = \frac{b_2}{a_2}$ | 3 |
| **Non-Algo** | **Does Not Fit (Special / Non-Proportional)** | External measurements, inverse proportion, algebra | 4 |
| **Total** | | | **39** |

> *Note on Hybrids*: Problem #12 (Example 12) is **Type 3+2** (Sharing then Rule of Three); Problem #25 (Fig it Out p.175 Q3) is **Type 3+1** (Sharing then Simplest Form); Problem #29 (Fig it Out p.176 Q2) is **Type 2+5** (Rule of Three with ceiling function $\lceil x \rceil$). They are listed under their primary algorithmic category with notes.

---

## 1. Type 1: Simplest Form & Ratio Equality

**Description**: Problems asking whether two ratios are equivalent/proportional ($a:b :: c:d$), or asking to reduce a ratio to its simplest form by dividing by the highest common factor (HCF/GCD), or generating scaled multiples of a ratio.  
**Core Logic / Invariant**: $a \cdot d = b \cdot c \quad \text{or} \quad \frac{a}{\gcd(a,b)} : \frac{b}{\gcd(a,b)}$  
**Total Problems**: 9

### 1. `g08-hegp107-ex001` — Example 1
- **Subtopic**: Simplest Form & Proportions
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Are the ratios 3 : 4 and 72 : 96 proportional?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $3 \cdot 96 = 288 = 4 \cdot 72$
- **Expected Result**: **Proportional (Yes)**

### 2. `g08-hegp107-ex004` — Example 4
- **Subtopic**: Simplest Form
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > In my school, there are 5 teachers and 170 students. The teacher-student ratio is 5 : 170. Is this in simplest form?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $\text{HCF}(5, 170) = 5 \implies 1:34$
- **Expected Result**: **$1 : 34$**

### 3. `g08-hegp107-ex005` — Example 5
- **Subtopic**: Simplest Form
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Measure the width and height (to the nearest cm) of the cover page of your textbook. Find the ratio of width to height in its simplest form. (Given measured width = 21 cm, height = 28 cm).
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $\text{HCF}(21, 28) = 7 \implies 3:4$
- **Expected Result**: **$3 : 4$**

### 4. `g08-hegp107-ex006` — Example 6
- **Subtopic**: Additive vs Multiplicative Change
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > When Neelima was 3 years old, her mother's age was 10 times her age. What will be the ratio of their ages when Neelima is 12 years old? Is the ratio still 1 : 10?
- **Unit Alignment (Step 1)**: $t_2 = 12, m_2 = 39$
- **Formula & Execution (Step 3 & 4)**: Ratio $12:39 = 4:13 \neq 1:10$
- **Expected Result**: **Not 1:10 (No)**

### 5. `g08-hegp107-p165-q1` — Figure it Out p.165 Q1
- **Subtopic**: Proportional Ratios
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Circle the following statements of proportion that are true: (i) 4:7::12:21 (ii) 8:3::24:6 (iii) 7:12::12:7 (iv) 21:6::35:10 (v) 12:18::28:12 (vi) 24:8::9:3
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: Check $a \cdot d = b \cdot c$ for (i)-(vi)
- **Expected Result**: **(i), (iv), (vi)**

### 6. `g08-hegp107-p165-q2` — Figure it Out p.165 Q2
- **Subtopic**: Proportional Ratios
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Write three ratios that are proportional to 4 : 9.
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: Scale $4:9$ by 2, 3, 4
- **Expected Result**: **8:18, 12:27, 16:36**

### 7. `g08-hegp107-p165-q5` — Figure it Out p.165 Q5
- **Subtopic**: Digital Images & Proportions
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Observe the given table of digital images A (60×40 mm), B (80×40 mm), C (30×20 mm), D (90×60 mm), E (40×40 mm). Find the ratio of width to height for each image in simplest form and identify which images are proportional.
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: A=3:2, B=2:1, C=3:2, D=3:2, E=1:1
- **Expected Result**: **A, C, D**

### 8. `g08-hegp107-p165-q6` — Figure it Out p.165 Q6
- **Subtopic**: Simplest Form
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Observe the two brick-wall patterns shown below. In each pattern, what is the ratio of grey bricks to coloured bricks in simplest form? Pattern (a): 9 grey, 6 coloured. Pattern (b): 16 grey, 12 coloured.
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: (a) $9:6 = 3:2$; (b) $16:12 = 4:3$
- **Expected Result**: **(a) 3:2, (b) 4:3**

### 9. `g08-hegp107-p176-q1` — Figure it Out p.176 Q1
- **Subtopic**: Simplest Form
- **Algorithm Type**: `Type 1`
- **Question Text**:
  > Anagh mixes 600 mL of orange juice with 900 mL of apple juice to make a fruit drink. Write the ratio of orange juice to apple juice in its simplest form.
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $\text{HCF}(600, 900) = 300 \implies 2:3$
- **Expected Result**: **$2 : 3$**

---

## 2. Type 2: Rule of Three (Trairāśika)

**Description**: Direct proportionality scaling problems where three values $a, b, c$ are given to compute an unknown fourth value $x$. Based on classical Indian mathematics (*Trairāśika* of Āryabhaṭa and Bhāskara II). Includes problems requiring Step 5 discrete adjustments (e.g., ceiling function $\lceil x \rceil$ for buses).  
**Core Logic / Invariant**: $a : b :: c : x \implies x = \frac{b \cdot c}{a}$  
**Total Problems**: 14

### 1. `g08-hegp107-ex002` — Example 2
- **Subtopic**: Rule of Three (Trairasika)
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > Kesang wanted to make lemonade for a celebration. She used 6 glasses of water and 10 spoons of sugar. Her father wants 18 more glasses of lemonade of the same sweetness. How many spoons of sugar would Kesang need for this?
- **Unit Alignment (Step 1)**: Total $T=6+18=24$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{10 \times 24}{6} = 40$
- **Expected Result**: **40 spoons**

### 2. `g08-hegp107-ex007` — Example 7
- **Subtopic**: Proportional Ratios
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > Fill in the missing numbers for the following ratios that are proportional to 4 : 5: 8:__, __:15, 12:__, __:25, 20:__.
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: Scale $4:5$ by factors 2, 3, 5
- **Expected Result**: **10, 12, 15, 20, 25**

### 3. `g08-hegp107-ex008` — Example 8
- **Subtopic**: Rule of Three (Trairasika)
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > For the mid-day meal in a school with 120 students, the cook usually makes 15 kg of rice. On a rainy day, only 80 students came to school. How many kilograms of rice should the cook make so that the food is not wasted?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $x = \frac{15 \times 80}{120} = 10$
- **Expected Result**: **10 kg**

### 4. `g08-hegp107-ex009` — Example 9
- **Subtopic**: Unit Matching & Rule of Three
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > A car travels 90 km in 150 minutes. If it continues at the same speed, what distance will it cover in 4 hours?
- **Unit Alignment (Step 1)**: $4\text{ hr} = 240\text{ min}$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{90 \times 240}{150} = 144$
- **Expected Result**: **144 km**

### 5. `g08-hegp107-p165-q3` — Figure it Out p.165 Q3
- **Subtopic**: Proportional Ratios
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > Fill in the missing numbers in the following ratios such that they are proportional to 18 : 24: 3:__, 12:__, 20:__, 27:__.
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: Scale $18:24 \implies 3:4$
- **Expected Result**: **4, 16, 80/3, 36**

### 6. `g08-hegp107-p170-q1` — Figure it Out p.170 Q1
- **Subtopic**: Rule of Three
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > The Earth travels approximately 940 million kilometres around the Sun in a year. How many kilometres will it travel in a week?
- **Unit Alignment (Step 1)**: $1\text{ yr} = 52\text{ wks}$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{940,000,000}{52} = 18,076,923$
- **Expected Result**: **18,076,923 km**

### 7. `g08-hegp107-p170-q2` — Figure it Out p.170 Q2
- **Subtopic**: Rule of Three & Geometric Calculation
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > A mason is building a house in the shape shown in the diagram. He needs to construct both the outer walls and the inner wall that separates two rooms. To build a wall of 10-feet, he requires approximately 1450 bricks. How many bricks would he need to build the house? Assume all walls are of the same height and thickness. (Total wall length = 12+12+12+15+9+15+9+9+9+6 = 108 ft).
- **Unit Alignment (Step 1)**: Sum $L = 108\text{ ft}$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{1450 \times 108}{10} = 15,660$
- **Expected Result**: **15,660 bricks**

### 8. `g08-hegp107-p176-q2` — Figure it Out p.176 Q2
- **Subtopic**: Rule of Three & Capacity
- **Algorithm Type**: `Type 2+5`
- **Question Text**:
  > Last year, we hired 3 buses for the school trip. We had a total of 162 students and teachers who went on that trip and all the buses were full. This year we have 204 students and teachers. How many buses will we need? Will all the buses be full?
- **Unit Alignment (Step 1)**: Cap per bus = 54
- **Formula & Execution (Step 3 & 4)**: $x = \frac{204}{54} = 3.78 \implies \lceil 3.78 \rceil = 4$
- **Expected Result**: **4 buses (Not full)**

### 9. `g08-hegp107-p176-q5` — Figure it Out p.176 Q5
- **Subtopic**: Rule of Three (Historical Lilavati Problem)
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > Let us try an ancient problem from Līlāvatī. At that time weights were measured in a unit named palas and niskas was a unit of money. 'If 2 1/2 palas of saffron costs 3/7 niskas, O expert businessman! tell me quickly what quantity of saffron can be bought for 9 niskas?'
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $x = \frac{2.5 \times 9}{3/7} = 22.5 \times \frac{7}{3} = 52.5$
- **Expected Result**: **52.5 palas**

### 10. `g08-hegp107-p176-q7` — Figure it Out p.176 Q7
- **Subtopic**: Rule of Three & Density
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > The mass of equal volumes of gold and water are in the ratio 37 : 2. If 1 litre of water is 1 kg in mass, what is the mass of 1 litre of gold?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $x = \frac{37 \times 1}{2} = 18.5$
- **Expected Result**: **18.5 kg**

### 11. `g08-hegp107-p176-q8` — Figure it Out p.176 Q8
- **Subtopic**: Unit Conversion & Rule of Three
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > It is good farming practice to apply 10 tonnes of cow manure for 1 acre of land. A farmer is planning to grow tomatoes in a plot of size 200 ft by 500 ft. How much manure should he buy?
- **Unit Alignment (Step 1)**: Area=$10^5\text{ ft}^2$, $10\text{t}=10^4\text{kg}$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{10000 \times 100000}{43560} = 22956.8$
- **Expected Result**: **22,956.8 kg**

### 12. `g08-hegp107-p176-q9` — Figure it Out p.176 Q9
- **Subtopic**: Unit Matching & Rule of Three
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > A tap takes 15 seconds to fill a mug of water. The volume of the mug is 500 mL. How much time does the same tap take to fill a bucket of water if the bucket has a 10-litre capacity?
- **Unit Alignment (Step 1)**: $10\text{ L} = 10,000\text{ mL}$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{15 \times 10000}{500} = 300\text{ s}$
- **Expected Result**: **5 minutes**

### 13. `g08-hegp107-p176-q10` — Figure it Out p.176 Q10
- **Subtopic**: Unit Matching & Land Valuation
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > One acre of land costs ₹15,00,000. What is the cost of 2,400 square feet of the same land?
- **Unit Alignment (Step 1)**: $1\text{ acre} = 43,560\text{ ft}^2$
- **Formula & Execution (Step 3 & 4)**: $x = \frac{1500000 \times 2400}{43560} = 82645$
- **Expected Result**: **₹82,645**

### 14. `g08-hegp107-p176-q11` — Figure it Out p.176 Q11
- **Subtopic**: Rate & Time Comparison
- **Algorithm Type**: `Type 2`
- **Question Text**:
  > A tractor can plough the same area of a field 4 times faster than a pair of oxen. A farmer wants to plough his 20-acre field. A pair of oxen takes 6 hours to plough an acre of land. How much time would it take if the farmer used a pair of oxen to plough the field? How much time would it take him if he decides to use a tractor instead?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: Oxen: $20 \times 6 = 120\text{ h}$; Tractor: $\frac{120}{4} = 30\text{ h}$
- **Expected Result**: **120 h & 30 h**

---

## 3. Type 3: Sharing in a Ratio (Partitioning a Whole)

**Description**: Problems where a total quantity $T$ is distributed or partitioned into parts proportional to a given ratio $m:n$ (or $m:n:p$). Also includes multi-step problems where partition outputs undergo subsequent ratio revision or scaling.  
**Core Logic / Invariant**: $P = \sum \text{ratio parts}; \quad u = \frac{T}{P}; \quad S_i = \text{part}_i \cdot u$  
**Total Problems**: 9

### 1. `g08-hegp107-ex011` — Example 11
- **Subtopic**: Sharing in a Ratio
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > Prashanti and Bhuvan started a food cart business near their school. Prashanti invested ₹75,000 and Bhuvan invested ₹25,000. At the end of the first month, they gained a profit of ₹4,000. They decided that they would share the profit in the same ratio as that of their investment. What is each person's share of the profit?
- **Unit Alignment (Step 1)**: $75k:25k = 3:1$
- **Formula & Execution (Step 3 & 4)**: $P=4, u = \frac{4000}{4} = 1000 \implies 3000, 1000$
- **Expected Result**: **₹3,000 & ₹1,000**

### 2. `g08-hegp107-ex012` — Example 12
- **Subtopic**: Sharing in a Ratio & Rule of Three
- **Algorithm Type**: `Type 3+2`
- **Question Text**:
  > A mixture of 40 kg contains sand and cement in the ratio of 3 : 1. How much cement should be added to the mixture to make the ratio of sand to cement 5 : 2?
- **Unit Alignment (Step 1)**: Sand=30, Cem=10
- **Formula & Execution (Step 3 & 4)**: $c_{\text{new}} = \frac{2 \times 30}{5} = 12$; $\text{Add} = 12 - 10$
- **Expected Result**: **2 kg**

### 3. `g08-hegp107-p175-q1` — Figure it Out p.175 Q1
- **Subtopic**: Sharing in a Ratio
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > Divide ₹4,500 into two parts in the ratio 2 : 3.
- **Unit Alignment (Step 1)**: $P = 2 + 3 = 5$
- **Formula & Execution (Step 3 & 4)**: $u = \frac{4500}{5} = 900 \implies 1800, 2700$
- **Expected Result**: **₹1,800 & ₹2,700**

### 4. `g08-hegp107-p175-q2` — Figure it Out p.175 Q2
- **Subtopic**: Sharing in a Ratio
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > In a science lab, acid and water are mixed in the ratio of 1 : 5 to make a solution. In a bottle that has 240 mL of the solution, how much acid and water does the solution contain?
- **Unit Alignment (Step 1)**: $P = 1 + 5 = 6$
- **Formula & Execution (Step 3 & 4)**: $u = \frac{240}{6} = 40 \implies 40, 200$
- **Expected Result**: **40 mL & 200 mL**

### 5. `g08-hegp107-p175-q3` — Figure it Out p.175 Q3
- **Subtopic**: Sharing in a Ratio & Ratio Revision
- **Algorithm Type**: `Type 3+1`
- **Question Text**:
  > Blue and yellow paints are mixed in the ratio of 3 : 5 to produce green paint. To produce 40 mL of green paint, how much of these two colours are needed? To make the paint a lighter shade of green, I added 20 mL of yellow to the mixture. What is the new ratio of blue and yellow in the paint?
- **Unit Alignment (Step 1)**: $P = 8, u=5$
- **Formula & Execution (Step 3 & 4)**: Blue=15, Yel=25; New Yel=45; $15:45$
- **Expected Result**: **1 : 3**

### 6. `g08-hegp107-p175-q4` — Figure it Out p.175 Q4
- **Subtopic**: Sharing in a Ratio
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > To make soft idlis, you need to mix rice and urad dal in the ratio of 2 : 1. If you need 6 cups of this mixture to make idlis tomorrow morning, how many cups of rice and urad dal will you need?
- **Unit Alignment (Step 1)**: $P = 2 + 1 = 3$
- **Formula & Execution (Step 3 & 4)**: $u = \frac{6}{3} = 2 \implies 4, 2$
- **Expected Result**: **4 cups & 2 cups**

### 7. `g08-hegp107-p175-q5` — Figure it Out p.175 Q5
- **Subtopic**: Sharing in a Ratio & Fractional Addition
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > I have one bucket of orange paint that I made by mixing red and yellow paints in the ratio of 3 : 5. I added another bucket of yellow paint to this mixture. What is the ratio of red paint to yellow paint in the new mixture?
- **Unit Alignment (Step 1)**: Fractions of bucket
- **Formula & Execution (Step 3 & 4)**: Red=$\frac{3}{8}$, Yel=$\frac{5}{8}+1 = \frac{13}{8} \implies 3:13$
- **Expected Result**: **$3 : 13$**

### 8. `g08-hegp107-p176-q4` — Figure it Out p.176 Q4
- **Subtopic**: Sharing in a Ratio
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > A crane of height 155 cm has its neck and the rest of its body in the ratio 4 : 6. For your height, if your neck and the rest of the body also had this ratio, how tall would your neck be? (Assuming student height = 150 cm).
- **Unit Alignment (Step 1)**: $P = 4 + 6 = 10$
- **Formula & Execution (Step 3 & 4)**: $h_{\text{neck}} = \frac{4}{10} \times 150 = 60$
- **Expected Result**: **60 cm**

### 9. `g08-hegp107-p176-q12` — Figure it Out p.176 Q12
- **Subtopic**: Sharing in a Ratio & Cost Analysis
- **Algorithm Type**: `Type 3`
- **Question Text**:
  > The ₹10 coin is an alloy of copper and nickel called 'cupro-nickel'. Copper and nickel are mixed in a 3 : 1 ratio to get this alloy. The mass of the coin is 7.74 grams. If the cost of copper is ₹906 per kg and the cost of nickel is ₹1,341 per kg, what is the cost of these metals in a ₹10 coin?
- **Unit Alignment (Step 1)**: $P=4$; $1\text{ kg}=1000\text{ g}$
- **Formula & Execution (Step 3 & 4)**: Cu: $5.805\text{g} \to ₹5.26$; Ni: $1.935\text{g} \to ₹2.59$
- **Expected Result**: **₹7.85**

---

## 4. Type 4: Unit Rate & Density Comparison

**Description**: Problems comparing two separate rate or density pairs $(a_1, b_1)$ and $(a_2, b_2)$ to determine which is larger, smaller, stronger, sweeter, denser, or more expensive. The quantities must be normalized into unit rates before comparison.  
**Core Logic / Invariant**: $R_1 = \frac{b_1}{a_1}, \quad R_2 = \frac{b_2}{a_2}; \quad \text{Compare } R_1 \gtrless R_2$  
**Total Problems**: 3

### 1. `g08-hegp107-ex003` — Example 3
- **Subtopic**: Simplest Form & Proportions
- **Algorithm Type**: `Type 4`
- **Question Text**:
  > Nitin and Hari were constructing a compound wall around their plot. Nitin built a 60 ft wall using 3 bags of cement, and Hari built a 40 ft wall using 2 bags of cement. Nitin thinks that Hari's wall is weaker because he used fewer bags of cement. Is Nitin right?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: $R_1 = \frac{60}{3} = 20$, $R_2 = \frac{40}{2} = 20$
- **Expected Result**: **Equal strength (No)**

### 2. `g08-hegp107-ex010` — Example 10
- **Subtopic**: Unit Matching & Comparison
- **Algorithm Type**: `Type 4`
- **Question Text**:
  > A small farmer in Himachal Pradesh sells each 200 g packet of tea for ₹200. A large estate in Meghalaya sells each 1 kg packet of tea for ₹800. Are the weight-to-price ratios in both places proportional? Which tea is more expensive?
- **Unit Alignment (Step 1)**: $1\text{ kg} = 1000\text{ g}$
- **Formula & Execution (Step 3 & 4)**: Himachal: ₹1000/kg; Meghalaya: ₹800/kg
- **Expected Result**: **Himachal tea**

### 3. `g08-hegp107-p176-q3` — Figure it Out p.176 Q3
- **Subtopic**: Population Density & Ratios
- **Algorithm Type**: `Type 4`
- **Question Text**:
  > The area of Delhi is 1,484 sq. km and the area of Mumbai is 550 sq. km. The population of Delhi is approximately 30 million and that of Mumbai is 20 million people. Which city is more crowded? Why do you say so?
- **Unit Alignment (Step 1)**: Direct
- **Formula & Execution (Step 3 & 4)**: Delhi: 20216/km²; Mumbai: 36364/km²
- **Expected Result**: **Mumbai**

---

## 5. Problems Which Do Not Fit Any Standard Type (Non-Algo / Special)

**Description**: Problems in the textbook chapter that cannot be solved by direct proportional closed-form formulas. These involve hands-on physical ruler measurements, qualitative drawing assessments, inverse relationships, or non-linear algebraic equations.  
**Core Logic / Invariant**: Requires domain-specific, manual, or algebraic methods (outside PS)  
**Total Problems**: 4

### 1. `g08-hegp107-p165-q4` — Figure it Out p.165 Q4
- **Subtopic**: Geometric Similarity & Ratios
- **Algorithm Type**: `Non-Algo`
- **Question Text**:
  > In the image on the side, five rectangles A, B, C, D and E are drawn at angles. Measure their width and height and determine which rectangles are similar.
- **Unit Alignment (Step 1)**: Ruler measurement
- **Formula & Execution (Step 3 & 4)**: Hands-on geometric measurement
- **Expected Result**: **Rectangles A, C, D**

### 2. `g08-hegp107-p165-q7` — Figure it Out p.165 Q7
- **Subtopic**: Real-world Body Proportions
- **Algorithm Type**: `Non-Algo`
- **Question Text**:
  > Let us draw some human figures. Measure your friend's body — the length of head to toe, length of arms, torso, legs. Find the ratios and check if your drawing looks more realistic when the ratios are proportional.
- **Unit Alignment (Step 1)**: Practical drawing
- **Formula & Execution (Step 3 & 4)**: Qualitative assessment of visual realism
- **Expected Result**: **Yes (Proportional)**

### 3. `g08-hegp107-p171-talk` — Math Talk p.171
- **Subtopic**: Non-Proportional / Inverse Relationships
- **Algorithm Type**: `Non-Algo`
- **Question Text**:
  > Puneeth's father went from Lucknow to Kanpur in 2 hours by riding his motorcycle at a speed of 50 km/h. If he drives at 75 km/h, how long will it take him to reach Kanpur? Can we form this problem as a proportion 50 : 2 :: 75 : __?
- **Unit Alignment (Step 1)**: Inverse Relation
- **Formula & Execution (Step 3 & 4)**: $D = 50 \times 2 = 100$; $t = \frac{100}{75} = 1.33\text{ h}$
- **Expected Result**: **Not Direct (1h 20m)**

### 4. `g08-hegp107-p176-q6` — Figure it Out p.176 Q6
- **Subtopic**: Additive vs Multiplicative Change
- **Algorithm Type**: `Non-Algo`
- **Question Text**:
  > Harmain is a 1-year-old girl. Her elder brother is 5 years old. What will be Harmain's age when the ratio of her age to her brother's age is 1 : 2?
- **Unit Alignment (Step 1)**: Linear Equation
- **Formula & Execution (Step 3 & 4)**: $\frac{1+x}{5+x} = \frac{1}{2} \implies x = 3 \implies 1+3=4$
- **Expected Result**: **4 years old**

### Detailed Breakdown of Why These 4 Problems Do Not Fit Standard Types

1. **`g08-hegp107-p165-q4` (Hands-on Geometric Ruler Measurement)**:
   - *Why it does not fit*: The problem does not supply numerical values in the text; it asks the student to physically measure rectangles printed on textbook page 164 using a ruler. It depends on physical measurement apparatus rather than algorithmic calculation from text givens.

2. **`g08-hegp107-p165-q7` (Qualitative Visual Realism & Drawing Task)**:
   - *Why it does not fit*: Asks whether a drawing is realistic based on human visual proportions. This is a perceptual / qualitative visual evaluation task with no numeric word problem inputs to execute arithmetic on.

3. **`g08-hegp107-p171-talk` (Inverse Proportionality / Speed-Time)**:
   - *Why it does not fit*: It features an **inverse proportion** relationship ($v_1 \cdot t_1 = v_2 \cdot t_2$), where speed is inversely proportional to time ($50 \text{ km/h} \times 2 \text{ h} = 100 \text{ km} \implies t = \frac{100}{75} = 1\text{h } 20\text{m}$). Standard direct proportion ($x = \frac{b \cdot c}{a}$) yields the wrong answer ($3\text{ h}$). It requires an Inverse Proportionality archetype ($x = \frac{a \cdot b}{c}$).

4. **`g08-hegp107-p176-q6` (Non-Linear Algebraic Age Equation)**:
   - *Why it does not fit*: Involves an additive shift in time across both numerator and denominator: $\frac{1 + x}{5 + x} = \frac{1}{2} \implies 2 + 2x = 5 + x \implies x = 3$. This is a linear algebraic equation in one variable, not a constant proportional scaling problem, because adding a constant to both terms changes their ratio non-linearly.

