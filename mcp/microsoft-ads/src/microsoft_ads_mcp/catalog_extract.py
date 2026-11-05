"""Reads the msads SDK's generated REST client, as source text, into catalog entries.

The SDK (`openapi_client/`, made by OpenAPI Generator) is parsed with `ast` and never
imported or run. Every shape this module does not recognise raises `CatalogError`
instead of being skipped: a silently skipped operation or field is how a catalog goes
quietly incomplete.
"""

import ast
from collections.abc import Iterator, Mapping
from typing import NotRequired, TypedDict

API_VERSION = "v13"
SERIALIZER_PREFIX = "_"
SERIALIZER_SUFFIX = "_serialize"
REQUEST_SUFFIX = "Request"
RESPONSE_SUFFIX = "Response"
HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
SCALARS = {
    "StrictStr": "string",
    "str": "string",
    "StrictInt": "integer",
    "StrictFloat": "number",
    "StrictBool": "boolean",
    "datetime": "datetime",
}
FLAG_NAMES_FUNCTION = "_to_str"
DISCRIMINATOR_FUNCTION = "from_dict"
DISCRIMINATOR_VARIABLE = "type"

Operation = dict[str, str]


class Subtype(TypedDict):
    """One subclass of a polymorphic type and the `Type` values that select it."""

    values: list[str]
    documented: str | None


class ObjectType(TypedDict):
    """A model class: its base, its fields as [wire name, type], and any subclasses."""

    base: str | None
    fields: list[list[str]]
    discriminator: NotRequired[dict[str, str]]
    subtypes: NotRequired[dict[str, Subtype]]


class EnumType(TypedDict):
    """An enum's wire values; `flags` marks one whose values combine."""

    values: list[str]
    flags: NotRequired[bool]


class CatalogError(ValueError):
    """Raised when the SDK source has a shape the catalog builder does not understand."""


def extract_operations(service: str, source: str) -> list[Operation]:
    """Return one entry per REST operation in a generated `*_service_api.py` module."""
    methods = {node.name: node for node in _methods(ast.parse(source))}
    return [
        _operation(service, methods[_public_name(name)], node)
        for name, node in methods.items()
        if name.startswith(SERIALIZER_PREFIX) and name.endswith(SERIALIZER_SUFFIX)
    ]


def extract_models(source: str) -> tuple[dict[str, ObjectType], dict[str, EnumType]]:
    """Return the object types and enums defined by one generated model module."""
    types: dict[str, ObjectType] = {}
    enums: dict[str, EnumType] = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [ast.unparse(base) for base in node.bases]
        if "Enum" in bases:
            enums[node.name] = {"values": _enum_values(node)}
        elif "Flag" in bases:
            enums[node.name] = {"values": _flag_values(node), "flags": True}
        else:
            types[node.name] = _object_type(node, bases)
    return types, enums


def _methods(tree: ast.Module) -> Iterator[ast.FunctionDef]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            yield from (item for item in node.body if isinstance(item, ast.FunctionDef))


def _public_name(serializer: str) -> str:
    return serializer.removeprefix(SERIALIZER_PREFIX).removesuffix(SERIALIZER_SUFFIX)


def _operation(service: str, public: ast.FunctionDef, serializer: ast.FunctionDef) -> Operation:
    request = _request_type(public)
    response = _name_of(public.returns, f"{public.name} return type")
    method = _literal_keyword(serializer, "method")
    path = _literal_keyword(serializer, "resource_path")
    if method not in HTTP_METHODS or not path.startswith(f"/{service}/{API_VERSION}/"):
        message = f"{public.name}: unexpected {method} {path} for service {service}"
        raise CatalogError(message)
    return {
        "name": _operation_name(public.name, request, response),
        "service": service,
        "method": method,
        "path": path,
        "request": request,
        "response": response,
    }


def _operation_name(method: str, request: str, response: str) -> str:
    """Microsoft's operation name: the request model's name, else the response model's."""
    for model, suffix in ((request, REQUEST_SUFFIX), (response, RESPONSE_SUFFIX)):
        if model.endswith(suffix):
            return model.removesuffix(suffix)
    message = f"{method}: neither {request!r} nor {response!r} names the operation"
    raise CatalogError(message)


def _request_type(public: ast.FunctionDef) -> str:
    """Return the request model's name, or "object" for an operation taking a bare dict."""
    parameters = public.args.args[1:]
    if not parameters or parameters[0].annotation is None:
        message = f"{public.name}: no annotated request parameter"
        raise CatalogError(message)
    annotation = parameters[0].annotation
    return annotation.id if isinstance(annotation, ast.Name) else "object"


def _name_of(node: ast.expr | None, what: str) -> str:
    if not isinstance(node, ast.Name):
        message = f"{what} is not a plain name"
        raise CatalogError(message)
    return node.id


