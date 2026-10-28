
// Universal solution-graph contract validator.
// Run: node test_universal_graph_structure.js
//
// This test intentionally fails while legacy graphs are being migrated. Its
// output is the checklist for Tasks 9-13 and the regression gate afterward.

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.join(__dirname, 'solution_graph');
const REQUIRED_ROOT_FIELDS = ['graph_meta', 'start_node', 'conclusion_node', 'nodes', 'edges'];
const REQUIRED_META_FIELDS = [
  'graph_id', 'problem_uuid', 'problem_text', 'navigation_label', 'problem_context',
  'graph_type', 'version', 'description', 'created', 'total_methods', 'total_nodes', 'total_edges'
];
const REQUIRED_EXTRACTIONS = ['given_extraction', 'goal_extraction'];
const REQUIRED_NODE_FIELDS = ['id', 'type', 'label', 'description', 'prompt', 'accept', 'hints'];
const ALLOWED_NODE_TYPES = new Set(['start', 'extraction', 'method', 'step', 'conclusion']);

function walk(directory, predicate) {
  const result = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...walk(fullPath, predicate));
    else if (predicate(entry.name)) result.push(fullPath);
  }
  return result;
}

function relative(filePath) {
  return path.relative(__dirname, filePath).split(path.sep).join('/');
}

function addIssue(issues, filePath, message) {
  if (!issues.has(filePath)) issues.set(filePath, []);
  issues.get(filePath).push(message);
}

function loadJavaScriptGraph(filePath, problemUuid) {
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(filePath, 'utf8'), context, { filename: filePath, timeout: 1000 });
  return context.window.SOLUTION_GRAPHS && context.window.SOLUTION_GRAPHS[problemUuid];
}

function reachesConclusion(graph, nodeIds) {
  const outgoing = new Map();
  for (const edge of graph.edges) {
    if (!outgoing.has(edge.from)) outgoing.set(edge.from, []);
    outgoing.get(edge.from).push(edge.to);
  }

  const visited = new Set([graph.start_node]);
  const queue = [graph.start_node];
  while (queue.length) {
    const nodeId = queue.shift();
    for (const next of outgoing.get(nodeId) || []) {
      if (!visited.has(next)) {
        visited.add(next);
        queue.push(next);
      }
    }
  }

  return {
    conclusionReachable: visited.has(graph.conclusion_node),
    unreachableNodeIds: [...nodeIds].filter(nodeId => !visited.has(nodeId))
  };
}

function isAcyclic(graph) {
  const outgoing = new Map();
  for (const edge of graph.edges) {
    if (!outgoing.has(edge.from)) outgoing.set(edge.from, []);
    outgoing.get(edge.from).push(edge.to);
  }

  const visiting = new Set();
  const visited = new Set();
  function visit(nodeId) {
    if (visiting.has(nodeId)) return false;
    if (visited.has(nodeId)) return true;
    visiting.add(nodeId);
    for (const next of outgoing.get(nodeId) || []) {
      if (!visit(next)) return false;
    }
    visiting.delete(nodeId);
    visited.add(nodeId);
    return true;
  }
  return graph.nodes.every(node => node && node.id && visit(node.id));
}

