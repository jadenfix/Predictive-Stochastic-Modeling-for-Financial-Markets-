#!/usr/bin/env python3
"""Render the checked temporal-alignment/MSPE demonstration.

The media uses the same hand-calculable fixture as test_forecast_evaluation.R.
It intentionally makes no claim about regime accuracy or forecast performance.
"""

from __future__ import annotations

import hashlib
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 960, 540
FPS = 10
BASE_COMMIT = "bc503584d827e19004501a219edfdb92db902bf1"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "demo"
BG = "#0b1020"
PANEL = "#151d33"
TEXT = "#f2f5ff"
MUTED = "#aeb9d6"
RED = "#ff6b6b"
GREEN = "#55d68b"
BLUE = "#65a7ff"
YELLOW = "#ffd166"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    return image, ImageDraw.Draw(image)


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, size: int, color: str = TEXT, bold: bool = False) -> None:
    face = font(size, bold)
    box = draw.textbbox((0, 0), text, font=face)
    draw.text(((WIDTH - (box[2] - box[0])) / 2, y), text, font=face, fill=color)


def footer(draw: ImageDraw.ImageDraw, helper_hash: str) -> None:
    draw.line((42, 490, WIDTH - 42, 490), fill="#2a3555", width=2)
    draw.text(
        (48, 500),
        f"Archived source: main@{BASE_COMMIT[:12]}  |  checked helper sha256:{helper_hash[:12]}",
        font=font(15),
        fill=MUTED,
    )


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str) -> None:
    draw.line((*start, *end), fill=color, width=8)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 18
    spread = 0.65
    points = [
        end,
        (end[0] - length * math.cos(angle - spread), end[1] - length * math.sin(angle - spread)),
        (end[0] - length * math.cos(angle + spread), end[1] - length * math.sin(angle + spread)),
    ]
    draw.polygon(points, fill=color)


def timeline(draw: ImageDraw.ImageDraw) -> dict[str, int]:
    months = ["Jan", "Feb", "Mar", "Apr"]
    xs = [195, 385, 575, 765]
    draw.line((xs[0], 275, xs[-1], 275), fill="#516080", width=4)
    for month, x in zip(months, xs):
        draw.ellipse((x - 12, 263, x + 12, 287), fill=BLUE)
        draw.text((x - 25, 300), month, font=font(20, True), fill=TEXT)
    return dict(zip(months, xs))


def scene_title(helper_hash: str) -> Image.Image:
    image, draw = canvas()
    centered(draw, "Checked evaluation mechanics", 120, 42, bold=True)
    centered(draw, "Forward dates + true mean squared prediction error", 185, 25, color=BLUE)
    draw.rounded_rectangle((175, 270, 785, 375), radius=22, fill=PANEL, outline="#334269", width=2)
    centered(draw, "Synthetic, hand-calculable fixture", 295, 25, color=TEXT, bold=True)
    centered(draw, "No market-performance claim", 338, 22, color=YELLOW)
    footer(draw, helper_hash)
    return image


def scene_backward(helper_hash: str) -> Image.Image:
    image, draw = canvas()
    centered(draw, "Archived horizon direction", 42, 35, bold=True)
    centered(draw, "lag(target, 1) pairs a later predictor with an earlier target", 92, 22, color=MUTED)
    xs = timeline(draw)
    draw.text((xs["Feb"] - 82, 185), "predictor: Feb", font=font(20, True), fill=TEXT)
    draw.text((xs["Jan"] - 70, 360), "target: Jan", font=font(20, True), fill=TEXT)
    arrow(draw, (xs["Feb"], 245), (xs["Jan"], 245), RED)
    centered(draw, "Backward pairing: this is not a forward forecast", 420, 24, color=RED, bold=True)
    footer(draw, helper_hash)
    return image


def scene_forward(helper_hash: str) -> Image.Image:
    image, draw = canvas()
    centered(draw, "Checked forward alignment", 42, 35, bold=True)
    centered(draw, "forward_horizon_inputs(..., h = 1)", 92, 23, color=MUTED)
    xs = timeline(draw)
    draw.text((xs["Jan"] - 77, 185), "predictor: Jan", font=font(20, True), fill=TEXT)
    draw.text((xs["Feb"] - 73, 360), "target: Feb", font=font(20, True), fill=TEXT)
    arrow(draw, (xs["Jan"], 245), (xs["Feb"], 245), GREEN)
    centered(draw, "predictor_date < target_date is enforced", 420, 24, color=GREEN, bold=True)
    footer(draw, helper_hash)
    return image


