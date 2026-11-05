"""What the API client and the downloader share: the user agent and a capped body read."""

from collections.abc import Callable

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

JsonObject = dict[str, object]
USER_AGENT = "microsoft-ads-mcp/0.1.0"


async def read_bounded(
    response: httpx2.Response, limit: int, too_large: Callable[[], ToolError]
) -> bytes:
    """Read a streamed body, giving up as soon as it passes `limit` bytes."""
    chunks: list[bytes] = []
    size = 0
    async for chunk in response.aiter_bytes():
        size += len(chunk)
        if size > limit:
            raise too_large()
        chunks.append(chunk)
    return b"".join(chunks)
