---
name: remarkable
description: >
  reMarkable Agent MCP - the reMarkable tablet as an agent front end. Read, search and
  render documents, and turn pen marks into structured results: pen review of
  drafts (change requests with source lines), code and LaTeX review, forms and
  yes/no questions answered with ticks, an Agent Inbox of handwritten
  requests, sketch -> Mermaid diagrams, tables, wireframes, math, reading
  highlights, near-live ink. Triggers: "reMarkable", "tablet", "handwritten",
  "send to my tablet", "review on paper", "ask me on the tablet",
  "what did I write", "sketch", "inbox".
---

# reMarkable Agent MCP: reMarkable for agents

Access your reMarkable tablet as a second brain. Browse, search, read,
and extract content from all documents including handwritten notes via OCR.

## Setup

Install from this repository (the new package has not been published yet):

```bash
uv tool install "remarkable-agent-mcp[web] @ git+https://github.com/comino/remarkable-agent-mcp"
remarkable-agent-mcp --register CODE
```

Configure your MCP client:

```json
{
  "mcpServers": {
    "remarkable": {
      "command": "remarkable-agent-mcp"
    }
  }
}
```

Cloud mode supports the full workflow, including forms and inbox replies.
A reMarkable account is needed; Connect adds unlimited sync, while limited
cloud sync is available without it. SSH can read raw strokes and manage files.
USB web reads flattened PDFs and can upload files, but cannot interpret raw
pen marks. Local-directory mode is read-only. See [docs/core.md](docs/core.md).

Set `REMARKABLE_HANDWRITING_BACKEND=none` to disable automatic remote handwriting
recognition. With no backend, request crops with `include_images=true` for the
agent to read. Those crops are still visible to the agent's provider. See
[PRIVACY.md](PRIVACY.md) before selecting a remote OCR provider.

## Tools

| Tool | Purpose |
|------|---------|
| `remarkable_read` | Read document content with text extraction, pagination, grep |
| `remarkable_browse` | Browse folders, search by name, filter by tags |
| `remarkable_search` | Multi-document content search with OCR |
| `remarkable_recent` | List recently modified documents |
| `remarkable_image` | Render pages as PNG or SVG |
| `remarkable_status` | Check connection and device info |
| `remarkable_annotations` | What the pen marks on a document mean (strike, underline, circle, notes) |
| `remarkable_review_send` | Send a Markdown draft to the tablet for pen review |
| `remarkable_review_collect` | Get the review's marks as change requests with source line numbers |
| `remarkable_review_list` | See which reviews have new marks |
| `remarkable_ask` / `remarkable_form_*` | Questions and forms answered with ticks on the tablet |
| `remarkable_inbox*` | Handwritten requests in an "Agent Inbox" become agent tasks |
| `remarkable_sketch` / `remarkable_regions` | Hand-drawn diagrams → graph + Mermaid; page ink → regions |
| `remarkable_clip` / `remarkable_reading_*` | Web articles → tablet; highlights → quotes with deep links |
| `remarkable_whats_new` | One call: what needs attention across all workflows |

## Workflow

1. Use `remarkable_browse` or `remarkable_search` to find documents
2. Use `remarkable_read` to extract text content
3. Use `remarkable_image` to render visual pages
4. Use `page` parameter to paginate through multi-page documents

## Review workflow

1. `remarkable_review_send(source_path="/path/draft.md")` uploads a review PDF to `/Review`
2. The user marks it up with the pen (strike = delete, circle/underline + note = change)
3. `remarkable_review_collect("<review>")` returns change requests with `src_line`
4. Edit the draft, then `remarkable_review_send(source_path=..., responses=[{id, status, reply}])`
