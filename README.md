# ainstein-math

A collection of math resources, validation data, and AI‑assisted problem‑solving tools for **Grade 8 NCERT** (and beyond). This repository contains:

- **Dataset** – JSON files with validated math problems (questions, answers, metadata).
- **Flowcharts** – Visual problem‑solving flowcharts under `problem_flowchart/`. 

## Repository layout
```
.
├─ dataset/                    # Raw data
│   └─ class08‑hegp107/        # Grade 8 – Chapter 7 (Proportional Reasoning)
│       └─ validation/         # *.validation.json files
│
├─ problem_flowchart/          # Flowchart assets
│   ├─ images/                 # PNG / SVG diagrams
│   ├─ docs/                   # Documentation for flowcharts (README.md)
│   └─ scripts/                # Generators (PlantUML, Mermaid, etc.)
│
├─ resources/                  # Resources for building Problem Solving Agents
│   ├─ .json/                  # Prototype .json file for building .json file
│   └─ .pdf/                   # .pdf files used for reasoning building
│
├─ .gitignore                  # Files/folders to ignore in Git
├─ LICENSE                     # Open‑source license (MIT)
└─ README.md                   # *(this file)*
```

## Getting started
1. **Clone the repo**
   ```bash
   git clone https://github.com/aryansingh975/UI-for-Ainstein-Math.git
   cd UI-for-Ainstein-Math
   ```
2. **Install Antigravity** (if not already installed)
   ```bash
   curl -sSf https://install.antigravity.dev | bash
   ```
3. **Open the project in Antigravity**
   ```bash
   agy . 
   ```
## Contributing
- Follow the existing folder structure.
- Add new validation JSON files under `dataset/<grade‑>/<chapter>/validation/`.
- Add new flowcharts under `problem_flowchart/` and update the `problem_flowchart/docs/README.md` accordingly.
- Submit pull requests with clear titles and concise descriptions.

## License
This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---
*Happy coding and happy math!*