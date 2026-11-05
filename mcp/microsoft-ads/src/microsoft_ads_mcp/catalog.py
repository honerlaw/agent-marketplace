"""The committed operation catalog: request lookup, and what the discovery tools print.

`catalog.json` ships inside the package (built by `catalog_build.py` from the pinned
msads sdist), so lookup and discovery never touch the network and cannot fail on it.
"""

import json
from importlib import resources

from mcp.server.mcpserver.exceptions import ToolError

from microsoft_ads_mcp.catalog_build import CATALOG_FILE, Catalog, normalize
from microsoft_ads_mcp.catalog_extract import EnumType, ObjectType, Operation, Subtype

JsonObject = dict[str, object]
LIST_PREFIX = "list["
NO_MODEL = "object"
POLYMORPHIC_NOTE = (
    'Polymorphic: send one of the subtypes, with its "Type" value set; the subtype lists '
    "every field."
)


def load_catalog() -> Catalog:
    """Read the catalog that ships with the package."""
    text = resources.files("microsoft_ads_mcp").joinpath(CATALOG_FILE).read_text("utf-8")
    catalog: Catalog = json.loads(text)
    return catalog


def element_type(kind: str) -> str:
    """Return the named type inside any number of list[...] wrappers."""
    while kind.startswith(LIST_PREFIX):
        kind = kind.removeprefix(LIST_PREFIX).removesuffix("]")
    return kind


class OperationCatalog:
    """Finds operations by name and renders operations and types for the model."""

    def __init__(self, catalog: Catalog, max_bytes: int) -> None:
        """Index the catalog; `max_bytes` caps every discovery output."""
        self._catalog = catalog
        self._keys = {normalize(name): name for name in catalog["operations"]}
        self._max_bytes = max_bytes

    def operation(self, name: str) -> tuple[str, Operation]:
        """Return an operation's canonical name and entry; case and `_` do not matter.

        A "Service." prefix, as `list_operations` prints it, is accepted and ignored.
        """
        canonical = self._keys.get(normalize(name.rsplit(".", 1)[-1]))
        if canonical is None:
            message = f"unknown operation {name!r}; find one with microsoft_ads_list_operations"
            raise ToolError(message)
        return canonical, self._catalog["operations"][canonical]

    def list_operations(self, text_filter: str | None) -> list[str]:
        """One line per operation, "Service.Name — METHOD /path → RequestType", filtered."""
        needle = (text_filter or "").lower()
        lines = [
            f"{entry['service']}.{name} — {entry['method']} {entry['path']} → {entry['request']}"
            for name, entry in self._catalog["operations"].items()
        ]
        selected = [line for line in lines if needle in line.lower()]
        self._check_size(selected)
        return selected

    def describe_operation(self, name: str) -> JsonObject:
        """Describe an operation, its request and response fields, and the types they name."""
        canonical, entry = self.operation(name)
        service = entry["service"]
        request = self._fields(service, entry["request"])
        response = self._fields(service, entry["response"])
        named = sorted(
            {element_type(kind) for kind in [*request.values(), *response.values()]}
            & set(self._catalog["types"][service])
        )
        types = {kind: self._type_view(service, kind) for kind in named}
        described: JsonObject = {
            "operation": canonical,
            **entry,
            "request_fields": request,
            "response_fields": response,
            "types": types,
            "enums": self._enums(
                service, [request, response, *(self._fields(service, kind) for kind in named)]
            ),
        }
        self._check_size(described)
        return described

    def describe_type(self, name: str, service: str | None = None) -> JsonObject:
        """Describe a type's fields (inherited ones included) and subtypes, or an enum."""
        owner = self._owner(name, service)
        enums = self._catalog["enums"][owner]
        if name in enums:
            described: JsonObject = {"name": name, "service": owner, **_enum_view(enums[name])}
        else:
            described = {
                "name": name,
                "service": owner,
                **self._type_view(owner, name),
                "enums": self._enums(owner, [self._fields(owner, name)]),
            }
        self._check_size(described)
        return described

    def _owner(self, name: str, service: str | None) -> str:
        owners = [
            owner
            for owner in self._catalog["types"]
            if name in self._catalog["types"][owner] or name in self._catalog["enums"][owner]
        ]
        if service is not None:
            owners = [owner for owner in owners if owner == service]
        if len(owners) == 1:
            return owners[0]
        hint = f"pass service= one of {owners}" if owners else "check the spelling"
        message = f"{len(owners)} services define a type or enum named {name!r}: {hint}"
        raise ToolError(message)

    def _fields(self, service: str, name: str) -> dict[str, str]:
        """Return a type's fields as {wire name: type}, its bases' fields after its own."""
        types = self._catalog["types"][service]
        fields: dict[str, str] = {}
        current: str | None = name
        while current is not None and current in types:
            for wire, kind in types[current]["fields"]:
                fields.setdefault(wire, kind)
            current = types[current]["base"]
        return fields

    def _type_view(self, service: str, name: str) -> JsonObject:
        entry: ObjectType = self._catalog["types"][service][name]
        view: JsonObject = {"base": entry["base"], "fields": self._fields(service, name)}
        subtypes = entry.get("subtypes")
        if subtypes:
            view["note"] = POLYMORPHIC_NOTE
            view["subtypes"] = {sub: _subtype_view(info) for sub, info in subtypes.items()}
        return view

    def _enums(self, service: str, field_sets: list[dict[str, str]]) -> JsonObject:
        enums = self._catalog["enums"][service]
        kinds = {element_type(kind) for fields in field_sets for kind in fields.values()}
        return {kind: _enum_view(enums[kind]) for kind in sorted(kinds) if kind in enums}

    def _check_size(self, value: object) -> None:
        size = len(json.dumps(value))
        if size > self._max_bytes:
            message = (
                f"the output would be {size} bytes, over MICROSOFT_ADS_MAX_RESPONSE_BYTES "
                f"({self._max_bytes}); narrow the filter or describe one type at a time"
            )
            raise ToolError(message)


def _subtype_view(info: Subtype) -> JsonObject:
    """Return the `Type` value to send for a subtype and the other spellings accepted."""
    documented = info["documented"]
    preferred = documented if documented is not None else info["values"][0]
    return {
        "Type": preferred,
        "sdk_aliases": [value for value in info["values"] if value != preferred],
        "documented": documented is not None,
    }


def _enum_view(entry: EnumType) -> JsonObject:
    view: JsonObject = {"values": entry["values"]}
    if entry.get("flags"):
        view["flags"] = "combine several values in one string, separated by ', '"
    return view
