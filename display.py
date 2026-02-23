#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import json
# import time
# import logging
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
# from fake_useragent import UserAgent
# ua = UserAgent(platforms='pc')
# user_agent = ua.random
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"
from scholarscrape import main as scrape
import time, socket, subprocess
from known_credentials import KNOWN_NETWORKS
from wifi_status import draw_wifi_icon, get_wifi_status


# ---
BASEDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
LOG_FILE = os.path.join(BASEDIR, "logs.json")
FONT_SMALL = ImageFont.truetype(os.path.join(BASEDIR, 'Font.ttc'), 22)
FONT_LARGE = ImageFont.truetype(os.path.join(BASEDIR, 'Font.ttc'), 80)
# ---
parser = argparse.ArgumentParser()
parser.add_argument("--dev", dest="IS_DEV", action="store_true", help="Dev mode: output image")
parser.add_argument("-s","--scholarid",dest="scholar_profile", help="Google Scholar ID")
args = parser.parse_args()
IS_DEV = args.IS_DEV
print("DEV", IS_DEV)
# ---
CONNECT_TIMEOUT = 15
INTERNET_CHECK_HOST = ("1.1.1.1", 80)
INTERNET_CHECK_TIMEOUT = 3
# ---

def _internet_reachable():
    try:
        s = socket.socket()
        s.settimeout(INTERNET_CHECK_TIMEOUT)
        s.connect(INTERNET_CHECK_HOST)
        s.close()
        return True
    except Exception:
        try: s.close()
        except Exception: pass
        return False

def _current_ssid():
    """Get the currently connected WiFi SSID, or None."""
    try:
        result = subprocess.run(
            ["iwgetid", "-r"], capture_output=True, text=True, timeout=5
        )
        ssid = result.stdout.strip()
        return ssid if ssid else None
    except Exception:
        return None

def _scan_networks():
    """Scan for available WiFi networks.
    Returns list of (ssid, signal, security) sorted by signal strength.
    signal: int 0-100. security: str, empty string for open networks.
    """
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY",
             "dev", "wifi", "list", "--rescan", "yes"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        networks = []
        seen = set()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.rsplit(':', 2)
            if len(parts) < 3:
                continue
            ssid, signal_str, security = parts
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)
            try:
                signal = int(signal_str)
            except ValueError:
                signal = 0
            networks.append((ssid, signal, security))
        networks.sort(key=lambda x: x[1], reverse=True)
        return networks
    except Exception:
        return []

def _connect_to(ssid, password=None):
    """Connect to a WiFi network via nmcli. Returns True if internet reachable after."""
    try:
        cmd = ["nmcli", "dev", "wifi", "connect", ssid]
        if password:
            cmd += ["password", password]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=CONNECT_TIMEOUT
        )
        if result.returncode != 0:
            print(f"nmcli connect failed for {ssid}: {result.stderr.strip()}")
            return False
        time.sleep(2)
        return _internet_reachable()
    except Exception:
        return False

def connect_wifi():
    """Connect to WiFi. Priority: existing > open networks > known networks.
    Returns (success: bool, ssid: str or None).
    """
    # 1) Already connected with internet? Keep it.
    if _internet_reachable():
        ssid = _current_ssid()
        return True, ssid or "connected"

    # 2) Scan and try open networks (strongest signal first)
    networks = _scan_networks()
    for ssid, signal, security in networks:
        if security:
            continue
        print(f"Trying open network: {ssid} (signal {signal})")
        if _connect_to(ssid):
            return True, ssid

    # 3) Try known/hardcoded networks
    for ssid, password in KNOWN_NETWORKS:
        print(f"Trying known network: {ssid}")
        if _connect_to(ssid, password=password):
            return True, ssid

    return False, None

def disconnect_wifi():
    """Disconnect WiFi to save battery."""
    try:
        subprocess.run(
            ["nmcli", "dev", "disconnect", "wlan0"],
            capture_output=True, timeout=5
        )
    except Exception:
        pass





