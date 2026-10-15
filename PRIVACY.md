# Privacy and data handling

The server connects your reMarkable to the agent you choose. Local processing,
tablet synchronization, handwriting recognition and the agent provider are
separate data flows.

| Component | Data it receives or stores |
|---|---|
| reMarkable Cloud | Documents synchronized by the tablet and PDFs this server uploads, including requests, replies and review sheets |
| SSH, USB or local-directory transport | Documents read from the configured device or directory; SSH/USB support selected write operations |
| Local workflow state | Source text and paths, document IDs, form answers, transcriptions, inbox requests and replies, review manifests and LaTeX source snapshots |
| Local cloud cache | Content-addressed sync blobs, including library metadata and smaller document/stroke blobs within the configured size limit |
| Handwriting/OCR service | Cropped handwriting images, strokes or page images required by the selected backend |
| Your MCP client and agent provider | Tool results and images you expose through the MCP connection; retention depends on that client/provider |
| Autopilot logs | Output of the configured agent command, which may contain document content and tool results |

This project does not add analytics or telemetry. Network access still occurs
for the selected transport, OCR, web clipping and configured agent. A direct
device transport can fall back to cloud when a token is available; set
`REMARKABLE_DISABLE_CLOUD_FALLBACK=1` to disable that fallback.

## Choose recognition deliberately

Workflow handwriting defaults to `REMARKABLE_HANDWRITING_BACKEND=auto`.
It selects MyScript when its keys are configured, then Google Vision, then
Anthropic, otherwise no transcription. MyScript receives stroke coordinates;
Google and Anthropic receive images. Explicit provider selections override
automatic choice. The core document OCR setting, `REMARKABLE_OCR_BACKEND`, is
separate: `auto` prefers configured Google Vision, otherwise local Tesseract.

To avoid remote OCR requests from this server:

```bash
export REMARKABLE_HANDWRITING_BACKEND=none
export REMARKABLE_OCR_BACKEND=tesseract
export REMARKABLE_DISABLE_CLOUD_FALLBACK=1
```

Install the Tesseract system executable for local document OCR. Workflow tools
can still return handwriting crops for your agent to read. An agent using a
remote model may send those crops to its provider. These settings therefore
do not make an entire agent session offline. Cloud mode itself continues to
use reMarkable Cloud.

## Local storage and retention

The existing paths are retained across the rename so ongoing reviews and
inboxes keep their state:

- `~/.rmapi`: cloud registration credentials, created with mode 0600.
- `~/.remarkable/cache`: downloaded/extracted documents and cloud blob cache.
  `REMARKABLE_CACHE_DIR` overrides the blob-cache location;
  `REMARKABLE_DISABLE_CACHE=1` disables that blob cache.
- `~/.local/state/remarkable-mcp` (or `$XDG_STATE_HOME/remarkable-mcp`): workflow
  state. Override with `REMARKABLE_WORKFLOW_STATE`, using a dedicated directory.
  Records use private directories and atomic files; LaTeX snapshots are kept
  beneath the same state root.
- `~/.config/remarkable-mcp/autopilot.json` (or the configured override): the
  optional agent command and scheduler settings.
- `autopilot.log` beneath the workflow state root: agent output, created with
  mode 0600. Before a new run, a log larger than 5 MB is moved to
  `autopilot.log.1`. A single run can exceed that size.

There is no automatic expiry of workflow records or source snapshots. Stop
the MCP server and autopilot before backing up or removing their state. Cache
directories can be removed and rebuilt. Removing workflow state loses review
mapping, acknowledgments and pending replies; old requests may be discovered
again. Keep a private backup if you want to preserve those interactions.
Removing local files does not delete copies on the tablet, in cloud sync or
with an agent/OCR provider. Old installations may have files created under
their original permission settings; check those directories during migration.

## Sharing examples and diagnostics

Use synthetic documents, requests and handwriting. The gallery is generated
from the fixtures in `docs/assets/make_gallery.py`; it does not use a personal
notebook. Remove document names, account IDs, paths, tokens and note content
from diagnostics before sharing them. Never upload runtime state or agent logs
as a sample dataset. See [SECURITY.md](SECURITY.md) for security boundaries and
[docs/releasing.md](docs/releasing.md) for checks before publishing.
