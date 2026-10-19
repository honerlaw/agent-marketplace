"""The scrub: credential literals, paging URLs and access_token fields."""

import hashlib
import hmac
import json

from meta_ads_mcp.scrub import REDACTED, Scrubber, appsecret_proof
from tests.conftest import APP_SECRET, PROOF, SECRETS, TOKEN


def test_the_proof_is_hmac_keyed_by_the_app_secret() -> None:
    expected = hmac.new(b"secret", b"token", hashlib.sha256).hexdigest()
    assert appsecret_proof("token", "secret") == expected


def test_literals_are_replaced_in_text_longest_first() -> None:
    scrubber = Scrubber([TOKEN, APP_SECRET, PROOF, ""])
    text = f"a {TOKEN} b {PROOF} c {APP_SECRET}|{APP_SECRET}"
    assert scrubber.text(text) == f"a {REDACTED} b {REDACTED} c {REDACTED}|{REDACTED}"


def test_paging_urls_lose_meta_credentials_and_keep_the_rest() -> None:
    scrubber = Scrubber(SECRETS)
    url = "https://graph.facebook.com/v26.0/x?access_token=OTHER&limit=2&APPSECRET_PROOF=Q&after=c"
    value = {"paging": {"next": url, "cursors": {"after": "c"}, "nested": [url]}}
    expected = "https://graph.facebook.com/v26.0/x?limit=2&after=c"
    assert scrubber.value(value) == {
        "paging": {"next": expected, "cursors": {"after": "c"}, "nested": [expected]}
    }


def test_strings_outside_paging_are_not_rewritten() -> None:
    link = "https://example.com/landing?access_token=campaign-tag"
    value = {"creative": {"link": link}, "paging": {"next": "not a url", "x": 1}}
    assert Scrubber(SECRETS).value(value) == value


def test_access_token_fields_are_redacted_at_any_depth() -> None:
    value = {"data": [{"id": "1", "Access_Token": "page-token"}], "access_token": None}
    assert Scrubber(SECRETS).value(value) == {
        "data": [{"id": "1", "Access_Token": REDACTED}],
        "access_token": REDACTED,
    }


def test_secrets_inside_json_strings_are_replaced() -> None:
    nested = json.dumps({"echo": TOKEN})
    scrubbed = Scrubber(SECRETS).value({"body": nested, "n": 3, "ok": True})
    assert scrubbed == {"body": json.dumps({"echo": REDACTED}), "n": 3, "ok": True}
