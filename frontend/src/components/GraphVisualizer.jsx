import React, { useState, useMemo } from 'react';

function cleanLabel(label) {
  if (!label) return '';
  return label.replace(/^Method\s*\d+\s*:\s*/i, '').trim();
}

export default function GraphVisualizer({ graph, session, stepResult }) {
  const [isOpen, setIsOpen] = useState(true);
  const [viewMode, setViewMode] = useState('path'); // 'path' or 'full'

  const isCompleted = session?.completed || false;
  const activeMethodId = session?.method_id;
  const trail = session?.trail || [];
  const jumpedNodeId = stepResult?.verdict === 'STEP_JUMP' ? stepResult?.jumped_node_id : null;

  // The node we just typed and verified (or Start if fresh session, Conclusion if solved)
  const currentVerifiedNodeId = useMemo(() => {
    if (isCompleted) return graph?.conclusion_node;
    if (trail && trail.length > 0) {
      return trail[trail.length - 1].nodeId;
    }
    return graph?.start_node;
  }, [trail, isCompleted, graph]);

  // The next expected node where input is awaited
  const nextExpectedNodeId = useMemo(() => {
    if (isCompleted) return null;
    return session?.active_node_id || session?.current_node_id;
  }, [session, isCompleted]);

  // Set of visited node IDs from the session trail
  const visitedNodeIds = useMemo(() => {
    const set = new Set();
    if (trail.length > 0 || isCompleted) {
      set.add(graph?.start_node);
    }
    trail.forEach((t) => {
      if (t.nodeId) set.add(t.nodeId);
    });
    return set;
  }, [trail, isCompleted, graph?.start_node]);

  const nodeMap = useMemo(() => {
    if (!graph || !graph.nodes) return {};
    const map = {};
    graph.nodes.forEach((n) => {
      map[n.id] = n;
    });
    return map;
  }, [graph]);

  // Method nodes in this graph
  const methodNodes = useMemo(() => {
    if (!graph || !graph.nodes) return [];
    return graph.nodes.filter((n) => n.type === 'method');
  }, [graph]);

  // Active path chain
  const activePathNodes = useMemo(() => {
    if (!graph || !graph.nodes) return [];

    const nodes = [];
    const seen = new Set();

    // 1. Extractions if present
    const givenExt = nodeMap['given_extraction'];
    const goalExt = nodeMap['goal_extraction'];
    if (givenExt && givenExt.optional === false) {
      nodes.push(givenExt);
      seen.add(givenExt.id);
    }
    if (goalExt && goalExt.optional === false) {
      nodes.push(goalExt);
      seen.add(goalExt.id);
    }

    // 2. Start node
    const startNode = nodeMap[graph.start_node] || { id: 'start', label: 'Start' };
    if (!seen.has(startNode.id)) {
      nodes.push(startNode);
      seen.add(startNode.id);
    }

    // 3. Method nodes sequence
    const effectiveMethodId = activeMethodId || (jumpedNodeId ? (stepResult?.method_id || methodNodes.find((m) => jumpedNodeId.startsWith(m.id.slice(0, 2)))?.id) : null);

    if (effectiveMethodId) {
      // Find method entry
      const methodNode = methodNodes.find(
        (m) => m.id === effectiveMethodId || m.id.startsWith(effectiveMethodId)
      );
      if (methodNode && !seen.has(methodNode.id)) {
        nodes.push(methodNode);
        seen.add(methodNode.id);
      }

      // Trace edges from methodNode to conclusion
      let curr = methodNode?.id;
      let depth = 0;
      while (curr && depth < 10) {
        depth++;
        const edge = (graph.edges || []).find((e) => e.from === curr);
        if (!edge) break;
        const nextNode = nodeMap[edge.to];
        if (!nextNode || seen.has(nextNode.id)) break;
        if (nextNode.id === graph.conclusion_node) {
          break; // We will append conclusion at the end
        }
        nodes.push(nextNode);
        seen.add(nextNode.id);
        curr = nextNode.id;
      }
    } else {
      // If no method locked yet, show placeholder or first step of trail
      if (trail.length > 0) {
        trail.forEach((t) => {
          const n = nodeMap[t.nodeId];
          if (n && !seen.has(n.id) && n.id !== graph.conclusion_node) {
            nodes.push(n);
            seen.add(n.id);
          }
        });
      }
    }

    // If jumped node is still not in the path (e.g. shared node), insert it before conclusion
    if (jumpedNodeId && nodeMap[jumpedNodeId] && !seen.has(jumpedNodeId)) {
      nodes.push(nodeMap[jumpedNodeId]);
      seen.add(jumpedNodeId);
    }

    // 4. Conclusion node
    const conclNode = nodeMap[graph.conclusion_node] || { id: 'conclusion', label: 'Conclusion' };
    if (!seen.has(conclNode.id)) {
      nodes.push(conclNode);
      seen.add(conclNode.id);
    }

    return nodes;
  }, [graph, nodeMap, methodNodes, activeMethodId, trail, jumpedNodeId, stepResult]);

  if (!graph || !graph.nodes) return null;

  const hereNode = nodeMap[currentVerifiedNodeId] || { label: 'Start' };

  return (
    <section className="graph-visualizer-container" aria-label="Graph Traversal Monitor">
      <header className="gv-header">
        <div className="gv-header-left">
          <span className="gv-title-icon">🗺️</span>
          <div>
            <h3 className="gv-title">Graph Traversal Monitor</h3>
            <span className="gv-subtitle">
              {isCompleted ? (
                <span className="gv-pointer-badge gv-pointer-completed">🏆 Solved! At Conclusion</span>
              ) : jumpedNodeId ? (
                <span className="gv-pointer-badge gv-pointer-jumped">
                  ⚠️ Step Jump: Pointer at <strong>{cleanLabel(hereNode.label)}</strong> (Leaped to {cleanLabel(nodeMap[jumpedNodeId]?.label)})
                </span>
              ) : (
                <span className="gv-pointer-badge">
                  📍 YOU ARE HERE: <strong>{cleanLabel(hereNode.label)}</strong>
                  {activeMethodId ? ` (${cleanLabel(session?.method_label || activeMethodId)})` : ''}
                </span>
              )}
            </span>
          </div>
        </div>

        <div className="gv-header-controls">
          <div className="gv-view-tabs">
            <button
              type="button"
              className={`gv-tab-btn ${viewMode === 'path' ? 'active' : ''}`}
              onClick={() => setViewMode('path')}
            >
              📍 Active Path
            </button>
            <button
              type="button"
              className={`gv-tab-btn ${viewMode === 'full' ? 'active' : ''}`}
              onClick={() => setViewMode('full')}
            >
              🕸️ All Methods ({methodNodes.length})
            </button>
          </div>

          <button
            type="button"
            className="gv-toggle-btn"
            onClick={() => setIsOpen((prev) => !prev)}
            title={isOpen ? 'Collapse Graph Monitor' : 'Expand Graph Monitor'}
          >
            {isOpen ? '▲ Hide' : '▼ Show'}
          </button>
        </div>
      </header>

      {isOpen && (
        <div className="gv-content">
          {viewMode === 'path' ? (
            /* --- 1. ACTIVE PATH STEPPER VIEW --- */
            <div className="gv-path-view">
              <div className="gv-stepper">
                {activePathNodes.map((node, idx) => {
                  const isHere = node.id === currentVerifiedNodeId;
                  const isNext = !isHere && !isCompleted && node.id === nextExpectedNodeId;
                  const isVisited = visitedNodeIds.has(node.id) && !isHere;
                  const isJumped = jumpedNodeId === node.id;

                  let cardStateClass = 'gv-node-upcoming';
                  let icon = '⚪';
                  let statusText = 'Upcoming';

                  if (isHere) {
                    cardStateClass = 'gv-node-here';
                    icon = isCompleted ? '🏆' : '📍';
                    statusText = isCompleted ? 'Completed' : 'YOU ARE HERE';
                  } else if (node.type === 'method') {
                    cardStateClass = 'gv-node-method-selected';
                    icon = '✓';
                    statusText = 'Method Selected';
                  } else if (isVisited) {
                    cardStateClass = 'gv-node-visited';
                    icon = '✓';
                    statusText = 'Visited';
                  } else if (isNext) {
                    cardStateClass = 'gv-node-next';
                    icon = '⚪';
                    statusText = 'Next Step';
                  } else if (isJumped) {
                    cardStateClass = 'gv-node-jumped';
                    icon = '⚠️';
                    statusText = 'Leaped Ahead';
                  }

                  const trailEntry = trail.find((t) => t.nodeId === node.id);

                  return (
                    <React.Fragment key={node.id}>
                      <div className={`gv-node-card ${cardStateClass}`}>
                        <div className="gv-node-top">
                          <span className="gv-node-badge">{icon} {statusText}</span>
                          <span className="gv-node-type">{node.type}</span>
                        </div>
                        <div className="gv-node-label">{cleanLabel(node.label)}</div>
                        {trailEntry?.input && (
                          <div className="gv-node-input">"{trailEntry.input}"</div>
                        )}
                        {isNext && !isCompleted && node.prompt && (
                          <div className="gv-node-prompt">{node.prompt}</div>
                        )}
                        {isHere && !trailEntry?.input && !isCompleted && node.prompt && (
                          <div className="gv-node-prompt">{node.prompt}</div>
                        )}
                      </div>

                      {idx < activePathNodes.length - 1 && (
                        <div className={`gv-arrow ${isVisited || isHere || node.type === 'method' ? 'gv-arrow-active' : ''}`}>
                          →
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>

              {!activeMethodId && !isCompleted && methodNodes.length > 0 && (
                <div className="gv-method-chips-note">
                  <span className="gv-note-icon">💡</span>
                  <span>Any valid method can be used. The tutor will lock into the branch you start:</span>
                  <div className="gv-chips">
                    {methodNodes.map((m) => (
                      <span key={m.id} className="gv-chip">
                        {cleanLabel(m.label)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* --- 2. FULL MULTI-BRANCH DAG VIEW --- */
            <div className="gv-full-view">
              <div className="gv-full-graph">
                {/* Start node */}
                <div className="gv-full-col gv-start-col">
                  <div
                    className={`gv-node-card ${
                      currentVerifiedNodeId === graph.start_node && !isCompleted
                        ? 'gv-node-here'
                        : 'gv-node-visited'
                    }`}
                  >
                    <div className="gv-node-top">
                      <span className="gv-node-badge">
                        {currentVerifiedNodeId === graph.start_node && !isCompleted ? '📍 YOU ARE HERE' : '✓ START'}
                      </span>
                    </div>
                    <div className="gv-node-label">Start Problem</div>
                  </div>
                </div>

                <div className="gv-full-arrow-col">
                  <span>↳</span>
                </div>

                {/* Methods Branches */}
                <div className="gv-full-col gv-methods-col">
                  {methodNodes.map((mNode) => {
                    const isThisActiveMethod =
                      activeMethodId && (mNode.id === activeMethodId || mNode.id.startsWith(activeMethodId));
                    const isMethodVisited = visitedNodeIds.has(mNode.id);

                    // Collect steps belonging to this method
                    const stepsOfMethod = (graph.nodes || []).filter(
                      (n) => n.type === 'step' && n.id.startsWith(mNode.id.slice(0, 3))
                    );

                    return (
                      <div
                        key={mNode.id}
                        className={`gv-method-branch ${isThisActiveMethod ? 'gv-branch-active' : ''}`}
                      >
                        <div className="gv-branch-header">
                          <span className="gv-branch-title">{cleanLabel(mNode.label)}</span>
                          {isThisActiveMethod && <span className="gv-branch-tag">ACTIVE BRANCH</span>}
                        </div>

                        <div className="gv-branch-steps">
                          {stepsOfMethod.map((sNode) => {
                            const isStepHere = currentVerifiedNodeId === sNode.id;
                            const isStepVisited = visitedNodeIds.has(sNode.id) && !isStepHere;
                            const isStepNext = !isStepHere && sNode.id === nextExpectedNodeId;
                            const isStepJumped = jumpedNodeId === sNode.id;

                            let pillClass = '';
                            let prefix = '';

                            if (isStepHere) {
                              pillClass = 'gv-pill-here';
                              prefix = '📍 ';
                            } else if (isStepVisited) {
                              pillClass = 'gv-pill-visited';
                              prefix = '✓ ';
                            } else if (isStepNext) {
                              pillClass = 'gv-pill-next';
                              prefix = '⚪ ';
                            } else if (isStepJumped) {
                              pillClass = 'gv-pill-jumped';
                              prefix = '⚠️ ';
                            }

                            return (
                              <span
                                key={sNode.id}
                                className={`gv-step-pill ${pillClass}`}
                                title={sNode.prompt || sNode.label}
                              >
                                {prefix}
                                {cleanLabel(sNode.label)}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="gv-full-arrow-col">
                  <span>→</span>
                </div>

                {/* Conclusion node */}
                <div className="gv-full-col gv-concl-col">
                  <div className={`gv-node-card ${isCompleted ? 'gv-node-here' : 'gv-node-upcoming'}`}>
                    <div className="gv-node-top">
                      <span className="gv-node-badge">{isCompleted ? '🏆 SOLVED' : '🏁 GOAL'}</span>
                    </div>
                    <div className="gv-node-label">Final Conclusion</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

