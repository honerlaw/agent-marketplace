"""What the configured token is and when it lapses, without ever returning the token."""

from datetime import UTC, datetime

from meta_ads_mcp.api import JsonObject, MetaAdsApi

REPORTED_FIELDS = ("is_valid", "type", "app_id", "scopes", "granular_scopes", "error")
TIMESTAMP_FIELDS = ("expires_at", "data_access_expires_at")
UNAVAILABLE: JsonObject = {
    "available": False,
    "reason": "set META_APP_ID and META_APP_SECRET to inspect the token",
}


async def token_status(api: MetaAdsApi, *, app_configured: bool) -> JsonObject:
    """Return `debug_token`'s facts about the token: validity, type, scopes and expiry.

    A timestamp of 0 means the token (or its data access) never expires.
    """
    if not app_configured:
        return dict(UNAVAILABLE)
    response = await api.debug_token()
    payload = response.get("json")
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return {"available": True, "status": response.get("status"), "response": payload}
    status: JsonObject = {"available": True}
    status.update({name: data[name] for name in REPORTED_FIELDS if name in data})
    status.update({name: _when(data[name]) for name in TIMESTAMP_FIELDS if name in data})
    return status


def _when(value: object) -> object:
    if value == 0:
        return "never"
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=UTC).isoformat()
    return value
