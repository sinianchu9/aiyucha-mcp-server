"""Validate review metadata and package public plugin files without any credentials."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission"
INCLUDED = ("plugin.json", "mcp.json", "assets/aiyucha-logo.svg")


def build(target: Path) -> None:
    plugin = json.loads((SUBMISSION / "plugin.json").read_text(encoding="utf-8"))
    mcp = json.loads((SUBMISSION / "mcp.json").read_text(encoding="utf-8"))
    cases = plugin["extensions"]["com.openai"]["review"]["test_cases"]
    assert len(cases["positive"]) == 5
    assert len(cases["negative"]) == 3
    assert mcp["mcpServers"]["aiyucha-domain-intelligence"]["url"] == "https://aiyucha.com/mcp"
    for relative in INCLUDED:
        assert (SUBMISSION / relative).is_file(), relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, mode="w", compression=ZIP_DEFLATED) as archive:
        for relative in INCLUDED:
            archive.write(SUBMISSION / relative, arcname=relative)


if __name__ == "__main__":
    build(ROOT / "submission" / "aiyucha-domain-intelligence-v1.zip")
