"""Endpoint discovery from the Ads API's published OpenAPI spec, loaded lazily."""

import json
from collections.abc import Iterator
from pathlib import Path

import anyio
import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from openai_ads_mcp.config import Settings

HTTP_METHODS = ("get", "post", "patch", "delete")
MAX_REF_DEPTH = 6
Spec = dict[str, object]
Node = object


class SpecCatalog:
    """Lists and describes API operations; fetches the spec on first use."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Remember where the spec lives; nothing is loaded until it is needed."""
        self._path = settings.openapi_path
        self._url = settings.openapi_url
        self._transport = transport
        self._spec: Spec | None = None

    async def list_endpoints(self, text_filter: str | None) -> list[str]:
        """Return `METHOD /path — summary` lines, optionally filtered by substring."""
        spec = await self._load()
        lines = [_summary_line(method, path, op) for method, path, op in _operations(spec)]
        needle = (text_filter or "").lower()
        return [line for line in lines if needle in line.lower()]

    async def describe(self, method: str, path: str, depth: int) -> dict[str, Node]:
        """Return one operation's parameters, request body and success responses.

        `$ref`s are inlined `depth` levels deep (clamped to 1..MAX_REF_DEPTH).
        """
        spec = await self._load()
        operation = _as_dict(_as_dict(spec.get("paths")).get(path)).get(method.lower())
        if not isinstance(operation, dict):
            message = (
                f"no operation {method.upper()} {path} in the spec; see openai_ads_list_endpoints"
            )
            raise ToolError(message)
        responses = _as_dict(operation.get("responses"))
        success = {code: body for code, body in responses.items() if str(code).startswith("2")}
        described = {
            "method": method.upper(),
            "path": path,
            "summary": operation.get("summary"),
            "description": operation.get("description"),
            "parameters": operation.get("parameters", []),
            "requestBody": operation.get("requestBody"),
            "responses": success,
        }
        bounded = min(max(depth, 1), MAX_REF_DEPTH)
        return _as_dict(resolve_refs(described, spec, bounded))

    async def _load(self) -> Spec:
        if self._spec is None:
            self._spec = _as_dict(json.loads(await self._read()))
        return self._spec

    async def _read(self) -> str:
        if self._path is not None:
            return await anyio.Path(Path(self._path)).read_text(encoding="utf-8")
        try:
            async with httpx2.AsyncClient(transport=self._transport, timeout=60) as client:
                response = await client.get(self._url)
                response.raise_for_status()
        except httpx2.HTTPError as error:
            message = f"could not load the OpenAPI spec from {self._url}: {error}"
            raise ToolError(message) from error
        return response.text


def resolve_refs(node: Node, spec: Spec, depth: int) -> Node:
    """Inline local `$ref`s up to `depth` levels; deeper refs are left as markers."""
    if isinstance(node, list):
        return [resolve_refs(item, spec, depth) for item in node]
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if isinstance(ref, str) and depth > 0:
        return resolve_refs(_lookup(spec, ref), spec, depth - 1)
    return {key: resolve_refs(value, spec, depth) for key, value in node.items()}


def _lookup(spec: Spec, ref: str) -> Node:
    node: Node = spec
    for part in ref.removeprefix("#/").split("/"):
        node = _as_dict(node).get(part)
    return node


def _operations(spec: Spec) -> Iterator[tuple[str, str, dict[str, Node]]]:
    for path, item in _as_dict(spec.get("paths")).items():
        for method in HTTP_METHODS:
            operation = _as_dict(item).get(method)
            if isinstance(operation, dict):
                yield method, path, operation


def _summary_line(method: str, path: str, operation: dict[str, Node]) -> str:
    summary = operation.get("summary") or operation.get("operationId") or ""
    return f"{method.upper()} {path} — {summary}"


def _as_dict(node: Node) -> dict[str, Node]:
    return node if isinstance(node, dict) else {}
