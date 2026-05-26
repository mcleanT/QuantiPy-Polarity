"""Real `quantipy download-demo` command (Phase 6).

Downloads the demo_bundle.zip from the latest GitHub Release of
mcleanT/QuantiPy-Polarity, extracts it to ~/.cache/quantipy/demo/
(or --output dir), verifies SHA-256, and prints usage instructions.

Network-failure handling:
  - Any network error → friendly fallback message pointing to demo/ in the repo.
  - Missing asset → friendly message with manual Release URL.
  - SHA-256 mismatch → extracted dir deleted, ClickException raised.

Requires the `requests` + `tqdm` packages (both in the `pipeline` extra).
"""

from __future__ import annotations

import hashlib
import io
import shutil
import tempfile
import zipfile
from pathlib import Path

import click

from quantipy_polarity.cli import main

_REPO = "mcleanT/QuantiPy-Polarity"
_ASSET_NAME = "demo_bundle.zip"
_DEFAULT_CACHE = Path.home() / ".cache" / "quantipy" / "demo"
_RELEASES_API = f"https://api.github.com/repos/{_REPO}/releases/latest"
_RELEASES_URL = f"https://github.com/{_REPO}/releases/latest"
_CHUNK = 65_536  # 64 KB


def _fallback_msg(output_dir: Path) -> str:
    return (
        f"\nAlternatively, clone the repo and use the committed demo files directly:\n"
        f"  git clone https://github.com/{_REPO}\n"
        f"  quantipy run --config QuantiPy-Polarity/demo/config.yaml "
        f"--output ./demo_results"
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_and_extract(url: str, output_dir: Path) -> None:
    """Stream-download zip from url and extract to output_dir."""
    try:
        import requests
        from tqdm import tqdm
    except ImportError as exc:
        raise click.ClickException(
            f"Missing dependency: {exc.name}. "
            "Install it with: pip install 'quantipy-polarity[pipeline]'"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0)) or None
            with open(tmp_path, "wb") as f:
                with tqdm(
                    total=total, unit="B", unit_scale=True,
                    desc="Downloading demo_bundle.zip", leave=False,
                ) as bar:
                    for chunk in resp.iter_content(chunk_size=_CHUNK):
                        f.write(chunk)
                        bar.update(len(chunk))

        with zipfile.ZipFile(tmp_path) as zf:
            zf.extractall(output_dir)

        # Verify SHA-256 via bundled SHA256SUMS.txt (if present)
        sums_path = output_dir / "SHA256SUMS.txt"
        if sums_path.exists():
            lines = sums_path.read_text(encoding="utf-8").strip().splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) == 2:
                    expected_hash, fname = parts
                    fpath = output_dir / fname
                    if fpath.exists():
                        actual = _sha256_file(fpath)
                        if actual != expected_hash:
                            shutil.rmtree(output_dir)
                            raise click.ClickException(
                                f"SHA-256 mismatch for {fname}. "
                                "The download may be corrupt. Please retry."
                            )
    finally:
        tmp_path.unlink(missing_ok=True)


@main.command("download-demo")
@click.option(
    "--output", "-o",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    help=f"Destination directory. Defaults to {_DEFAULT_CACHE}.",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    default=False,
    help="Re-download even if demo already exists in destination.",
)
def download_demo_cmd(output: Path | None, force: bool) -> None:
    """Pull demo bundle from latest GitHub Release."""
    output_dir = output or _DEFAULT_CACHE

    if output_dir.exists() and not force:
        config = output_dir / "config.yaml"
        if config.exists():
            click.echo(f"Demo already downloaded to {output_dir}.")
            click.echo(
                f"Run: quantipy run --config {config} --output ./demo_results\n"
                "Use --force to re-download."
            )
            return

    try:
        import requests
    except ImportError as exc:
        raise click.ClickException(
            "requests is required for download-demo. "
            "Install with: pip install 'quantipy-polarity[pipeline]'"
        ) from exc

    click.echo(f"Fetching release info from {_RELEASES_API} ...")
    try:
        resp = requests.get(_RELEASES_API, timeout=10)
        resp.raise_for_status()
        release = resp.json()
    except Exception as exc:  # noqa: BLE001
        click.echo(
            f"Could not reach GitHub Releases API: {exc}\n"
            f"Manual download: {_RELEASES_URL}"
            + _fallback_msg(output_dir),
            err=True,
        )
        raise click.Abort() from None

    assets = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}
    if _ASSET_NAME not in assets:
        click.echo(
            f"Release {release.get('tag_name', '?')} does not contain {_ASSET_NAME!r}.\n"
            f"Check {_RELEASES_URL} for available assets."
            + _fallback_msg(output_dir),
            err=True,
        )
        raise click.Abort() from None

    url = assets[_ASSET_NAME]
    click.echo(f"Downloading {_ASSET_NAME} → {output_dir} ...")

    try:
        _download_and_extract(url, output_dir)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        click.echo(
            f"Download failed: {exc}" + _fallback_msg(output_dir),
            err=True,
        )
        raise click.Abort() from None

    config = output_dir / "config.yaml"
    click.echo(f"\nDemo ready in {output_dir}")
    if config.exists():
        click.echo(
            f"Run: quantipy run --config {config} --output ./demo_results"
        )
