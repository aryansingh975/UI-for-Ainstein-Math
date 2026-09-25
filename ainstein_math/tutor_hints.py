"""Supportive hint content and stuck-reply detection for the verification engine.

Everything in this module is original to the ainstein_math package. The
progressive-hint *idea* (gentle nudge -> specific pointer -> worked example)
is shared with the rest of the repository, but no hint text is copied from
any solution_graph asset or dataset file.

Hint ladders per node:
  Level 1  - a gentle nudge that re-frames the question
  Level 2  - a specific pointer toward the needed quantity or operation
  Level 3  - a fully worked example of the step (reveal)
"""

import re

# --- Stuck ("I don't know") detection ----------------------------------------
# Only digit-free messages are treated as stuck, so replies that already
# contain math (e.g. "i don't know, is it 3:4?") are still evaluated by the
# node handler instead of being swallowed by the hint ladder.
_STUCK_PATTERNS = (
    r"\bidk\b",
    r"\bdunno\b",
    r"\bno idea\b",
    r"\bdon'?t know\b",
    r"\bdo not know\b",
    r"\bdon'?t understand\b",
    r"\bdo not understand\b",
    r"\bdon'?t get (it|this)\b",
    r"\bdo not get (it|this)\b",
    r"\bconfused\b",
    r"\bi'?m stuck\b",
    r"\bi am stuck\b",
    r"^\s*stuck\s*$",
    r"^\s*help\s*$",
    r"\bhelp me\b",
    r"\bneed help\b",
    r"\bplease help\b",
    r"\bcan you help\b",
    r"\bcan u help\b",
    r"\bteach me\b",
    r"\bhow do i (do|start|solve|begin)\b",
    r"\bwhat should i do\b",
    r"\bwhat do i do\b",
    r"\bgive up\b",
    r"\bcan'?t do (this|it)\b",
    r"\bcannot do (this|it)\b",
    r"^\s*(a\s+)?hint( please)?\s*$",
    r"\bgive me a hint\b",
)

# --- Reveal policy -------------------------------------------------------------
# Nodes whose level-3 hint fully demonstrates the step. When reached, the
# engine records the node as *assisted* and moves on so a struggling student
# is never permanently blocked. Conclusion nodes are deliberately excluded:
# there we show the reasoning but let the student type the final answer.
REVEAL_COMPLETES_NODES = frozenset({
    "node_001",
    "node_002",
    "node_003",
    "node_crs-mul_001",
    "node_sim_001",
    "node_scale_001",
})

# Method chosen on the student's behalf when node_003 is revealed.
METHOD_REVEAL = "simplification"

MAX_HINT_LEVEL = 3

# --- Original hint ladders (nudge -> pointer -> worked example) ----------------
NODE_HINTS = {
    "node_001": [
        "A 'given' is just information the problem hands you. Look back at the "
        "problem statement at the top and tell me what you find there.",
        "The problem hands you two ratios written with colons - one pair of "
        "small numbers and one pair of larger numbers. Try writing each pair "
        "as 'number : number'.",
        "Here they are: the first ratio is 3:4 and the second ratio is 72:96. "
        "You can type both at once, like this: '3:4 and 72:96'.",
    ],
    "node_002": [
        "Look again at the question at the top of the problem. It is asking "
        "you to decide something about the two ratios - what is that decision?",
        "The problem wants to know whether the two ratios describe the same "
        "relationship. The math word for that idea starts with 'pro...'.",
        "The goal is to decide whether the ratios are proportional (equal "
        "ratios). Something like 'to check if the ratios are proportional' works.",
    ],
    "node_003": [
        "There are several standard ways to compare two ratios. Which ones do "
        "you remember from class?",
        "For example: dividing 72 and 96 by their largest common factor, "
        "multiplying diagonally (3 with 96 and 4 with 72), or scaling 3:4 up "
        "with one multiplier.",
        "Let's choose one: type 'simplification' and we will go step by step.",
    ],