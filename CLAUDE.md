# CLAUDE.md — reMarkable Agent MCP

MCP server that turns a reMarkable tablet into an agent front end. Fork of
SamMorrowDrums/remarkable-mcp (core: transports, sync client, extraction) plus
a workflow layer (`remarkable_mcp/workflows/`). README.md is the overview; `docs/workflows.md`
documents every workflow tool; `docs/core.md` the core tools.

## Working here

- `uv sync --all-extras && uv run pytest -q` — ~1080 offline tests, ~60 s. Gate
  commits on pytest's exit code (not on `| tail`).
- `uv run ruff check . && uv run ruff format --check .` — line length 100;
  long fixtures are allowed in tests and the gallery generator.
- Python ≥ 3.10 (CI matrix 3.10–3.12): no 3.12-only syntax (nested same-quote
  f-strings etc.).
- The package import name stays `remarkable_mcp` and the MCP server/tool names
  stay `remarkable` / `remarkable_*` on purpose: clients key tool names on them.
  The distribution is `remarkable-agent-mcp` (console scripts `remarkable-agent-mcp`,
  `remarkable-agent-mcp-autopilot`, plus the old `remarkable-*` aliases).

## Layout

- `remarkable_mcp/server.py` assembles the server; `cli.py` is the entry point.
- `core/` the core tools (docs/core.md), resources and prompts; `transports/`
  cloud, SSH, USB web, local cache; `documents/` extraction and exports.
- `workflows/` one subpackage per workflow (`ink/`, `review/`, `forms/`,
  `inbox/`, `structure/`, `reading/`, `live/`), engine next to its `*tools`
  module; `workflows/tools.py` registers them all.

## Facts not obvious from the code

- **Coordinates:** ink is mapped to PDF points with `x = rm_x*ppu + page_w/2`,
  `y = rm_y*ppu` (`workflows/ink/page.py`), `ppu` from the page's SceneInfo grid. Verified on
  real device markup. PyMuPDF word boxes span ascender→descender: use the
  estimated baseline, not box edges (`ink/marks.py: _horizontal_target`). PyMuPDF
  splits one visual line into several "blocks" — group words geometrically.
- **Sync API rate limit:** ~30 requests per short window per account, shared by
  every client. Metadata refreshes must be coalesced (`live/watcher.py: Watcher`); a bug
  that refreshed every 3 s plus a reconnect loop produced 15×429/min.
- **Notification socket:** `wss://internal.cloud.remarkable.com/notifications/ws/json/1`
  with `Authorization: Bearer <user token>`; the server drops it every few
  minutes; messages only say *that* a device synced — diff stroke-file hashes
  from metadata (`workflows/cloud.py: ink_token`, `live/watcher.py: snapshot`) to know *what*.
- A freshly uploaded document object has no file index: its ink baseline is
  `cloud.EMPTY_INK`, never `ink_token(doc)`.
- MuPDF is not thread-safe: wrap render/analysis in `cloud.MUPDF_LOCK`, but
  never hold it across network calls (OCR).
- "Seen" tracking is per stroke (`Mark.seen_keys`), keyed by PDF page / tablet
  page id — so a note added next to an already collected mark comes back.
- Tests live in `tests/` and never touch real state: `tests/conftest.py` points
  `REMARKABLE_WORKFLOW_STATE` and `REMARKABLE_AUTOPILOT_CONFIG` at temp dirs. Transport is
  swapped in one place (`workflows.cloud`, see `FakeCloud` in tests/test_workflows.py).
- Secrets: the reMarkable token lives in `~/.rmapi`. Never print, log or put
  credentials in tests or fixtures. Follow PRIVACY.md and SECURITY.md.
- Real user documents (the maintainer's annotated PDFs) must not become
  fixtures in this public repo; synthesise ink instead (`tests/test_workflows.py`
  helpers write real v6 `.rm` files).

## Release and compatibility

Work on feature branches and submit pull requests. Run the tests, lint,
formatting, build, and privacy checks before a release. The distribution and
primary CLI are `remarkable-agent-mcp`; `remarkable_mcp`, MCP tool names,
`REMARKABLE_*` variables, and existing state paths remain stable. Old console
commands remain compatibility aliases. Keep private deployment notes outside
this repository. See docs/releasing.md for release preparation.
