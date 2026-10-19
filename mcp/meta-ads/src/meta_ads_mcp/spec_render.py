"""Turns Meta's codegen specs into endpoint templates, list lines and descriptions.

One template spelling everywhere. A node operation (`#get`, `#update`, `#delete`) is
`METHOD /{NodeType}`; an edge is `METHOD /{NodeType}/<edge>`; the few operations Meta
roots at a fixed path (`basePath`) are that literal path. The model fills ids in itself:
`/{AdAccount}/campaigns` is called as `/act_<id>/campaigns`.
"""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

NODE_OPERATIONS = frozenset({"#get", "#update", "#delete"})
ENUMS_FILE = "enum_types.json"
LIST_TYPE = re.compile(r"list<(.+)>")
Node = dict[str, object]


@dataclass(frozen=True)
class Operation:
    """One Graph operation as the discovery tools present it."""

    method: str
    template: str
    node: str
    returns: str
    params: tuple[Mapping[str, object], ...]

    @property
    def line(self) -> str:
        """The `METHOD template → Return` line `list_endpoints` prints."""
        return f"{self.method} {self.template} → {self.returns}"


@dataclass(frozen=True)
class Catalog:
    """Every node type, its operations, and the enum values types refer to."""

    nodes: Mapping[str, Node]
    operations: tuple[Operation, ...]
    enums: Mapping[str, list[str]]


def build_catalog(files: Mapping[str, bytes]) -> Catalog:
    """Parse the spec files (one per node type, plus `enum_types.json`)."""
    enums = {
        str(entry["name"]): list(entry["values"])
        for entry in json.loads(files.get(ENUMS_FILE, b"[]"))
    }
    nodes = {
        name.removesuffix(".json"): _as_node(json.loads(content))
        for name, content in files.items()
        if name != ENUMS_FILE
    }
    operations = tuple(
        _operation(node, api) for node in sorted(nodes) for api in _apis(nodes[node])
    )
    return Catalog(nodes, operations, enums)


def describe_operation(operation: Operation, enums: Mapping[str, list[str]]) -> Node:
    """Describe one operation: the node, what it returns and each parameter."""
    return {
        "method": operation.method,
        "path": operation.template,
        "node": operation.node,
        "returns": operation.returns,
        "params": [_typed(param, enums) for param in operation.params],
    }


def describe_node(catalog: Catalog, name: str) -> Node:
    """Describe one node type: its fields (with enum values) and its operations."""
    node = catalog.nodes[name]
    fields = node.get("fields", [])
    return {
        "type": name,
        "fields": [_typed(field, catalog.enums) for field in _mappings(fields)],
        "endpoints": [op.line for op in catalog.operations if op.node == name],
    }


def _operation(node: str, api: Mapping[str, object]) -> Operation:
    return Operation(
        method=str(api.get("method", "GET")).upper(),
        template=_template(node, api),
        node=node,
        returns=str(api.get("return", "Object")),
        params=tuple(_mappings(api.get("params", []))),
    )


def _template(node: str, api: Mapping[str, object]) -> str:
    endpoint = str(api.get("endpoint") or "")
    base_path = api.get("basePath")
    if base_path:
        return "/" + "/".join(part for part in (str(base_path), endpoint) if part)
    if api.get("name") in NODE_OPERATIONS or not endpoint:
        return f"/{{{node}}}"
    return f"/{{{node}}}/{endpoint}"


def _typed(entry: Mapping[str, object], enums: Mapping[str, list[str]]) -> Node:
    described: Node = dict(entry)
    values = enums.get(_element_type(str(entry.get("type", ""))))
    if values is not None:
        described["enum"] = values
    return described


def _element_type(type_name: str) -> str:
    while match := LIST_TYPE.fullmatch(type_name):
        type_name = match.group(1)
    return type_name


def _apis(node: Node) -> list[Mapping[str, object]]:
    return _mappings(node.get("apis", []))


def _mappings(value: object) -> list[Mapping[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _as_node(value: object) -> Node:
    return value if isinstance(value, dict) else {}