class FAKE_EPD:
    def __init__(self, width, height):
        self.width = width
        self.height = height

if not IS_DEV:
    try:
        from waveshare_epd import epd2in13_V4
        epd = epd2in13_V4.EPD()
        IS_PI = True
    except Exception:
        IS_DEV = True

if IS_DEV:
    IS_PI = False
    epd = FAKE_EPD(width=250, height=122)
print("IS_PI", IS_PI)






class DISPLAY:
  def __init__(self, epd, is_pi=False):
    self.epd = epd
    self.is_pi = is_pi
    if is_pi:
      self.image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
    else:
      self.image = Image.new('1', (self.epd.width, self.epd.height), 255)  # 255: clear the frame

  def render(self, citations, hindex, diff, weekly_increase, monthly_increase, fiveyears):
    # image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([(2,2),(248,120)], outline=0)
    # draw.text((32, 3), citations, font=FONT_LARGE, fill=0)
    # draw.text((95, 90), f"h = {hindex}", font=FONT_SMALL, fill=0)
    # image.save("output.png")
    # image.show()
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([(2,2),(248,120)], outline=0)
    # draw.text((32, 3), citations, font=FONT_LARGE, fill=0)
    # draw.text((95, 90), f"h = {hindex}", font=FONT_SMALL, fill=0)
    draw = ImageDraw.Draw(self.image)

    draw.rectangle([(1,1),(249,121)], outline=0)
    # draw.rectangle([(0,0),(250,122)], outline=0)

    draw.text((5, 0), str(citations), font=FONT_LARGE, fill=0)

    # draw.line([(2,90), (185,90)])
    # draw.line([(185,2),(185,120)])

    # draw.text((5, 90), f"h = {hindex}", font=FONT_SMALL, fill=0)
    draw.text((195, 15), f"h.{str(hindex)}", font=FONT_SMALL, fill=0)

    # dev
    if monthly_increase['citations_increase'] is None: monthly_increase['citations_increase'] = 0

    try: dsign = '+' if diff >= 0 else '-'
    except: dsign = ' '
    try: wsign = '+' if weekly_increase['citations_increase'] >= 0 else '-'
    except: wsign = ' '
    # try: bisign = '+' if biweekly_increase['citations_increase'] >= 0 else '-'
    # except: bisign = ' '
    try: msign = '+' if monthly_increase['citations_increase'] >= 0 else '-'
    except: msign = ' '

    longtext = f"{dsign}{str(abs(diff))}  w{wsign}{str(abs(weekly_increase['citations_increase']))}  m{msign}{str(abs(monthly_increase['citations_increase']))}"
    draw.text((15, 92), longtext, font=FONT_SMALL, fill=0)
    # draw.text((15, 90), f"{dsign}{str(diff)}", font=FONT_SMALL, fill=0)
    # try:
    #   draw.text((65, 90), f"w{wsign}{str(weekly_increase['citations_increase'])}", font=FONT_SMALL, fill=0)
    # except: pass
    # try:
    #   draw.text((110, 90), f"b{bisign}{str(biweekly_increase['citations_increase'])}", font=FONT_SMALL, fill=0)
    # except: pass
    # try:
    #   draw.text((165, 90), f"m{msign}{str(monthly_increase['citations_increase'])}", font=FONT_SMALL, fill=0)
    # except: pass

    barw, pad, H = 5, 5, 65
    minv, maxv = min(fiveyears), max(fiveyears)
    for i, y in enumerate(fiveyears):
        x0 = 190 + pad + i*(barw+pad)
        x1 = x0 + barw
        y1 = 115
        scale = (y - minv) / (maxv - minv) if maxv > minv else 0
        y0 = y1 - int(H * scale)
        draw.rectangle([(x0, y0), (x1, y1)], fill="black", outline=0)

    # Draw WiFi status icon in upper-right corner
    connected, bars = get_wifi_status()
    draw_wifi_icon(draw, connected, bars)

    # Save pre-rotation image for wifi_status.py partial updates
    self.image.save(os.path.join(BASEDIR, "display_state.png"))

    if self.is_pi:
      self.image = self.image.rotate(180) # rotate
      self.epd.init()
      self.epd.Clear(0xFF)
      self.epd.displayPartBaseImage(epd.getbuffer(self.image))
      self.epd.sleep()
    else:
      self.image.save("output.png")
      self.image.show()





