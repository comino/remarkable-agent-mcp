# Changelog

Earlier releases were tagged `marginalia-X.Y.Z`; plain `vX.Y.Z` tags come from
the upstream remarkable-mcp history. Newest first.

## 1.3.0 — Unreleased

- Rename the distribution and primary commands to `remarkable-agent-mcp`;
  preserve MCP tools, Python imports, state paths and compatibility commands.
- Remove the TRMNL display integration. All reMarkable workflows remain.
- Replace personal-looking examples with synthetic content and remove inherited
  notebook screenshots. Add privacy, dependency-license and release guidance.
- Apply local-file access restrictions to core PDF/EPUB uploads in every transport.
- Persist reply delivery separately from task completion, with stable document
  IDs and retries that do not rerun completed requests or overwrite reply ink.
- Trigger autopilot for new ink in an existing inbox, persist cooldown/progress
  across restarts, and retry work that an agent did not acknowledge.
- Restrict workflow/cache permissions and stop echoing invalid token content.
- Reuse geometric measurements while classifying dense inbox and sketch pages;
  retain the existing recognition rules and performance budgets.
- Scan Git history and built artifacts in CI and restrict distribution contents.

- **Sketch:** a single box counts (the sketch tool and live watch no longer
  need three shapes or an edge before they report anything).
- **Sketch, from a live test on the tablet:**
  - tall letters closing a narrow outline inside a line of writing are text, not a box;
  - a separate arrowhead drawn *ahead* of the line's end makes the edge directed;
  - arrows can point at notes: each written line is a note with an id (`t1`, `t2`, …), and
    Mermaid draws pointed-at notes as flag nodes;
  - a label hanging over a box's edge (a closing "?") belongs to the box;
  - joined-up cursive words are writing, not dropped connectors.
- **Docs:** the tablet syncs when a document is closed or a page is left, not while the pen
  moves; live watch docs and tool descriptions say so.
- **README:** animated hero and a gallery generated from the real engines
  (`docs/assets/make_gallery.py`).

## 1.2.0 — 2026-09-26

- The optional display integration was separated from the autopilot. It is
  removed in 1.3.0.
- **Autopilot** only starts the configured agent and exits when no command is set.
- **Code layout:** modules were organized into `core/`, `transports/`,
  `documents/` and workflow groups.

## 1.1.2 / 1.1.1 — 2026-09-26

- **Autopilot:** SIGTERM (systemd stop/restart) is a clean shutdown: the run loop is cancelled
  from inside, the live watcher closes its socket (bounded), exit code 0.

## 1.1.0 — 2026-09-26

- **Security:** tool parameters that reach local files or the network are vetted: sensitive
  locations refused, suffix and size caps, optional `REMARKABLE_ALLOWED_ROOTS`, SSRF guard
  including tailnet addresses, redirects re-checked hop by hop.
- **Ink classifiers hardened by adversarial testing:** split, wavy, short and overshooting
  strikes and underlines; circles drawn as arcs; label circling, off-centre and crossed ticks
  on forms; multi-pull and wavy cancels and dividers in the inbox; sketch shapes fitted rather
  than corner-counted, with filled, in-stroke and one-barb arrowheads.
- **Tests:** MCP end-to-end, metamorphic invariants, adversarial regression tests, docs
  consistency; about 1080 offline tests on Python 3.10–3.12.
- **Performance:** dense pages (2000 strokes) analyse about 2.5× faster.

## 1.0.0 — 2026-09-26

The first release under the **Marginalia** name: pen review with source lines, code review to GitHub
comments, LaTeX review via SyncTeX, forms / questions / triage sheets, clarify on paper, the
Agent Inbox, sketches → Mermaid and SVG, tables, wireframes and math, the reading queue, the
ink digest, live watch and the autopilot. Builds on
[remarkable-mcp](https://github.com/SamMorrowDrums/remarkable-mcp) by Sam Morrow.
