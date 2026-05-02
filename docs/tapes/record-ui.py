"""Record the bundled dashboard as a GIF.

Drives a Playwright Chromium against a running `kb-arena demo` instance.
Captures video, then converts to a palette-optimised GIF via ffmpeg.

Usage (with the demo running on http://127.0.0.1:9911):

    .venv/bin/python docs/tapes/record-ui.py
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:9911"
OUT_DIR = Path(__file__).resolve().parents[1]  # docs/
TMP_DIR = Path("/tmp/kbarena-ui-recording")


async def main(target_gif: str, viewport_width: int = 1400, viewport_height: int = 850) -> None:
    # Recording surface — gets stitched into a single GIF at the end.
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            record_video_dir=str(TMP_DIR),
            record_video_size={"width": viewport_width, "height": viewport_height},
        )
        page = await context.new_page()

        # 1. Benchmark page — the main hero.
        await page.goto(f"{BASE}/benchmark/", wait_until="networkidle")
        await page.wait_for_timeout(2200)

        # 2. Leaderboard — the new public surface.
        await page.goto(f"{BASE}/leaderboard/", wait_until="networkidle")
        await page.wait_for_timeout(2200)

        # 3. Retriever Lab — flagship v0.5.0 feature.
        await page.goto(f"{BASE}/retriever-lab/", wait_until="networkidle")
        await page.wait_for_timeout(2500)

        # 4. Graph viewer — keeps a small motion beat at the end.
        await page.goto(f"{BASE}/graph/", wait_until="networkidle")
        await page.wait_for_timeout(2500)

        await context.close()
        await browser.close()

    # Locate the .webm Playwright produced.
    webm_files = sorted(TMP_DIR.glob("*.webm"))
    if not webm_files:
        print("ERROR: no .webm captured", file=sys.stderr)
        sys.exit(1)
    webm = webm_files[-1]

    # Two-pass palette generation for a tight GIF.
    palette = TMP_DIR / "palette.png"
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(webm),
            "-vf",
            "fps=12,scale=1100:-1:flags=lanczos,palettegen=stats_mode=diff",
            str(palette),
        ]
    )
    out = OUT_DIR / target_gif
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(webm),
            "-i",
            str(palette),
            "-lavfi",
            "fps=12,scale=1100:-1:flags=lanczos[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=4",
            str(out),
        ]
    )
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "demo-ui-walkthrough.gif"
    asyncio.run(main(target))
