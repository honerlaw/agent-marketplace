"""Endpoint discovery from Google's Discovery document for the Google Ads API, loaded lazily.

The Discovery format is not OpenAPI: methods sit in nested `resources`, each with an
`httpMethod` and a `path` such as `v26/customers/{+customerId}/googleAds:search`, and
schemas are referenced by bare name (`{"$ref": "GoogleAdsGoogleadsV26Resources__AdGroup"}`).
Every template is shown in one spelling, relative to the versioned base URL with reserved
expansion dropped: `/customers/{customerId}/googleAds:search`.
"""

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import anyio
import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from google_ads_mcp.config import Settings

MAX_REF_DEPTH = 6
SUMMARY_LENGTH = 100
VERSION_PREFIX = re.compile(r"^v[0-9]+(?=[/:])")
FIRST_SENTENCE = re.compile(r"^(.*?[.!?])(\s|$)", re.DOTALL)
Spec = dict[str, object]
Node = object


@dataclass(frozen=True)
class Operation:
    """One Discovery method, keyed by its HTTP method and display template."""

    method: str
    template: str
    body: dict[str, Node]


class SpecCatalog:
    """Lists and describes API operations and schemas; fetches the document on first use."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Remember where the document lives; nothing is loaded until it is needed."""
        self._path = settings.discovery_path
        self._url = settings.discovery_url
        self._max_bytes = settings.max_response_bytes
        self._transport = transport
        self._spec: Spec | None = None

    async def list_endpoints(self, text_filter: str | None) -> list[str]:
        """Return `METHOD /template — summary` lines, optionally filtered by substring."""
        spec = await self._load()
        lines = [_summary_line(operation) for operation in operations(spec)]
        needle = (text_filter or "").lower()
        return [line for line in lines if needle in line.lower()]

    async def describe(self, method: str, path: str, depth: int) -> dict[str, Node]:
        """Return one operation's parameters, request schema and response schema.

        A few catch-all templates are shared by two methods (`GET /{name}` is both
        `operations.get` and `operations.list`); then every match is returned, each with
        its Discovery `id`.
        """
        spec = await self._load()
        matches = _find(spec, method.upper(), path)
        schemas, bounded = _schemas(spec), _bounded(depth)
        described = [_as_dict(resolve_refs(_described(op), schemas, bounded)) for op in matches]
        if len(described) == 1:
            return self._capped(described[0])
        return self._capped({"method": method.upper(), "path": path, "operations": described})

    async def describe_schema(self, name: str, depth: int) -> dict[str, Node]:
        """Return one named schema with its `$ref`s expanded `depth` levels."""
        spec = await self._load()
        schemas = _schemas(spec)
        if name not in schemas:
            message = f"no schema {name!r} in the Discovery document"
            raise ToolError(message)
        return self._capped(_as_dict(resolve_refs({"$ref": name}, schemas, _bounded(depth))))

    def _capped(self, described: dict[str, Node]) -> dict[str, Node]:
        """Refuse a description too large for the model, the way large responses are."""
        size = len(json.dumps(described))
        if size > self._max_bytes:
            message = (
                f"the description is {size} bytes, over {self._max_bytes} "
                "(GOOGLE_ADS_MAX_RESPONSE_BYTES). Use a lower depth and open nested schemas "
                "one at a time with google_ads_describe_schema."
            )
            raise ToolError(message)
        return described

    async def _load(self) -> Spec:
        if self._spec is None:
            text = await self._read()
            try:
                self._spec = _as_dict(json.loads(text))
            except ValueError as error:
                message = f"the Discovery document is not valid JSON: {error}"
                raise ToolError(message) from error
        return self._spec

    async def _read(self) -> str:
        if self._path is not None:
            return await _read_file(self._path)
        try:
            async with httpx2.AsyncClient(transport=self._transport, timeout=60) as client:
                response = await client.get(self._url)
                response.raise_for_status()
        except httpx2.HTTPError as error:
            message = f"could not load the Discovery document from {self._url}: {error}"
            raise ToolError(message) from error
        return response.text


async def _read_file(path: str) -> str:
    try:
        return await anyio.Path(Path(path)).read_text(encoding="utf-8")
    except OSError as error:
        message = f"could not read the Discovery document from {path}: {error}"
        raise ToolError(message) from error


def operations(spec: Spec) -> Iterator[Operation]:
    """Yield every method in the document, depth first, in document order."""
    yield from _walk(_as_dict(spec.get("resources")))


def display_template(path: str) -> str:
    """Turn `v26/customers/{+customerId}/x:y` into `/customers/{customerId}/x:y`.

    A version-level method such as `v26:listPlannableLocations` becomes
    `:listPlannableLocations`, which is also the path the request tool takes for it.
    """
    return VERSION_PREFIX.sub("", path).replace("{+", "{")


def resolve_refs(node: Node, schemas: dict[str, Node], depth: int) -> Node:
    """Inline `$ref`s up to `depth` levels; deeper refs stay as `{"$ref": name}` markers."""
    if isinstance(node, list):
        return [resolve_refs(item, schemas, depth) for item in node]
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if isinstance(ref, str) and depth > 0 and ref in schemas:
        # A property's own keys (its description says how this field is used) win over
        # the referenced schema's generic ones.
        siblings = {key: value for key, value in node.items() if key != "$ref"}
        return {**_as_dict(resolve_refs(schemas[ref], schemas, depth - 1)), **siblings}
    return {key: resolve_refs(value, schemas, depth) for key, value in node.items()}


def _walk(resources: dict[str, Node]) -> Iterator[Operation]:
    for resource in resources.values():
        for method in _as_dict(_as_dict(resource).get("methods")).values():
            body = _as_dict(method)
            template = display_template(str(body.get("path", "")))
            yield Operation(str(body.get("httpMethod", "")).upper(), template, body)
        yield from _walk(_as_dict(_as_dict(resource).get("resources")))


def _find(spec: Spec, method: str, template: str) -> list[Operation]:
    key = (method, template)
    matches = [op for op in operations(spec) if (op.method, op.template) == key]
    if not matches:
        message = (
            f"no operation {method} {template} in the Discovery document; copy the template "
            "exactly as google_ads_list_endpoints prints it"
        )
        raise ToolError(message)
    return matches


def _described(operation: Operation) -> dict[str, Node]:
    return {
        "method": operation.method,
        "path": operation.template,
        "id": operation.body.get("id"),
        "description": operation.body.get("description"),
        "parameters": operation.body.get("parameters", {}),
        "request": operation.body.get("request"),
        "response": operation.body.get("response"),
    }


def _summary_line(operation: Operation) -> str:
    return f"{operation.method} {operation.template} — {_summary(operation.body)}"


def _summary(body: dict[str, Node]) -> str:
    description = str(body.get("description") or body.get("id") or "").strip()
    match = FIRST_SENTENCE.match(description)
    sentence = " ".join((match.group(1) if match else description).split())
    if len(sentence) <= SUMMARY_LENGTH:
        return sentence
    return sentence[: SUMMARY_LENGTH - 1].rstrip() + "…"


def _schemas(spec: Spec) -> dict[str, Node]:
    return _as_dict(spec.get("schemas"))


def _bounded(depth: int) -> int:
    return min(max(depth, 1), MAX_REF_DEPTH)


def _as_dict(node: Node) -> dict[str, Node]:
    return node if isinstance(node, dict) else {}
