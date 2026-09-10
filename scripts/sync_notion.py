#!/usr/bin/env python3
"""Publish the local MasterKva status to the Notion Projects data source."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from urllib.error import HTTPError
from urllib.request import Request, urlopen

NOTION_VERSION = "2025-09-03"
DATA_SOURCE_ID = "3d6df911-2b98-8043-a76f-000b451777e7"
PROJECT_NAME = "MasterKva"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def notion_request(method: str, path: str, payload: dict | None = None) -> dict:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN is not set")

    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"https://api.notion.com/v1/{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API {error.code}: {details}") from error


def find_project() -> dict | None:
    result = notion_request(
        "POST",
        f"data_sources/{DATA_SOURCE_ID}/query",
        {"filter": {"property": "Name", "title": {"equals": PROJECT_NAME}}},
    )
    pages = result.get("results", [])
    return pages[0] if pages else None


def main() -> int:
    branch = git("branch", "--show-current")
    commit = git("rev-parse", "--short", "HEAD")
    project = find_project()
    if project is None:
        raise RuntimeError(
            f"Notion project {PROJECT_NAME!r} was not found in data source {DATA_SOURCE_ID}"
        )

    notion_request(
        "PATCH",
        f"pages/{project['id']}",
        {
            "properties": {
                "Stage": {"select": {"name": "In Progress"}},
                "Timeline": {"date": {"start": date.today().isoformat()}},
            }
        },
    )
    print(f"Synced {PROJECT_NAME}: branch={branch}, commit={commit}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"sync_notion: {error}", file=sys.stderr)
        raise SystemExit(1)
