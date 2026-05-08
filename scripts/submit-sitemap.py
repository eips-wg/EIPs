#!/usr/bin/env python3
"""Submit the production sitemap to configured search providers.

Configuration comes from environment variables:

- SITE_URL: required production site URL.
- SITEMAP_URL: optional, defaults to {SITE_URL.rstrip('/')}/sitemap.xml.
- GOOGLE_ACCESS_TOKEN: optional Google access token; enables Google submission.
- GOOGLE_SEARCH_CONSOLE_SITE_URL: optional, defaults to SITE_URL.
- INDEXNOW_KEY: optional IndexNow key; enables IndexNow when valid.
- INDEXNOW_ENDPOINT: optional, defaults to https://api.indexnow.org/indexnow.
- DRY_RUN: set to 1 to print intended requests without making external calls.
- SITEMAP_SUBMIT_STRICT: set to 1 to exit nonzero after enabled provider failures.
- HTTP_TIMEOUT_SECONDS: optional positive integer, defaults to 15.
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable


DEFAULT_INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_TIMEOUT_SECONDS = 15
INDEXNOW_KEY_PATTERN = re.compile(r"[A-Za-z0-9-]{8,128}")
RETRY_DELAY_SECONDS = 10
RESPONSE_EXCERPT_LENGTH = 300


class SubmissionError(Exception):
    """Raised when a provider submission attempt fails."""


@dataclass(frozen=True)
class Config:
    site_url: str
    sitemap_url: str
    google_access_token: str
    google_site_url: str
    indexnow_key: str
    indexnow_endpoint: str
    dry_run: bool
    strict: bool
    timeout_seconds: int


def actions_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def warning(title: str, message: str) -> None:
    print(
        f"::warning title={actions_escape(title)}::{actions_escape(message)}",
        file=sys.stderr,
    )


def parse_timeout_seconds() -> int:
    raw_timeout = os.environ.get("HTTP_TIMEOUT_SECONDS")
    if raw_timeout is None:
        return DEFAULT_TIMEOUT_SECONDS

    try:
        timeout_seconds = int(raw_timeout)
    except ValueError:
        warning(
            "Invalid HTTP timeout",
            f"HTTP_TIMEOUT_SECONDS must be a positive integer; using {DEFAULT_TIMEOUT_SECONDS}",
        )
        return DEFAULT_TIMEOUT_SECONDS

    if timeout_seconds <= 0:
        warning(
            "Invalid HTTP timeout",
            f"HTTP_TIMEOUT_SECONDS must be greater than 0; using {DEFAULT_TIMEOUT_SECONDS}",
        )
        return DEFAULT_TIMEOUT_SECONDS

    return timeout_seconds


def load_config() -> Config:
    site_url = os.environ.get("SITE_URL", "").strip()
    if not site_url:
        print("SITE_URL is required", file=sys.stderr)
        raise SystemExit(2)

    sitemap_url = os.environ.get("SITEMAP_URL", "").strip()
    if not sitemap_url:
        sitemap_url = f"{site_url.rstrip('/')}/sitemap.xml"

    google_site_url = os.environ.get("GOOGLE_SEARCH_CONSOLE_SITE_URL", "").strip()
    if not google_site_url:
        google_site_url = site_url

    return Config(
        site_url=site_url,
        sitemap_url=sitemap_url,
        google_access_token=os.environ.get("GOOGLE_ACCESS_TOKEN", "").strip(),
        google_site_url=google_site_url,
        indexnow_key=os.environ.get("INDEXNOW_KEY", "").strip(),
        indexnow_endpoint=os.environ.get(
            "INDEXNOW_ENDPOINT", DEFAULT_INDEXNOW_ENDPOINT
        ).strip()
        or DEFAULT_INDEXNOW_ENDPOINT,
        dry_run=os.environ.get("DRY_RUN", "").strip() == "1",
        strict=os.environ.get("SITEMAP_SUBMIT_STRICT", "").strip() == "1",
        timeout_seconds=parse_timeout_seconds(),
    )


def response_excerpt(body: bytes) -> str:
    text = body.decode("utf-8", errors="replace").strip()
    if len(text) <= RESPONSE_EXCERPT_LENGTH:
        return text
    return f"{text[:RESPONSE_EXCERPT_LENGTH]}..."


def redact(value: str, redactions: list[str]) -> str:
    redacted = value
    for secret in redactions:
        if secret:
            redacted = redacted.replace(secret, "***")
    return redacted


def request_failure_message(error: BaseException) -> str:
    if isinstance(error, urllib.error.HTTPError):
        body = response_excerpt(error.read())
        message = f"HTTP {error.code} {error.reason}"
        if body:
            message = f"{message}: {body}"
        return message

    if isinstance(error, urllib.error.URLError):
        if isinstance(error.reason, TimeoutError):
            return "request timed out"
        return f"URL error: {error.reason}"

    if isinstance(error, socket.timeout | TimeoutError):
        return "request timed out"

    return str(error)


def open_request(
    request: urllib.request.Request,
    timeout_seconds: int,
    success_statuses: Callable[[int], bool],
) -> None:
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = response.status
            body = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, TimeoutError) as error:
        raise SubmissionError(request_failure_message(error)) from error

    if not success_statuses(status):
        body_excerpt = response_excerpt(body)
        message = f"HTTP {status}"
        if body_excerpt:
            message = f"{message}: {body_excerpt}"
        raise SubmissionError(message)


def google_request_url(google_site_url: str, sitemap_url: str) -> str:
    encoded_site_url = urllib.parse.quote(google_site_url, safe="")
    encoded_sitemap_url = urllib.parse.quote(sitemap_url, safe="")
    return (
        "https://www.googleapis.com/webmasters/v3/sites/"
        f"{encoded_site_url}/sitemaps/{encoded_sitemap_url}"
    )


def submit_google(config: Config) -> None:
    request_url = google_request_url(config.google_site_url, config.sitemap_url)
    request = urllib.request.Request(
        request_url,
        headers={"Authorization": f"Bearer {config.google_access_token}"},
        method="PUT",
    )
    open_request(
        request,
        config.timeout_seconds,
        lambda status: 200 <= status <= 299,
    )


def indexnow_key_location(site_url: str, indexnow_key: str) -> str:
    return f"{site_url.rstrip('/')}/{indexnow_key}.txt"


def build_indexnow_payload(config: Config) -> dict[str, object]:
    host = urllib.parse.urlparse(config.site_url).netloc
    if not host:
        raise SubmissionError("SITE_URL must include a host for IndexNow submission")

    return {
        "host": host,
        "key": config.indexnow_key,
        "keyLocation": indexnow_key_location(config.site_url, config.indexnow_key),
        "urlList": [config.sitemap_url],
    }


def redacted_indexnow_payload(config: Config) -> dict[str, object]:
    payload = build_indexnow_payload(config)
    payload["key"] = "***"
    payload["keyLocation"] = indexnow_key_location(config.site_url, "***")
    return payload


def submit_indexnow(config: Config) -> None:
    payload = build_indexnow_payload(config)
    request = urllib.request.Request(
        config.indexnow_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    open_request(
        request,
        config.timeout_seconds,
        lambda status: status in {200, 202},
    )


def submit_with_retry(
    provider_name: str,
    submit: Callable[[], None],
    redactions: list[str] | None = None,
) -> bool:
    redactions = redactions or []
    last_error = ""

    for attempt in range(1, 3):
        try:
            submit()
            print(f"{provider_name} sitemap submission succeeded")
            return True
        except SubmissionError as error:
            last_error = redact(str(error), redactions)
            if attempt == 1:
                print(
                    f"{provider_name} sitemap submission failed; "
                    f"retrying in {RETRY_DELAY_SECONDS} seconds: {last_error}",
                    file=sys.stderr,
                )
                time.sleep(RETRY_DELAY_SECONDS)

    warning(
        "Sitemap submission failed",
        f"{provider_name} failed after retry: {last_error}",
    )
    return False


def dry_run(config: Config, indexnow_enabled: bool) -> None:
    if config.google_access_token:
        print("DRY RUN Google request:")
        print(f"  PUT {google_request_url(config.google_site_url, config.sitemap_url)}")
        print("  Authorization: Bearer ***")
    else:
        warning(
            "Sitemap provider skipped",
            "GOOGLE_ACCESS_TOKEN is not configured; skipping Google submission",
        )

    if indexnow_enabled:
        print("DRY RUN IndexNow request:")
        print(f"  POST {config.indexnow_endpoint}")
        print(
            json.dumps(
                redacted_indexnow_payload(config),
                indent=2,
                sort_keys=True,
            )
        )
    elif not config.indexnow_key:
        warning(
            "Sitemap provider skipped",
            "INDEXNOW_KEY is not configured; skipping IndexNow submission",
        )


def main() -> int:
    config = load_config()
    failures = 0

    print(f"SITE_URL={config.site_url}")
    print(f"SITEMAP_URL={config.sitemap_url}")

    indexnow_enabled = False
    if config.indexnow_key:
        if INDEXNOW_KEY_PATTERN.fullmatch(config.indexnow_key):
            indexnow_enabled = True
        else:
            warning(
                "Invalid IndexNow key",
                "INDEXNOW_KEY must match ^[A-Za-z0-9-]{8,128}$; "
                "skipping IndexNow submission",
            )

    if config.dry_run:
        dry_run(config, indexnow_enabled)
        return 0

    if config.google_access_token:
        if not submit_with_retry(
            "Google",
            lambda: submit_google(config),
            [config.google_access_token],
        ):
            failures += 1
    else:
        warning(
            "Sitemap provider skipped",
            "GOOGLE_ACCESS_TOKEN is not configured; skipping Google submission",
        )

    if indexnow_enabled:
        if not submit_with_retry(
            "IndexNow",
            lambda: submit_indexnow(config),
            [config.indexnow_key],
        ):
            failures += 1
    elif not config.indexnow_key:
        warning(
            "Sitemap provider skipped",
            "INDEXNOW_KEY is not configured; skipping IndexNow submission",
        )

    if failures and config.strict:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
