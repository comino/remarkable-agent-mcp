"""Check distribution contents and optionally unpack them for secret scanning.

Uses only the standard library. Extraction is restricted to validated regular
files; runtime files, old notebook screenshots and image metadata are rejected.
"""

from __future__ import annotations

import argparse
import stat
import struct
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

PROJECT = "remarkable-agent-mcp"
FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".remarkable",
    ".rmapi",
    ".mcp.json",
    "credentials.json",
    "autopilot.json",
    "workflow-state",
    "handwriting-cache",
    "private",
    "debug-exports",
    "snapshots",
    "trmnl",
}
FORBIDDEN_FILES = {"resources-screenshot.png", "tool-calls-screenshot.png"}
SOURCE_DIRS = {"remarkable_mcp", "tests", "smoke", "docs", "contrib", "scripts"}
SOURCE_FILES = {
    ".gitignore",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "PRIVACY.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "SKILL.md",
    "pyproject.toml",
    "uv.lock",
    "server.json",
    "remarkable-mcp-bridge.nix",
    ".gitleaks.toml",
    "PKG-INFO",
}


def members(archive: Path) -> dict[str, bytes]:
    result = {}
    total = 0

    def add(name, size, is_file, read):
        nonlocal total
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError(f"Unsafe archive path: {name}")
        if not is_file:
            raise ValueError(f"Non-regular archive member: {name}")
        total += size
        if size > 50_000_000 or total > 200_000_000:
            raise ValueError(f"Unexpected archive size: {name}")
        if name in result:
            raise ValueError(f"Duplicate archive member: {name}")
        result[name] = read()

    if archive.suffix == ".whl":
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                if member.is_dir():
                    continue
                add(
                    member.filename,
                    member.file_size,
                    not stat.S_ISLNK(member.external_attr >> 16),
                    lambda: z.read(member),
                )
    elif archive.name.endswith(".tar.gz"):
        with tarfile.open(archive) as t:
            for member in t.getmembers():
                if member.isdir():
                    continue
                add(member.name, member.size, member.isfile(), lambda: t.extractfile(member).read())
    else:
        raise ValueError(f"Unsupported release file: {archive.name}")
    return result


def check(archive: Path) -> dict[str, bytes]:
    files = members(archive)
    wheel = archive.suffix == ".whl"
    metadata = []
    notices = False
    for name, data in files.items():
        parts = PurePosixPath(name).parts
        relative = parts if wheel else parts[1:]
        if not relative:
            raise ValueError(f"Missing source archive root: {name}")
        filename = relative[-1]
        if (
            set(relative) & FORBIDDEN_PARTS
            or filename in FORBIDDEN_FILES
            or filename.startswith((".env", "service-account"))
            or filename.endswith((".pyc", ".pyo", ".log", ".log.1", ".pem", ".key"))
            or filename.endswith("-credentials.json")
        ):
            raise ValueError(f"Private/runtime file in distribution: {name}")
        if wheel:
            if relative[0] != "remarkable_mcp" and not relative[0].endswith(".dist-info"):
                raise ValueError(f"Unexpected wheel member: {name}")
        elif relative[0] not in SOURCE_DIRS | SOURCE_FILES:
            raise ValueError(f"Unexpected source archive member: {name}")
        if filename == ("METADATA" if wheel else "PKG-INFO"):
            metadata.append(BytesParser().parsebytes(data))
        notices |= filename == "THIRD_PARTY_NOTICES.md"
        if filename.endswith(".png"):
            offset = 8
            while offset + 12 <= len(data):
                size = struct.unpack_from(">I", data, offset)[0]
                kind = data[offset + 4 : offset + 8]
                if kind in {b"eXIf", b"tEXt", b"iTXt", b"zTXt"}:
                    raise ValueError(f"Unreviewed PNG metadata in {name}")
                offset += size + 12
    if len(metadata) != 1 or metadata[0]["Name"] != PROJECT:
        raise ValueError("Missing or incorrect distribution identity")
    if not notices:
        raise ValueError("Dependency-license notices are missing")
    print(f"OK {archive.name}: {len(files)} files, version {metadata[0]['Version']}")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract-to", type=Path)
    parser.add_argument("archives", nargs="+", type=Path)
    args = parser.parse_args()
    for archive in args.archives:
        files = check(archive)
        if args.extract_to:
            destination = args.extract_to / archive.name
            # A fresh destination avoids following pre-existing symlinks.
            destination.mkdir(parents=True, exist_ok=False)
            for name, data in files.items():
                path = destination / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)


if __name__ == "__main__":
    main()
