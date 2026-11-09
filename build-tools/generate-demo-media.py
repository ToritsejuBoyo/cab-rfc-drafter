#!/usr/bin/env python3
"""
generate-demo-media.py - Generates demo.gif and demo.mp4 for cab-rfc-drafter.
Simulates terminal interaction, RFC readiness evaluation, risk calculation, and ITSM ticket output.
Zero external dependencies other than Pillow and local ffmpeg.
"""

import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

WIDTH, HEIGHT = 1000, 620
BG_COLOR = (15, 23, 42)        # Slate-900
HEADER_COLOR = (30, 41, 59)    # Slate-800
BORDER_COLOR = (51, 65, 85)    # Slate-700
TEXT_MAIN = (241, 245, 249)    # Slate-100
TEXT_MUTED = (148, 163, 184)   # Slate-400
TEXT_ACCENT = (56, 189, 248)   # Sky-400
TEXT_GREEN = (74, 222, 128)    # Green-400
TEXT_YELLOW = (250, 204, 21)   # Yellow-400
TEXT_RED = (248, 113, 113)     # Red-400
TEXT_BORDER_COLOR = (51, 65, 85) # Slate-700

try:
    FONT_REGULAR = ImageFont.truetype("consola.ttf", 15)
    FONT_BOLD = ImageFont.truetype("consolab.ttf", 15)
    FONT_TITLE = ImageFont.truetype("consolab.ttf", 16)
except Exception:
    FONT_REGULAR = ImageFont.load_default()
    FONT_BOLD = FONT_REGULAR
    FONT_TITLE = FONT_REGULAR