function validateGraph(jsonPath, issues) {
  const folder = path.dirname(jsonPath);
  const jsPath = path.join(folder, 'graph.js');
  const svgPath = path.join(folder, 'graph.svg');
  let graph;

  try {
    graph = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
  } catch (error) {
    addIssue(issues, jsonPath, `invalid JSON: ${error.message}`);
    return;
  }

  for (const field of REQUIRED_ROOT_FIELDS) {
    if (!(field in graph)) addIssue(issues, jsonPath, `missing root field: ${field}`);
  }

  if (!graph.graph_meta || typeof graph.graph_meta !== 'object' || Array.isArray(graph.graph_meta)) {
    addIssue(issues, jsonPath, 'graph_meta must be an object');
  } else {
    for (const field of REQUIRED_META_FIELDS) {
      if (!(field in graph.graph_meta)) addIssue(issues, jsonPath, `missing graph_meta field: ${field}`);
    }
    if (graph.graph_meta.graph_type && graph.graph_meta.graph_type !== 'directed_acyclic_graph') {
      addIssue(issues, jsonPath, 'graph_meta.graph_type must be "directed_acyclic_graph"');
    }
    if (graph.graph_meta.problem_context && (typeof graph.graph_meta.problem_context !== 'object' || Array.isArray(graph.graph_meta.problem_context))) {
      addIssue(issues, jsonPath, 'graph_meta.problem_context must be an object');
    }
  }

  if (!Array.isArray(graph.nodes)) {
    addIssue(issues, jsonPath, 'nodes must be an array');
    return;
  }
  if (!Array.isArray(graph.edges)) {
    addIssue(issues, jsonPath, 'edges must be an array');
    return;
  }

  for (const [index, node] of graph.nodes.entries()) {
    if (!node || typeof node !== 'object' || Array.isArray(node)) {
      addIssue(issues, jsonPath, `node ${index} must be an object`);
      continue;
    }
    for (const field of REQUIRED_NODE_FIELDS) {
      if (!(field in node)) addIssue(issues, jsonPath, `node ${node.id || index} missing field: ${field}`);
    }
    if (node.type && !ALLOWED_NODE_TYPES.has(node.type)) {
      addIssue(issues, jsonPath, `node ${node.id || index} has unsupported type: ${node.type}`);
    }
    for (const field of ['label', 'description', 'prompt']) {
      if (field in node && (typeof node[field] !== 'string' || !node[field].trim())) {
        addIssue(issues, jsonPath, `node ${node.id || index} field ${field} must be a non-empty string`);
      }
    }
    for (const field of ['accept', 'hints']) {
      if (field in node && !Array.isArray(node[field])) {
        addIssue(issues, jsonPath, `node ${node.id || index} field ${field} must be an array`);
      }
    }
  }

  const nodeIds = graph.nodes.map(node => node && node.id).filter(Boolean);
  const nodeMap = new Map(graph.nodes.filter(node => node && node.id).map(node => [node.id, node]));
  if (nodeIds.length !== graph.nodes.length) addIssue(issues, jsonPath, 'every node must have an id');
  if (new Set(nodeIds).size !== nodeIds.length) addIssue(issues, jsonPath, 'node ids must be unique');

  const startNode = nodeMap.get(graph.start_node);
  if (graph.start_node !== 'start') addIssue(issues, jsonPath, 'start_node must be "start"');
  if (!startNode || startNode.type !== 'start') addIssue(issues, jsonPath, 'start_node must reference a node with type "start"');
  const conclusionNode = nodeMap.get(graph.conclusion_node);
  if (graph.conclusion_node !== 'conclusion') addIssue(issues, jsonPath, 'conclusion_node must be "conclusion"');
  if (!conclusionNode || conclusionNode.type !== 'conclusion') {
    addIssue(issues, jsonPath, 'conclusion_node must reference a node with type "conclusion"');
  }

  for (const extractionId of REQUIRED_EXTRACTIONS) {
    const extraction = nodeMap.get(extractionId);
    if (!extraction) {
      addIssue(issues, jsonPath, `missing required extraction node: ${extractionId}`);
      continue;
    }
    if (extraction.type !== 'extraction') addIssue(issues, jsonPath, `${extractionId} must have type "extraction"`);
    if (typeof extraction.optional !== 'boolean') {
      addIssue(issues, jsonPath, `${extractionId} must declare boolean optional`);
    }
  }

  const LEGACY_EXTRACTION_IDS = ['extraction', 'node_givens', 'node_goal'];
  for (const legacyId of LEGACY_EXTRACTION_IDS) {
    if (nodeMap.has(legacyId)) {
      addIssue(issues, jsonPath, `legacy extraction node "${legacyId}" must be removed; use given_extraction/goal_extraction only`);
    }
  }

  const hasEdge = (from, to) => graph.edges.some(edge => edge && edge.from === from && edge.to === to);
  const guidedMethodIds = graph.edges
    .filter(edge => edge && edge.from === 'goal_extraction')
    .map(edge => nodeMap.get(edge.to))
    .filter(node => node && node.type === 'method')
    .map(node => node.id);
  const directMethodIds = graph.edges
    .filter(edge => edge && edge.from === 'start')
    .map(edge => nodeMap.get(edge.to))
    .filter(node => node && node.type === 'method')
    .map(node => node.id);
  const givenExtraction = nodeMap.get('given_extraction');
  const goalExtraction = nodeMap.get('goal_extraction');
  if (givenExtraction && goalExtraction && typeof givenExtraction.optional === 'boolean' && typeof goalExtraction.optional === 'boolean') {
    if (givenExtraction.optional !== goalExtraction.optional) {
      addIssue(issues, jsonPath, 'given_extraction and goal_extraction must use the same optional value');
    }
    if (!hasEdge('start', 'given_extraction')) addIssue(issues, jsonPath, 'missing extraction edge: start -> given_extraction');
    if (!hasEdge('given_extraction', 'goal_extraction')) addIssue(issues, jsonPath, 'missing extraction edge: given_extraction -> goal_extraction');
    if (guidedMethodIds.length === 0) addIssue(issues, jsonPath, 'goal_extraction must connect to at least one method node');

    if (!givenExtraction.optional && directMethodIds.length > 0) {
      addIssue(issues, jsonPath, 'required extraction graph must not contain a direct start -> method bypass');
    }
    if (givenExtraction.optional) {
      for (const methodId of guidedMethodIds) {
        if (!directMethodIds.includes(methodId)) {
          addIssue(issues, jsonPath, `optional extraction graph is missing bypass edge: start -> ${methodId}`);
        }
      }
    }
  }

  for (const [index, edge] of graph.edges.entries()) {
    if (!edge || typeof edge.from !== 'string' || typeof edge.to !== 'string') {
      addIssue(issues, jsonPath, `edge ${index} must include string from and to ids`);
      continue;
    }
    if (!nodeMap.has(edge.from)) addIssue(issues, jsonPath, `edge ${index} references unknown source: ${edge.from}`);
    if (!nodeMap.has(edge.to)) addIssue(issues, jsonPath, `edge ${index} references unknown target: ${edge.to}`);
  }

  if (graph.graph_meta && typeof graph.graph_meta === 'object') {
    if (graph.graph_meta.total_nodes !== graph.nodes.length) {
      addIssue(issues, jsonPath, `graph_meta.total_nodes is ${graph.graph_meta.total_nodes}; expected ${graph.nodes.length}`);
    }
    if (graph.graph_meta.total_edges !== graph.edges.length) {
      addIssue(issues, jsonPath, `graph_meta.total_edges is ${graph.graph_meta.total_edges}; expected ${graph.edges.length}`);
    }
    const methodCount = graph.nodes.filter(node => node && node.type === 'method').length;
    if (graph.graph_meta.total_methods !== methodCount) {
      addIssue(issues, jsonPath, `graph_meta.total_methods is ${graph.graph_meta.total_methods}; expected ${methodCount}`);
    }
  }

  if (nodeMap.has(graph.start_node) && nodeMap.has(graph.conclusion_node)) {
    const reachability = reachesConclusion(graph, nodeMap.keys());
    if (!reachability.conclusionReachable) addIssue(issues, jsonPath, 'conclusion is not reachable from start_node');
    if (reachability.unreachableNodeIds.length) {
      addIssue(issues, jsonPath, `unreachable nodes: ${reachability.unreachableNodeIds.join(', ')}`);
    }
  }
  if (!isAcyclic(graph)) addIssue(issues, jsonPath, 'graph contains a cycle');

  if (!fs.existsSync(svgPath)) addIssue(issues, jsonPath, 'missing co-located graph.svg');

  if (!fs.existsSync(jsPath)) {
    addIssue(issues, jsonPath, 'missing co-located graph.js');
  } else if (!graph.graph_meta || typeof graph.graph_meta.problem_uuid !== 'string') {
    addIssue(issues, jsonPath, 'cannot compare graph.js without graph_meta.problem_uuid');
  } else {
    try {
      const jsGraph = loadJavaScriptGraph(jsPath, graph.graph_meta.problem_uuid);
      if (!jsGraph) addIssue(issues, jsonPath, `graph.js does not register ${graph.graph_meta.problem_uuid}`);
      // The graph.js object is created in a VM realm, so comparing its object
      // prototype with JSON.parse output would produce false mismatches. JSON
      // serialization compares the portable graph data instead.
      else if (JSON.stringify(graph) !== JSON.stringify(jsGraph)) addIssue(issues, jsonPath, 'graph.js data differs from graph.json');
    } catch (error) {
      addIssue(issues, jsonPath, `graph.js cannot load: ${error.message}`);
    }
  }
}

