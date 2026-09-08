# Math Socratic AI

A question-first math tutor, built to mirror how NCERT's *Ganita Prakash*
textbook already teaches: instead of explaining a rule and then giving
practice problems, it asks the next small question that moves your own
thinking forward, and only confirms the rule once you've found it
yourself.

**Currently covers:** Grade 8, Chapter 7 — *Proportional Reasoning-1*
(ratios, proportion, simplest form, the Rule of Three, sharing a quantity
in a given ratio, unit conversion, and telling direct from inverse
relationships). Built to add more chapters without changing the app code.

## How it works

- `app/` — a static chat page (HTML/CSS/JS), deployable as-is on GitHub
  Pages. No build step, no framework.
- `prompts/socratic-system-prompt.md` — the tutoring behavior: hint
  ladders one step at a time, never state the answer first, diagnose
  wrong turns instead of just correcting them, ask the student to
  generalize the rule in their own words.
- `content/ch07-proportional-reasoning.json` — the chapter's concepts,
  worked examples, and every "Figure it Out" problem, each with an
  ordered hint ladder, a reference answer, and known misconceptions
  ("traps") tagged to the problems where they show up.

At runtime, the page loads both files and sends them to Claude as the
system prompt on every turn, so the tutor always has the full chapter
content and its own ground rules in context.

## Running it

1. Open `app/index.html` directly in a browser, or serve the repo root
   with any static file server (e.g. `python3 -m http.server`) — the app
   fetches `../content/...json` and `../prompts/...md` with relative
   paths, so it expects to be served from inside the repo, not standalone.
2. On first load it'll ask for a Claude API key
   (from [console.anthropic.com](https://console.anthropic.com)).
3. Pick a topic from the sidebar, or just start typing.

### Deploying to GitHub Pages

```
git init
git add .
git commit -m "Initial Socratic tutor for Ch. 7"
git branch -M main
git remote add origin https://github.com/<you>/math-socratic-ai.git
git push -u origin main
```

Then in the repo's Settings → Pages, deploy from the `main` branch. The
app will be reachable at `https://<you>.github.io/math-socratic-ai/app/`.

## ⚠️ About the API key — read this before sharing the link widely

This is a **static site with no backend**, so there is nowhere to hide a
secret key on the server — the key lives in the browser's local storage
and is sent straight to Anthropic's API from the visitor's own browser.
That's fine for personal use, or for a teacher/parent using their own
key on their own device. It is **not** safe to publish widely as-is,
because:

- Each visitor needs (and pays for) their own key.
- A key pasted into any browser is vulnerable if the device is shared
  or compromised.

If you want to hand this to a whole class without every student needing
an API key, the standard fix is a tiny serverless proxy (a Cloudflare
Worker, Vercel/Netlify function, or similar) that holds the real key
server-side and forwards requests — happy to help scaffold that as a
next step; it's a small addition to `app/script.js`'s `callClaude()`
function (point `API_URL` at your proxy instead of Anthropic directly).

## Extending to more chapters

1. Add `content/ch<NN>-<slug>.json` following the same schema as the
   Chapter 7 file (`concepts`, `workedExamples`, `problemSets`, `traps`).
2. Add a small chapter picker to `app/index.html`/`script.js` (currently
   hard-coded to load Chapter 7's file — this is the one place that'll
   need a few lines of code once a second chapter exists).
3. The system prompt in `prompts/socratic-system-prompt.md` is already
   chapter-agnostic in its *behavior* — only its references to "Chapter
   7" and the specific concept names need generalizing if you want one
   prompt to serve every chapter.

## License

MIT — see `LICENSE`. NCERT textbook content is used here only as
structured reference data (problem statements, not the original page
layout/artwork) for educational tutoring purposes.
