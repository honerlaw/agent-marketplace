"""Endpoint discovery over Meta's codegen specs, loaded once and checked by content hash."""

import json
from pathlib import Path
from typing import TypeVar

import anyio
import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from meta_ads_mcp.config import Settings
from meta_ads_mcp.spec_fetch import SPEC_CONTENT_HASH, SpecFiles, fetch_archive, verified
from meta_ads_mcp.spec_render import Catalog, Node, build_catalog, describe_node, describe_operation

Output = TypeVar("Output")


class SpecCatalog:
    """Lists and describes Graph operations and node types; loads the specs on first use.

    The specs come from `META_ADS_SPEC_PATH` (the Docker image sets it) or, without it,
    from the pinned archive on GitHub. Either way the content must match `expected_hash`,
    which defaults to the pinned constant; only tests pass another.
    """

    def __init__(
        self,
        settings: Settings,
        transport: httpx2.AsyncBaseTransport | None = None,
        expected_hash: str = SPEC_CONTENT_HASH,
    ) -> None:
        """Remember where the specs live; nothing is loaded until it is needed."""
        self._path = settings.spec_path
        self._max_bytes = settings.max_response_bytes
        self._transport = transport
        self._expected_hash = expected_hash
        self._catalog: Catalog | None = None
        self._lock = anyio.Lock()

    async def list_endpoints(self, text_filter: str | None) -> list[str]:
        """Return `METHOD template → Return` lines, optionally filtered by substring."""
        catalog = await self._load()
        needle = (text_filter or "").lower()
        return self._capped([op.line for op in catalog.operations if needle in op.line.lower()])

    async def describe_endpoint(self, method: str, path: str) -> Node:
        """Describe every operation listed as `method path`; usually exactly one."""
        catalog = await self._load()
        wanted = (method.upper(), path)
        matches = [op for op in catalog.operations if (op.method, op.template) == wanted]
        if not matches:
            message = (
                f"no operation {method.upper()} {path}: pass a template exactly as "
                "meta_ads_list_endpoints prints it, e.g. /{AdAccount}/campaigns, not a "
                "concrete path with ids"
            )
            raise ToolError(message)
        described = [describe_operation(op, catalog.enums) for op in matches]
        if len(described) == 1:
            return self._capped(described[0])
        return self._capped({"method": method.upper(), "path": path, "operations": described})

    async def describe_type(self, name: str) -> Node:
        """Describe one node type: its fields, with enum values, and its operations."""
        catalog = await self._load()
        if name not in catalog.nodes:
            message = f"no node type {name!r} in the Meta API specs"
            raise ToolError(message)
        return self._capped(describe_node(catalog, name))

    def _capped(self, described: Output) -> Output:
        """Refuse an output too large for the model, the way large API responses are."""
        size = len(json.dumps(described))
        if size > self._max_bytes:
            message = (
                f"the output is {size} bytes, over {self._max_bytes} "
                "(META_ADS_MAX_RESPONSE_BYTES); narrow the filter"
            )
            raise ToolError(message)
        return described

    async def _load(self) -> Catalog:
        async with self._lock:
            if self._catalog is None:
                files = verified(await self._read(), self._expected_hash)
                self._catalog = build_catalog(files)
            return self._catalog

    async def _read(self) -> SpecFiles:
        if self._path is not None:
            return await anyio.to_thread.run_sync(_read_directory, Path(self._path))
        return (await fetch_archive(self._transport)).files


def _read_directory(directory: Path) -> SpecFiles:
    try:
        return {path.name: path.read_bytes() for path in sorted(directory.glob("*.json"))}
    except OSError as error:
        message = f"could not read the Meta API specs from {directory}: {error}"
        raise ToolError(message) from error
