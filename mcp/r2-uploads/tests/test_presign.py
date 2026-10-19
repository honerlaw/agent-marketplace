"""Signature Version 4 query signing, checked against AWS's published example."""

from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

from r2_uploads_mcp.presign import Credentials, S3Request, presign

# "Example: A presigned URL" in AWS's "Authenticating Requests: Using Query Parameters"
# (Signature Version 4) documentation.
AWS_CREDENTIALS = Credentials(
    access_key_id="AKIAIOSFODNN7EXAMPLE",
    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",  # noqa: S106 - AWS's example
    region="us-east-1",
)
AWS_URL = (
    "https://examplebucket.s3.amazonaws.com/test.txt"
    "?X-Amz-Algorithm=AWS4-HMAC-SHA256"
    "&X-Amz-Credential=AKIAIOSFODNN7EXAMPLE%2F20130524%2Fus-east-1%2Fs3%2Faws4_request"
    "&X-Amz-Date=20130524T000000Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host"
    "&X-Amz-Signature=aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404"
)
NOW = datetime(2013, 5, 24, tzinfo=UTC)


def test_matches_the_aws_documented_example() -> None:
    request = S3Request("GET", "examplebucket.s3.amazonaws.com", "/test.txt")
    assert presign(request, AWS_CREDENTIALS, NOW, 86400) == AWS_URL


def test_extra_query_parameters_are_encoded_and_sorted_into_the_signature() -> None:
    request = S3Request("GET", "h.example", "/bucket", {"prefix": "a b/c", "list-type": "2"})
    url = urlsplit(presign(request, AWS_CREDENTIALS, NOW, 60))
    names = [pair.split("=")[0] for pair in url.query.split("&")]
    assert names[:2] == ["X-Amz-Algorithm", "X-Amz-Credential"]
    assert names[-3:] == ["list-type", "prefix", "X-Amz-Signature"]
    assert "prefix=a%20b%2Fc" in url.query
    assert parse_qs(url.query)["X-Amz-Expires"] == ["60"]


def test_path_keeps_slashes_and_encodes_everything_else() -> None:
    request = S3Request("PUT", "h.example", "/bucket/2026-10-19/ab/my file+1.mp4")
    url = urlsplit(presign(request, AWS_CREDENTIALS, NOW, 60))
    assert url.path == "/bucket/2026-10-19/ab/my%20file%2B1.mp4"


def test_the_secret_is_not_in_the_credentials_repr() -> None:
    assert "EXAMPLEKEY" not in repr(AWS_CREDENTIALS)