const issues = new Map();
const graphJsonPaths = walk(ROOT, name => name === 'graph.json');
const graphSvgPaths = walk(ROOT, name => name === 'graph.svg');

if (graphJsonPaths.length === 0) addIssue(issues, ROOT, 'no graph.json files found');
for (const jsonPath of graphJsonPaths) validateGraph(jsonPath, issues);

for (const svgPath of graphSvgPaths) {
  const folder = path.dirname(svgPath);
  if (!fs.existsSync(path.join(folder, 'graph.json')) || !fs.existsSync(path.join(folder, 'graph.js'))) {
    addIssue(issues, svgPath, 'graph.svg must be co-located with graph.json and graph.js');
  }
}

const issueCount = [...issues.values()].reduce((total, messages) => total + messages.length, 0);
console.log(`=== UNIVERSAL GRAPH VALIDATION (${graphJsonPaths.length} graphs) ===`);

if (issueCount === 0) {
  console.log('PASS | all solution graphs satisfy the universal contract');
  process.exit(0);
}

for (const [filePath, messages] of [...issues.entries()].sort(([left], [right]) => left.localeCompare(right))) {
  console.log(`\nFAIL | ${relative(filePath)}`);
  for (const message of messages) console.log(`  - ${message}`);
}

console.log(`\n=== RESULTS: ${issueCount} violation(s) across ${issues.size} file(s) ===`);
process.exit(1);
