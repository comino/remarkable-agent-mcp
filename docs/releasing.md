# Preparing a release

The distribution and primary command are `remarkable-agent-mcp`; the display
name is **reMarkable Agent MCP**. The optional daemon command is
`remarkable-agent-mcp-autopilot`. This is a continuation of Marginalia and of
the upstream `remarkable-mcp` codebase.

`remarkable_mcp`, `remarkable_*` tools, `REMARKABLE_*` variables and existing
state directories remain stable. The old `marginalia`, `marginalia-autopilot`,
`remarkable-mcp` and `remarkable-autopilot` commands are compatibility aliases
provided by this distribution. Installing an unrelated package with one of
those names does not install this project.

## Install before PyPI publication

Install a reviewed checkout or wheel. The new package name is not a promise
that a PyPI release already exists:

```bash
uv tool install --force .
# Or, from a built release:
uv tool install --force dist/remarkable_agent_mcp-1.3.0-py3-none-any.whl
remarkable-agent-mcp --help
```

For a Git installation, use the repository URL in the README and pin a
reviewed commit or release tag. Update MCP configuration to invoke
`remarkable-agent-mcp`. Existing state needs no migration. If another uv tool
owns a compatibility executable, `--force` replaces that executable; inspect
`uv tool list` first. Do not remove your credentials or workflow state.

## Release checks

Work on a feature branch and submit a PR. Version numbers are explicit in
`pyproject.toml`, `uv.lock` and `server.json`; they are not derived from tags.
There is currently no workflow that publishes to PyPI or the MCP Registry.

1. Review source, documentation and generated assets for personal information.
   Keep examples synthetic and preserve third-party copyright notices.
2. Run the supported Python matrix (3.10, 3.11, 3.12), lint, formatting and
   package checks:

   ```bash
   uv sync --all-extras --frozen
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest -v
   uv build
   uv run python scripts/check_release.py dist/*
   uv run --isolated --no-project --with dist/*.whl remarkable-agent-mcp --help
   gitleaks git --log-opts="--all" --redact --config .gitleaks.toml .
   ```

   CI also extracts and scans the actual wheel and source archive. Do not
   publish artifacts from a dirty directory containing private runtime files.
3. Test a synthetic round trip on a real tablet: request and reply, follow-up,
   draft review and revision, interrupted upload and retry, daemon restart.
   Offline tests do not certify device, firmware or account compatibility.
4. Review [privacy](../PRIVACY.md) and [dependency licenses](../THIRD_PARTY_NOTICES.md).
   Confirm the distribution approach before advertising licensing terms.
5. Confirm the GitHub repository name, PyPI ownership, registry metadata and
   release version. Publish the reviewed artifacts only after these checks;
   a prepared `server.json` is not evidence of registry publication.

## Existing public history

This fork was recreated from upstream on **2026-10-15**, with the reMarkable
agent workflows and public-release cleanup consolidated into one commit.
If your clone predates that reset, make a fresh clone before contributing.
Transfer unpublished work as reviewed patches; merging or pushing the old
fork history can bring removed content back. Keep original-history backups
private and outside the repository. Upstream history is retained, and the
reset does not erase old commits from GitHub's shared fork network or other
people's clones.

Deleting a file in a new commit leaves its old versions reachable through
history and tags. A rename does not remove old content either. Prepare any
history rewrite in a disposable mirror with a private backup, inspect the
changed refs and scan the result before replacing remote history.

Coordinate a rewrite with collaborators. Release archives, PR refs, caches,
forks and other clones may still retain old data; follow
[GitHub's sensitive-data removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
Revoke any exposed live credential first. Do not mix a destructive remote
rewrite with an ordinary release PR.
