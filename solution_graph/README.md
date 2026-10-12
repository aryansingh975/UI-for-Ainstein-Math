# Solution Graphs

Graphs are organized by textbook chapter so the project stays easy to browse and maintain.

```text
solution_graph/
  README.md
  chapter-7/
    ratio-proportion/
      g08-hegp107-ex001/
        graph.js
        graph.json
        graph.svg
      g08-hegp107-ex002-lemonade/
        graph.js
        graph.json
        graph.svg
      g08-hegp107-ex002-ratio/
        graph.js
        graph.json
        graph.svg
      g08-hegp107-ex003/
        graph.js
        graph.json
        graph.svg
      ...
      g08-hegp107-ex010/
        graph.js
        graph.json
        graph.svg
  chapter-10/
    quadratic-equation/
      g10-quad-ex001/
        graph.js
        graph.json
        graph.svg
```

Folder names identify the question; `graph_meta.problem_uuid` is its stable ID. Keep IDs unique, especially when one textbook example has multiple questions. The lemonade question retains `g08-hegp107-ex002`; the 6:8 ratio question uses `g08-hegp107-ex002-ratio`.

The `.json` file is the portable graph data, `.js` makes a graph available to the browser, and `.svg` is its visual representation. When adding or changing a graph, keep the same content and metadata in all three files. Update any app or test paths that load a graph after moving it.
