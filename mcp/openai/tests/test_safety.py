"""The path and header guards that keep the API key on the configured host."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from openai_mcp.safety import check_headers, check_path

UNSAFE_PATHS = [
    "models",
    "https://evil.test/v1/models",
    "//evil.test/models",
    "/%2Fevil.test/models",
    "/files/../../admin",
    "/files/%2e%2e/admin",
    "/models?limit=1",
    "/models#top",
    "/models\\x",
    "/redirect/https://evil.test",
]


@pytest.mark.parametrize("path", ["/models", "/files/file-abc/content", "/v1..beta/x"])
def test_plain_paths_pass(path: str) -> None:
    assert check_path(path) == path


@pytest.mark.parametrize("path", UNSAFE_PATHS)
def test_unsafe_paths_are_refused(path: str) -> None:
    with pytest.raises(ToolError):
        check_path(path)


def test_ordinary_headers_pass() -> None:
    assert check_headers({"OpenAI-Beta": "assistants=v2"}) == {"OpenAI-Beta": "assistants=v2"}
    assert check_headers(None) == {}


@pytest.mark.parametrize(
    "name", ["Authorization", "authorization", "Host", "OpenAI-Organization", "OpenAI-Project"]
)
def test_protected_headers_are_refused(name: str) -> None:
    with pytest.raises(ToolError, match="cannot be overridden"):
        check_headers({name: "x"})
