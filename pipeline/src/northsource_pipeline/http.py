"""HTTP download helper. Raw files are never overwritten."""

from __future__ import annotations

import logging
from pathlib import Path

import requests

log = logging.getLogger(__name__)

USER_AGENT = "northsource-pipeline/0.1 (+https://github.com/aex-partners/northsource)"


def download(url: str, dest: Path, *, timeout: int = 120) -> Path:
    """Download url to dest unless dest already exists. Writes to a .part file first."""
    if dest.exists():
        log.info("skip (exists) %s", dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    log.info("GET %s -> %s", url, dest)
    with requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            f.writelines(r.iter_content(chunk_size=1 << 20))
    tmp.replace(dest)
    return dest