# Compute increases
def compute_increase(latest, past_log):
  if latest and past_log:
    return {
      "citations_increase": latest["citations"] - past_log["citations"],
      "hindex_increase": latest["hindex"] - past_log["hindex"]
    }
  return {"citations_increase": 0, "hindex_increase": 0}

# Function to get the closest log entry before a given time
def get_closest_log(past_time, logs):
  return max((log for log in logs if log["timestamp"] <= past_time), 
    key=lambda x: x["timestamp"], default=None)

def get_earliest_log(past_time, logs):
    eligible = [log for log in logs if log["timestamp"] <= past_time]
    if not eligible:
        return logs[0]  # fallback to oldest
    return max(eligible, key=lambda x: x["timestamp"])



def scrape_and_display(scholar_profile):
  res = scrape(["-s", scholar_profile])
  fiveyears = res['yearlycitations'][-5:]
  print("Last five years", fiveyears)

  # Load logs
  try:
      with open(LOG_FILE, "r") as f: logs = json.load(f)
  except FileNotFoundError:
      logs = []

  # Convert timestamps to datetime objects and sort by time
  for log in logs: log["timestamp"] = datetime.fromisoformat(log["timestamp"])
  logs.sort(key=lambda x: x["timestamp"])

  # Get latest values
  try: latest = logs[-1]
  except: latest = None
  try: second = logs[-2]
  except: second = None

  # check if changes
  if (latest is None) or (second is None):
    print("Not enough log entries. Exiting.")
    sys.exit()

  citations = str(latest["citations"])
  hindex = str(latest["hindex"])

  # time windows
  now = datetime.now()
  log_week = get_closest_log(now - timedelta(weeks=1), logs)
  log_biweek = get_closest_log(now - timedelta(weeks=2), logs)
  log_month = get_earliest_log(now - timedelta(days=30), logs)

  weekly_increase = compute_increase(latest, log_week)
  biweekly_increase = compute_increase(latest, log_biweek)
  monthly_increase = compute_increase(latest, log_month)

  if latest['citations'] == second['citations']:
    ### NOTHING NEW
    print(f'No changes [{latest["citations"]} citations]')
    diff = 0

  else:
    ### NEW CITATIONS
    diff = latest['citations'] - second['citations']
    print(f"{diff} new citations!")

    # Print results
    print("Weekly Increase:", weekly_increase)
    print("Biweekly Increase:", biweekly_increase)
    print("Monthly Increase:", monthly_increase)

    # update the display
    # print("Update display...")
    epaper = DISPLAY(epd=epd, is_pi=IS_PI)
    epaper.render(citations, hindex, diff, weekly_increase, monthly_increase, fiveyears)

  # DEV = always pop up image on PC
  if not IS_PI or IS_DEV:
    # output an image
    print("Output image...")
    epaper = DISPLAY(epd=epd, is_pi=IS_PI)
    print('citations', citations, 'hindex', hindex, 'diff', diff, 'weekly_increase', weekly_increase, 'monthly_increase', monthly_increase, 'fiveyears', fiveyears)
    epaper.render(citations, hindex, diff, weekly_increase, monthly_increase, fiveyears)




def main(scrape_callback, scholar_profile, disconnect_after=True):
    ok, used = connect_wifi()
    if not ok: return False, "no-network"
    try: scrape_callback(scholar_profile)
    finally:
        if disconnect_after: disconnect_wifi()
    return True, used


if __name__ == "__main__":
    ok, wifi_ssid = main(scrape_and_display, args.scholar_profile)
    if ok: print("Success, used:", wifi_ssid)
    else: print("Failed to get network:", wifi_ssid)


