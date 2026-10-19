"""Cut tests/fixtures/discovery.json from Google's full Discovery document.

Usage, from mcp/google-ads/:

    curl -sS -o /tmp/v26.json 'https://googleads.googleapis.com/$discovery/rest?version=v26'
    .venv/bin/python -m tests.cut_discovery /tmp/v26.json tests/fixtures/discovery.json

It keeps the methods in KEEP_METHODS, under their original resource nesting, and the
schemas in KEEP_SCHEMAS. Any property whose `$ref` (or `items.$ref`) names a schema that
was not kept is dropped, so every reference left in the fixture resolves. Top-level keys
such as `version` and `revision` are copied, recording which document it was cut from.
"""

import json
import sys
from pathlib import Path

Node = object
PREFIX = "GoogleAdsGoogleadsV26"
KEEP_METHODS = {
    ("customers",): {"listAccessibleCustomers"},
    ("customers", "googleAds"): {"search", "searchStream", "mutate"},
    ("customers", "adGroups"): {"mutate"},
    ("customers", "operations"): {"get", "list", "delete"},
    ("googleAdsFields",): {"get"},
}
KEEP_SCHEMAS = {
    f"{PREFIX}Services__ListAccessibleCustomersResponse",
    f"{PREFIX}Services__SearchGoogleAdsRequest",
    f"{PREFIX}Services__SearchGoogleAdsResponse",
    f"{PREFIX}Services__SearchGoogleAdsStreamRequest",
    f"{PREFIX}Services__SearchGoogleAdsStreamResponse",
    f"{PREFIX}Services__MutateGoogleAdsRequest",
    f"{PREFIX}Services__MutateGoogleAdsResponse",
    f"{PREFIX}Services__MutateAdGroupsRequest",
    f"{PREFIX}Services__MutateAdGroupsResponse",
    f"{PREFIX}Services__AdGroupOperation",
    f"{PREFIX}Services__MutateAdGroupResult",
    f"{PREFIX}Resources__AdGroup",
    f"{PREFIX}Resources_AdGroup_DemandGenAdGroupSettings",
    f"{PREFIX}Resources_AdGroupDemandGenAdGroupSettings_DemandGenChannelControls",
    f"{PREFIX}Resources_AdGroupDemandGenAdGroupSettingsDemandGenChannelControls_DemandGenSelectedChannels",
    f"{PREFIX}Resources__GoogleAdsField",
    "GoogleLongrunning__Operation",
    "GoogleLongrunning__ListOperationsResponse",
    "GoogleProtobuf__Empty",
    "GoogleRpc__Status",
}
KEEP_TOP_LEVEL = ("kind", "discoveryVersion", "id", "name", "version", "revision", "rootUrl")


def cut(full: dict[str, Node]) -> dict[str, Node]:
    """Return the trimmed Discovery document."""
    cut_doc: dict[str, Node] = {key: full[key] for key in KEEP_TOP_LEVEL if key in full}
    cut_doc["resources"] = _resources(_as_dict(full.get("resources")), ())
    schemas = _as_dict(full.get("schemas"))
    cut_doc["schemas"] = {name: _closed(schemas[name]) for name in sorted(KEEP_SCHEMAS)}
    return cut_doc


def _resources(resources: dict[str, Node], trail: tuple[str, ...]) -> dict[str, Node]:
    kept: dict[str, Node] = {}
    for name, resource in resources.items():
        here = (*trail, name)
        body = _as_dict(resource)
        methods = _as_dict(body.get("methods"))
        wanted = KEEP_METHODS.get(here, set())
        entry: dict[str, Node] = {}
        if wanted:
            entry["methods"] = {key: methods[key] for key in sorted(wanted)}
        children = _resources(_as_dict(body.get("resources")), here)
        if children:
            entry["resources"] = children
        if entry:
            kept[name] = entry
    return kept


def _closed(schema: Node) -> Node:
    body = _as_dict(schema)
    properties = _as_dict(body.get("properties"))
    kept = {key: value for key, value in properties.items() if _resolves(value)}
    return {**body, "properties": kept} if properties else body


def _resolves(prop: Node) -> bool:
    body = _as_dict(prop)
    ref = body.get("$ref") or _as_dict(body.get("items")).get("$ref")
    return ref is None or ref in KEEP_SCHEMAS


def _as_dict(node: Node) -> dict[str, Node]:
    return node if isinstance(node, dict) else {}


def main(source: str, target: str) -> None:
    """Read `source`, write the cut fixture to `target`."""
    full = _as_dict(json.loads(Path(source).read_text(encoding="utf-8")))
    Path(target).write_text(json.dumps(cut(full), indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
