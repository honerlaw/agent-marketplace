"""Endpoint discovery from the vendored Clerk Backend API spec, loaded on first use.

`bapi.json` ships inside the package; `bapi.LICENSE` says where it came from. The API
version every request sends is the spec's own version, so the two cannot drift: a test
holds `CLERK_API_VERSION` equal to the spec's `info.version`.
"""

import json
from collections.abc import Iterator
from importlib import resources

from mcp.server.mcpserver.exceptions import ToolError

CLERK_API_VERSION = "2026-08-20"
SPEC_FILE = "bapi.json"
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
MAX_REF_DEPTH = 6
MULTIPART_NOTE = "multipart upload: not callable through clerk_request"
Spec = dict[str, object]
Node = object


def load_spec() -> Spec:
    """Read the spec that ships with the package."""
    text = resources.files("clerk_mcp").joinpath(SPEC_FILE).read_text("utf-8")
    return _as_dict(json.loads(text))


class SpecCatalog:
    """Lists and describes API operations; reads the spec on first use."""

    def __init__(self, spec: Spec | None = None) -> None:
        """Use `spec` if given (tests), else the vendored one when first needed."""
        self._spec = spec

    def version(self) -> object:
        """Return the spec's `info.version`."""
        return _as_dict(self._load().get("info")).get("version")

    def list_endpoints(self, text_filter: str | None) -> list[str]:
        """Return `METHOD /path — summary` lines, optionally filtered by substring."""
        lines = [_summary_line(method, path, op) for method, path, op in _operations(self._load())]
        needle = (text_filter or "").lower()
        return [line for line in lines if needle in line.lower()]

    def describe(self, method: str, path: str, depth: int) -> dict[str, Node]:
        """Return one operation's parameters, request body and success responses.

        `$ref`s are inlined `depth` levels deep (clamped to 1..MAX_REF_DEPTH).
        """
        spec = self._load()
        operation = _as_dict(_as_dict(spec.get("paths")).get(path)).get(method.lower())
        if not isinstance(operation, dict):
            message = f"no operation {method.upper()} {path} in the spec; see clerk_list_endpoints"
            raise ToolError(message)
        responses = _as_dict(operation.get("responses"))
        described: dict[str, Node] = {
            "method": method.upper(),
            "path": path,
            "summary": operation.get("summary"),
            "description": operation.get("description"),
            "parameters": operation.get("parameters", []),
            "requestBody": operation.get("requestBody"),
            "responses": {code: body for code, body in responses.items() if code.startswith("2")},
        }
        if _is_multipart(operation):
            described["note"] = MULTIPART_NOTE
        bounded = min(max(depth, 1), MAX_REF_DEPTH)
        return _as_dict(resolve_refs(described, spec, bounded))

    def _load(self) -> Spec:
        if self._spec is None:
            self._spec = load_spec()
        return self._spec


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
    line = f"{method.upper()} {path} — {summary}"
    return f"{line} ({MULTIPART_NOTE})" if _is_multipart(operation) else line


def _is_multipart(operation: dict[str, Node]) -> bool:
    content = _as_dict(_as_dict(operation.get("requestBody")).get("content"))
    return any("multipart" in content_type for content_type in content)


def _as_dict(node: Node) -> dict[str, Node]:
    return node if isinstance(node, dict) else {}
