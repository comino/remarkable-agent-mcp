"""
reMarkable Agent MCP

Two-way reMarkable workflows for an MCP-connected agent.
"""

from importlib.metadata import PackageNotFoundError, version

# Capability checking utilities
from remarkable_mcp.core.capabilities import (
    client_supports_elicitation,
    client_supports_experimental,
    client_supports_roots,
    get_client_capabilities,
    get_client_info,
    get_protocol_version,
)

try:
    __version__ = version("remarkable-agent-mcp")
except PackageNotFoundError:
    __version__ = "0+unknown"


def get_mcp():
    """Get the MCP server instance. Only imports when called."""
    from remarkable_mcp.server import mcp

    return mcp


__all__ = [
    "get_mcp",
    "__version__",
    # Capability checking
    "get_client_capabilities",
    "client_supports_elicitation",
    "client_supports_roots",
    "client_supports_experimental",
    "get_client_info",
    "get_protocol_version",
]
