#!/usr/bin/python3
# -*- coding: utf-8 -*-
# wifi_status.py — Standalone WiFi status icon updater
# Uses partial e-ink refresh to update the upper-right corner
# without redrawing the full citation display.

import os
import sys
import socket
import argparse
from PIL import Image, ImageDraw

BASEDIR = os.path.dirname(os.path.realpath(__file__))
STATE_FILE = os.path.join(BASEDIR, "display_state.png")

# Same connectivity check as display.py
INTERNET_CHECK_HOST = ("1.1.1.1", 80)
INTERNET_CHECK_TIMEOUT = 3


def is_wifi_connected():
    """Returns True if internet is reachable (same rule as display.py)."""
    try:
        s = socket.socket()
        s.settimeout(INTERNET_CHECK_TIMEOUT)
        s.connect(INTERNET_CHECK_HOST)
        s.close()
        return True
    except Exception:
        try:
            s.close()
        except Exception:
            pass
        return False


def get_signal_strength():
    """Read WiFi signal strength from /proc/net/wireless. Returns 0-3 bars."""
    try:
        with open("/proc/net/wireless") as f:
            for line in f:
                if "wlan0" in line:
                    # Format: "wlan0: STATUS  LINK  LEVEL  NOISE ..."
                    parts = line.split()
                    dbm = float(parts[3].rstrip('.'))
                    if dbm >= -50:
                        return 3  # excellent
                    elif dbm >= -70:
                        return 2  # good
                    else:
                        return 1  # weak
    except Exception:
        pass
    return 0  # no signal / interface not found


def get_wifi_status():
    """Returns (connected: bool, bars: int 0-3)."""
    connected = is_wifi_connected()
    bars = get_signal_strength() if connected else 0
    return connected, bars


def draw_wifi_icon(draw, connected, bars=0):
    """Draw WiFi status icon at upper-right of the pre-rotation image.

    Args:
        draw: PIL ImageDraw instance
        connected: bool - internet reachable
        bars: int 0-3 - signal strength level
    """
    # Clear icon area (white fill to erase previous state)
    draw.rectangle([(232, 1), (248, 14)], fill="white")

    if not connected:
        # X mark
        draw.line([(235, 3), (245, 12)], fill="black", width=1)
        draw.line([(245, 3), (235, 12)], fill="black", width=1)
        return

    # 3 bars of increasing height; filled = active, outlined = inactive
    bar_coords = [
        (233, 9, 235, 13),   # short bar
        (238, 5, 240, 13),   # medium bar
        (243, 2, 246, 13),   # tall bar
    ]
    for i, (x0, y0, x1, y1) in enumerate(bar_coords):
        if i < bars:
            draw.rectangle([(x0, y0), (x1, y1)], fill="black")
        else:
            draw.rectangle([(x0, y0), (x1, y1)], outline="black")


def main(is_dev=False):
    connected, bars = get_wifi_status()
    print(f"WiFi: connected={connected}, bars={bars}")

    # Load existing display state or create blank image
    if os.path.exists(STATE_FILE):
        image = Image.open(STATE_FILE).convert('1')
    else:
        image = Image.new('1', (250, 122), 255)

    draw = ImageDraw.Draw(image)
    draw_wifi_icon(draw, connected, bars)
    image.save(STATE_FILE)

    if is_dev:
        image.save(os.path.join(BASEDIR, "wifi_output.png"))
        image.show()
    else:
        from waveshare_epd import epd2in13_V4
        epd = epd2in13_V4.EPD()
        epd.init()
        epd.displayPartial(epd.getbuffer(image.rotate(180)))
        epd.sleep()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", dest="IS_DEV", action="store_true",
                        help="Dev mode: save to wifi_output.png instead of hardware")
    args = parser.parse_args()
    main(is_dev=args.IS_DEV)
