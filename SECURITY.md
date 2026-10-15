# Security

reMarkable Agent MCP runs with the permissions of its host process. Documents,
web pages and handwriting can contain untrusted instructions. File and URL
checks reduce exposure through this server; they do not sandbox an agent or
the other tools it can use.

## What is protected

- **Local files** a tool is asked to read (drafts, PDFs, images) must be regular
  files with an allowed suffix and under a size cap, outside sensitive locations
  (`~/.ssh`, `~/.gnupg`, `~/.aws`, `~/.config`, `~/.rmapi`, `/proc`, `/etc`, …).
  Set `REMARKABLE_ALLOWED_ROOTS` to restrict reads to specific directories.
- **URLs** (`remarkable_clip`) must be http(s); hosts resolving to loopback,
  private, link-local, carrier-grade NAT / tailnet (`100.64.0.0/10`) or other
  non-public addresses are refused, and every redirect hop is re-checked.
- **Write access** to the tablet can be switched off with
  `REMARKABLE_READ_ONLY=1`. This does not disable local caches or prevent another
  agent tool from writing files. MCP annotations describe tools; they are not
  an authorization system.
- **Credentials** are loaded from local configuration or environment variables
  and sent to the relevant service for authentication. Registration saves
  `~/.rmapi` with mode 0600. Do not paste tokens into issues, prompts or logs.
- **Workflow records** are written atomically in private directories. Replies
  that fail to upload remain queued and can be retried without executing the
  original task again.

`REMARKABLE_ALLOWED_ROOTS` scopes local input files, not the tablet library;
`REMARKABLE_ROOT_PATH` scopes library access. File checks resolve symlinks, but
are not a defense against a hostile process changing files on the same host.
The URL guard can be explicitly bypassed with `REMARKABLE_ALLOW_PRIVATE_URLS=1`;
only use that for sources you control.

Use stdio for a local MCP client. HTTP mode should stay on loopback unless
protected by a separately configured authentication and network boundary.
Autopilot is opt-in and launches the configured command with your permissions.
Review its agent configuration before enabling unattended actions.

See [PRIVACY.md](PRIVACY.md) for providers, stored data and retention. CI scans
Git history and built packages for recognizable secrets. Scanning is a useful
check, not proof that arbitrary private content is absent.

## Reporting a vulnerability

Use [GitHub's private vulnerability reporting](https://github.com/comino/remarkable-agent-mcp/security/advisories/new)
when available. If it is unavailable, open an issue asking for a private
contact without including exploit details or private data. Include what an
attacker controls, the impact, affected version and a synthetic reproduction.