def _literal_keyword(function: ast.FunctionDef, keyword: str) -> str:
    values = [
        node.value.value
        for node in ast.walk(function)
        if isinstance(node, ast.keyword)
        and node.arg == keyword
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(values) != 1:
        message = f"{function.name}: expected one literal {keyword}=, found {len(values)}"
        raise CatalogError(message)
    return values[0]


def _enum_values(node: ast.ClassDef) -> list[str]:
    values = [
        item.value.value
        for item in node.body
        if isinstance(item, ast.Assign)
        and isinstance(item.value, ast.Constant)
        and isinstance(item.value.value, str)
    ]
    return list(dict.fromkeys(values))


def _flag_values(node: ast.ClassDef) -> list[str]:
    """Return a flags enum's wire names, from the `_NAME_MAPPING` dict in `_to_str`."""
    mappings = [
        mapping
        for item in node.body
        if isinstance(item, ast.FunctionDef) and item.name == FLAG_NAMES_FUNCTION
        for mapping in ast.walk(item)
        if isinstance(mapping, ast.Dict)
    ]
    if len(mappings) != 1:
        message = f"{node.name}: expected one name mapping in {FLAG_NAMES_FUNCTION}"
        raise CatalogError(message)
    return [_string(value, node.name) for value in mappings[0].values]


def _string(node: ast.expr, owner: str) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    message = f"{owner}: expected a string literal, got {ast.unparse(node)}"
    raise CatalogError(message)


def _object_type(node: ast.ClassDef, bases: list[str]) -> ObjectType:
    parents = [base for base in bases if base != "BaseModel"]
    entry: ObjectType = {
        "base": parents[0] if parents else None,
        "fields": [
            _field(node.name, item)
            for item in node.body
            if isinstance(item, ast.AnnAssign) and not _is_class_var(item)
        ],
    }
    discriminator = _discriminator(node)
    if discriminator:
        entry["discriminator"] = discriminator
    return entry


def _is_class_var(item: ast.AnnAssign) -> bool:
    return ast.unparse(item.annotation).startswith("ClassVar")


def _field(owner: str, item: ast.AnnAssign) -> list[str]:
    aliases = [
        keyword.value
        for keyword in (item.value.keywords if isinstance(item.value, ast.Call) else [])
        if keyword.arg == "alias"
    ]
    if len(aliases) != 1:
        message = f"{owner}.{ast.unparse(item.target)}: field has no alias="
        raise CatalogError(message)
    return [_string(aliases[0], owner), type_text(item.annotation, owner)]


def type_text(node: ast.expr, owner: str) -> str:
    """Render an annotation as the catalog writes it: "string", "list[Campaign]", ..."""
    if isinstance(node, ast.Name):
        return SCALARS.get(node.id, node.id)
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        # A map: the SDK writes Dict[...], and once StrictDict[str, Str] (sic).
        if node.value.id.endswith("Dict"):
            return "object"
        inner = type_text(node.slice, owner)
        wrappers = {"Optional": inner, "List": f"list[{inner}]"}
        if node.value.id in wrappers:
            return wrappers[node.value.id]
    message = f"{owner}: unsupported annotation {ast.unparse(node)}"
    raise CatalogError(message)


def _discriminator(node: ast.ClassDef) -> dict[str, str]:
    """Map each `Type` value the base's `from_dict` dispatches on to the subclass it picks."""
    functions = [
        item
        for item in node.body
        if isinstance(item, ast.FunctionDef) and item.name == DISCRIMINATOR_FUNCTION
    ]
    return {
        value: subclass
        for function in functions
        for value, subclass in _dispatch_branches(function)
    }


def _dispatch_branches(function: ast.FunctionDef) -> Iterator[tuple[str, str]]:
    for node in ast.walk(function):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            if not _compares_type(node.test):
                continue
            imports = [item for item in node.body if isinstance(item, ast.ImportFrom)]
            subclass = imports[0].names[0].name if imports else None
            if subclass is None:
                message = f"{function.name}: a Type branch imports no subclass"
                raise CatalogError(message)
            yield _string(node.test.comparators[0], function.name), subclass


def _compares_type(test: ast.Compare) -> bool:
    return (
        isinstance(test.left, ast.Name)
        and test.left.id == DISCRIMINATOR_VARIABLE
        and len(test.comparators) == 1
    )


def documented_subtypes(
    types: Mapping[str, ObjectType], enums: Mapping[str, EnumType], base: str
) -> dict[str, Subtype]:
    """Group a base's discriminator values by subclass and pick the documented spelling.

    The documented value is the one listed in the subclass's own `Type` enum (Microsoft's
    REST examples send `"Type": "AppInstall"`, the `AdType` value); any other value the SDK
    also accepts is an alias. When the subclass's `Type` is not an enum, none is marked.
    """
    grouped: dict[str, list[str]] = {}
    for value, subclass in types[base].get("discriminator", {}).items():
        grouped.setdefault(subclass, []).append(value)
    return {
        subclass: _subtype(values, _type_enum(types, enums, subclass))
        for subclass, values in grouped.items()
    }


def _type_enum(
    types: Mapping[str, ObjectType], enums: Mapping[str, EnumType], name: str
) -> list[str]:
    fields = types[name]["fields"] if name in types else []
    kinds = [kind for wire, kind in fields if wire == "Type" and kind in enums]
    return enums[kinds[0]]["values"] if kinds else []


def _subtype(values: list[str], enum_values: list[str]) -> Subtype:
    documented = [value for value in values if value in enum_values]
    return {"values": values, "documented": documented[0] if documented else None}