def scene_metric(helper_hash: str) -> Image.Image:
    image, draw = canvas()
    centered(draw, "True MSPE keeps cancelling errors visible", 38, 34, bold=True)
    draw.rounded_rectangle((65, 115, 895, 420), radius=24, fill=PANEL, outline="#334269", width=2)
    draw.text((105, 145), "actual", font=font(22, True), fill=MUTED)
    draw.text((305, 145), "[0.5, 0.5]", font=font(25), fill=TEXT)
    draw.text((105, 190), "prediction", font=font(22, True), fill=MUTED)
    draw.text((305, 190), "[1.0, 0.0]", font=font(25), fill=TEXT)
    draw.text((105, 235), "errors", font=font(22, True), fill=MUTED)
    draw.text((305, 235), "[+0.5, -0.5]", font=font(25), fill=TEXT)
    draw.line((95, 285, 865, 285), fill="#334269", width=2)
    draw.text((105, 310), "(mean(error))²", font=font(23, True), fill=RED)
    draw.text((420, 310), "= 0.00   (cancels)", font=font(25), fill=RED)
    draw.text((105, 360), "mean(error²)", font=font(23, True), fill=GREEN)
    draw.text((420, 360), "= 0.25   (true MSPE)", font=font(25), fill=GREEN)
    footer(draw, helper_hash)
    return image


def scene_limits(helper_hash: str) -> Image.Image:
    image, draw = canvas()
    centered(draw, "What this check establishes", 55, 36, bold=True)
    draw.rounded_rectangle((90, 130, 870, 395), radius=24, fill=PANEL, outline="#334269", width=2)
    draw.text((135, 165), "✓  Target date is later than predictor date", font=font(24), fill=GREEN)
    draw.text((135, 215), "✓  MSPE is the mean of squared errors", font=font(24), fill=GREEN)
    draw.text((135, 280), "Not established:", font=font(23, True), fill=YELLOW)
    draw.text((135, 325), "regime accuracy, forecast skill, calibration, or trading returns", font=font(20), fill=TEXT)
    footer(draw, helper_hash)
    return image


def render() -> None:
    helper_hash = hashlib.sha256((ROOT / "forecast_evaluation.R").read_bytes()).hexdigest()
    scenes = [
        scene_title(helper_hash),
        scene_backward(helper_hash),
        scene_forward(helper_hash),
        scene_metric(helper_hash),
        scene_limits(helper_hash),
    ]
    frames: list[Image.Image] = []
    hold = 14
    transition = 4
    for index, scene in enumerate(scenes):
        frames.extend([scene.copy() for _ in range(hold)])
        if index + 1 < len(scenes):
            next_scene = scenes[index + 1]
            for step in range(1, transition + 1):
                frames.append(Image.blend(scene, next_scene, step / (transition + 1)))

    gif_path = OUTPUT_DIR / "evaluation-correction.gif"
    # GIF keeps one frame per scene with explicit holds. This is compact enough
    # for repository review while the MP4 retains the cross-fade animation.
    scenes[0].save(
        gif_path,
        save_all=True,
        append_images=scenes[1:],
        duration=[1800] * len(scenes),
        loop=0,
        optimize=True,
        disposal=2,
    )

    mp4_path = OUTPUT_DIR / "evaluation-correction.mp4"
    with tempfile.TemporaryDirectory(prefix="evaluation-demo-") as frame_dir:
        frame_dir_path = Path(frame_dir)
        for index, frame in enumerate(frames):
            frame.save(frame_dir_path / f"frame-{index:04d}.png")
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-framerate", str(FPS),
                "-i", str(frame_dir_path / "frame-%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-metadata", f"comment=main@{BASE_COMMIT}; helper-sha256:{helper_hash}; mechanics only",
                str(mp4_path),
            ],
            check=True,
        )

    print(f"wrote {gif_path.relative_to(ROOT)}")
    print(f"wrote {mp4_path.relative_to(ROOT)}")
    print(f"helper sha256 {helper_hash}")


if __name__ == "__main__":
    render()
