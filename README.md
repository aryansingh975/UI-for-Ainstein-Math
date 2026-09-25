
# Ainstein Math

Ainstein Math is an interactive, step-by-step math tutor for Grade 8 NCERT
ratio and proportion problems. It provides two ways to practice:

- A browser-based tutor with a visual interface, free-form math input, LaTeX
  preview, hints, and solution tracking.
- A Python terminal tutor that validates one student step at a time using the
  same problem dataset.

The current example asks whether the ratios `3 : 4` and `72 : 96` are
proportional. The tutor accepts several valid solution methods, identifies
incorrect or irrelevant steps, and guides the student toward a conclusion.

## Features

- Free-form student input for arithmetic and ratio steps.
- Method detection for simplification, cross multiplication, decimals,
  fractions, scaling, and related approaches.
- Immediate feedback for correct, incorrect, irrelevant, or incomplete steps.
- Solution graph data shared by the browser tutor and its tests.
- Python validation engine backed by a structured JSON dataset.
- Automated Node.js tests for parsing, matching, validation, and dialogue flow.

## Project Structure

```text
.
├── index.html                         Browser tutor page
├── styles.css                         Browser tutor styles
├── app.js                             Browser UI and feedback logic
├── tutor-engine.js                    JavaScript tutor and validation engine
├── ainstein_math/
│   ├── terminal_tutor.py              Interactive Python terminal tutor
│   ├── verification_engine.py         Python validation engine
│   ├── reusable_functions.py          Shared math helpers
│   ├── tutor_hints.py                  Tutor hint definitions
│   └── verification_engine_algorithm.md
├── dataset/                            Validation datasets
├── solution_graph/                     Solution graph JSON, JS, SVG, and notes
├── problem_flowchart/                  Problem-solving flowchart documentation
├── resource/                           Supporting learning resources
├── test_tutor_engine.js                JavaScript tutor tests
├── test_solution_graph.js              Solution graph matching tests
└── README.md                           Project documentation
```

## Requirements

- Python 3.9 or newer for the terminal tutor.
- Node.js 16 or newer for the JavaScript tests.
- A modern web browser for the browser tutor.

The browser tutor has no npm dependencies. The Python tutor uses only the
standard library.

## Run the Browser Tutor

From the project folder, start a local web server:

```powershell
python -m http.server 8000
```

Open <http://localhost:8000> in a browser and use the tutor interface.

Stop the server with `Ctrl+C`.

## Run the Terminal Tutor

From the project folder, run:

```powershell
python .\ainstein_math\terminal_tutor.py
```

Enter one math step at a time at the `You:` prompt. Type `q`, `quit`, or
`exit` to end the session.

## Run the Tests

Run the JavaScript tutor and solution graph tests from the project folder:

```powershell
node .\test_tutor_engine.js
node .\test_solution_graph.js
```

Compile-check the Python tutor with:

```powershell
python -m py_compile .\ainstein_math\terminal_tutor.py
```

## GitHub Repository

Project repository:

<https://github.com/aryansingh975/UI-for-Ainstein-Math>

To clone the project:

```powershell
git clone https://github.com/aryansingh975/UI-for-Ainstein-Math.git
cd UI-for-Ainstein-Math
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
details.