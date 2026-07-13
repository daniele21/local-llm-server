"""
downloader.py — model download with resume support and inline progress bar.

No external dependencies (uses stdlib urllib only).
"""
from __future__ import annotations

import logging
import sys
import urllib.request
from pathlib import Path

logger = logging.getLogger("local-llm.downloader")


def download_huggingface_snapshot(model_id: str) -> Path:
    """Download a Hugging Face repository through the optional HF cache."""
    try:
        from huggingface_hub import snapshot_download
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Hugging Face downloads require the vision/MLX dependencies. "
            'Install with: pip install "local-llm-server[vision]"'
        ) from exc
    return Path(snapshot_download(repo_id=model_id))


def is_huggingface_snapshot_cached(model_id: str) -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache
    except ModuleNotFoundError:
        return False
    cached = try_to_load_from_cache(model_id, "config.json")
    return isinstance(cached, str)


def ensure_model(url: str, dest: Path, *, resume: bool = True, no_download: bool = False) -> None:
    """
    Ensure the model file exists at *dest*.

    If it is already present, this is a no-op.
    If it is absent and *no_download* is True, raises FileNotFoundError.
    Otherwise downloads from *url* with resume support.
    """
    if dest.exists():
        return

    if no_download:
        raise FileNotFoundError(
            f"Model not found at {dest} and --no-download is set. "
            "Run 'local-llm download <model>' first."
        )

    if not url:
        raise ValueError(
            f"Model not found at {dest} and no download URL is configured for this model."
        )

    download_model(url=url, dest=dest, resume=resume)


def download_model(url: str, dest: Path, *, resume: bool = True, max_retries: int = 3) -> None:
    """
    Download *url* to *dest* with resume, atomic write, and a progress bar.

    Uses a temporary *.part* file and renames atomically on success.
    Retries up to *max_retries* times on network errors.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, max_retries + 1):
        try:
            _download_attempt(url=url, dest=dest, part=part, resume=resume)
            return
        except Exception as exc:
            if attempt == max_retries:
                raise RuntimeError(f"Download failed after {max_retries} attempts: {exc}") from exc
            logger.warning("Download attempt %d/%d failed: %s — retrying…", attempt, max_retries, exc)


def _download_attempt(url: str, dest: Path, part: Path, resume: bool) -> None:
    resume_size = part.stat().st_size if (resume and part.exists()) else 0

    req = urllib.request.Request(url, headers={"User-Agent": "local-llm-server/0.1"})
    if resume_size > 0:
        req.add_header("Range", f"bytes={resume_size}-")
        logger.info("Resuming download from %.1f MB", resume_size / 1024 / 1024)

    with urllib.request.urlopen(req, timeout=3600) as response:
        content_length = int(response.headers.get("Content-Length") or 0)
        total = content_length + resume_size

        downloaded = resume_size
        mode = "ab" if resume_size > 0 else "wb"
        chunk_size = 1024 * 1024  # 1 MB

        logger.info("Downloading %s → %s (%.1f GB)", url, dest, total / 1024 / 1024 / 1024)

        with open(part, mode) as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                _print_progress(downloaded, total)

    # Final newline after progress bar
    print(flush=True)

    # Validate size if server reported Content-Length
    if total > 0 and part.stat().st_size < total:
        raise RuntimeError(f"Incomplete download: got {part.stat().st_size} bytes, expected {total}")

    # Atomic rename
    part.rename(dest)
    logger.info("Model saved to %s", dest)


def _print_progress(downloaded: int, total: int) -> None:
    if total <= 0:
        mb = downloaded / 1024 / 1024
        print(f"\r  Downloading… {mb:.0f} MB", end="", flush=True)
        return

    pct = downloaded / total
    bar_width = 30
    filled = int(bar_width * pct)
    bar = "█" * filled + "░" * (bar_width - filled)
    dl_gb = downloaded / 1024 / 1024 / 1024
    total_gb = total / 1024 / 1024 / 1024
    print(
        f"\r  [{bar}] {pct * 100:.1f}% — {dl_gb:.2f}/{total_gb:.2f} GB",
        end="",
        file=sys.stderr,
        flush=True,
    )