def draw_window_frame(draw: ImageDraw.ImageDraw, title: str):
    """Draw professional terminal header with control buttons."""
    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=BG_COLOR)
    draw.rectangle([0, 0, WIDTH, 38], fill=HEADER_COLOR)
    draw.line([(0, 38), (WIDTH, 38)], fill=BORDER_COLOR, width=1)

    # Mac/terminal window dots
    draw.ellipse([14, 13, 26, 25], fill=(239, 68, 68))   # Red
    draw.ellipse([34, 13, 46, 25], fill=(234, 179, 8))   # Yellow
    draw.ellipse([54, 13, 66, 25], fill=(34, 197, 94))   # Green

    draw.text((WIDTH // 2 - 180, 10), title, font=FONT_TITLE, fill=TEXT_MUTED)


def create_terminal_frames() -> list:
    frames = []

    content_states = [
        # Frame 1: Command prompt
        [
            ("user@edge-bastion:~$ ", TEXT_ACCENT),
            ("python3 ./scripts/validate_rfc_readiness.py --input rfc-core-fw.json --sanitize", TEXT_MAIN)
        ],
        # Frame 2: Executing
        [
            ("user@edge-bastion:~$ ", TEXT_ACCENT),
            ("python3 ./scripts/validate_rfc_readiness.py --input rfc-core-fw.json --sanitize", TEXT_MAIN),
            ("", TEXT_MAIN),
            ("[*] Loading RFC document: 'Core Edge Firewall HA Firmware Upgrade'...", TEXT_MUTED),
            ("[*] Applying Rule 4 client-side data sanitization (SHA-256 + RFC 5737)...", TEXT_MUTED),
            ("[+] All 9 mandatory ITIL 4 sections verified present.", TEXT_GREEN)
        ],
        # Frame 3: Risk Calculation
        [
            ("user@edge-bastion:~$ ", TEXT_ACCENT),
            ("python3 ./scripts/validate_rfc_readiness.py --input rfc-core-fw.json --sanitize", TEXT_MAIN),
            ("", TEXT_MAIN),
            ("[*] Loading RFC document: 'Core Edge Firewall HA Firmware Upgrade'...", TEXT_MUTED),
            ("[+] All 9 mandatory ITIL 4 sections verified present.", TEXT_GREEN),
            ("", TEXT_MAIN),
            ("=======================================================================", TEXT_BORDER_COLOR),
            ("  ITIL 4 CHANGE ADVISORY BOARD (CAB) EVALUATION REPORT", TEXT_ACCENT),
            ("=======================================================================", TEXT_BORDER_COLOR),
            ("RFC Reference     : RFC-2026-11-049 (Target: fw-edge-node01/02)", TEXT_MAIN),
            ("Readiness Score   : 100.0% [CAB READY: YES]", TEXT_GREEN),
            ("CAB Recommendation: APPROVED FOR CAB SUBMISSION", TEXT_GREEN),
            ("Calculated Risk   : HIGH RISK (Score: 7/12 | Tier: MAJOR CHANGE)", TEXT_YELLOW),
            ("  - User Impact Scope    : 3/3 (Enterprise-wide perimeter)", TEXT_MUTED),
            ("  - Service Redundancy   : 1/3 (Active-passive HA pair)", TEXT_MUTED),
            ("  - Reversibility        : 1/3 (Instant cluster failback < 10m)", TEXT_MUTED),
            ("  - Operational Precedent: 2/3 (Staging deployment validated)", TEXT_MUTED)
        ],
        # Frame 4: Window Arithmetic & Rollback
        [
            ("user@edge-bastion:~$ ", TEXT_ACCENT),
            ("python3 ./scripts/validate_rfc_readiness.py --input rfc-core-fw.json --sanitize", TEXT_MAIN),
            ("", TEXT_MAIN),
            ("=======================================================================", TEXT_BORDER_COLOR),
            ("  ITIL 4 CHANGE ADVISORY BOARD (CAB) EVALUATION REPORT", TEXT_ACCENT),
            ("=======================================================================", TEXT_BORDER_COLOR),
            ("RFC Reference     : RFC-2026-11-049 (Target: fw-edge-node01/02)", TEXT_MAIN),
            ("Readiness Score   : 100.0% [CAB READY: YES]", TEXT_GREEN),
            ("CAB Recommendation: APPROVED FOR CAB SUBMISSION", TEXT_GREEN),
            ("Calculated Risk   : HIGH RISK (Score: 7/12 | Tier: MAJOR CHANGE)", TEXT_YELLOW),
            ("", TEXT_MAIN),
            ("TEMPORAL WINDOW ARITHMETIC AUDIT:", TEXT_ACCENT),
            ("  - Scheduled Maintenance Window : 120 mins (01:00 to 03:00 UTC)", TEXT_MAIN),
            ("  - Planned Implementation Time  : 60 mins (4 procedural steps)", TEXT_MAIN),
            ("  - Estimated Rollback Duration  : 20 mins (cluster backout)", TEXT_MAIN),
            ("  - Total Active Duration        : 80 mins", TEXT_MAIN),
            ("  - Safety Headroom Buffer       : 40 mins (33.3% contingency reserve)", TEXT_GREEN),
            ("  - Go / No-Go Decision Cutoff   : 02:15:00 UTC [VALIDATED]", TEXT_GREEN),
            ("", TEXT_MAIN),
            ("ROLLBACK TRIGGER & VERIFICATION STATUS:", TEXT_ACCENT),
            ("  - Trigger Condition: Ping packet loss > 5% for > 3m or IPsec tunnel down", TEXT_MUTED),
            ("  - Pre-Check Count  : 3 verified baseline commands recorded", TEXT_GREEN),
            ("  - Post-Check Count : 3 post-change verification tests configured", TEXT_GREEN),
            ("=======================================================================", TEXT_BORDER_COLOR),
            ("[CAB VERDICT] RFC package is technically sound, verified, and audit-ready.", TEXT_GREEN)
        ]
    ]

    durations = [1200, 1400, 2500, 4500]

    for state, dur in zip(content_states, durations):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        draw_window_frame(draw, "cab-rfc-drafter — bash (read-only audit)")

        y = 52
        for line_item in state:
            if isinstance(line_item, tuple):
                text, color = line_item
                draw.text((20, y), text, font=FONT_REGULAR, fill=color)
                y += 22
            else:
                y += 22
        frames.append((img, dur))

    return frames


def build_media():
    print("[*] Generating terminal animation frames...")
    frames = create_terminal_frames()

    gif_path = os.path.join(ASSETS_DIR, "demo.gif")
    mp4_path = os.path.join(ASSETS_DIR, "demo.mp4")

    # Save animated GIF
    imgs = [f[0] for f in frames]
    durs = [f[1] for f in frames]

    imgs[0].save(
        gif_path,
        save_all=True,
        append_images=imgs[1:],
        duration=durs,
        loop=0,
        optimize=True
    )
    print(f"[+] Successfully generated GIF: {gif_path} ({os.path.getsize(gif_path) / 1024:.1f} KB)")

    # Save frames to temp directory for ffmpeg
    temp_dir = os.path.join(BASE_DIR, "build-tools", "temp_frames")
    os.makedirs(temp_dir, exist_ok=True)

    frame_idx = 0
    fps = 30
    for img, dur in frames:
        count = int((dur / 1000.0) * fps)
        for _ in range(count):
            img.save(os.path.join(temp_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(temp_dir, "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        mp4_path
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[+] Successfully generated MP4: {mp4_path} ({os.path.getsize(mp4_path) / 1024:.1f} KB)")
    except Exception as e:
        print(f"[WARN] ffmpeg conversion failed: {e}")
    finally:
        # Cleanup temp frames
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        os.rmdir(temp_dir)


if __name__ == "__main__":
    build_media()
